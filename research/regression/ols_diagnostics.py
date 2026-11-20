"""Run diagnostics on a training-only continuous-response table."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor


def run(source, outdir, predictors, cutoff, mode):
    if mode not in {"real", "synthetic"}:
        raise ValueError("Set data provenance")
    data = pd.read_csv(source, dtype={"visitorid": str})
    reserved = {"visitorid", "snapshot_date", "feature_max_event_time", "outcome_end", "next_engagement", "status"}
    if not predictors or len(set(predictors)) != len(predictors) or any(
        key in reserved or key.startswith(("future_", "target_", "label_", "post_")) for key in predictors
    ):
        raise ValueError("Supply a unique pre-T predictor allowlist")
    for key in ("snapshot_date", "feature_max_event_time", "outcome_end"):
        data[key] = pd.to_datetime(data[key], utc=True)
        if data[key].isna().any():
            raise ValueError(f"Missing {key}")
    if data.visitorid.isna().any() or data.duplicated(["visitorid", "snapshot_date"]).any():
        raise ValueError("Missing or duplicate visitor/snapshot keys")
    if (data.feature_max_event_time > data.snapshot_date).any() or (data.outcome_end <= data.snapshot_date).any():
        raise ValueError("Invalid temporal provenance")
    end = pd.to_datetime(cutoff, utc=True)
    data = data[data.outcome_end <= end]
    matrix = sm.add_constant(data[predictors].astype(float), has_constant="add")
    y = data.next_engagement.astype(float)
    if len(y) <= matrix.shape[1] + 1 or not np.isfinite(matrix).all().all() or not np.isfinite(y).all():
        raise ValueError("Insufficient finite training data")
    if np.linalg.matrix_rank(matrix) < matrix.shape[1] or y.nunique() < 2:
        raise ValueError("Degenerate regression design")
    cov = {"cov_type": "HC3"}
    repeated = data.visitorid.duplicated().any()
    if repeated:
        if data.visitorid.nunique() < 3:
            raise ValueError("Too few distinct visitor clusters")
        cov = {"cov_type": "cluster", "cov_kwds": {"groups": data.visitorid}}
    full = sm.OLS(y, matrix).fit(**cov)
    baseline = sm.OLS(y, matrix[["const", predictors[0]]]).fit(**cov)
    cooks = full.get_influence().cooks_distance[0]
    influential = cooks > 4 / len(y)
    retained = ~influential
    sensitivity = None
    if retained.sum() > matrix.shape[1]+1 and np.linalg.matrix_rank(matrix[retained]) == matrix.shape[1]:
        sensitivity = sm.OLS(y[retained], matrix[retained]).fit().params.to_dict()
    vif = {key: float(variance_inflation_factor(matrix.to_numpy(), i))
           for i, key in enumerate(matrix.columns) if key != "const"}
    result = {"data_mode": mode, "training_cutoff": str(end), "n": len(y),
              "covariance": cov["cov_type"], "vif": vif,
              "breusch_pagan_p": None if repeated else float(het_breuschpagan(full.resid, matrix)[1]),
              "bp_note": "Omitted for clustered rows" if repeated else "Exploratory residual variance test",
              "influence_flags": int(influential.sum()), "cook_threshold": 4/len(y),
              "baseline_adjusted_r2": float(baseline.rsquared_adj), "full_adjusted_r2": float(full.rsquared_adj),
              "full_coefficients": full.params.to_dict(), "sensitivity_coefficients": sensitivity,
              "interpretation": "Influence flags warrant review. The full fit retains every training row."}
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out/"diagnostics.json").write_text(json.dumps(result, indent=2, allow_nan=False))
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    axes[0].scatter(full.fittedvalues, full.resid, s=10)
    axes[0].axhline(0)
    axes[0].set(xlabel="Fitted", ylabel="Residual")
    sm.qqplot(full.resid, line="s", ax=axes[1])
    fig.suptitle(f"{mode.upper()} OLS diagnostics")
    fig.tight_layout()
    fig.savefig(out/"diagnostics.png")
    plt.close(fig)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--predictors", nargs="+", required=True)
    parser.add_argument("--cutoff", required=True)
    parser.add_argument("--mode", choices=["real", "synthetic"], required=True)
    args = parser.parse_args()
    run(args.input, args.outdir, args.predictors, args.cutoff, args.mode)
