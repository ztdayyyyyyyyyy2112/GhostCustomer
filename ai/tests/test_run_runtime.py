"""End-to-end run (AI-09/10/11/13 outputs) and the backend runtime (AI-12)."""
import json

import joblib
import pandas as pd
import pytest

from ai.inference import runtime
from ai.training import config
from backend.app.schemas.api import ModelMetricsResponse, PredictResponse


# ---------------------------------------------------------------- run outputs
def test_run_writes_reviewable_outputs(trained):
    summary, out, model_path, _ = trained
    for name in ["metrics.json", "split_manifest.json", "model_comparison.csv", "tuning.csv", "ablation.csv",
                 "threshold_study.csv", "permutation_importance.csv", "attribution_summary.csv",
                 "run_summary.json", "model_meta.json", "figures/model_pr_roc.png",
                 "figures/model_calibration.png", "figures/model_confusion_matrix.png"]:
        assert (out / name).exists(), name
    assert model_path.exists() and summary["synthetic"] is True


def test_metrics_json_matches_backend_contract(trained):
    _, out, _, _ = trained
    m = ModelMetricsResponse.model_validate(json.loads((out / "metrics.json").read_text()))
    assert m.evaluation_context.split == "test"
    assert m.evaluation_context.model_version.startswith("synthetic-")
    assert "SYNTHETIC" in m.dataset_notice
    tn_fp, fn_tp = m.confusion_matrix
    test_row = next(r for r in m.models if r.model_version == m.evaluation_context.model_version and r.split == "test")
    assert sum(tn_fp) + sum(fn_tp) == test_row.support
    assert sum(b.n for b in m.calibration) == test_row.support


def test_threshold_and_selection_use_validation_only(trained):
    summary, out, _, _ = trained
    tuning = pd.read_csv(out / "tuning.csv")
    assert set(tuning.columns) >= {"model", "params", "val_pr_auc"} and "test_pr_auc" not in tuning
    assert "validation" in summary["threshold"]["rule"]


def test_ablation_reports_circularity_diagnostic(trained):
    _, out, _, _ = trained
    ab = pd.read_csv(out / "ablation.csv")
    assert set(ab.feature_set) == set(config.FEATURE_SETS)


def test_synthetic_run_cannot_overwrite_tracked_results(merged):
    from ai.training.run import run
    with pytest.raises(ValueError):
        run(out_dir=config.EVALUATION_DIR, synthetic=True, merged=merged, n_boot=5, make_figures=False)


# ---------------------------------------------------------------- runtime
@pytest.fixture
def rt(trained, monkeypatch):
    _, _, model_path, features_csv = trained
    monkeypatch.setenv("GHOST_MODEL_PATH", str(model_path))
    monkeypatch.setenv("GHOST_FEATURES_PATH", str(features_csv))
    runtime.reload()
    yield runtime
    runtime.reload()


@pytest.fixture
def known_row(trained):
    _, _, _, features_csv = trained
    row = pd.read_csv(features_csv).iloc[0]
    return str(row.customer_id), pd.Timestamp(row.snapshot_date).strftime("%Y-%m-%d")


def test_predict_by_id_matches_contract(rt, known_row):
    cid, snap = known_row
    out = rt.predict({"customer_id": cid, "snapshot_date": snap})
    PredictResponse.model_validate(out)
    assert out["risk_label"] in {"low", "medium", "high"}
    assert len(out["top_factors"]) <= runtime.TOP_K
    json.dumps(out)


def test_predict_by_features_equals_id_path(rt, known_row, trained):
    _, _, model_path, features_csv = trained
    cid, snap = known_row
    art = joblib.load(model_path)
    table = pd.read_csv(features_csv)
    row = table[(table.customer_id.astype(str) == cid)].iloc[0]
    feats = {f: (None if pd.isna(row[f]) else (bool(row[f]) if isinstance(row[f], (bool,)) else float(row[f])))
             for f in art["features"]}
    a = rt.predict({"customer_id": cid, "snapshot_date": snap})
    b = rt.predict({"features": feats})
    assert a["score"] == pytest.approx(b["score"], abs=1e-4)


@pytest.mark.parametrize("payload,exc", [
    ({"customer_id": "no-such-visitor", "snapshot_date": "2015-07-06"}, LookupError),
    ({"customer_id": "1", "snapshot_date": "2015-02-30"}, ValueError),
    ({"customer_id": "1"}, ValueError),
    ({}, ValueError),
    ({"features": {}}, ValueError),
    ({"features": {"feature_sessions_4w": 2, "future_events": 3}}, ValueError),
    ({"features": {"feature_sessions_4w": 2}}, ValueError),
    ("not a dict", ValueError),
])
def test_invalid_requests(rt, payload, exc):
    with pytest.raises(exc):
        rt.predict(payload)


def test_both_id_and_features_rejected(rt, known_row):
    cid, snap = known_row
    with pytest.raises(ValueError):
        rt.predict({"customer_id": cid, "snapshot_date": snap, "features": {"feature_sessions_4w": 1}})


def test_feature_values_validated(rt, trained):
    art = joblib.load(trained[2])
    base = {f: 0 for f in art["features"]}
    with pytest.raises(ValueError):
        rt.predict({"features": {**base, art["features"][0]: "abc"}})
    with pytest.raises(ValueError):
        rt.predict({"features": {**base, "feature_sessions_4w": -1}})
    with pytest.raises(ValueError):
        rt.predict({"features": {f: None for f in art["features"]}})
    assert 0 <= rt.predict({"features": base})["score"] <= 1


def test_post_t_feature_row_refused(trained, monkeypatch, tmp_path, known_row):
    _, _, model_path, features_csv = trained
    cid, snap = known_row
    table = pd.read_csv(features_csv)
    mask = (table.customer_id.astype(str) == cid) & (pd.to_datetime(table.snapshot_date, utc=True).dt.strftime("%Y-%m-%d") == snap)
    table.loc[mask, "feature_max_event_time_utc"] = f"{snap}T00:00:00Z"
    bad = tmp_path / "bad.csv"
    table.to_csv(bad, index=False)
    monkeypatch.setenv("GHOST_MODEL_PATH", str(model_path))
    monkeypatch.setenv("GHOST_FEATURES_PATH", str(bad))
    runtime.reload()
    with pytest.raises(ValueError):
        runtime.predict({"customer_id": cid, "snapshot_date": snap})
    runtime.reload()


def test_missing_model_is_runtime_error(monkeypatch, tmp_path):
    monkeypatch.setenv("GHOST_MODEL_PATH", str(tmp_path / "none.joblib"))
    runtime.reload()
    with pytest.raises(RuntimeError):
        runtime.predict({"customer_id": "1", "snapshot_date": "2015-07-06"})
    runtime.reload()


def test_model_loaded_once(rt, known_row, monkeypatch):
    calls = []
    real = joblib.load
    monkeypatch.setattr(runtime.joblib, "load", lambda p: calls.append(p) or real(p))
    rt.reload()
    for _ in range(3):
        rt.predict({"customer_id": known_row[0], "snapshot_date": known_row[1]})
    assert len(calls) == 1
