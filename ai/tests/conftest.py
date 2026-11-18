"""Shared fixtures: synthetic events pushed through Lâm's real data functions,
then one full training run. Synthetic numbers are never research results."""
from __future__ import annotations

import pytest

from ai.training.data import build_supervised, merge_features_labels
from ai.training.split import plan_split, split_frames
from ai.training.synthetic import build_processed


@pytest.fixture(scope="session")
def processed(tmp_path_factory):
    f, lab = build_processed(n_visitors=900, seed=11, workdir=tmp_path_factory.mktemp("raw"))
    return f, lab


@pytest.fixture(scope="session")
def merged(processed):
    f, lab = processed
    return merge_features_labels(f, lab).assign(is_synthetic=True)


@pytest.fixture(scope="session")
def supervised(merged):
    return build_supervised(merged)


@pytest.fixture(scope="session")
def plan(supervised):
    return plan_split(supervised)


@pytest.fixture(scope="session")
def parts(supervised, plan):
    return split_frames(supervised, plan)


@pytest.fixture(scope="session")
def trained(merged, processed, tmp_path_factory):
    """One complete synthetic run; returns (summary, out_dir, model_path, features_csv)."""
    from ai.training.run import run
    out = tmp_path_factory.mktemp("run")
    model_path = out / "ghost_model.joblib"
    summary = run(out_dir=out, model_path=model_path, synthetic=True, merged=merged,
                  n_boot=40, make_figures=True)
    features_csv = out / "customer_features.csv"
    processed[0].to_csv(features_csv, index=False)
    return summary, out, model_path, features_csv
