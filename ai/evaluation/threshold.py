"""Threshold study and risk bands (AI-10) - chosen on VALIDATION only.

The operating threshold minimises expected cost
    cost = C_FN * FN + C_FP * FP
with C_FN > C_FP (missing a disengaging customer is assumed costlier than an
unnecessary retention touch). Costs are a stated business assumption, not
an estimate; the full precision/recall/alert-volume table is exported so the
team can pick another operating point. Interventions triggered by a score are
not evidence that the intervention works (observational data).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..training import config

GRID = np.round(np.arange(0.02, 0.99, 0.01), 2)


def threshold_table(y, score, c_fn: float = config.COST_FALSE_NEGATIVE,
                    c_fp: float = config.COST_FALSE_POSITIVE) -> pd.DataFrame:
    y = np.asarray(y).astype(int)
    score = np.asarray(score, dtype=float)
    rows = []
    for t in GRID:
        pred = score >= t
        tp = int((pred & (y == 1)).sum())
        fp = int((pred & (y == 0)).sum())
        fn = int((~pred & (y == 1)).sum())
        precision = tp / (tp + fp) if tp + fp else None
        recall = tp / (tp + fn) if tp + fn else None
        f1 = (2 * precision * recall / (precision + recall)) if precision and recall else 0.0
        rows.append({"threshold": float(t), "alerts": int(pred.sum()),
                     "alerts_per_1000": round(1000 * pred.mean(), 1), "tp": tp, "fp": fp, "fn": fn,
                     "precision": precision, "recall": recall, "f1": round(f1, 5),
                     "expected_cost": c_fn * fn + c_fp * fp,
                     "cost_per_customer": round((c_fn * fn + c_fp * fp) / len(y), 5)})
    return pd.DataFrame(rows)


def choose_threshold(table: pd.DataFrame) -> dict:
    """Min expected cost; ties -> higher threshold (fewer alerts)."""
    best_cost = table.loc[table["expected_cost"] == table["expected_cost"].min()].iloc[-1]
    best_f1 = table.loc[table["f1"] == table["f1"].max()].iloc[-1]
    reach = table.loc[table["recall"].fillna(0) >= config.MEDIUM_RECALL_TARGET]
    medium = float(reach["threshold"].max()) if not reach.empty else float(table["threshold"].min())
    operating = float(best_cost["threshold"])
    medium = min(medium, operating)
    return {
        "operating_threshold": operating,
        "rule": f"min expected cost on validation, C_FN={config.COST_FALSE_NEGATIVE}, C_FP={config.COST_FALSE_POSITIVE}",
        "f1_max_threshold": float(best_f1["threshold"]),
        "bands": {"high": operating, "medium": medium},
        "band_rule": f"high >= operating threshold; medium >= threshold where validation recall >= "
                     f"{config.MEDIUM_RECALL_TARGET:.0%}; else low",
    }


def risk_label(score: float, bands: dict) -> str:
    if score >= bands["high"]:
        return "high"
    if score >= bands["medium"]:
        return "medium"
    return "low"
