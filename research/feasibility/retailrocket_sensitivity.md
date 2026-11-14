# Legacy Retailrocket O-to-C snapshot sensitivity

> **Legacy exploratory output.** The label below compares O to C and does not implement the current proposed baseline-to-confirmation label in `data/scripts/labels.py`. Use the newer E-02 summaries in ignored `data/processed/cohort_flow.json` and `data/processed/sensitivity.json` for the current baseline-relative label. Do not cite the Ghost counts in this legacy file as current label results.

Generated: 2026-11-14T03:05:59.603Z

## Source check

- File: `data/raw/events.csv`; 2,756,101 rows; 1,407,580 visitor IDs; SHA-256 `3745aa83238b1e6d44d8fda209807899f420084398f94ddf745f3cbcfecbf9e7`.
- Event counts: view 2,664,312 (96.7%), addtocart 69,332 (2.5%), transaction 22,457 (0.8%).
- Date range: 2015-05-03T03:00:04.384Z to 2015-09-18T02:59:47.788Z; 19 complete Monday weeks from 2015-05-04 through 2015-09-14 (end exclusive).
- Raw duplicate rows are retained, matching the earlier audit; no item properties/category tree are needed for these event-count labels.

## Candidate windows and eligibility sensitivity

Base cohort: at least 5 or 10 events in baseline+observation, activity in at least 2 or 3 distinct weeks, and at least one baseline event. `observation_any` additionally requires any event during O; `observation_views_or_cart` requires a view/add-to-cart during O. Snapshot and visitor counts below require a fully observed C horizon; right-censored candidates are listed separately and labeled unknown. Counts below are for min 5 events and 2 active weeks unless stated.

| B+O+C (weeks) | Eligibility rule | Complete snapshots | Visitors | Repeat visitors | No O activity | No C activity | Active in O and C (any event) | Active in O and C (view/cart) | Censored candidates | Ghost at 50%* |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4+2+2 | history_only | 85,899 | 24,768 | 20,989 | 42,674 | 71,301 | 11,472 | 11,468 | 11,590 | 5,039 (43.9%) |
| 4+2+2 | observation_any | 43,225 | 21,375 | 11,373 | 0 | 31,753 | 11,472 | 11,468 | 5,977 | 5,039 (43.9%) |
| 4+2+2 | observation_views_or_cart | 43,213 | 21,369 | 11,370 | 0 | 31,743 | 11,470 | 11,468 | 5,976 | 5,039 (43.9%) |
| 4+3+2 | history_only | 86,629 | 24,820 | 21,112 | 37,560 | 73,742 | 10,923 | 10,919 | 13,511 | 4,019 (36.8%) |
| 4+3+2 | observation_any | 49,069 | 21,488 | 12,188 | 0 | 38,146 | 10,923 | 10,919 | 7,593 | 4,019 (36.8%) |
| 4+3+2 | observation_views_or_cart | 49,058 | 21,482 | 12,187 | 0 | 38,137 | 10,921 | 10,919 | 7,590 | 4,019 (36.8%) |
| 6+2+4 | history_only | 88,280 | 23,644 | 19,955 | 53,523 | 71,618 | 11,267 | 11,265 | 40,043 | 7,024 (62.4%) |
| 6+2+4 | observation_any | 34,757 | 17,395 | 9,714 | 0 | 23,490 | 11,267 | 11,265 | 14,719 | 7,024 (62.4%) |
| 6+2+4 | observation_views_or_cart | 34,750 | 17,391 | 9,713 | 0 | 23,485 | 11,265 | 11,265 | 14,713 | 7,024 (62.4%) |

*Ghost50 is the view+cart decline candidate among snapshots with nonzero view+cart activity in both O and C, not a verified churn rate. Sensitivity cells use the same threshold across complete C horizons.*

### 4+2+2 history and activity eligibility

