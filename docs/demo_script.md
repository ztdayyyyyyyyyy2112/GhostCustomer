# Dashboard demo script

## Before recording

Run the project from a clean checkout, set the intended data mode in `frontend/.env.local`, and check all links. In `mock` mode, say at the start and on screen that every customer and score is illustrative and the statistics/forecast/model metrics are unavailable. Use `real` mode for the final research demonstration only after all seven endpoints pass `docs/integration_test.md` and numbers match result files.

## Walkthrough

1. **Overview:** Explain the date range, cohort denominator, operational Ghost label, and dataset notice. In mock mode, identify the KPI values as interface examples.
2. **Customer List:** Search a customer ID, filter a status, sort by risk score, and change the page size. Show how unknown values remain blank rather than zero.
3. **Customer Detail:** Point to snapshot T. Explain that baseline and observation features are at or before T, while confirmation happens after T and is excluded from prediction input.
4. **Statistics:** If results exist, show N, distribution, CI, p-value, effect size, and assumptions together. Otherwise state that the analysis has not been run and do not improvise a conclusion.
5. **Forecast:** If results exist, distinguish observed, fitted, and future lines, CI band, train end, and baseline comparison. Otherwise explain the minimum data needed.
6. **Prediction:** Submit a valid snapshot and read score as a probability estimate, with model version and attribution limits. Demonstrate an unknown/insufficient-data case. In mock mode, say the score is not a trained-model output.
7. **Model Metrics:** Show held-out support, prevalence, precision/recall/PR-AUC and calibration when available; otherwise leave the panel empty.

## Recording checks

Keep the browser at readable zoom, show the route and labels, capture one complete successful flow and one error/unknown flow, avoid exposing local secrets or raw visitor data, and verify the saved video opens with sound. Use the final slide deck and report to cross-check wording and numbers.
