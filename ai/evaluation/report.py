"""Render the numeric part of the ML results section from a finished run (AI-13).

    python -m ai.evaluation.report                     # reads ai/evaluation/
    python -m ai.evaluation.report --dir data/processed/ai_dryrun

Writes results_tables.md next to the run outputs. Every number comes from
the run files, so report, slides and API stay consistent.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ..training import config


def _fmt(v, nd=3):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    if isinstance(v, (list, tuple)) and len(v) == 2:
        return f"[{_fmt(v[0], nd)}, {_fmt(v[1], nd)}]"
    return f"{v:.{nd}f}" if isinstance(v, float) else str(v)


def _table(df: pd.DataFrame) -> str:
    head = "| " + " | ".join(df.columns) + " |\n|" + "---|" * len(df.columns) + "\n"
    return head + "\n".join("| " + " | ".join(_fmt(v) for v in row) + " |" for row in df.itertuples(index=False))


def render(run_dir: Path) -> str:
    s = json.loads((run_dir / "run_summary.json").read_text(encoding="utf-8"))
    split = json.loads((run_dir / "split_manifest.json").read_text(encoding="utf-8"))
    comp = pd.read_csv(run_dir / "model_comparison.csv")
    ablation = pd.read_csv(run_dir / "ablation.csv")
    perm = pd.read_csv(run_dir / "permutation_importance.csv").head(10)
    sel = s["selected_model"]
    t = s["test"]
    lines = []
    if s["synthetic"]:
        lines.append(f"> **{config.SYNTHETIC_NOTICE}.** Do not copy these numbers into the report.\n")
    lines += [
        f"**Run:** `{sel['model_version']}` · split `{s['split_version']}` · label task `{s['label_task']}` "
        f"(label version `{s['label_version']}`, scenario `{s['scenario_id']}`) · generated {s['generated_utc'][:19]}Z",
        "",
        "**Table ML-1. Visitor-aware temporal split.**",
        "",
        _table(pd.DataFrame([{"split": k, **v} for k, v in split["splits"].items()])),
        "",
        f"{split['rows_dropped_by_purge_or_bucket']} of {split['supervised_rows']} supervised rows are not used "
        "because of label purging or visitor bucketing.",
        "",
        "**Table ML-2. Model comparison (selection on validation PR-AUC; test evaluated once).**",
        "",
        _table(comp[["name", "family", "val_pr_auc", "test_pr_auc", "test_pr_auc_ci95", "test_roc_auc",
                     "test_recall", "test_precision", "test_f1", "test_brier", "threshold"]]
               .assign(test_pr_auc_ci95=lambda d: d.test_pr_auc_ci95.fillna("—"))),
        "",
        f"No-skill PR-AUC equals test prevalence = {_fmt(t['prevalence'])}. Rank-only models "
        "(SVM, Isolation Forest) have no Brier score because their outputs are not probabilities.",
        "",
        f"**Selected model:** {sel['name']} with {sel['params']}; calibration: {sel['calibration']}.",
        "",
        f"**Operating point (chosen on validation):** threshold {s['threshold']['operating_threshold']} "
        f"({s['threshold']['rule']}); risk bands {s['threshold']['bands']}.",
        "",
        f"**Test at the operating threshold:** support {t['support']}, Ghost {t['positives']} "
        f"(prevalence {_fmt(t['prevalence'])}), precision {_fmt(t['precision'])}, recall {_fmt(t['recall'])}, "
        f"F1 {_fmt(t['f1'])}, ROC-AUC {_fmt(t['roc_auc'])}, PR-AUC {_fmt(t['pr_auc'])}, Brier {_fmt(t['brier'])}, "
        f"ECE {_fmt(s['test_ece'])}; confusion matrix [[TN, FP], [FN, TP]] = {t['confusion_matrix']}.",
        "",
        "**Table ML-3. Circularity ablation (label uses baseline sessions/week).**",
        "",
        _table(ablation),
        "",
        "**Table ML-4. Permutation importance on validation (PR-AUC drop).**",
        "",
        _table(perm),
        "",
        f"Explanations: {s['explanations']}. These are associations, not causal effects.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dir", type=Path, default=config.EVALUATION_DIR)
    a = p.parse_args()
    text = render(a.dir)
    (a.dir / "results_tables.md").write_text(text, encoding="utf-8")
    print(f"Wrote {a.dir / 'results_tables.md'}")


if __name__ == "__main__":
    main()