| History minimum | Activity weeks | Rule | Eligible snapshots | Distinct visitors | O/C view+cart active | Ghost at 50% | Ghost rate in comparable O/C cohort |
| 5 | 2 | history_only | 85,899 | 24,768 | 11,468 | 5,039 | 43.9% |
| 5 | 2 | observation_any | 43,225 | 21,375 | 11,468 | 5,039 | 43.9% |
| 5 | 2 | observation_views_or_cart | 43,213 | 21,369 | 11,468 | 5,039 | 43.9% |
| 5 | 3 | history_only | 30,698 | 9,179 | 8,439 | 3,569 | 42.3% |
| 5 | 3 | observation_any | 22,479 | 8,520 | 8,439 | 3,569 | 42.3% |
| 5 | 3 | observation_views_or_cart | 22,475 | 8,519 | 8,439 | 3,569 | 42.3% |
| 10 | 2 | history_only | 34,566 | 9,555 | 6,769 | 3,145 | 46.5% |
| 10 | 2 | observation_any | 18,773 | 8,261 | 6,769 | 3,145 | 46.5% |
| 10 | 2 | observation_views_or_cart | 18,767 | 8,258 | 6,769 | 3,145 | 46.5% |
| 10 | 3 | history_only | 16,514 | 4,658 | 5,623 | 2,526 | 44.9% |
| 10 | 3 | observation_any | 12,383 | 4,307 | 5,623 | 2,526 | 44.9% |
| 10 | 3 | observation_views_or_cart | 12,381 | 4,307 | 5,623 | 2,526 | 44.9% |

## Candidate labels on the 4+2+2 table

Operational label rule: `Ghost` means view+addtocart events per week in C are at least the selected percentage lower than in O, while C has some view/cart engagement. `Inactive` means no event of any type in C; `Recovered` means O had no events and C has an event; `Active` means C has an event but does not meet the decline rule; `Unknown` means C is not fully observed. Purchase-only future activity stays active and is not called inactive. Three labels are emitted for threshold sensitivity.

| Decline threshold | Ghost | Active | Recovered | Inactive | Unknown | Unscorable active* | Binary Ghost (O/C view+cart active) | Binary Active | All-event alternative Ghost (same cohort) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 50% | 5,039 (5.2% overall) | 6,433 (6.6%) | 3,126 (3.2%) | 71,301 (73.1%) | 11,590 (11.9%) | 4 | 5,039 (43.9%) | 6,429 (56.1%) | 5,037 (43.9%) |
| 60% | 3,814 (3.9% overall) | 7,658 (7.9%) | 3,126 (3.2%) | 71,301 (73.1%) | 11,590 (11.9%) | 4 | 3,814 (33.3%) | 7,654 (66.7%) | 3,818 (33.3%) |
| 70% | 2,760 (2.8% overall) | 8,712 (8.9%) | 3,126 (3.2%) | 71,301 (73.1%) | 11,590 (11.9%) | 4 | 2,760 (24.1%) | 8,708 (75.9%) | 2,773 (24.2%) |

*Unscorable active = O or C has no view/cart denominator, but future nonzero event activity keeps the visitor out of Ghost/Inactive. Binary Active equals the comparable O/C-engaged cohort minus Ghost; all-event scoring is shown on that same cohort for sensitivity.*

## Recommendation and limitations

- Recommended audit candidate: **B=4, O=2, C=2 weeks; minimum 5 history events across at least 2 distinct weeks; at least one baseline event; require O view/cart activity for the primary Ghost-vs-Active modeling cohort.** Keep recovered, inactive, and censored unknown as separate outcomes outside that binary cohort.
- Recommended initial threshold: **50%**, as the proposal’s lower-bound scenario; retain 60% and 70% as sensitivity results. A 50% cutoff is more permissive (larger Ghost class) than 60% or 70%. This is a proposed operational rule, not ground truth or team approval.
- Use view+addtocart as the engagement numerator and purchases as a separate activity signal. Views are the overwhelming majority of raw events; all-event totals largely become a view count and transactions are sparse.
- A relative O-to-C label necessarily depends on O. For modeling, report that target construction and either exclude the exact O engagement-rate feature from the Ghost-vs-Active model or compare against a future-only target definition; do not claim an independent label.
- Keep all snapshots for descriptive flow; for inferential/model evaluation, use a visitor-aware temporal split and prevent one visitor appearing across partitions. There are few distinct T dates, so weekly forecasting remains constrained.
- Snapshot counts are dependent repeated visitor-rows. The event log has no verified person-level customer identity, session ID, impression/exposure, or item/category context in this file. This output does not test the 30-minute session assumption, deduplicate 460 raw rows, estimate model quality, or validate dataset license for redistribution.

## Generated artifacts

- Labels CSV: `data/processed/retailrocket_labels_4-2-2.csv` (97,489 visitor-snapshot rows; ignored by Git because it is generated data).
- Reproduce: `node research/feasibility/retailrocket_sensitivity.mjs data/raw/events.csv research/feasibility/retailrocket_sensitivity.md data/processed/retailrocket_labels_4-2-2.csv`.
- Input is read directly; exact SHA-256 appears above. Review and approve D-02/D-03 in `docs/decision_log.md` before copying these labels into report/model claims.
