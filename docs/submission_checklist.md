# Submission checklist

Deadline in the team assignment: **before 20 November 2026**. Complete each item only after opening the final artifact and checking its evidence. The course outline requires the full report, IEEE paper, and slides to be submitted directly to the course system; large code, data, or video files may be linked from cloud storage.

## Status of the local defense build, 20 November 2026

- [x] Pinned Retailrocket `events.csv` was verified by byte count and SHA-256, and the 4+2+2 pipeline produced 97,489 history-eligible snapshots. Source, license, censoring, and sensitivity are recorded in E-01–E-03.
- [x] Visitor-level inferential test, OLS, logistic inference, short-series naive forecast, shared-split ML comparison, and observation-only ablation were reproduced from real artifacts. See E-04–E-08. Their operational definitions remain proposals.
- [x] The structural artifact checker passed 97,489 detail files; all seven real API routes and 404/422 cases passed. Python: 122 tests passed. Frontend: lint and real-mode production build passed.
- [x] A 12-slide Vietnamese defense draft was exported and passed package/layout validation: `reports/slides/defense_deck.pptx`. The route-by-route speaker notes are in `reports/defense/brief.md` and `docs/demo_script.md`.
- [x] An English full report DOCX of 29 A4 pages, with 14 figures and 21 tables, has been built and visually reviewed at `reports/full-report/GhostCustomer_STAT3013_Full_Report_EN.docx`. Final team factual/signature review remains open.
- [ ] The two-column paper DOCX is a **7-page review draft** with figures and tables, but is not yet in the official IEEE template. Apply the official template and verify pagination before submission.
- [ ] D-01–D-05 (cohort, label, windows and split) and D-07 (SEM) need a documented scientific/lecturer decision. No SEM result or ARIMA claim has been invented.
- [ ] A narrated demo video, similarity/AI audit screenshots, final class/group repo name, and course-system uploads require the responsible people and accounts. No submission is claimed.

## Research integrity

- [ ] Dataset source, license, version, hash, field dictionary, and usable observation period are recorded.
- [ ] Cohort/window/label decisions use actual coverage, class counts, censoring, and sensitivity evidence in `docs/decision_log.md`.
- [ ] Features use events at or before T; future labels and confirmation events are excluded from predictors.
- [ ] Split respects time and repeated visitors; preprocessing fits on train only.
- [ ] Every test includes H0/H1, N, statistic, p-value, CI or justified absence, effect size, assumptions, and interpretation.
- [ ] Regression, forecasting, and ML results cite reproducible outputs and compare with simple baselines.
- [ ] SEM status follows lecturer guidance and valid measurement data; no invented survey or SEM result.
- [ ] Mock/synthetic values are labeled as demo data and never reported as findings.

## Product and reproducibility

- [ ] A clean clone runs using README and pinned requirements/lockfile.
- [ ] All seven API endpoints pass `docs/integration_test.md` against the real backend, including an error case.
- [ ] Dashboard works on desktop and phone; charts distinguish observed, fitted, and predicted periods.
- [ ] Model version, class support, prevalence, threshold, and calibration match the saved evaluation.
- [ ] No secrets, raw dataset, large processed files, or unlicensed material are committed.
- [ ] GitHub repo name is confirmed against the course convention `STAT3013.QXX_GroupYY` (current `GhostCustomer` name needs a decision).

## Submission artifacts

- [ ] Full report is approximately 30 pages and includes introduction, related work, methodology, descriptive/inferential statistics, regression, SEM status, forecasting, ML, results/discussion, limitations, references, and appendix.
- [ ] IEEE paper is 7–10 pages in two-column conference style with figures, citations, and numbers consistent with the full report.
- [ ] Presentation slides explain problem, dataset, cohort/label, EDA, tests, regression, forecast, ML, limitations, and recommendations.
- [ ] Demo video opens and follows the agreed route through the web app; every demo value is identified as real or mock.
- [ ] Turnitin screenshot shows similarity ≤10%; AI-generated-content audit screenshot and explanation are included as requested by the course.
- [ ] Links to code, data access instructions, and video work for reviewers.
- [ ] Full report, IEEE paper, and slides are uploaded directly to the course system; large files are linked.
- [ ] All four members can explain the full research design and their own contributions.
