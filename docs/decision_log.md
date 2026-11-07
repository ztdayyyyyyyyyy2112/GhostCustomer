# Research decision log

Record the date, owner, alternatives, quantitative evidence, decision, and consequences before treating a working assumption as final. Entries below are open; examples are not approved thresholds.

| ID | Decision | Current state | Evidence needed | Owner |
| --- | --- | --- | --- | --- |
| D-01 | Dataset and permitted use | Retailrocket preferred for audit; fallback open | Source/license, coverage, repeat visitors, usable history | Lâm; Thành approves |
| D-02 | Baseline, observation and confirmation windows | Open; compare at least 2–3 configurations | Eligible visitors, positive/negative/unknown counts, censoring | Lâm; Thành approves |
| D-03 | Ghost/active/recovered/inactive label and decline threshold | Open | Future behavior distribution and threshold sensitivity | Lâm; Thành approves |
| D-04 | Session boundary | 30 minutes is a test assumption | Sensitivity of weekly features and labels | Lâm |
| D-05 | Temporal split and repeated visitors | Open | Snapshot overlap, label horizon, visitor grouping | Kiệt and Long |
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
