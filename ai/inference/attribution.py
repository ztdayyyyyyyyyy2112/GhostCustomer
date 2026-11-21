"""Model-agnostic local attribution used by the runtime and offline analysis.

Method "baseline replacement": for feature j, contribution_j =
    score(x) - score(x with x_j set to the training median of j).
Positive values push the Ghost score up. Units are probability points. It
works for any saved model (no SHAP dependency in the backend), but ignores
interactions between features and is an association, not a causal effect.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

METHOD = "baseline_replacement_train_median"


def local_contributions(model, X: pd.DataFrame, baseline: dict, top_k: int | None = 5,
                        min_abs: float = 1e-4) -> list[list[dict]]:
    """One list of {feature, contribution, value} per row of X, largest |effect| first."""
    features = list(X.columns)
    base_scores = model.predict_proba(X)[:, 1]
    variants = []
    for f in features:
        alt = X.copy()
        alt[f] = baseline.get(f, np.nan)
        variants.append(alt)
    alt_scores = model.predict_proba(pd.concat(variants, ignore_index=True))[:, 1]
    alt_scores = alt_scores.reshape(len(features), len(X))
    out = []
    for i in range(len(X)):
        rows = []
        for j, f in enumerate(features):
            c = float(base_scores[i] - alt_scores[j, i])
            if abs(c) >= min_abs:
                v = X.iat[i, j]
                rows.append({"feature": f, "contribution": round(c, 4),
                             "value": None if pd.isna(v) else float(v)})
        rows.sort(key=lambda r: abs(r["contribution"]), reverse=True)
        out.append(rows[:top_k] if top_k else rows)
    return out
