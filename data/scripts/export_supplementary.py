from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path

import pandas as pd

from data.scripts.cohort import iter_cohort_snapshots
from data.scripts.config import ROOT, load_config, verify_source
from data.scripts.features import build_features
from data.scripts.labels import build_labels
from data.scripts.sessions import build_sessions


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _counts(values: pd.Series) -> dict[str, int]:
    return {str(key): int(value) for key, value in values.value_counts(dropna=False).items()}


def _window_sensitivity(events: pd.DataFrame, config: dict) -> list[dict]:
    results = []
    for scenario in config["scenarios"]:
        row = {"scenario_id": scenario["id"], "candidate_snapshots": 0, "history_eligible_snapshots": 0,
               "audit_complete_snapshots": 0, "research_complete_snapshots": 0,
               "censored_history_eligible_snapshots": 0}
        visitors: set[int] = set()
        repeat_visitors = 0
        for trace in iter_cohort_snapshots(events, config, scenario):
            eligible_ids = set(trace.loc[trace.history_eligible, "visitorid"].tolist())
            row["candidate_snapshots"] += len(trace)
            row["history_eligible_snapshots"] += len(eligible_ids)
            row["audit_complete_snapshots"] += int(trace.eligible_audit.sum())
            row["research_complete_snapshots"] += int(trace.eligible_research.sum())
            row["censored_history_eligible_snapshots"] += int((trace.history_eligible & ~trace.horizon_mature).sum())
            repeat_visitors += len(visitors.intersection(eligible_ids))
            visitors.update(eligible_ids)
        row["distinct_history_eligible_visitors"] = len(visitors)
        row["repeat_visitors"] = repeat_visitors
        results.append(row)
    return results


def _label_sensitivity(labels: pd.DataFrame, features: pd.DataFrame) -> list[dict]:
    data = labels.merge(features[["visitorid", "snapshot_date", "feature_baseline_sessions_per_week",
                                  "feature_observation_sessions_per_week", "feature_baseline_events_per_week",
                                  "feature_observation_events_per_week"]],
                        on=["visitorid", "snapshot_date"], validate="one_to_one")
    rows = []
    for unit in ("sessions", "events"):
        baseline = data[f"feature_baseline_{unit}_per_week"]
        observation = data[f"feature_observation_{unit}_per_week"]
        future_count = data[f"future_{unit}"]
        confirmation_rate = future_count / 2
        for theta in (0.5, 0.4, 0.3):
            inactive = data.future_events.eq(0)
            unscorable = baseline.isna() | baseline.le(0)
            ghost = data.future_events.gt(0) & (confirmation_rate / baseline < theta) & ~unscorable
            recovered = (observation / baseline < theta) & (confirmation_rate / baseline >= theta) & ~inactive & ~unscorable
            status = pd.Series("active", index=data.index, dtype="string")
            status.loc[ghost] = "ghost"
            status.loc[recovered] = "recovered"
            status.loc[inactive] = "inactive"
            status.loc[unscorable & ~inactive] = "unknown"
            status.loc[~data.horizon_mature] = "unknown"
            counts = _counts(status)
            row = {"engagement_unit": unit, "theta": theta, "counts": counts}
            if unit == "sessions":
                moved = int((ghost & data.future_purchases.gt(0)).sum())
                no_purchase = dict(counts)
                no_purchase["ghost"] -= moved
                no_purchase["active"] = no_purchase.get("active", 0) + moved
                row["no_purchase_variant_counts"] = no_purchase
                row["purchase_positive_ghosts_moved_to_active"] = moved
            rows.append(row)
    return rows


