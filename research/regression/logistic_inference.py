"""Reproducible OLS/logit inference and temporal evaluation; no causal claims."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.metrics import (roc_auc_score,average_precision_score,precision_score,recall_score,f1_score,
    brier_score_loss,confusion_matrix,roc_curve,precision_recall_curve)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

FEATURES=['sessions','recency_days','engagement_change']

def clean_json(obj):
    if isinstance(obj,dict): return {str(k):clean_json(v) for k,v in obj.items()}
    if isinstance(obj,(list,tuple,np.ndarray)): return [clean_json(v) for v in obj]
    if isinstance(obj,(np.integer,)):return int(obj)
    if isinstance(obj,(float,np.floating)):return float(obj) if np.isfinite(obj) else None
    return obj

def save_json(path,obj):path.write_text(json.dumps(clean_json(obj),indent=2,allow_nan=False))

def split_time(df):
    dates=sorted(df.snapshot_date.unique())
    if len(dates)<8:raise ValueError('Need at least eight snapshot dates for purged temporal train/validation/test')
    val_start=dates[max(3,int(len(dates)*.5))]
    test_start=dates[max(6,int(len(dates)*.75))]
    if val_start>=test_start:raise ValueError('No validation window between train and test')
    # A label may be used only if its entire confirmation window ended before
    # the next partition starts. This allows a two-week horizon with short data.
    train=df[(df.snapshot_date<val_start)&(df.label_end<val_start)].copy()
    val=df[(df.snapshot_date>=val_start)&(df.snapshot_date<test_start)&(df.label_end<test_start)].copy()
    test=df[df.snapshot_date>=test_start].copy()
    if min(map(len,[train,val,test]))<20:raise ValueError('Insufficient samples after label-overlap purging')
    # Conservative evaluation: remove users present in an earlier partition.
    val=val[~val.visitorid.isin(train.visitorid)]
    test=test[~test.visitorid.isin(pd.concat([train.visitorid,val.visitorid]))]
    for part in [train,val,test]:
        if len(part)<20 or part.target_ghost.nunique()!=2:raise ValueError('Each partition needs >=20 rows and two target classes')
    return train,val,test

def coefficient_table(model,logit=False):
    ci=model.conf_int();rows=[]
    for k in model.params.index:
        row={'term':k,'coefficient':model.params[k],'ci_low':ci.loc[k,0],'ci_high':ci.loc[k,1],'p_value':model.pvalues[k]}
        if logit:row.update(odds_ratio=np.exp(row['coefficient']),or_ci_low=np.exp(row['ci_low']),or_ci_high=np.exp(row['ci_high']))
        rows.append(row)
    return rows

def design(df,cols=FEATURES):return sm.add_constant(df[cols].astype(float),has_constant='add')

def metrics(y,p,threshold):
    pred=(np.array(p)>=threshold).astype(int)
    return {'n':len(y),'positive_support':int(np.sum(y)),'prevalence':float(np.mean(y)),
            'threshold':threshold,'roc_auc':roc_auc_score(y,p),'pr_auc_average_precision':average_precision_score(y,p),
            'precision':precision_score(y,pred,zero_division=0),'recall':recall_score(y,pred,zero_division=0),
            'f1':f1_score(y,pred,zero_division=0),'brier':brier_score_loss(y,p),'confusion_matrix':confusion_matrix(y,pred,labels=[0,1]).tolist()}


def run(source, outdir, observed_through, mode):
    if mode not in {"synthetic", "real"}:
        raise ValueError("Set data provenance")
    data = pd.read_csv(source, dtype={"visitorid": str})
    required = {"visitorid", "snapshot_date", "feature_max_event_time", "label_end",
                "label_status", "target_ghost", *FEATURES}
    if not required.issubset(data.columns):
        raise ValueError("Missing fields from the documented logistic input schema")
    if data.visitorid.isna().any() or data.visitorid.str.strip().eq("").any():
        raise ValueError("Missing visitor")
    for key in ["snapshot_date", "feature_max_event_time", "label_end"]:
        data[key] = pd.to_datetime(data[key], utc=True)
        if data[key].isna().any():
            raise ValueError(f"Missing {key}")
    if data.duplicated(["visitorid", "snapshot_date"]).any():
        raise ValueError("Duplicate snapshot")
    if (data.feature_max_event_time > data.snapshot_date).any() or (data.label_end <= data.snapshot_date).any():
        raise ValueError("Invalid feature or label horizon")
    excluded = data.label_status.isin(["unknown", "candidate"])
    if not data.label_status.isin(["unknown", "candidate", "active", "ghost", "recovered", "inactive"]).all():
        raise ValueError("Invalid label status")
    if data.loc[excluded, "target_ghost"].notna().any():
        raise ValueError("Unconfirmed targets must be null")
    end = pd.to_datetime(observed_through, utc=True)
    if pd.isna(end):
        raise ValueError("Observation cutoff required")
    eligible = data[~excluded & (data.label_end <= end)].copy()
    if not eligible.target_ghost.eq(eligible.label_status.eq("ghost").astype(int)).all():
        raise ValueError("Target/status mismatch")
    if not np.isfinite(eligible[FEATURES].to_numpy(dtype=float)).all():
        raise ValueError("Nonfinite predictors")
    train, val, test = split_time(eligible)
    matrix = design(train)
    if np.linalg.matrix_rank(matrix) < matrix.shape[1]:
        raise ValueError("Rank-deficient design")
    cov = {"cov_type": "HC0"}
    if train.visitorid.duplicated().any():
        cov = {"cov_type": "cluster", "cov_kwds": {"groups": train.visitorid}}
    fit = sm.Logit(train.target_ghost, matrix).fit(disp=0, **cov)
    if not fit.mle_retvals.get("converged") or not np.isfinite(fit.bse).all():
        raise ValueError("Logit failed convergence or covariance checks")
    probabilities = fit.predict(design(val))
    threshold = float(max(np.linspace(.1, .9, 17),
                          key=lambda t: f1_score(val.target_ghost, probabilities >= t, zero_division=0)))
    predictions = fit.predict(design(test))
    calibration = pd.DataFrame({"p": predictions, "y": test.target_ghost})
    calibration["bin"] = pd.cut(calibration.p, np.linspace(0, 1, 6), include_lowest=True)
    bins = calibration.groupby("bin", observed=True).agg(n=("y", "size"), mean_predicted=("p", "mean"), observed_rate=("y", "mean"))
    result = {"data_mode": mode, "observed_through": str(end), "covariance": cov["cov_type"],
              "input_sha256": hashlib.sha256(Path(source).read_bytes()).hexdigest(),
              "label_task": "ghost_vs_rest among mature snapshots; inactive and recovered are negative",
              "decision_status": "Exploratory result under proposed 4+2+2 cohort/label and purged temporal split",
              "eligible_rows": len(eligible), "excluded_rows": len(data)-len(eligible),
              "split": {name: {"n": len(part), "positive": int(part.target_ghost.sum()),
                               "first_snapshot": str(part.snapshot_date.min()), "last_label_end": str(part.label_end.max())}
                        for name, part in [("train", train), ("validation", val), ("test", test)]},
              "vif": {name: variance_inflation_factor(matrix.to_numpy(), i) for i, name in enumerate(matrix) if name != "const"},
              "coefficients": coefficient_table(fit, True), "threshold_policy": "validation F1",
              "test": metrics(test.target_ghost, predictions, threshold),
              "prevalence_baseline": metrics(test.target_ghost, np.repeat(train.target_ghost.mean(), len(test)), .5),
              "calibration": bins.to_dict("records")}
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    save_json(out/"logit_results.json", result)
    pd.DataFrame(result["coefficients"]).to_csv(out/"logit_coefficients.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    fpr, tpr, _ = roc_curve(test.target_ghost, predictions)
    precision, recall, _ = precision_recall_curve(test.target_ghost, predictions)
    axes[0].plot(fpr, tpr)
    axes[0].set(xlabel="False positive rate", ylabel="True positive rate")
    axes[1].plot(recall, precision)
    axes[1].set(xlabel="Recall", ylabel="Precision")
    fig.suptitle(f"{mode.upper()} logistic evaluation")
    fig.tight_layout()
    fig.savefig(out/"logit_roc_pr.png")
    plt.close(fig)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("input", "outdir", "observed-through"):
        parser.add_argument(f"--{argument}", required=True)
    parser.add_argument("--mode", choices=["real", "synthetic"], required=True)
    args = parser.parse_args()
    run(args.input, args.outdir, args.observed_through, args.mode)
