"""Train-only preprocessing (AI-04).

All statistics (medians, scaling) are learned inside an sklearn Pipeline, so
they are fitted on the training split only and re-applied unchanged to
validation, test and inference rows.

- counts / rates / days  -> log1p (heavy right skew), negative values clipped to 0
- slopes (can be < 0)    -> kept linear
- booleans / *_is_null   -> 0/1, no transform
- missing values         -> median imputation + missing-indicator columns
- linear models / SVM    -> standard scaling afterwards
"""
from __future__ import annotations

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

BINARY_HINTS = ("_is_null", "any_purchase_pre")
SIGNED_HINTS = ("slope",)


def _log1p_nonneg(x):
    return np.log1p(np.clip(x, 0, None))


def feature_groups(features: list[str]) -> dict[str, list[str]]:
    binary = [f for f in features if f.endswith(BINARY_HINTS) or any(h in f for h in BINARY_HINTS)]
    signed = [f for f in features if f not in binary and any(h in f for h in SIGNED_HINTS)]
    skewed = [f for f in features if f not in binary and f not in signed]
    return {"skewed": skewed, "signed": signed, "binary": binary}


def build_preprocessor(features: list[str], scale: bool) -> Pipeline:
    groups = feature_groups(features)
    blocks = []
    if groups["skewed"]:
        blocks.append(("skewed", Pipeline([
            ("impute", SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True)),
            ("log1p", FunctionTransformer(_log1p_nonneg, feature_names_out="one-to-one")),
        ]), groups["skewed"]))
    if groups["signed"]:
        blocks.append(("signed", SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True),
                       groups["signed"]))
    if groups["binary"]:
        blocks.append(("binary", SimpleImputer(strategy="most_frequent", keep_empty_features=True),
                       groups["binary"]))
    steps = [("columns", ColumnTransformer(blocks, remainder="drop", verbose_feature_names_out=False))]
    if scale:
        steps.append(("scale", StandardScaler()))
    return Pipeline(steps)
