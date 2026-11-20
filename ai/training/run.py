"""End-to-end training & evaluation run (AI-02 ... AI-11).

    python -m ai.training.run                       # real data in data/processed/
    python -m ai.training.run --synthetic           # dry run on generated events

Steps: load -> leakage audit -> visitor-aware temporal split -> tune every
candidate on validation PR-AUC -> optional Platt calibration (fitted on
train out-of-fold) -> pick the served model on validation -> choose the
operating threshold on validation -> evaluate ALL models once on the
untouched test split -> ablation without label-defining features ->
explanations -> write reviewable outputs + model artifact.

Real-data outputs go to ai/evaluation/ (tracked, small) and the model binary
to ai/models/ (ignored). Synthetic runs go to data/processed/ai_dryrun/ and
can never overwrite ai/evaluation/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn

from ..evaluation import explain as ex
from ..evaluation.metrics import bootstrap_ci, calibration_bins, classification_metrics, expected_calibration_error
from ..evaluation.threshold import choose_threshold, threshold_table
from . import config
from .data import build_supervised, feature_set, is_synthetic, load_observed_through, merge_features_labels, read_table, to_matrix
from .models import PlattCalibrated, candidates, fit_candidate
from .split import export_benchmark_csv, manifest, plan_split, split_frames


def _artifact_path(path: Path) -> str:
    """Keep committed run manifests portable across team machines."""
    try:
        return path.resolve().relative_to(config.ROOT.resolve()).as_posix()
    except ValueError:
        return f"external/{path.name}"


def _sha256(path: Path) -> str | None:
    if not path or not Path(path).exists():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _json(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return None if np.isnan(obj) else float(obj)
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    raise TypeError(type(obj).__name__)


def _r(v, n=4):
    return None if v is None else round(float(v), n)


def _xy(part: pd.DataFrame, features):
    return to_matrix(part, features), part["y"].astype(int)


# --------------------------------------------------------------------------- main run
def run(features_path=None, labels_path=None, out_dir: Path | None = None, model_path: Path | None = None,
        synthetic: bool = False, label_task: str = config.DEFAULT_LABEL_TASK,
        primary_set: str = config.PRIMARY_FEATURE_SET, include_optional: bool = False,
        val_weeks=None, test_weeks=None, visitor_fractions=None, visitor_disjoint: bool = True, n_boot: int = 500,
        merged: pd.DataFrame | None = None, make_figures: bool = True) -> dict:
    t0 = datetime.now(timezone.utc)
    features_path = Path(features_path or config.FEATURES_PATH)
    labels_path = Path(labels_path or config.LABELS_PATH)
    if merged is None:
        merged = merge_features_labels(read_table(features_path), read_table(labels_path))
    synthetic = synthetic or is_synthetic(merged)
    out_dir = Path(out_dir or (config.DRYRUN_DIR if synthetic else config.EVALUATION_DIR))
    if synthetic and out_dir.resolve() == config.EVALUATION_DIR.resolve():
        raise ValueError("Refusing to write synthetic results into ai/evaluation/")
    model_path = Path(model_path or (out_dir / "ghost_model.joblib" if synthetic else config.MODEL_PATH))
    fig_dir = out_dir / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- data, audit, split ------------------------------------------------
    observed_through = load_observed_through()
    data = build_supervised(merged, label_task, observed_through)
    plan = plan_split(data, val_weeks, test_weeks, visitor_fractions, visitor_disjoint=visitor_disjoint)
    parts = split_frames(data, plan)
    feats = feature_set(data, primary_set)
    split_info = manifest(data, parts, plan, feats, label_task)
    (Xtr, ytr), (Xva, yva), (Xte, yte) = (_xy(parts[k], feats) for k in ("train", "validation", "test"))
    groups_tr, groups_te = parts["train"]["customer_id"].to_numpy(), parts["test"]["customer_id"].to_numpy()
    print(f"[split] {plan.version}: " + ", ".join(f"{k}={v['rows']} rows/{v['positives']} ghost"
                                                  for k, v in split_info["splits"].items()), flush=True)

    # ---- fit & tune every candidate on validation (AI-02, 05, 06, 07, 08) ---
    fitted, tuning = {}, []
    for cand in candidates(include_optional, has_eds="feature_eds" in feats):
        f = fit_candidate(cand, feats, Xtr, ytr, Xva, yva)
        fitted[cand.name] = f
        tuning += f.tuning
        print(f"[fit] {cand.name:24s} val PR-AUC={f.val_pr_auc:.4f} params={f.params}", flush=True)

    servable = {k: v for k, v in fitted.items() if v.candidate.family in ("linear", "tree", "boosting")}
    best_name = max(servable, key=lambda k: servable[k].val_pr_auc)
    best = servable[best_name]

    # ---- calibration (fit on train OOF only, keep if validation Brier improves)
    raw_brier = float(np.mean((best.estimator.predict_proba(Xva)[:, 1] - yva) ** 2))
    calibrated = PlattCalibrated(best.candidate.build(feats, best.params)).fit(Xtr, ytr, groups=groups_tr)
    cal_brier = float(np.mean((calibrated.predict_proba(Xva)[:, 1] - yva) ** 2))
    use_cal = cal_brier < raw_brier
    final = calibrated if use_cal else best.estimator
    calibration_note = {"method": "Platt on visitor-grouped train out-of-fold scores",
                        "val_brier_raw": _r(raw_brier, 5), "val_brier_calibrated": _r(cal_brier, 5),
                        "applied": bool(use_cal)}
    final_name = best_name + ("+platt" if use_cal else "")

    # ---- threshold on validation (AI-10) ----------------------------------
    val_scores = final.predict_proba(Xva)[:, 1]
    t_table = threshold_table(yva, val_scores)
    t_choice = choose_threshold(t_table)
    thr = t_choice["operating_threshold"]

    stamp = hashlib.sha256((plan.version + final_name + json.dumps(best.params, sort_keys=True, default=str)
                            + str(_sha256(features_path))).encode()).hexdigest()[:8]
    model_version = f"ghost-{best_name.replace('_', '-')}-{'cal-' if use_cal else ''}{stamp}"
    if synthetic:
        model_version = "synthetic-" + model_version

    # ---- evaluate every model once on test (AI-09) -------------------------
    rows, comparison, cis = [], [], {}
    scored = {name: f.estimator for name, f in fitted.items()}
    scored[final_name] = final
    for name, est in scored.items():
        cand = fitted[name.split("+")[0]].candidate
        prob = cand.probabilistic
        sv, st = est.predict_proba(Xva)[:, 1], est.predict_proba(Xte)[:, 1]
        own_thr = thr if name == final_name else choose_threshold(threshold_table(yva, sv))["operating_threshold"]
        version = model_version if name == final_name else f"{name}@{plan.version[:28]}"
        for split, y, s in (("validation", yva, sv), ("test", yte, st)):
            m = classification_metrics(y, s, own_thr, probabilistic=prob)
            rows.append({"name": name, "model_version": version, "split": split, "support": m["support"],
                         "prevalence": _r(m["prevalence"]), "threshold": own_thr, "precision": _r(m["precision"]),
                         "recall": _r(m["recall"]), "f1": _r(m["f1"]), "roc_auc": _r(m["roc_auc"]),
                         "pr_auc": _r(m["pr_auc"]), "brier": _r(m["brier"])})
        cis[name] = bootstrap_ci(yte, st, groups_te, own_thr, n_boot=n_boot)
        test_row = rows[-1]
        comparison.append({"name": name, "family": cand.family, "feature_set": primary_set,
                           "selected": name == final_name, "probabilistic": prob,
                           "val_pr_auc": rows[-2]["pr_auc"], "test_pr_auc": test_row["pr_auc"],
                           "test_pr_auc_ci95": (cis.get(name) or {}).get("pr_auc"),
                           "test_roc_auc": test_row["roc_auc"], "test_f1": test_row["f1"],
                           "test_recall": test_row["recall"], "test_precision": test_row["precision"],
                           "test_brier": test_row["brier"], "threshold": own_thr,
                           "params": fitted[name.split('+')[0]].params})

    test_scores = final.predict_proba(Xte)[:, 1]
    final_test = classification_metrics(yte, test_scores, thr)
    cal_bins = calibration_bins(yte, test_scores)

    # ---- ablation: circularity diagnostic --------------------------------------
    ablation = []
    for set_name in config.FEATURE_SETS:
        try:
            fs = feature_set(data, set_name)
        except ValueError as exc:
            ablation.append({"feature_set": set_name, "note": str(exc)})
            continue
        Xa_tr, Xa_va, Xa_te = (to_matrix(parts[k], fs) for k in ("train", "validation", "test"))
        for fam_name in ([best_name, "logistic_regression"] if best_name != "logistic_regression" else [best_name]):
            c = fitted[fam_name].candidate
            est = c.build(fs, fitted[fam_name].params).fit(Xa_tr, ytr)
            ablation.append({"feature_set": set_name, "model": fam_name, "n_features": len(fs),
                             "val_pr_auc": _r(classification_metrics(yva, est.predict_proba(Xa_va)[:, 1], .5)["pr_auc"]),
                             "test_pr_auc": _r(classification_metrics(yte, est.predict_proba(Xa_te)[:, 1], .5)["pr_auc"]),
                             "test_roc_auc": _r(classification_metrics(yte, est.predict_proba(Xa_te)[:, 1], .5)["roc_auc"])})
    for a in ablation:
        comparison.append({"name": f"ablation:{a.get('model', '-')}", "feature_set": a["feature_set"], **a})

    # ---- explanations (AI-11) -------------------------------------------------
    baseline = {k: (None if pd.isna(v) else float(v)) for k, v in Xtr.median().items()}
    perm = ex.permutation_table(final, Xva, yva)
    attr = ex.attribution_summary(final, Xte, baseline)
    shap_tab, shap_note = ex.shap_table(final, Xte, best.candidate.family)
    logit = fitted.get("logistic_regression")
    coef = ex.logistic_coefficients(logit.estimator, feats) if logit else None

    # ---- write outputs ------------------------------------------------------------
    notice = (config.SYNTHETIC_NOTICE + ". " if synthetic else "") + config.DATASET_NOTICE + \
        f" Label task {label_task}; split {plan.version}; threshold chosen on validation."
    metrics_payload = {
        "models": rows,
        "comparison": comparison,
        "evaluation_context": {"model_version": model_version, "split": "test", "threshold": thr},
        "confusion_matrix": final_test["confusion_matrix"],
        "calibration": cal_bins,
        "dataset_notice": notice,
    }
    (out_dir / "metrics.json").write_text(json.dumps(metrics_payload, indent=2, default=_json), encoding="utf-8")
    (out_dir / "split_manifest.json").write_text(json.dumps(split_info, indent=2, default=_json), encoding="utf-8")
    pd.DataFrame(comparison[:len(scored)]).to_csv(out_dir / "model_comparison.csv", index=False)
    pd.DataFrame(tuning).to_csv(out_dir / "tuning.csv", index=False)
    pd.DataFrame(ablation).to_csv(out_dir / "ablation.csv", index=False)
    t_table.to_csv(out_dir / "threshold_study.csv", index=False)
    perm.to_csv(out_dir / "permutation_importance.csv", index=False)
    attr.to_csv(out_dir / "attribution_summary.csv", index=False)
    if shap_tab is not None:
        shap_tab.to_csv(out_dir / "shap_importance.csv", index=False)
    else:
        (out_dir / "shap_importance.csv").unlink(missing_ok=True)
    if coef is not None:
        coef.to_csv(out_dir / "logistic_coefficients.csv", index=False)

    summary = {
        "pipeline_version": config.PIPELINE_VERSION, "generated_utc": t0.isoformat(),
        "synthetic": synthetic, "label_task": label_task, "label_spec": config.LABEL_TASKS[label_task],
        "label_version": str(merged["label_version"].iloc[0]) if "label_version" in merged else None,
        "scenario_id": str(merged["scenario_id"].iloc[0]) if "scenario_id" in merged else None,
        "observed_through": observed_through.isoformat(),
        "inputs": {"features": _artifact_path(features_path), "features_sha256": _sha256(features_path),
                   "labels": _artifact_path(labels_path), "labels_sha256": _sha256(labels_path)},
        "environment": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                        "pandas": pd.__version__, "numpy": np.__version__},
        "split_version": plan.version, "primary_feature_set": primary_set, "features": feats,
        "selected_model": {"name": final_name, "model_version": model_version, "params": best.params,
                           "selected_on": "validation PR-AUC among linear/tree/boosting models",
                           "calibration": calibration_note},
        "threshold": t_choice,
        "test": {k: final_test[k] for k in final_test},
        "test_ece": _r(expected_calibration_error(cal_bins), 5),
        "bootstrap_ci_test": cis,
        "explanations": {"permutation": "validation PR-AUC drop, 10 repeats",
                         "local": "baseline replacement (train medians), probability points",
                         "shap": shap_note},
    }
    (out_dir / "run_summary.json").write_text(json.dumps(summary, indent=2, default=_json), encoding="utf-8")

    if make_figures:
        _figures(fig_dir, scored, final_name, Xte, yte, cal_bins, t_table, thr, perm, final_test)

    # ---- model artifact + benchmark CSV ------------------------------------------
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "model": final, "features": feats, "model_version": model_version, "label_task": label_task,
        "label_version": summary["label_version"], "scenario_id": summary["scenario_id"],
        "split_version": plan.version, "threshold": t_choice, "baseline": baseline,
        "attribution_method": "baseline_replacement_train_median", "synthetic": synthetic,
        "dataset_notice": notice, "created_utc": t0.isoformat(), "sklearn": sklearn.__version__,
    }, model_path)
    (out_dir / "model_meta.json").write_text(json.dumps({
        "model_version": model_version, "path": _artifact_path(model_path), "sha256": _sha256(model_path),
        "features": feats, "threshold": t_choice, "split_version": plan.version}, indent=2, default=_json),
        encoding="utf-8")
    if label_task == "ghost_vs_active" and visitor_disjoint:
        csv_dir = config.DRYRUN_DIR if synthetic else config.PROCESSED_DIR
        csv_dir.mkdir(parents=True, exist_ok=True)
        export_benchmark_csv(parts, feats, csv_dir / "modeling_snapshots.csv")
    print(f"[done] {model_version}: test PR-AUC={final_test['pr_auc']:.4f} "
          f"(prevalence {final_test['prevalence']:.3f}), threshold={thr}", flush=True)
    return summary


# --------------------------------------------------------------------------- figures
def _figures(fig_dir, scored, final_name, Xte, yte, cal_bins, t_table, thr, perm, final_test):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import precision_recall_curve, roc_curve

    fig_dir.mkdir(parents=True, exist_ok=True)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.5))
    for name, est in scored.items():
        if name.startswith(("svm", "isolation", "majority")):
            continue  # rank-only or constant scores; prevalence line is the no-skill reference
        s = est.predict_proba(Xte)[:, 1]
        p, r, _ = precision_recall_curve(yte, s)
        f, t, _ = roc_curve(yte, s)
        lw = 2.4 if name == final_name else 1.1
        a1.plot(r, p, lw=lw, label=name)
        a2.plot(f, t, lw=lw, label=name)
    a1.axhline(yte.mean(), ls="--", c="grey", lw=1, label="no-skill (prevalence)")
    a1.set(xlabel="Recall", ylabel="Precision", title="Precision-Recall (test)")
    a2.plot([0, 1], [0, 1], ls="--", c="grey", lw=1)
    a2.set(xlabel="False positive rate", ylabel="True positive rate", title="ROC (test)")
    a1.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(fig_dir / "model_pr_roc.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(4.8, 4.5))
    ax.plot([0, 1], [0, 1], ls="--", c="grey", lw=1)
    ax.plot([b["mean_predicted"] for b in cal_bins], [b["observed_rate"] for b in cal_bins], "o-")
    ax.set(xlabel="Mean predicted", ylabel="Observed Ghost rate", title=f"Calibration (test) {final_name}")
    fig.tight_layout()
    fig.savefig(fig_dir / "model_calibration.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4.2))
    ax.plot(t_table.threshold, t_table.precision, label="precision")
    ax.plot(t_table.threshold, t_table.recall, label="recall")
    ax.plot(t_table.threshold, t_table.f1, label="F1")
    ax.axvline(thr, c="k", ls=":", label=f"operating {thr:.2f}")
    ax.set(xlabel="Threshold", title="Threshold study (validation)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(fig_dir / "model_threshold.png", dpi=150)
    plt.close(fig)

    cm = np.array(final_test["confusion_matrix"])
    fig, ax = plt.subplots(figsize=(4, 3.6))
    ax.imshow(cm, cmap="Blues")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, cm[i, j], ha="center", va="center")
    ax.set(xticks=[0, 1], yticks=[0, 1], xticklabels=["pred active", "pred ghost"],
           yticklabels=["active", "ghost"], title=f"Confusion matrix (test, t={thr:.2f})")
    fig.tight_layout()
    fig.savefig(fig_dir / "model_confusion_matrix.png", dpi=150)
    plt.close(fig)

    top = perm.head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=(6.5, 5))
    ax.barh(top.feature.str.removeprefix("feature_"), top.pr_auc_drop_mean, xerr=top.pr_auc_drop_sd)
    ax.set(xlabel="PR-AUC drop when permuted (validation)", title="Permutation importance")
    fig.tight_layout()
    fig.savefig(fig_dir / "shap_or_permutation_importance.png", dpi=150)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--features", type=Path)
    p.add_argument("--labels", type=Path)
    p.add_argument("--out", type=Path)
    p.add_argument("--model-path", type=Path)
    p.add_argument("--synthetic", action="store_true", help="generate events and run Lâm's pipeline in memory")
    p.add_argument("--synthetic-visitors", type=int, default=1500)
    p.add_argument("--label-task", default=config.DEFAULT_LABEL_TASK, choices=list(config.LABEL_TASKS))
    p.add_argument("--feature-set", default=config.PRIMARY_FEATURE_SET, choices=config.FEATURE_SETS)
    p.add_argument("--optional-models", action="store_true", help="also run SVM and Isolation Forest (AI-08)")
    p.add_argument("--val-weeks", type=int)
    p.add_argument("--test-weeks", type=int)
    p.add_argument("--visitor-fractions", type=float, nargs=3, metavar=("TRAIN", "VAL", "TEST"))
    p.add_argument("--no-visitor-disjoint", action="store_true",
                   help="time-only split as a sensitivity run (more rows; visitors may repeat across splits)")
    p.add_argument("--bootstrap", type=int, default=500)
    a = p.parse_args()
    merged = None
    if a.synthetic:
        from .synthetic import build_processed
        f, lab = build_processed(n_visitors=a.synthetic_visitors)
        merged = merge_features_labels(f, lab).assign(is_synthetic=True)
    run(a.features, a.labels, a.out, a.model_path, synthetic=a.synthetic, label_task=a.label_task,
        primary_set=a.feature_set, include_optional=a.optional_models, val_weeks=a.val_weeks,
        test_weeks=a.test_weeks, visitor_fractions=a.visitor_fractions,
        visitor_disjoint=not a.no_visitor_disjoint, n_boot=a.bootstrap, merged=merged)


if __name__ == "__main__":
    main()
