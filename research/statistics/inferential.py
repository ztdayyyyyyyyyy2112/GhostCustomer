"""Visitor-level exploratory inference for the proposed Ghost/Active label."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportion_confint


ROOT = Path(__file__).resolve().parents[2]


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def analyze(features: pd.DataFrame, labels: pd.DataFrame) -> tuple[dict, dict]:
    required_features = {"visitorid", "snapshot_date", "feature_recency_days"}
    required_labels = {"visitorid", "snapshot_date", "horizon_mature", "label_status"}
    if not required_features <= set(features) or not required_labels <= set(labels):
        raise ValueError("Missing feature or label columns")
    if features.duplicated(["visitorid", "snapshot_date"]).any() or labels.duplicated(["visitorid", "snapshot_date"]).any():
        raise ValueError("Duplicate visitor snapshots")
    merged = features[list(required_features)].merge(
        labels[list(required_labels)], on=["visitorid", "snapshot_date"], validate="one_to_one"
    )
    mature = merged.loc[merged.horizon_mature].copy()
    # Select one mature observation per visitor before choosing comparison groups.
    # This keeps an older Ghost/Active row from replacing a later Inactive row.
    mature = mature.sort_values(["visitorid", "snapshot_date"]).drop_duplicates("visitorid", keep="last")
    mature = mature.loc[mature.label_status.isin(["ghost", "active"])].copy()
    ghost = pd.to_numeric(mature.loc[mature.label_status.eq("ghost"), "feature_recency_days"], errors="coerce").dropna()
    active = pd.to_numeric(mature.loc[mature.label_status.eq("active"), "feature_recency_days"], errors="coerce").dropna()
    if min(len(ghost), len(active)) < 30 or not np.isfinite(ghost).all() or not np.isfinite(active).all():
        raise ValueError("Need at least 30 finite, independent observations per group")
    ng, na = len(ghost), len(active)
    vg, va = ghost.var(ddof=1), active.var(ddof=1)
    se = np.sqrt(vg / ng + va / na)
    if se <= 0:
        raise ValueError("Both groups have zero sampling variance")
    degrees = (vg / ng + va / na) ** 2 / ((vg / ng) ** 2 / (ng - 1) + (va / na) ** 2 / (na - 1))
    difference = float(ghost.mean() - active.mean())
    radius = float(stats.t.ppf(.975, degrees) * se)
    t, p = stats.ttest_ind(ghost, active, equal_var=False)
    pooled = np.sqrt(((ng - 1) * vg + (na - 1) * va) / (ng + na - 2))
    d = float(difference / pooled)
    positive = int(mature.label_status.eq("ghost").sum())
    lower, upper = proportion_confint(positive, len(mature), alpha=.05, method="wilson")
    result = {
        "tests": [{
            "name": "Pre-snapshot recency: ghost minus active",
            "hypothesis": "H0: mean pre-snapshot recency is equal in the two operational-label groups; H1: it differs.",
            "n": ng + na, "statistic": float(t), "p_value": float(p), "effect_size": d,
            "ci_low": difference - radius, "ci_high": difference + radius,
            "method": "Two-sided Welch t test; 95% Welch CI for mean difference; Cohen d effect size",
            "assumptions": ["One latest mature snapshot per visitor", "Independent visitors are assumed", "Skew and selection bias may limit the mean-based interpretation", "Observational association only; proposed label"],
        }],
        "estimates": [{
            "name": "Ghost share among mature Ghost/Active visitors", "n": len(mature),
            "estimate": positive / len(mature), "ci_low": float(lower), "ci_high": float(upper),
            "method": "Wilson 95% binomial interval; one latest snapshot per visitor", "unit": "proportion",
        }],
        "assumptions": [
            "Inferential rows contain one latest mature snapshot per visitor; descriptive groups retain repeated snapshots.",
            "Ghost and active are operational labels under the proposed 4+2+2 configuration, not externally validated churn.",
            "The test is exploratory and does not establish causation or model performance.",
        ],
    }
    audit = {
        "input_pairs": len(merged), "mature_ghost_or_active_visitors": len(mature),
        "ghost_visitors": positive, "active_visitors": len(mature) - positive,
        "recency_n_ghost": ng, "recency_n_active": na,
        "ghost_mean_days": float(ghost.mean()), "active_mean_days": float(active.mean()),
        "mean_difference_days": difference, "welch_df": float(degrees),
        "selection": "Latest mature snapshot per visitor, then Ghost/Active comparison; excludes inactive, recovered, candidate and unknown",
    }
    return result, audit


def run(features_path: Path, labels_path: Path, statistics_path: Path, audit_path: Path) -> dict:
    features = pd.read_parquet(features_path)
    labels = pd.read_parquet(labels_path)
    inferential, audit = analyze(features, labels)
    existing = json.loads(statistics_path.read_text(encoding="utf-8"))
    if not isinstance(existing.get("groups"), list):
        raise ValueError("Descriptive groups must be generated before inference")
    existing.update(tests=inferential["tests"], estimates=inferential["estimates"],
                    p_values=[row["p_value"] for row in inferential["tests"]],
                    cis=[{"low": row["ci_low"], "high": row["ci_high"]} for row in inferential["tests"]],
                    assumptions=inferential["assumptions"],
                    dataset_notice="Retailrocket exploratory statistics; proposed cohort/label, not approved final findings")
    audit.update(features_sha256=_sha(features_path), labels_sha256=_sha(labels_path))
    statistics_path.write_text(json.dumps(existing, indent=2, allow_nan=False), encoding="utf-8")
    audit_path.write_text(json.dumps(audit, indent=2, allow_nan=False), encoding="utf-8")
    manifest_path = ROOT / "data/processed/manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest.setdefault("sha256", {})["research/statistics/results.json"] = _sha(statistics_path)
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return audit


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", type=Path, default=ROOT / "data/processed/customer_features.parquet")
    parser.add_argument("--labels", type=Path, default=ROOT / "data/processed/customer_labels.parquet")
    parser.add_argument("--statistics", type=Path, default=ROOT / "research/statistics/results.json")
    parser.add_argument("--audit", type=Path, default=ROOT / "research/statistics/inference_audit.json")
    args = parser.parse_args()
    print(json.dumps(run(args.features, args.labels, args.statistics, args.audit), indent=2))
