from __future__ import annotations

import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from data.scripts.aggregate import aggregate_user_week
from data.scripts.clean import clean_events
from data.scripts.cohort import iter_cohort_snapshots
from data.scripts.config import ROOT, load_config, verify_source
from data.scripts.features import build_features
from data.scripts.labels import build_labels, minimal_labels
from data.scripts.sessions import build_sessions


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_default(value):
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if pd.isna(value):
        return None
    raise TypeError(f"cannot serialize {type(value).__name__}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Reproduce the Retailrocket data pipeline")
    parser.add_argument("--config", type=Path, default=ROOT / "data/config/pipeline.json")
    parser.add_argument("--mode", choices=["audit_compat", "research"], default="audit_compat")
    args = parser.parse_args()
    config = load_config(args.config)
    raw_path = ROOT / config["source"]["raw_path"]
    source = verify_source(raw_path, config["source"]["sha256"])
    out = ROOT / "data/processed"
    out.mkdir(parents=True, exist_ok=True)
    print(f"source verified: {source['rows']:,} rows sha256={source['sha256']}", flush=True)

    events = clean_events(raw_path, config["extreme_visitor_quantile"])
    sessions, assigned = build_sessions(events, config["sessions"]["preferred_gap_minutes"])
    weekly = aggregate_user_week(assigned)
    if int(weekly.events.sum()) != len(events):
        raise AssertionError("user-week event totals do not reconcile to raw rows")
    events.to_parquet(out / "events_clean.parquet", index=False)
    sessions.to_parquet(out / "sessions.parquet", index=False)
    weekly.to_parquet(out / "customer_weekly.parquet", index=False)

    scenario = next(item for item in config["scenarios"] if item["id"] == config["preferred_scenario_id"].split("_min")[0])
    traces = list(iter_cohort_snapshots(events, config, scenario))
    trace = pd.concat(traces, ignore_index=True)
    trace.to_parquet(out / "cohort_trace.parquet", index=False)
    primary = trace.loc[trace.history_eligible].copy()
    primary["eligible"] = primary["eligible_audit" if args.mode == "audit_compat" else "eligible_research"]
    primary["exclusion_reason"] = primary["exclusion_reason_audit" if args.mode == "audit_compat" else "exclusion_reason_research"]
    features = build_features(events, sessions, primary, config)
    labels = build_labels(events, sessions, primary, features, config)
    features.to_parquet(out / "customer_features.parquet", index=False)
    labels.to_parquet(out / "customer_labels.parquet", index=False)
    minimal_labels(labels).to_csv(out / "ghost_labels.csv", index=False)

    merged = features.merge(labels, on=["visitorid", "snapshot_date"], validate="one_to_one")
    counts = merged.label_status.value_counts(dropna=False).to_dict()
    customers = pd.DataFrame({
        "customer_id": merged.customer_id,
        "snapshot_date": pd.to_datetime(merged.snapshot_date, utc=True).dt.strftime("%Y-%m-%d"),
        "status": merged.display_status,
        "sessions": merged.feature_sessions_4w,
        "views": merged.feature_views_4w,
        "decay": merged.feature_decay_ratio,
        "risk_score": pd.NA,
    })
    customers.to_json(out / "customers.json", orient="records", indent=2)
    total = len(customers)
    count = {status: int((customers.status == status).sum()) for status in ["active", "ghost", "candidate", "unknown", "inactive", "recovered"]}
    overview = {"total_customers": total, **{f"{k}_count": v for k,v in count.items()},
        "active_rate": count["active"] / total if total else None,
        "ghost_rate": count["ghost"] / total if total else None,
        "date_range": {"start": customers.snapshot_date.min(), "end": customers.snapshot_date.max()} if total else None,
        "dataset_notice": "Retailrocket derived data — proposed cohort and label; see E-01/E-02"}
    (out / "overview.json").write_text(json.dumps(overview, indent=2, default=_json_default), encoding="utf-8")

    # E-03 is descriptive only; repeated snapshots are retained and their dependence is disclosed.
    complete = merged.loc[merged.horizon_mature & merged.label_status.ne("unknown")]
    metrics = ["feature_sessions_4w", "feature_views_4w", "feature_carts_4w", "feature_purchases_4w", "feature_active_days_4w", "feature_decay_ratio"]
    groups = []
    for status, frame in complete.groupby("label_status", sort=True):
        for metric in metrics:
            values = pd.to_numeric(frame[metric], errors="coerce").dropna()
            if values.empty: continue
            hist, edges = __import__("numpy").histogram(values, bins=10)
            groups.append({"name": str(status), "metric": metric, "unit": "count" if "sessions" in metric or "views" in metric or "carts" in metric or "purchases" in metric or "days" in metric else "ratio", "n": int(len(values)), "mean": float(values.mean()), "median": float(values.median()), "q1": float(values.quantile(.25)), "q3": float(values.quantile(.75)), "min": float(values.min()), "max": float(values.max()), "histogram": [{"lower": float(edges[i]), "upper": float(edges[i+1]), "count": int(hist[i])} for i in range(len(hist))]})
    eda = {"groups": groups, "estimates": [], "tests": [], "p_values": [], "cis": [], "assumptions": ["Descriptive statistics only; no hypothesis tests or confidence intervals.", "Rows are repeated visitor snapshots and are not independent."], "dataset_notice": "Descriptive Retailrocket output; proposed cohort and label, not approved findings"}
    (out / "descriptive_statistics.json").write_text(json.dumps(eda, indent=2, default=_json_default), encoding="utf-8")
    (ROOT / "research/statistics").mkdir(parents=True, exist_ok=True)
    (ROOT / "research/statistics/results.json").write_text(json.dumps(eda, indent=2, default=_json_default), encoding="utf-8")

    manifest = {"generated_utc": datetime.now(timezone.utc).isoformat(), "source": source,
        "config_sha256": sha256(args.config), "git_revision": __import__("subprocess").run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
        "python": platform.python_version(), "pandas": pd.__version__, "mode": args.mode,
        "rows": {"clean_events": len(events), "sessions": len(sessions), "customer_weekly": len(weekly), "cohort_trace": len(trace), "features": len(features), "labels": len(labels), "label_status": {k: int(v) for k,v in counts.items()}},
        "output_sha256": {p.name: sha256(p) for p in out.iterdir() if p.is_file()}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest["rows"], indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
