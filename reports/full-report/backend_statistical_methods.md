# Backend verification and statistical methods

## Reproduction

Install backend requirements and run `python -m pytest backend/tests -q`. Start the service from the repository root with `python -m uvicorn backend.app.main:app --port 8000`. Record the commit, input versions, package versions, test output and endpoint response for every real-data run. Demonstration fixtures establish interface behavior only.

## Continuous outcome and logistic inference

The OLS analysis estimates the conditional association between a continuous future outcome and pre-snapshot predictors. Compare a prespecified simple model against a multiple model on the same training population. Report coefficient estimates with 95% intervals and p-values, adjusted R-squared, held-out error, residual plots, VIF and influence sensitivity. Use HC3 for independent visitors and visitor-cluster covariance for repeated snapshots. Robust covariance does not repair a misspecified conditional mean.

The logistic analysis estimates log odds of the approved future ghost label. Exponentiate coefficients and confidence limits for odds ratios. Exclude unknown and immature outcomes. Purge overlapping label periods, separate visitors across temporal partitions, and select the score threshold on validation data. Report held-out support, prevalence, ROC-AUC, average precision, confusion matrix, Brier score and calibration bins. The inferential model is separate from the team's deployed ML model.

## Weekly forecast

Define each weekly rate as positive ghost labels divided by eligible known labels. At each historical prediction origin, use only outcomes whose confirmation periods had ended. Compare the last mature rate against ARIMA candidates chosen on validation data. Report MAE, RMSE and sMAPE on later origins. Inspect residual autocorrelation and acknowledge operational-label uncertainty and repeated visitors. A short or irregular series can limit the work to an explicitly unavailable forecast.

## Evidence needed for final results

Record approved label definitions, observation cutoff, cohort counts, continuous outcome definition, model version, actual diagnostic findings and held-out results after inputs are supplied. The current evidence supports software verification. Real endpoint integration and a final interpretation require the corresponding handoffs. SEM requires confirmation of course requirements and a defensible measurement design.
