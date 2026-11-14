# Data dictionary — proposed v1

This is the handoff schema for the Retailrocket event pipeline. It distinguishes an anonymous `visitorid` from the API's string `customer_id`. Feature intervals are half-open and end at snapshot T: an event exactly at T is future data and cannot affect a feature. Labels use the confirmation interval `[T,T+C)`; immature confirmation windows have `label_status=unknown` and null targets. Current parameters are proposals, not approvals for D-01–D-04.

## Feature row

One row is `(visitorid, snapshot_date, scenario_id)`. `customer_id` is `str(visitorid)` for the API; it is not a source identity. `snapshot_index` orders repeated snapshots for a visitor. All `feature_*` fields use only raw event timestamps `< T`.

| Column | Type / unit | Definition / null rule |
|---|---|---|
| `visitorid` | int64 | Retailrocket anonymous visitor ID. |
| `customer_id` | string | String form of `visitorid`, for API/display only. |
| `snapshot_date` | ISO date, UTC Monday | Snapshot T at 00:00 UTC. |
| `scenario_id` | string | Window/eligibility configuration identifier. |
| `snapshot_index` | int32 | Zero-based chronological snapshot index per visitor. |
| `feature_max_event_time_utc` | ISO-8601 UTC timestamp | Maximum actual event timestamp used; must be `< snapshot_date` at 00:00 UTC. |
| `feature_sessions_{1,2,4,6}w` | count | Sessions with start in the preceding half-open window. |
| `feature_views_{1,2,4,6}w` | count | View events in the preceding window, counted once per raw row. |
| `feature_carts_{1,2,4,6}w` | count | Add-to-cart events in the preceding window. |
| `feature_purchases_{1,2,4,6}w` | count | Transaction events in the preceding window; not merged with carts. |
| `feature_events_{1,2,4,6}w` | count | All event rows in the preceding window, including retained duplicates. |
| `feature_active_days_4w` | days | Distinct UTC event dates in the preceding four weeks. |
| `feature_recency_days` | days | T minus the latest pre-T event. |
| `feature_days_since_last_{view,cart,purchase}` | days or null | T minus latest matching pre-T event; null if never observed. |
| `feature_frequency_events_per_active_week` | events/week | Pre-T event count divided by active pre-T weeks; null if no active week. |
| `feature_baseline_sessions_per_week` | sessions/week | Sessions in B divided by B weeks; used by the proposed label and flagged as target-component. |
| `feature_observation_sessions_per_week` | sessions/week | Sessions in O divided by O weeks. |
| `feature_decay_ratio` | ratio or null | Observation sessions/week divided by baseline sessions/week; null and `feature_decay_ratio_is_null=true` when baseline rate is zero. |
| `feature_eds` | score or null | `max(0, 1 - feature_decay_ratio)`; null and corresponding flag when ratio is null. This is a descriptive feature, not a probability. |
| `feature_slope_sessions_6w` | sessions/week² or null | OLS slope of weekly sessions over six pre-T weeks; null when fewer than three weeks are observed, with a null flag. |
| `feature_cart_to_view` | ratio or null | Pre-T carts divided by views; null and flag when no views exist. |
| `feature_any_purchase_pre` | boolean | Whether any pre-T transaction exists. |
| `feature_n_distinct_items_pre` | count | Distinct pre-T item IDs; raw item IDs are not exposed as predictors. |
| `feature_total_events_pre` | count | All pre-T event rows, including retained duplicates. |
| `*_is_null` | boolean | Explicitly distinguishes undefined ratios/slopes from numeric zero. |
| `is_synthetic` | boolean, mock only | `true` on every tracked sample row; never appears on real processed rows. |

The relative-label denominator uses baseline sessions/week. Kiệt should run the baseline-only circularity diagnostic and compare the model without `feature_baseline_sessions_per_week`, `feature_decay_ratio`, and `feature_eds`; do not claim independent predictive evidence from a feature that directly defines the target.

## Label row

`customer_labels.parquet` contains `visitorid`, `snapshot_date`, `label_end_utc`, `label_status`, `target_ghost`, `target_disengaged`, `future_activity`, `future_engagement_rate`, `horizon_mature`, `label_rule_id`, `label_version`, and `params_hash`. The proposed session-based rule compares confirmation sessions/week with baseline sessions/week using theta 0.5, 0.4, or 0.3. `inactive` has zero future events; `ghost` is still active but below the baseline ratio; `recovered` dipped below theta in O then returned to or above theta in C; remaining mature cases are `active`; immature C is `unknown`. Unknown targets are null. A no-purchase variant is reported separately.

The minimal forecast handoff CSV has exactly `visitorid,snapshot_date,label_end,label_status,target_ghost`. Regression input includes `visitorid,snapshot_date,feature_max_event_time,outcome_end,next_engagement` followed by the chosen predictor columns; `next_engagement=log1p(confirmation sessions per week)` in the proposed export.

