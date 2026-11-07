# Literature map — starter set

This is a source map for the related-work section, not a written literature review or evidence about this project's dataset. The papers below were checked against publisher, proceedings, or university repository pages on 8 November 2026. Read the complete paper before making a detailed comparison or quoting it in the final report. Record page numbers for every direct quote. Apply the course's required citation style consistently.

| Source | Verified scope | Use in this project | Transfer limit / question to check |
| --- | --- | --- | --- |
| Neslin et al. (2006), [Defection Detection](https://doi.org/10.1509/jmkr.43.2.204) | Compares predictive accuracy of customer churn models in a validation tournament using telecom data. | Motivate explicit baselines and out-of-sample comparison. | Telecom contractual defection is different from an event-data operational ghost label. Verify the original outcome and horizons before comparing results. |
| Burez and Van den Poel (2009), [Handling class imbalance in customer churn prediction](https://doi.org/10.1016/j.eswa.2008.05.027) | Investigates class imbalance in customer churn prediction. | Motivate reporting class counts and comparing strategies on the same held-out cohort. | Do not assume ghost prevalence or a preferred resampling method before the dataset audit. |
| Saito and Rehmsmeier (2015), [The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced Datasets](https://doi.org/10.1371/journal.pone.0118432) | Studies PR and ROC interpretation for imbalanced binary classification. | Pre-specify PR-AUC with prevalence and class support alongside ROC-AUC. | The paper's examples are from bioinformatics; our label and operational threshold need their own analysis. |
| Guo et al. (2017), [On Calibration of Modern Neural Networks](https://proceedings.mlr.press/v70/guo17a.html) | Evaluates probability calibration of neural networks and post-processing methods. | Motivate checking whether displayed risk scores agree with observed event rates. | Findings about neural networks do not prove that logistic, forest, or boosting models here are calibrated. Measure on validation/held-out data. |
| Lundberg and Lee (2017), [A Unified Approach to Interpreting Model Predictions](https://proceedings.neurips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html) | Introduces SHAP feature attribution for predictions. | Explain the provenance of per-prediction feature contributions if Kiệt supplies them. | Attribution describes the fitted model, not causal effects or a reason for a customer's behavior. |

## Planned synthesis

1. Define the proposed ghost label, observation window, and prediction horizon explicitly; contrast them with each paper's outcome rather than equating all forms of churn.
2. Organize the review around outcome definition, class imbalance, validation, probability quality, and explanation. Connect each point to RQ1–RQ4 in `docs/research_scope.md`.
3. Add a dataset-specific methods paper only after the dataset is selected. Verify dataset licensing and provenance from the original host.
4. Add primary sources for temporal validation and forecasting after the exact split and forecasting method are chosen. Until then, the practical leakage check is recorded in the research scope and decision log.

## Citation checklist

- [ ] Full text read and page-specific notes made for each cited claim.
- [ ] Authors, year, venue, DOI, and page range checked against the publisher record.
- [ ] Outcome, data context, split, metrics, and limitations recorded in the report's comparison table.
- [ ] Every reference appearing in the report also appears in the paper's bibliography, if cited there.
