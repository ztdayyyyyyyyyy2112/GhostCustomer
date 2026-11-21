"""Rebuild the local real-data research outputs and seven-endpoint demo."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from research.baselines.decision_tree import run as run_tree
from research.baselines.gaussian_nb import run as run_nb


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def call(*args: str) -> None:
    command = [sys.executable, "-m", *args]
    print("RUN", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def run(from_processed: bool = False) -> None:
    config = json.loads((ROOT / "data/config/pipeline.json").read_text(encoding="utf-8"))
    observed_through = config["time"]["observed_through"][:10]
    if not from_processed:
        call("data.scripts.run_pipeline", "--mode", "audit_compat")
        call("data.scripts.export_supplementary")
    else:
        manifest = json.loads((PROCESSED / "manifest.json").read_text(encoding="utf-8"))
        if manifest["source"]["sha256"] != config["source"]["sha256"]:
            raise ValueError("Processed source hash differs from the configured raw file")

    call("research.statistics.inferential")
    forecast_dir = PROCESSED / "forecasting"
    call("research.forecasting.prepare_weekly", "--labels", str(PROCESSED / "ghost_labels.csv"),
         "--output-dir", str(forecast_dir), "--observed-through", observed_through,
         "--data-mode", "real", "--label-version", config["labels"]["version"])
    call("research.forecasting.forecast_models", "--rates", str(forecast_dir / "weekly_rates.csv"),
         "--outdir", str(forecast_dir), "--observed-through", observed_through,
         "--mode", "real", "--horizon", "2")
    forecast = json.loads((forecast_dir / "forecast.json").read_text(encoding="utf-8"))
    if not forecast["available"]:
        raise ValueError(f"Forecast unavailable: {forecast['reason']}")
    api_forecast = ROOT / "research/forecasting/results.json"
    shutil.copyfile(forecast_dir / "forecast_api_candidate.json", api_forecast)
    forecast_meta = {
        "data_mode": "real", "source_events_sha256": config["source"]["sha256"],
        "labels_csv_sha256": sha(PROCESSED / "ghost_labels.csv"),
        "weekly_rates_sha256": sha(forecast_dir / "weekly_rates.csv"),
        "forecast_analysis_sha256": sha(forecast_dir / "forecast.json"),
        "api_result_sha256": sha(api_forecast), "n_mature_weeks": forecast["n_weeks"],
        "method": forecast["method"], "test_metrics": forecast["test_metrics"],
        "decision_status": "Exploratory under proposed 4+2+2 cohort and operational label",
    }
    (ROOT / "research/forecasting/analysis_manifest.json").write_text(
        json.dumps(forecast_meta, indent=2), encoding="utf-8")

    call("research.regression.prepare_inputs")
    regression = PROCESSED / "regression"
    results = ROOT / "research/regression/results"
    predictors = ["feature_sessions_4w", "feature_views_4w", "feature_recency_days"]
    call("research.regression.linear_models", "--input", str(regression / "ols_input.csv"),
         "--output-dir", str(results), "--predictors", *predictors,
         "--train-end", "2015-08-03", "--test-start", "2015-08-17",
         "--observed-through", observed_through, "--data-mode", "real",
         "--outcome-definition", "future sessions per week over the 2-week confirmation horizon")
    call("research.regression.logistic_inference", "--input", str(regression / "logit_input.csv"),
         "--outdir", str(results), "--observed-through", observed_through, "--mode", "real")
    call("research.regression.ols_diagnostics", "--input", str(regression / "ols_input.csv"),
         "--outdir", str(results), "--predictors", *predictors,
         "--cutoff", "2015-08-03", "--mode", "real")

    call("ai.training.run", "--optional-models")
    call("ai.evaluation.report")
    summary = json.loads((ROOT / "ai/evaluation/run_summary.json").read_text(encoding="utf-8"))
    shared_csv = PROCESSED / "modeling_snapshots.csv"
    runs = {}
    for key, runner in (("decision_tree", run_tree), ("gaussian_nb", run_nb)):
        runs[key] = runner(shared_csv, ROOT / f"research/baselines/{key}_results.json",
                           summary["features"], observed_through,
                           summary["label_version"], summary["split_version"])
    (ROOT / "ai/evaluation/benchmark_shared_split.json").write_text(json.dumps({
        "note": "Independent Decision Tree and Gaussian NB rerun on the shared real-data split; proposed scientific decisions remain open.",
        "runs": runs,
    }, indent=2), encoding="utf-8")
    call("scripts.check_integration_artifacts", "--require-complete")
    call("scripts.verify_real_demo")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-processed", action="store_true", help="Reuse verified local pipeline tables and customer detail files")
    args = parser.parse_args()
    run(args.from_processed)
