"""Shared settings for the AI/ML pipeline (AI-01).

Everything a reviewer needs to reproduce a run lives here or in the run
manifest. Values marked PROPOSED wait for team decisions (D-03 label mapping,
D-05 split) recorded in docs/decision_log.md.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
FEATURES_PATH = PROCESSED_DIR / "customer_features.parquet"
LABELS_PATH = PROCESSED_DIR / "customer_labels.parquet"
PIPELINE_CONFIG = ROOT / "data" / "config" / "pipeline.json"

EVALUATION_DIR = ROOT / "ai" / "evaluation"           # small, reviewable outputs (tracked)
FIGURES_DIR = EVALUATION_DIR / "figures"
MODELS_DIR = ROOT / "ai" / "models"                   # binaries (ignored by Git)
MODEL_PATH = Path(os.environ.get("GHOST_MODEL_PATH", MODELS_DIR / "ghost_model.joblib"))
DRYRUN_DIR = PROCESSED_DIR / "ai_dryrun"              # synthetic runs land here, never in ai/evaluation

SEED = 3013                                          # same seed as the data pipeline
PIPELINE_VERSION = "ai-pipeline-1.0.0"

# --------------------------------------------------------------------------- keys
KEY_COLUMNS = ["visitorid", "customer_id", "snapshot_date", "scenario_id"]
NON_FEATURE_COLUMNS = {
    "visitorid", "customer_id", "snapshot_date", "scenario_id", "snapshot_index",
    "feature_max_event_time_utc", "is_synthetic",
}

# --------------------------------------------------------------------------- label task (PROPOSED, D-03)
# Matches Thành's Decision Tree / Lâm's Gaussian NB benchmark contract so that
# all RQ3 models are compared on the same rows: ghost (1) vs active (0);
# inactive, recovered, unknown and candidate rows are excluded.
LABEL_TASKS = {
    "ghost_vs_active": {"positive": ["ghost"], "negative": ["active"]},
    # sensitivity: pipeline target_ghost, everyone mature is scored
    "ghost_vs_rest": {"positive": ["ghost"], "negative": ["active", "recovered", "inactive"]},
}
DEFAULT_LABEL_TASK = "ghost_vs_active"

# --------------------------------------------------------------------------- features
# Columns that are inputs to the relative label (r_conf / r_base < theta).
# They are legitimate pre-T values but make the task partly circular, so every
# run reports an ablation without them (see docs/data_dictionary.md).
TARGET_COMPONENT_FEATURES = [
    "feature_baseline_sessions_per_week",
    "feature_decay_ratio", "feature_decay_ratio_is_null",
    "feature_eds", "feature_eds_is_null",
]
OBSERVATION_ONLY_FEATURES = [
    f"feature_{kind}_{weeks}w"
    for kind in ("sessions", "views", "carts", "purchases", "events")
    for weeks in (1, 2)
]
FEATURE_SETS = ("full", "no_target_components", "observation_only", "baseline_only")
PRIMARY_FEATURE_SET = "full"                         # PROPOSED; ablation always reported

# --------------------------------------------------------------------------- split (PROPOSED, D-05)
SPLIT_DEFAULTS = {
    "val_weeks": 2,            # mature snapshot weeks in validation
    "test_weeks": 2,           # last mature snapshot weeks, untouched until the end
    "visitor_fractions": (0.5, 0.25, 0.25),   # train / validation / test visitor buckets
}

# --------------------------------------------------------------------------- threshold (AI-10)
COST_FALSE_NEGATIVE = 5.0      # missing a Ghost costs more than an unnecessary alert
COST_FALSE_POSITIVE = 1.0
MEDIUM_RECALL_TARGET = 0.80    # "medium" band starts where validation recall reaches 80 %

DATASET_NOTICE = (
    "Retailrocket-derived proposed cohort/label; Ghost is an operational label, not proof of churn. "
    "Scores are associations, not causal effects."
)
SYNTHETIC_NOTICE = "SYNTHETIC DRY RUN - generated events, not research results"
