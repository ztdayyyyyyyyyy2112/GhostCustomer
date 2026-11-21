"""AI-01 / AI-03: schema, leakage audit and visitor-aware temporal split."""
import pandas as pd
import pytest

from ai.training import config
from ai.training.data import build_supervised, check_no_forbidden, feature_set, leakage_audit, to_matrix
from ai.training.split import SplitPlan, assign_split, export_benchmark_csv, manifest, split_frames


def test_supervised_rows_are_mature_active_or_ghost(supervised):
    assert set(supervised.label_status) == {"active", "ghost"}
    assert (supervised.y == (supervised.label_status == "ghost")).all()
    assert (supervised.label_end_utc > supervised.snapshot_date).all()


def test_ghost_vs_rest_task_keeps_inactive_and_recovered(merged):
    rest = build_supervised(merged, "ghost_vs_rest")
    assert {"inactive", "recovered"} <= set(rest.label_status)
    assert "unknown" not in set(rest.label_status)


def test_leakage_audit_catches_post_t_feature(supervised):
    bad = supervised.head(5).copy()
    bad.loc[bad.index[0], "feature_max_event_time_utc"] = bad.snapshot_date.iloc[0] + pd.Timedelta(hours=1)
    assert leakage_audit(bad, pd.Timestamp("2015-09-14", tz="UTC"))["features_before_snapshot"] is False


@pytest.mark.parametrize("bad", ["visitorid", "customer_id", "snapshot_date", "target_ghost", "label_status",
                                 "future_events", "feature_max_event_time_utc", "split", "scenario_id"])
def test_forbidden_inputs_rejected(bad):
    with pytest.raises(ValueError):
        check_no_forbidden(["feature_sessions_4w", bad])


def test_feature_sets(supervised):
    full = feature_set(supervised, "full")
    no_tc = feature_set(supervised, "no_target_components")
    observation = feature_set(supervised, "observation_only")
    assert observation
    assert all(name.endswith(("_1w", "_2w")) for name in observation)
    assert "feature_max_event_time_utc" not in full and all(c.startswith("feature_") for c in full)
    assert not set(config.TARGET_COMPONENT_FEATURES) & set(no_tc)
    assert feature_set(supervised, "baseline_only") == ["feature_baseline_sessions_per_week"]


def test_to_matrix_handles_bool_and_inf():
    df = pd.DataFrame({"feature_a": [True, False], "feature_b": [1.0, float("inf")]})
    X = to_matrix(df, ["feature_a", "feature_b"])
    assert X.feature_a.tolist() == [1.0, 0.0] and X.feature_b.isna().tolist() == [False, True]


def test_splits_are_time_ordered_and_purged(parts):
    tr, va, te = parts["train"], parts["validation"], parts["test"]
    assert tr.snapshot_date.max() < va.snapshot_date.min() <= va.snapshot_date.max() < te.snapshot_date.min()
    assert tr.label_end_utc.max() < va.snapshot_date.min()
    assert va.label_end_utc.max() < te.snapshot_date.min()


def test_visitors_never_cross_splits(parts):
    ids = {k: set(v.customer_id) for k, v in parts.items()}
    assert not ids["train"] & ids["validation"]
    assert not ids["train"] & ids["test"]
    assert not ids["validation"] & ids["test"]


def test_test_period_is_last_mature_weeks(supervised, parts, plan):
    assert parts["test"].snapshot_date.max() == supervised.snapshot_date.max()
    assert plan.test_start == parts["test"].snapshot_date.min().strftime("%Y-%m-%d")


def test_split_is_deterministic(supervised, plan, parts):
    again = split_frames(supervised, plan)
    for k in parts:
        pd.testing.assert_frame_equal(parts[k], again[k])
    m1 = manifest(supervised, parts, plan, ["feature_sessions_4w"], "ghost_vs_active")
    m2 = manifest(supervised, again, plan, ["feature_sessions_4w"], "ghost_vs_active")
    assert m1["assignment_sha256"] == m2["assignment_sha256"]


def test_visitor_bucket_does_not_depend_on_behaviour(supervised, plan):
    a = assign_split(supervised, plan)
    flipped = supervised.assign(y=1 - supervised.y, feature_sessions_4w=0)
    pd.testing.assert_series_equal(a, assign_split(flipped, plan))


def test_bad_fractions_rejected(supervised, plan):
    bad = SplitPlan(**{**plan.__dict__, "visitor_fractions": (0.5, 0.5, 0.5)})
    with pytest.raises(ValueError):
        assign_split(supervised, bad)


def test_benchmark_csv_passes_shared_validator(parts, supervised, tmp_path):
    from research.baselines import decision_tree as dt
    feats = feature_set(supervised, "no_target_components")
    path = tmp_path / "modeling_snapshots.csv"
    export_benchmark_csv(parts, feats, path)
    records, excluded = dt.read_input(path, feats, pd.Timestamp("2015-09-14").date())
    groups = dt.validate_splits(records)
    assert {k: len(v) for k, v in groups.items()} == {
        "train": len(parts["train"]), "validation": len(parts["validation"]), "test": len(parts["test"])}


def test_time_only_sensitivity_keeps_more_rows(supervised, parts):
    from ai.training.split import plan_split
    loose = split_frames(supervised, plan_split(supervised, visitor_disjoint=False))
    assert sum(len(v) for v in loose.values()) > sum(len(v) for v in parts.values())
    assert loose["train"].label_end_utc.max() < loose["validation"].snapshot_date.min()
