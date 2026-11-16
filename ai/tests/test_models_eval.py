"""AI-02, AI-04 .. AI-11 building blocks."""
import numpy as np
import pandas as pd
import pytest

from ai.evaluation.metrics import bootstrap_ci, calibration_bins, classification_metrics
from ai.evaluation.threshold import choose_threshold, risk_label, threshold_table
from ai.inference.attribution import local_contributions
from ai.training.data import feature_set, to_matrix
from ai.training.models import PlattCalibrated, RuleScore, ScoreToProba, candidates, fit_candidate
from ai.training.preprocess import build_preprocessor, feature_groups


@pytest.fixture(scope="module")
def xy(parts, supervised):
    feats = feature_set(supervised, "full")
    out = {k: (to_matrix(v, feats), v.y) for k, v in parts.items()}
    return feats, out


# ---------------------------------------------------------------- AI-04
def test_preprocessor_learns_from_train_only(xy):
    feats, d = xy
    X_tr = d["train"][0]
    prep = build_preprocessor(feats, scale=False).fit(X_tr)
    shifted = d["test"][0].copy() * 1000
    prep2 = build_preprocessor(feats, scale=False).fit(X_tr)
    a, b = prep.transform(X_tr), prep2.transform(X_tr)
    np.testing.assert_allclose(a, b)                         # deterministic
    out = prep.transform(shifted)                            # transforming test does not refit
    np.testing.assert_allclose(prep.transform(X_tr), a)
    assert np.isfinite(out).all()


def test_preprocessor_groups():
    g = feature_groups(["feature_views_4w", "feature_slope_sessions_6w", "feature_eds_is_null",
                        "feature_any_purchase_pre"])
    assert g["signed"] == ["feature_slope_sessions_6w"]
    assert set(g["binary"]) == {"feature_eds_is_null", "feature_any_purchase_pre"}


def test_preprocessor_handles_all_missing_column(xy):
    feats, d = xy
    X = d["train"][0].copy()
    X["feature_days_since_last_purchase"] = np.nan
    assert np.isfinite(build_preprocessor(feats, scale=True).fit_transform(X)).all()


# ---------------------------------------------------------------- AI-02 / AI-08 wrappers
def test_rule_score_is_feature_clipped():
    X = pd.DataFrame({"feature_eds": [0.2, None, 1.7]})
    np.testing.assert_allclose(RuleScore().fit(X, [0, 1, 0]).predict_proba(X)[:, 1], [0.2, 0.0, 1.0])


def test_score_to_proba_range(xy):
    from sklearn.ensemble import IsolationForest
    _, d = xy
    m = ScoreToProba(IsolationForest(random_state=0), kind="anomaly").fit(d["train"][0].fillna(0), d["train"][1])
    p = m.predict_proba(d["test"][0].fillna(0))[:, 1]
    assert ((p >= 0) & (p <= 1)).all()


# ---------------------------------------------------------------- AI-05..07 tuning + calibration
def test_tuning_selects_best_validation_score(xy):
    feats, d = xy
    cand = next(c for c in candidates() if c.name == "logistic_regression")
    cand.grid = cand.grid[:3]
    f = fit_candidate(cand, feats, *d["train"], *d["validation"])
    assert f.val_pr_auc == max(t["val_pr_auc"] for t in f.tuning) or abs(
        f.val_pr_auc - max(t["val_pr_auc"] for t in f.tuning)) < 1e-4


def test_platt_calibration_outputs_probabilities(xy, parts):
    feats, d = xy
    base = next(c for c in candidates() if c.name == "logistic_regression").build(feats, {"C": 1.0})
    cal = PlattCalibrated(base).fit(*d["train"], groups=parts["train"].customer_id)
    p = cal.predict_proba(d["validation"][0])[:, 1]
    assert ((p > 0) & (p < 1)).all()


def test_every_candidate_trains(xy):
    feats, d = xy
    for c in candidates(include_optional=True):
        c.grid = c.grid[:1]
        est = fit_candidate(c, feats, *d["train"], *d["validation"]).estimator
        p = est.predict_proba(d["test"][0])[:, 1]
        assert p.shape == (len(d["test"][0]),) and np.nanmin(p) >= 0 and np.nanmax(p) <= 1


# ---------------------------------------------------------------- AI-09
def test_confusion_matrix_orientation():
    m = classification_metrics([0, 0, 1, 1, 1], [0.1, 0.8, 0.9, 0.2, 0.7], 0.5)
    assert m["confusion_matrix"] == [[1, 1], [1, 2]]      # [[TN, FP], [FN, TP]]
    assert m["precision"] == pytest.approx(2 / 3) and m["recall"] == pytest.approx(2 / 3)
    assert m["prevalence"] == pytest.approx(0.6) and m["support"] == 5


def test_non_probabilistic_scores_have_no_brier():
    assert classification_metrics([0, 1], [0.2, 0.9], 0.5, probabilistic=False)["brier"] is None


def test_calibration_bins_cover_all_rows():
    rng = np.random.default_rng(0)
    s = rng.random(300)
    y = (rng.random(300) < s).astype(int)
    bins = calibration_bins(y, s)
    assert sum(b["n"] for b in bins) == 300


def test_bootstrap_resamples_visitors_deterministically():
    y = np.array([0, 1] * 50)
    s = np.linspace(0, 1, 100)
    g = np.repeat(np.arange(20), 5)
    a, b = bootstrap_ci(y, s, g, 0.5, n_boot=50), bootstrap_ci(y, s, g, 0.5, n_boot=50)
    assert a == b and a["unit"] == "visitor" and a["pr_auc"][0] <= a["pr_auc"][1]


# ---------------------------------------------------------------- AI-10
def test_threshold_choice_minimises_cost():
    y = np.array([0] * 80 + [1] * 20)
    s = np.r_[np.linspace(0, 0.6, 80), np.linspace(0.4, 1, 20)]
    table = threshold_table(y, s)
    choice = choose_threshold(table)
    assert table.loc[table.threshold == choice["operating_threshold"], "expected_cost"].item() == table.expected_cost.min()
    assert choice["bands"]["medium"] <= choice["bands"]["high"]
    assert risk_label(0.99, choice["bands"]) == "high" and risk_label(0.0, choice["bands"]) == "low"


# ---------------------------------------------------------------- AI-11
def test_local_contributions_sign_and_order(xy):
    feats, d = xy
    est = next(c for c in candidates() if c.name == "logistic_regression").build(feats, {"C": 1.0})
    est.fit(*d["train"])
    baseline = d["train"][0].median().to_dict()
    rows = local_contributions(est, d["test"][0].head(3), baseline, top_k=5)
    for r in rows:
        assert len(r) <= 5
        mags = [abs(x["contribution"]) for x in r]
        assert mags == sorted(mags, reverse=True)
    same = local_contributions(est, pd.DataFrame([baseline])[feats], baseline, top_k=None)
    assert same[0] == []                                   # at the baseline nothing moves the score
