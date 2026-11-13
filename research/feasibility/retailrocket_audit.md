# Retailrocket data feasibility audit

Date: 8 November 2026. This is an exploratory audit for discussion of D-01–D-03. It does not approve a final cohort, label, or model.

## Source and reproducibility

- Source: [Retailrocket recommender system dataset, Kaggle](https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset), dataset version 2. Kaggle lists license **CC BY-NC-SA 4.0**. Review the license and attribution requirements before distributing derived data.
- File audited: `events.csv`, 94,237,913 bytes, downloaded outside the repository. SHA-256: `3745aa83238b1e6d44d8fda209807899f420084398f94ddf745f3cbcfecbf9e7`.
- Reproduce the counts with `python retailrocket_audit.py /path/to/events.csv /path/to/result.json` (audited here with pandas 3.0.1 and NumPy 2.3.5). The script is delivered beside this report; raw data is not included.
- Columns: `timestamp`, `visitorid`, `event`, `itemid`, `transactionid`. Total rows: **2,756,101**. Distinct `visitorid`: **1,407,580**. A visitor ID is not proof of a unique identified customer.
- Event types: view **2,664,312**, addtocart **69,332**, transaction **22,457**.
- Timestamp range (UTC): `2015-05-03T03:00:04.384000+00:00` to `2015-09-18T02:59:47.788000+00:00`. For complete-week comparisons, exclude the partial boundary weeks and use **19** Monday-to-Monday weeks from `2015-05-04` through but excluding `2015-09-14`.
- Exact duplicate rows: **460**. They are counted as recorded here; investigate before any cleaning rule. `transactionid` is absent in 2,733,644 rows, matching non-transaction event types. Other columns have no missing values in this file.

## Candidate cohort counts

A snapshot is a Monday 00:00 UTC. Baseline and observation lie before T; confirmation lies after T. A provisional candidate has at least **5 or 10 events** in the combined pre-T history, activity in at least **2 distinct weeks**, and at least **1 baseline event**. These are sensitivity conditions, not approved eligibility rules. The table uses only T dates with complete weeks in all three intervals.

| Baseline + observation + confirmation | Min pre-T events | Complete T dates | Eligible snapshots | Distinct visitors | Visitors with >1 snapshot | Zero events in confirmation | Activity in observation and confirmation | Censored candidate snapshots* |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 + 2 + 2 weeks | 5 | 12 | 85,899 | 24,768 | 20,989 | 71,301 | 11,472 | 11,590 |
| 4 + 2 + 2 weeks | 10 | 12 | 34,566 | 9,555 | 8,187 | 26,484 | 6,772 | 4,534 |
| 4 + 3 + 2 weeks | 5 | 11 | 86,629 | 24,820 | 21,112 | 73,742 | 10,923 | 13,511 |
| 4 + 3 + 2 weeks | 10 | 11 | 34,780 | 9,560 | 8,221 | 27,567 | 6,408 | 5,242 |
| 6 + 2 + 4 weeks | 5 | 8 | 88,280 | 23,644 | 19,955 | 71,618 | 11,267 | 40,043 |
| 6 + 2 + 4 weeks | 10 | 8 | 35,022 | 9,116 | 7,729 | 26,331 | 6,466 | 15,506 |

*Censored candidate snapshots are additional T dates with sufficient history but less than the specified number of **complete** future weeks remaining. They are excluded from the eligible and future-behavior columns; they would be `unknown` for that horizon. The count depends on the selected weekly T grid.

## What these counts imply

- In the 4 + 2 + 2 week, 5-event scenario, **83.0%** of eligible snapshots have no event in the fully observed 2-week confirmation interval. This is a future-activity diagnostic, **not** the Ghost rate. A still-active Ghost label cannot include those zero-event snapshots without changing its definition.
- **84.7%** of distinct eligible visitors in that scenario appear at more than one T. A random row split would therefore mix dependent visitor histories. Select one T per visitor for an independent inferential sample or document a visitor-aware temporal validation design.
- If the **earliest eligible T** is selected once per visitor, that scenario has 24,768 rows; 20,154 have no event in confirmation and 4,315 have activity in both observation and confirmation. This is a diagnostic subset, not a trained-model cohort or Ghost label.
- **42,674** eligible snapshots have no event in the 2-week observation interval, despite activity in the longer pre-T history. If the research question is early decline among currently active visitors, consider requiring observation activity and recompute the cohort before modeling.
- The three scenarios provide only 12, 11, or 8 fully observed weekly T dates. This constrains time-series holdout and forecasting; compare a simple baseline before attempting ARIMA and report when the series is too short.
- The proposed 50%, 60%, and 70% decline thresholds are **not evaluated here**. A final label needs an explicit engagement formula, denominator, handling of baseline or observation zero, and a decision about whether pre-T quantities may enter the target definition. Do not publish a Ghost prevalence from this audit.

## First scenario by snapshot date

4 + 2 + 2 weeks; at least 5 history events and 2 active history weeks; baseline activity required.

| T (UTC) | Eligible snapshots | Zero confirmation events |
| --- | ---: | ---: |
| 2015-06-15 | 7,492 | 6,160 |
| 2015-06-22 | 7,551 | 6,248 |
| 2015-06-29 | 7,230 | 5,925 |
| 2015-07-06 | 7,017 | 5,749 |
| 2015-07-13 | 7,101 | 5,821 |
| 2015-07-20 | 7,145 | 5,909 |
| 2015-07-27 | 7,368 | 6,162 |
| 2015-08-03 | 7,237 | 6,096 |
| 2015-08-10 | 7,407 | 6,238 |
| 2015-08-17 | 7,163 | 5,980 |
| 2015-08-24 | 6,733 | 5,646 |
| 2015-08-31 | 6,455 | 5,367 |

## Decisions still needed

1. **D-01:** Confirm the downloaded file hash/version, usage conditions, and whether item properties are required. Keep raw data out of Git.
2. **D-02:** Compare the scenarios using one snapshot per visitor and an explicit observation-activity rule. Record the actual eligible count in each train/validation/test period, not just the total across T.
3. **D-03:** Define Ghost and Active from a reproducible future behavior rule. Test any relative-decline label for circularity when its pre-T denominator also appears in prediction features. Keep zero-future activity as a separate inactive outcome and right-censored rows as unknown.
4. **D-05/D-06:** Design a visitor-aware temporal split and determine whether the number of fully labeled weekly points supports forecasting beyond a naive baseline.

The audit is exploratory. Exact duplicates were not removed, no label was assigned, and no predictive or inferential statistic was computed. The research team should review the cohort rule before using these counts in the report or dashboard.