def _gap_sensitivity(events: pd.DataFrame, features: pd.DataFrame, labels: pd.DataFrame, config: dict) -> list[dict]:
    scenario = config["scenarios"][0]
    results = []
    for gap in config["sessions"]["gap_minutes"]:
        sessions, _ = build_sessions(events, int(gap))
        sessions["week"] = sessions.session_start_utc.dt.normalize() - pd.to_timedelta(sessions.session_start_utc.dt.dayofweek, unit="D")
        weekly = sessions.groupby(["visitorid", "week"], sort=False).size().rename("sessions").reset_index()
        counts = features[["visitorid", "snapshot_date"]].copy()
        counts["baseline"] = 0.0
        counts["observation"] = 0.0
        for snapshot, indices in counts.groupby("snapshot_date", sort=True).groups.items():
            t = pd.Timestamp(snapshot)
            ids = counts.loc[indices, "visitorid"]
            by_snapshot = weekly.loc[weekly.visitorid.isin(ids)]
            base = by_snapshot.loc[(by_snapshot.week >= t - pd.Timedelta(7 * (scenario["baseline_weeks"] + scenario["observation_weeks"]), "D")) &
                                   (by_snapshot.week < t - pd.Timedelta(7 * scenario["observation_weeks"], "D"))]
            obs = by_snapshot.loc[(by_snapshot.week >= t - pd.Timedelta(7 * scenario["observation_weeks"], "D")) & (by_snapshot.week < t)]
            counts.loc[indices, "baseline"] = base.groupby("visitorid").sessions.sum().reindex(ids, fill_value=0).to_numpy() / scenario["baseline_weeks"]
            counts.loc[indices, "observation"] = obs.groupby("visitorid").sessions.sum().reindex(ids, fill_value=0).to_numpy() / scenario["observation_weeks"]
        data = labels[["visitorid", "snapshot_date", "future_events", "future_sessions", "horizon_mature"]].merge(counts, on=["visitorid", "snapshot_date"], validate="one_to_one")
        base = data.baseline
        inactive = data.future_events.eq(0)
        ghost = data.future_events.gt(0) & (data.future_sessions / 2 / base < config["labels"]["preferred_theta"]) & base.gt(0)
        recovered = (data.observation / base < config["labels"]["preferred_theta"]) & (data.future_sessions / 2 / base >= config["labels"]["preferred_theta"]) & ~inactive & base.gt(0)
        status = pd.Series("active", index=data.index, dtype="string")
        status.loc[ghost] = "ghost"
        status.loc[recovered] = "recovered"
        status.loc[inactive] = "inactive"
        status.loc[base.le(0) & ~inactive] = "unknown"
        status.loc[~data.horizon_mature] = "unknown"
        results.append({"gap_minutes": int(gap), "sessions_total": int(len(sessions)), "label_counts": _counts(status)})
    return results


def _duplicate_sensitivity(events: pd.DataFrame, config: dict) -> dict:
    kept = events.loc[~events.is_exact_duplicate].copy()
    scenario = config["scenarios"][0]
    traces = list(iter_cohort_snapshots(kept, config, scenario))
    cohort = pd.concat(traces, ignore_index=True)
    cohort = cohort.loc[cohort.history_eligible]
    sessions, _ = build_sessions(kept, int(config["sessions"]["preferred_gap_minutes"]))
    features = build_features(kept, sessions, cohort, config)
    labels = build_labels(kept, sessions, cohort, features, config)
    return {"policy": "exclude excess exact duplicates only for sensitivity; primary pipeline retains them",
            "removed_rows": int(events.is_exact_duplicate.sum()), "remaining_events": int(len(kept)),
            "history_eligible_snapshots": int(len(cohort)), "label_counts": _counts(labels.label_status)}


