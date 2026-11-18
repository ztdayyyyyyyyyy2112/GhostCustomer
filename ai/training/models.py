"""Model zoo: baselines (AI-02), Logistic (AI-05), Random Forest (AI-06),
gradient boosting (AI-07), optional SVM / Isolation Forest (AI-08), and
post-hoc calibration.

Each candidate is an sklearn-compatible estimator taking the raw feature
DataFrame (preprocessing is inside the pipeline). Hyper-parameters are
chosen on the validation split by PR-AUC; the test split is never used here.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin, clone
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, IsolationForest, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC

from . import config
from .preprocess import build_preprocessor

try:  # optional dependency; HistGradientBoosting is used when absent
    from xgboost import XGBClassifier  # type: ignore
except Exception:  # pragma: no cover - depends on environment
    XGBClassifier = None


# --------------------------------------------------------------------------- baselines (AI-02)
class RuleScore(BaseEstimator, ClassifierMixin):
    """Benchmark that ranks rows by one pre-T feature (e.g. EDS). Not a trained model."""

    def __init__(self, feature: str = "feature_eds", fill: float = 0.0):
        self.feature = feature
        self.fill = fill

    def fit(self, X, y):
        self.classes_ = np.array([0, 1])
        return self

    def predict_proba(self, X):
        s = pd.to_numeric(pd.DataFrame(X)[self.feature], errors="coerce").fillna(self.fill)
        s = np.clip(s.to_numpy(dtype=float), 0, 1)
        return np.column_stack([1 - s, s])

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)


class ScoreToProba(BaseEstimator, ClassifierMixin):
    """Wrap estimators without predict_proba (SVM decision function,
    Isolation Forest anomaly score) as a monotone rank score in [0, 1].
    The output ranks rows; it is NOT a calibrated probability."""

    def __init__(self, estimator=None, kind: str = "decision"):
        self.estimator = estimator
        self.kind = kind

    def fit(self, X, y):
        self.estimator_ = clone(self.estimator)
        if self.kind == "anomaly":
            self.estimator_.fit(X)
        else:
            self.estimator_.fit(X, y)
        raw = self._raw(X)
        self.lo_, self.hi_ = float(np.min(raw)), float(np.max(raw))
        self.classes_ = np.array([0, 1])
        return self

    def _raw(self, X):
        if self.kind == "anomaly":
            return -self.estimator_.score_samples(X)        # higher = more anomalous
        return self.estimator_.decision_function(X)

    def predict_proba(self, X):
        s = (self._raw(X) - self.lo_) / max(self.hi_ - self.lo_, 1e-12)
        s = np.clip(s, 0, 1)
        return np.column_stack([1 - s, s])

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)


# --------------------------------------------------------------------------- calibration
class PlattCalibrated(BaseEstimator, ClassifierMixin):
    """Sigmoid (Platt) calibration fitted on visitor-grouped out-of-fold
    predictions of the TRAINING split, then the base model is refit on all of
    train. Validation/test are never used to fit the calibrator."""

    def __init__(self, estimator=None, n_splits: int = 3):
        self.estimator = estimator
        self.n_splits = n_splits

    def fit(self, X, y, groups=None):
        y = np.asarray(y)
        groups = np.asarray(groups) if groups is not None else np.arange(len(y))
        oof = np.full(len(y), np.nan)
        for tr, te in GroupKFold(n_splits=self.n_splits).split(X, y, groups):
            m = clone(self.estimator).fit(_rows(X, tr), y[tr])
            oof[te] = m.predict_proba(_rows(X, te))[:, 1]
        self.calibrator_ = LogisticRegression(C=1e6).fit(_logit(oof).reshape(-1, 1), y)
        self.estimator_ = clone(self.estimator).fit(X, y)
        self.classes_ = np.array([0, 1])
        return self

    def predict_proba(self, X):
        raw = self.estimator_.predict_proba(X)[:, 1]
        p = self.calibrator_.predict_proba(_logit(raw).reshape(-1, 1))[:, 1]
        return np.column_stack([1 - p, p])

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)


def _rows(X, idx):
    return X.iloc[idx] if hasattr(X, "iloc") else X[idx]


def _logit(p):
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


# --------------------------------------------------------------------------- candidates
@dataclass
class Candidate:
    name: str
    family: str
    build: callable                    # (features, params) -> estimator
    grid: list[dict] = field(default_factory=lambda: [{}])
    probabilistic: bool = True         # False -> rank score only (no Brier/calibration claims)
    max_train_rows: int | None = None  # subsample for expensive models (SVM)


def _pipe(features, model, scale):
    return Pipeline([("prep", build_preprocessor(features, scale=scale)), ("model", model)])


def candidates(include_optional: bool = False, has_eds: bool = True) -> list[Candidate]:
    seed = config.SEED
    out = [
        Candidate("majority", "baseline", lambda f, p: DummyClassifier(strategy="prior")),
        Candidate("logistic_regression", "linear",
                  lambda f, p: _pipe(f, LogisticRegression(max_iter=2000, random_state=seed, **p), scale=True),
                  [{"C": c, "class_weight": w} for c in (0.01, 0.1, 1.0, 10.0) for w in (None, "balanced")]),
        Candidate("random_forest", "tree",
                  lambda f, p: _pipe(f, RandomForestClassifier(n_estimators=300, n_jobs=-1, random_state=seed, **p),
                                     scale=False),
                  [{"max_depth": d, "min_samples_leaf": leaf, "class_weight": w}
                   for d in (6, 12) for leaf in (5, 25) for w in (None, "balanced_subsample")]),
    ]
    if has_eds:
        out.insert(1, Candidate("rule_eds", "baseline", lambda f, p: RuleScore("feature_eds")))
    if XGBClassifier is not None:
        out.append(Candidate("xgboost", "boosting",
                             lambda f, p: _pipe(f, XGBClassifier(n_estimators=400, learning_rate=0.05, subsample=0.8,
                                                                 colsample_bytree=0.8, eval_metric="aucpr",
                                                                 random_state=seed, n_jobs=-1, **p), scale=False),
                             [{"max_depth": d, "min_child_weight": w} for d in (3, 5) for w in (1, 10)]))
    else:
        out.append(Candidate("hist_gradient_boosting", "boosting",
                             lambda f, p: _pipe(f, HistGradientBoostingClassifier(
                                 learning_rate=0.05, max_iter=400, early_stopping=True, validation_fraction=0.15,
                                 random_state=seed, **p), scale=False),
                             [{"max_depth": d, "min_samples_leaf": leaf} for d in (3, 6) for leaf in (20, 60)]))
    if include_optional:
        out.append(Candidate("svm_rbf", "optional",
                             lambda f, p: ScoreToProba(_pipe(f, SVC(kernel="rbf", random_state=seed, **p), scale=True)),
                             [{"C": c, "class_weight": "balanced"} for c in (0.3, 1.0, 3.0)],
                             probabilistic=False, max_train_rows=8000))
        out.append(Candidate("isolation_forest", "optional",
                             lambda f, p: ScoreToProba(_pipe(f, IsolationForest(n_estimators=300, random_state=seed, **p),
                                                             scale=False), kind="anomaly"),
                             [{"contamination": "auto"}], probabilistic=False))
    return out


@dataclass
class Fitted:
    candidate: Candidate
    params: dict
    estimator: object
    val_pr_auc: float
    tuning: list[dict]


def fit_candidate(cand: Candidate, features, X_tr, y_tr, X_va, y_va) -> Fitted:
    """Grid search on validation PR-AUC (ties -> first/simpler setting)."""
    rng = np.random.default_rng(config.SEED)
    if cand.max_train_rows and len(X_tr) > cand.max_train_rows:
        idx = np.sort(rng.choice(len(X_tr), cand.max_train_rows, replace=False))
        X_tr, y_tr = X_tr.iloc[idx], y_tr.iloc[idx]
    best, tuning = None, []
    for params in cand.grid:
        est = cand.build(features, params).fit(X_tr, y_tr)
        score = float(average_precision_score(y_va, est.predict_proba(X_va)[:, 1]))
        tuning.append({"model": cand.name, "params": params, "val_pr_auc": round(score, 5)})
        if best is None or score > best[0] + 1e-9:
            best = (score, params, est)
    return Fitted(cand, best[1], best[2], best[0], tuning)
