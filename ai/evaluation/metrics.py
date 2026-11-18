"""Classification evaluation (AI-09).

Never relies on accuracy alone: reports support, prevalence, precision,
recall, F1 at an explicit threshold, ROC-AUC, PR-AUC (with prevalence as the
no-skill reference), Brier score, calibration bins, the confusion matrix
[[TN, FP], [FN, TP]], and visitor-cluster bootstrap CIs.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import (average_precision_score, brier_score_loss, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)


def _safe(fn, *args, **kw):
    try:
        v = float(fn(*args, **kw))
        return None if np.isnan(v) else v
    except ValueError:
        return None


def classification_metrics(y, score, threshold: float, probabilistic: bool = True) -> dict:
    y = np.asarray(y).astype(int)
    score = np.asarray(score, dtype=float)
    pred = (score >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "support": int(len(y)),
        "positives": int(y.sum()),
        "prevalence": float(y.mean()) if len(y) else None,
        "threshold": float(threshold),
        "precision": _safe(precision_score, y, pred, zero_division=0),
        "recall": _safe(recall_score, y, pred, zero_division=0),
        "f1": _safe(f1_score, y, pred, zero_division=0),
        "roc_auc": _safe(roc_auc_score, y, score),
        "pr_auc": _safe(average_precision_score, y, score),
        "brier": _safe(brier_score_loss, y, score) if probabilistic else None,
        "alert_rate": float(pred.mean()) if len(y) else None,
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
    }


def calibration_bins(y, score, n_bins: int = 10) -> list[dict]:
    """Equal-width reliability bins; empty bins are omitted."""
    y = np.asarray(y).astype(int)
    score = np.clip(np.asarray(score, dtype=float), 0, 1)
    edges = np.linspace(0, 1, n_bins + 1)
    idx = np.clip(np.digitize(score, edges[1:-1]), 0, n_bins - 1)
    out = []
    for b in range(n_bins):
        m = idx == b
        if m.any():
            out.append({"mean_predicted": round(float(score[m].mean()), 5),
                        "observed_rate": round(float(y[m].mean()), 5), "n": int(m.sum())})
    return out


def expected_calibration_error(bins: list[dict]) -> float | None:
    n = sum(b["n"] for b in bins)
    if not n:
        return None
    return float(sum(b["n"] * abs(b["mean_predicted"] - b["observed_rate"]) for b in bins) / n)


def bootstrap_ci(y, score, groups, threshold: float, n_boot: int = 500, seed: int = 3013,
                 alpha: float = 0.05) -> dict:
    """Percentile CIs, resampling whole visitors (repeated snapshots are dependent)."""
    y = np.asarray(y).astype(int)
    score = np.asarray(score, dtype=float)
    groups = np.asarray(groups)
    uniq, inv = np.unique(groups, return_inverse=True)
    members = [np.flatnonzero(inv == g) for g in range(len(uniq))]
    rng = np.random.default_rng(seed)
    stats = {"pr_auc": [], "roc_auc": [], "f1": [], "recall": [], "precision": []}
    for _ in range(n_boot):
        pick = rng.integers(0, len(uniq), len(uniq))
        idx = np.concatenate([members[g] for g in pick])
        yb, sb = y[idx], score[idx]
        if yb.min() == yb.max():
            continue
        pb = (sb >= threshold).astype(int)
        stats["pr_auc"].append(average_precision_score(yb, sb))
        stats["roc_auc"].append(roc_auc_score(yb, sb))
        stats["f1"].append(f1_score(yb, pb, zero_division=0))
        stats["recall"].append(recall_score(yb, pb, zero_division=0))
        stats["precision"].append(precision_score(yb, pb, zero_division=0))
    out = {"n_boot_effective": len(stats["pr_auc"]), "unit": "visitor", "level": 1 - alpha}
    for k, v in stats.items():
        if v:
            lo, hi = np.quantile(v, [alpha / 2, 1 - alpha / 2])
            out[k] = [round(float(lo), 4), round(float(hi), 4)]
        else:
            out[k] = None
    return out