def _export_details(out: Path, features: pd.DataFrame, labels: pd.DataFrame, weekly: pd.DataFrame) -> int:
    customers = json.loads((out / "customers.json").read_text(encoding="utf-8"))
    customer_by_pair = {(row["customer_id"], row["snapshot_date"]): row for row in customers}
    weekly["week_start"] = pd.to_datetime(weekly.week_start, utc=True)
    weekly_by_visitor = {int(key): group for key, group in weekly.groupby("visitorid", sort=False)}
    merged = features.merge(labels, on=["visitorid", "snapshot_date"], validate="one_to_one")
    count = 0
    for visitor, rows in merged.groupby("visitorid", sort=False):
        visitor_weekly = weekly_by_visitor.get(int(visitor), weekly.iloc[:0])
        for _, row in rows.iterrows():
            t = pd.Timestamp(row.snapshot_date)
            customer = customer_by_pair[(str(visitor), t.strftime("%Y-%m-%d"))]
            end = pd.Timestamp(row.label_end_utc)
            visible = visitor_weekly.loc[(visitor_weekly.week_start >= t - pd.Timedelta(42, "D")) & (visitor_weekly.week_start < end)]
            timeline = []
            for _, week in visible.iterrows():
                start = week.week_start
                phase = "baseline" if start < t - pd.Timedelta(14, "D") else "observation" if start < t else "confirmation"
                timeline.append({"week_start": start.strftime("%Y-%m-%d"), "views": int(week.views), "carts": int(week.carts),
                                 "purchases": int(week.purchases), "sessions": int(week.sessions), "active_days": int(week.active_days), "phase": phase})
            columns = ["feature_sessions_1w", "feature_sessions_2w", "feature_sessions_4w", "feature_sessions_6w",
                       "feature_views_1w", "feature_views_2w", "feature_views_4w", "feature_views_6w",
                       "feature_days_since_last_view", "feature_days_since_last_cart", "feature_days_since_last_purchase", "feature_decay_ratio"]
            current = {name: None if pd.isna(row[name]) else float(row[name]) for name in columns}
            detail = {"customer": customer, "current_features": current, "weekly_timeline": timeline,
                      "status": customer["status"], "dataset_notice": "Retailrocket derived snapshot; proposed label, not approved research finding"}
            folder = out / "customer_details" / customer["snapshot_date"]
            folder.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256(customer["customer_id"].encode("utf-8")).hexdigest()
            (folder / f"{digest}.json").write_text(json.dumps(detail, allow_nan=False), encoding="utf-8")
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate supplementary Retailrocket evidence and customer details")
    parser.add_argument("--config", type=Path, default=ROOT / "data/config/pipeline.json")
    parser.add_argument("--skip-duplicate-sensitivity", action="store_true", help="Skip the full duplicate-exclusion reprocessing step")
    args = parser.parse_args()
    config = load_config(args.config)
    source = verify_source(ROOT / config["source"]["raw_path"], config["source"]["sha256"])
    out = ROOT / "data/processed"
    events = pd.read_parquet(out / "events_clean.parquet")
    sessions = pd.read_parquet(out / "sessions.parquet")
    features = pd.read_parquet(out / "customer_features.parquet")
    labels = pd.read_parquet(out / "customer_labels.parquet")
    weekly = pd.read_parquet(out / "customer_weekly.parquet")

    primary_scenario = config["scenarios"][0]
    traces = list(iter_cohort_snapshots(events, config, primary_scenario))
    primary_flow = []
    for trace in traces:
        primary_flow.append({"scenario_id": primary_scenario["id"], "snapshot_date": trace.snapshot_date.iloc[0].strftime("%Y-%m-%d"),
                            "candidates": int(len(trace)), "history_eligible": int(trace.history_eligible.sum()),
                            "audit_complete": int(trace.eligible_audit.sum()), "research_complete": int(trace.eligible_research.sum()),
                            "censored_history_eligible": int((trace.history_eligible & ~trace.horizon_mature).sum())})
    cohort_flow = {"primary_scenario": primary_flow, "window_comparison": _window_sensitivity(events, config),
                   "eligibility": "min 5 history events, at least 2 active weeks, baseline activity; audit vs research eligibility shown separately"}
    (out / "cohort_flow.json").write_text(json.dumps(cohort_flow, indent=2), encoding="utf-8")

    sensitivity = {"scenario": primary_scenario["id"], "label_sensitivity": _label_sensitivity(labels, features),
                   "session_gap_sensitivity": _gap_sensitivity(events, features, labels, config)}
    if not args.skip_duplicate_sensitivity:
        sensitivity["duplicate_exclusion"] = _duplicate_sensitivity(events, config)
    (out / "sensitivity.json").write_text(json.dumps(sensitivity, indent=2), encoding="utf-8")
    details = _export_details(out, features, labels, weekly)

    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    manifest.update({"source": source, "config_sha256": _sha(args.config),
                     "git_revision": subprocess.run(["git", "-c", f"safe.directory={ROOT}", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
                     "python": platform.python_version(), "pandas": pd.__version__,
                     "supplementary_rows": {"customer_details": details, "window_scenarios": len(cohort_flow["window_comparison"])}})
    manifest["supplementary_sha256"] = {str(path.relative_to(out)): _sha(path) for path in (out / "cohort_flow.json", out / "sensitivity.json")}
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"window_comparison": cohort_flow["window_comparison"], "sensitivity": sensitivity,
                      "customer_details": details, "source_sha256": source["sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
