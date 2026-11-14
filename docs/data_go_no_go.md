# Retailrocket data go/no-go (proposed)

Generated from the local source whose SHA-256 is pinned in `data/config/pipeline.json`. Regenerate with `python -m data.scripts.run_pipeline --mode audit_compat`; outputs are local under ignored `data/processed/`.

## Recommendation

**GO for a reproducible course-project prototype; NO-GO for claiming validated ghost-customer prediction or publishing derived records.** The file has 2,756,101 events and 1,407,580 anonymous visitor IDs, but views are 96.7% of events, exact duplicates are retained and flagged, and `visitorid` is not a verified person/account. The label is a behavioral proxy, not observed churn.

## Primary proposed setup

Use B+O+C = 4+2+2 weeks, minimum 5 history events across at least 2 active weeks, one baseline event, 30-minute sessions, and `sessions/week` confirmation-to-baseline ratio with theta 0.5. Keep `audit_compat` and `research` cohorts visible separately; the latter requires activity during O and changes the target population. These are proposals, not approved decisions (D-01–D-04 remain with Thành/Lâm).

For the primary run, `data/processed/cohort_flow.json` records 85,899 complete audit-eligible snapshots, 24,768 distinct visitors, 20,989 repeat visitors, and 11,590 history-eligible right-censored snapshots. E-00 golden counts are reproduced by `data/scripts/tests/test_cohort.py`.

## Main risks and gates

- Two latest T dates (2015-08-24 and 2015-08-31) are candidate temporal test snapshots by prior team discussion; freeze only after Kiệt/Long approve visitor grouping and purge overlapping confirmation horizons.
- Relative labels use baseline engagement in their denominator. Report the circularity; compare an ablation without baseline/decay/EDS features before model claims.
- Zero-baseline users are not scoreable by the ratio rule; keep them `unknown` rather than silently forcing a ratio.
- Confirmation horizons past the observation boundary remain `unknown` with null targets.
- Session gap 15/30/60, duplicate exclusion, no-purchase variant, and all three window configurations must be reviewed before D-02/D-03/D-04 are closed.
- License is CC BY-NC-SA 4.0 per the source page. Do not redistribute raw data; get course-team review before sharing derived data.

## Data products

`manifest.json`, `cohort_flow.json`, `sensitivity.json`, `customer_features.parquet`, `customer_labels.parquet`, `ghost_labels.csv`, `customers.json`, `overview.json`, and `descriptive_statistics.json` are generated and ignored by Git. E-03 is descriptive only, retains repeated snapshots, and does not include inferential tests or confidence intervals.
