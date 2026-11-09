# BE-07 Simple and multiple linear regression

The first predictor defines the simple OLS model; the full explicit allowlist defines multiple OLS. Outputs include coefficient/p/95% CI, R2/adjusted R2, held-out errors and residual/QQ plots. HC3 is used for unique training visitors, cluster covariance for repeated visitors. Inference is associational, not causal. BE-09 remains responsible for fuller model diagnostics/sensitivity.

Install `python -m pip install -r research/regression/requirements-ols.txt`. The backend's lightweight dependencies and contract are unchanged. CSV must contain visitorid, snapshot_date, feature_max_event_time, outcome_end, next_engagement and the explicitly chosen predictor columns. IDs are strings. Dates/timestamps are interpreted in UTC. The data owner must establish genuine pre-T provenance; a supplied max-event field is only a check. Unknown/immature outcomes are not imputed. Missing mature values fail for explicit preprocessing review.

Example after approved data and cutoffs exist:

```bash
python -m research.regression.linear_models --input data/processed/regression_inputs.csv --output-dir data/processed/ols --predictors sessions_4w recency_days --train-end 2015-07-13 --test-start 2015-07-20 --observed-through 2015-09-14 --data-mode real --outcome-definition "Approved future continuous engagement index; units and horizon in D-02"
python -m pytest backend/tests research/regression/tests/test_linear_models.py -q
```

Dates above are illustrative, not a selected split. Training snapshots and their outcome ends must be <= train-end; test snapshots begin at test-start and their outcomes must be mature at observed-through. Test visitors appearing in training are excluded and counted. This conservative design may leave too little data; select D-05 on coverage evidence, not after inspecting test performance.

The target must have a defensible continuous definition. A session count is not automatically a suitable Gaussian response. Inspect count-model alternatives, residuals and negative predictions. Singular designs, constant responses, missing dates and nonfinite inference fail explicitly. No binary model is silently substituted.

Outputs are research JSON/CSV/PNG, not the frontend StatisticsResponse. Review E-05 and adapt approved results to the API in a later integration PR. This task does not overwrite research/statistics/results.json or claim empirical completion. Synthetic tests verify planted effects, cluster handling, temporal separation and failure paths; no synthetic result is committed as research evidence.
