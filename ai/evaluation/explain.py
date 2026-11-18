"""Explainability (AI-11).

1. Global permutation importance on the VALIDATION split (drop in PR-AUC).
2. SHAP values on a test sample when the `shap` package is installed
   (TreeExplainer for tree/boosting, LinearExplainer for logistic regression).
3. Model-agnostic summary: mean |baseline-replacement contribution| over a
   test sample (same method the API returns as top_factors).
4. Logistic coefficients (per-SD log-odds / odds ratios) to cross-check with
   Long's statistical logistic regression.
All are associations in observational data, not causal effects.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import average_precision_score

from ..inference.attribution import local_contributions
from ..training import config


def permutation_table(model, X, y, n_repeats: int = 10) -> pd.DataFrame:
    def pr_auc(est, X_, y_):
        return average_precision_score(y_, est.predict_proba(X_)[:, 1])

    r = permutation_importance(model, X, y, scoring=pr_auc, n_repeats=n_repeats,
                               random_state=config.SEED, n_jobs=1)
    return (pd.DataFrame({"feature": X.columns, "pr_auc_drop_mean": r.importances_mean,
                          "pr_auc_drop_sd": r.importances_std})
            .sort_values("pr_auc_drop_mean", ascending=False).reset_index(drop=True))


def attribution_summary(model, X: pd.DataFrame, baseline: dict, max_rows: int = 400) -> pd.DataFrame:
    sample = X.sample(min(len(X), max_rows), random_state=config.SEED) if len(X) > max_rows else X
    rows = local_contributions(model, sample, baseline, top_k=None, min_abs=0.0)
    flat = pd.DataFrame([r for row in rows for r in row])
    g = flat.groupby("feature")["contribution"]
    return (pd.DataFrame({"mean_abs_contribution": g.apply(lambda s: s.abs().mean()),
                          "mean_contribution": g.mean(), "share_increasing": g.apply(lambda s: (s > 0).mean())})
            .sort_values("mean_abs_contribution", ascending=False).reset_index())


def _original_name(transformed: str, features: list[str]) -> str:
    for f in sorted(features, key=len, reverse=True):
        if transformed == f or transformed.endswith(f):
            return f
    return transformed


def shap_table(model, X: pd.DataFrame, family: str, max_rows: int = 500):
    """Mean |SHAP| per original feature, or None when shap is unavailable."""
    try:
        import shap  # type: ignore
    except Exception:
        return None, "shap not installed; see permutation and baseline-replacement summaries"
    est = getattr(model, "estimator_", model)          # unwrap PlattCalibrated (explains the base model)
    if not hasattr(est, "named_steps"):
        return None, "model is not a preprocessing pipeline"
    prep, clf = est.named_steps["prep"], est.named_steps["model"]
    sample = X.sample(min(len(X), max_rows), random_state=config.SEED)
    Z = prep.transform(sample)
    names = list(prep.get_feature_names_out())
    if family == "linear":
        explainer = shap.LinearExplainer(clf, Z)
        values = explainer.shap_values(Z)
        unit = "log-odds"
    else:
        explainer = shap.TreeExplainer(clf)
        values = explainer.shap_values(Z)
        if isinstance(values, list):
            values = values[1]
        values = np.asarray(values)
        if values.ndim == 3:
            values = values[:, :, 1]
        unit = "model margin (log-odds for boosting, probability for forests)"
    df = pd.DataFrame(np.abs(values), columns=names)
    per = df.T.groupby(lambda n: _original_name(n, list(X.columns))).sum().T.mean()
    table = per.sort_values(ascending=False).rename("mean_abs_shap").reset_index().rename(columns={"index": "feature"})
    return table, f"SHAP ({type(explainer).__name__}), unit: {unit}, n={len(sample)} test rows"


def logistic_coefficients(model, features: list[str]) -> pd.DataFrame | None:
    est = getattr(model, "estimator_", model)
    if not hasattr(est, "named_steps") or not hasattr(est.named_steps["model"], "coef_"):
        return None
    names = list(est.named_steps["prep"].get_feature_names_out())
    coef = est.named_steps["model"].coef_.ravel()
    return (pd.DataFrame({"term": names, "coef_per_sd_log_odds": coef, "odds_ratio_per_sd": np.exp(coef)})
            .sort_values("coef_per_sd_log_odds", key=np.abs, ascending=False).reset_index(drop=True))
