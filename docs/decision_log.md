# Research decision log

Record the date, owner, alternatives, quantitative evidence, decision, and consequences before treating a working assumption as final. Entries below are open; examples are not approved thresholds.

| ID | Decision | Current state | Evidence needed | Owner |
| --- | --- | --- | --- | --- |
| D-01 | Dataset and permitted use | Retailrocket preferred for audit; fallback open | Source/license, coverage, repeat visitors, usable history | Lâm; Thành approves |
| D-02 | Baseline, observation and confirmation windows | Open; E-02 compares 4+2+2, 4+3+2, and 6+2+4; no selection approved | Eligible visitors, positive/negative/unknown counts, censoring; see local `data/processed/cohort_flow.json` and `docs/data_go_no_go.md` | Lâm; Thành approves |
| D-03 | Ghost/active/recovered/inactive label and decline threshold | Open; E-02 compares baseline-relative session/event labels at theta 0.5/0.4/0.3; no selection approved | Label counts, censoring, no-purchase variant, circularity risk; see local `data/processed/sensitivity.json` | Lâm; Thành approves |
| D-04 | Session boundary | Open; E-02 compares 15/30/60 minutes; no selection approved | Session and label sensitivity; see local `data/processed/sensitivity.json` | Lâm; Thành approves |
| D-05 | Temporal split and repeated visitors | Proposed by Kiệt, awaiting Long/Thành review: last 2 mature weeks test, previous 2 validation, strict label purge, visitor SHA-256 buckets 50/25/25 (`ai/training/split.py`); time-only run as sensitivity | Rows/visitors/prevalence per split and purge losses in `ai/evaluation/split_manifest.json` | Kiệt and Long |
| D-06 | Forecasting method | Naive baseline first; ARIMA conditional | Number of fully labeled weeks and holdout performance | Long |
| D-07 | SEM requirement | Clarification pending | Lecturer guidance and valid measurement model | Thành and Long |

## Decision record template

### D-XX — Short title

- Date and participants:
- Alternatives:
- Evidence (file, version, counts, plot):
- Decision and reason:
- Impact on data, API, analysis, and report:
- Revisit trigger:
