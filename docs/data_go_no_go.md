# Retailrocket data go/no-go (proposed)

Computed from the local source whose SHA-256 is pinned in `data/config/pipeline.json`. Run `python -m data.scripts.run_pipeline --mode audit_compat`, then `python -m data.scripts.export_supplementary` to reproduce core and supplementary outputs. All processed outputs are ignored by Git.

A small reviewable row-count/hash snapshot is committed at `research/feasibility/retailrocket_run_manifest.json`; raw and customer-level processed artifacts remain local and ignored.

## Recommendation

**GO for a reproducible course-project prototype; NO-GO for claiming validated ghost-customer prediction or publishing derived records.** The file has 2,756,101 events and 1,407,580 anonymous visitor IDs, but views are 96.7% of events, exact duplicates are retained and flagged, and `visitorid` is not a verified person/account. The label is a behavioral proxy, not observed churn.

## Primary proposed setup

Use B+O+C = 4+2+2 weeks, minimum 5 history events across at least 2 active weeks, one baseline event, 30-minute sessions, and `sessions/week` confirmation-to-baseline ratio with theta 0.5. Keep `audit_compat` and `research` cohorts visible separately; the latter requires activity during O and changes the target population. These are proposals, not approved decisions (D-01–D-04 remain with Thành/Lâm).

For the primary run, `data/processed/cohort_flow.json` records 85,899 complete audit-eligible snapshots, 24,768 distinct visitors, 20,989 repeat visitors, and 11,590 history-eligible right-censored snapshots. E-00 golden counts are reproduced by `data/scripts/tests/test_cohort.py`. Across the three configured windows, history-eligible snapshot counts are 97,489 (4+2+2), 100,140 (4+3+2), and 128,323 (6+2+4); the last option has 40,043 censored history-eligible snapshots, a substantial coverage cost.

The primary theta sensitivity gives session-based Ghost counts 2,619 / 1,740 / 1,188 for theta 0.5 / 0.4 / 0.3. Event-based counts are 5,127 / 3,997 / 3,027, showing how view-heavy event volume changes the operational label. The no-purchase variant moves 36 / 24 / 15 session-based Ghost rows to Active at those thresholds. With theta 0.5, session gaps 15/30/60 produce 2,998 / 2,619 / 2,310 Ghost rows. These are label sensitivity counts, not churn prevalence estimates.

The configured active-week sensitivity `[2, 3]` was rerun from raw events by `research/feasibility/retailrocket_sensitivity.mjs`, which now reads both eligibility threshold arrays from `data/config/pipeline.json`. For the 4+2+2 window and minimum 5 history events, raising the requirement from 2 to 3 active weeks reduces history-only eligible snapshots from 85,899 to 30,698 (24,768 to 9,179 visitors); the comparable O/C view-cart cohort falls from 11,468 to 8,439, and its diagnostic Ghost-at-50% count falls from 5,039 to 3,569. These Ghost counts use the report's view/cart alternative label and are not the main pipeline's session-based Ghost counts. The main pipeline still uses 2 weeks as its configured primary threshold. This comparison is sensitivity evidence, not an approval of either setting.

E-03 was regenerated from the verified raw file. Its 28 group/metric rows cover each mature non-unknown label group and all seven RQ1 metrics (sessions, views, carts, purchases, active days, recency, and decay), with sample SD, `n_total`, observed `n`, `missing_n`, and `missing_rate`. One missing value occurs for `feature_decay_ratio` in the inactive group (1/71,301; rate 0.0000140, or 0.0014%); all other group/metric combinations have zero missing values. It remains descriptive and preliminary because D-01–D-04 are still open.

## Main risks and gates

- Two latest T dates (2015-08-24 and 2015-08-31) are candidate temporal test snapshots by prior team discussion; freeze only after Kiệt/Long approve visitor grouping and purge overlapping confirmation horizons.
- Relative labels use baseline engagement in their denominator. Report the circularity; compare an ablation without baseline/decay/EDS features before model claims.
- Zero-baseline users are not scoreable by the ratio rule; keep them `unknown` rather than silently forcing a ratio.
- Confirmation horizons past the observation boundary remain `unknown` with null targets.
- The configured windows, session gaps 15/30/60, no-purchase session-label variant, and duplicate-exclusion sensitivity are in `data/processed/sensitivity.json`. Active-week eligibility values 2/3 are in `research/feasibility/retailrocket_sensitivity.md`. Review these outputs and obtain owner approval before closing D-02/D-03/D-04.
- Excluding the 460 excess exact duplicate rows changes eligible-history snapshots from 97,489 to 97,478. At the primary theta 0.5 rule, inactive rows change 71,301→71,295 and unknown rows 11,590→11,585; ghost/active/recovered counts remain 2,619 / 9,263 / 2,716. This suggests low observed label sensitivity to these exact duplicates for this configuration, but does not establish that all anomalous-event handling is harmless.
- License is CC BY-NC-SA 4.0 per the source page. Do not redistribute raw data; get course-team review before sharing derived data.

## Data products

`manifest.json`, `cohort_flow.json`, `sensitivity.json`, `customer_features.parquet`, `customer_labels.parquet`, `ghost_labels.csv`, `customers.json`, `overview.json`, `descriptive_statistics.json`, and hashed per-snapshot `customer_details/` files are generated and ignored by Git. E-03 is descriptive only, retains repeated snapshots, reports sample SD and feature missingness by group, and does not include inferential tests or confidence intervals. Long owns E-03 analysis; Lâm reviews its cohort and feature inputs.
