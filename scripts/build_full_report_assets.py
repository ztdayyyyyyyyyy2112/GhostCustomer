"""Create aggregate, reproducible figures for the English full report."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/full-report/figures"
OUT.mkdir(parents=True, exist_ok=True)
NAVY, BLUE, TEAL, GREY = "#102c3c", "#14759c", "#3db8a7", "#748891"


def save(name: str) -> None:
    plt.savefig(OUT / name, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close()


def design() -> None:
    fig, ax = plt.subplots(figsize=(9, 2.5))
    widths = [4, 2, 2]
    labels = ["Baseline (4 weeks)", "Observation (2 weeks)", "Future label (2 weeks)"]
    colors = [BLUE, TEAL, GREY]
    pos = 0
    for width, label, color in zip(widths, labels, colors):
        ax.barh(0, width, left=pos, height=.5, color=color)
        ax.text(pos + width / 2, 0, label, ha="center", va="center", color="white", fontsize=8.5, weight="bold")
        pos += width
    ax.axvline(6, color=NAVY, lw=2)
    ax.text(5.9, .57, "T: score issued", ha="right", color=NAVY, fontsize=9, weight="bold")
    ax.set_xlim(0, 8)
    ax.set_ylim(-.7, .8)
    ax.set_yticks([])
    ax.set_xlabel("Weeks; all model features end before T", fontsize=10)
    ax.spines[:].set_visible(False)
    ax.tick_params(axis="x", length=0)
    save("study_design.png")


def cohort() -> None:
    labels = ["Inactive", "Active", "Recovered", "Ghost", "Immature / unknown"]
    values = [71301, 9263, 2716, 2619, 11590]
    colors = [GREY, BLUE, TEAL, "#df8e50", "#b5c5cc"]
    fig, ax = plt.subplots(figsize=(8, 3.5))
    bars = ax.barh(labels[::-1], values[::-1], color=colors[::-1])
    for bar, value in zip(bars, values[::-1]):
        ax.text(value + 600, bar.get_y() + bar.get_height()/2, f"{value:,}", va="center", fontsize=9)
    ax.set_xlim(0, 79000)
    ax.set_xlabel("History-eligible weekly snapshots; one visitor may contribute multiple rows")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", color="#e4e8eb", zorder=0)
    ax.set_axisbelow(True)
    save("cohort_status.png")


def recency() -> None:
    audit = json.loads((ROOT / "research/statistics/inference_audit.json").read_text(encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    values = [audit["active_mean_days"], audit["ghost_mean_days"]]
    bars = ax.bar(["Active (n=896)", "Ghost (n=371)"], values, color=[BLUE, TEAL], width=.55)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, value + .25, f"{value:.2f}", ha="center", fontsize=10)
    ax.set_ylabel("Mean pre-T recency (days)")
    ax.set_ylim(0, 20)
    ax.text(.5, 19.2, "Difference 11.39 days; 95% CI [10.27, 12.51]", ha="center", fontsize=9, color=NAVY)
    ax.spines[["top", "right"]].set_visible(False)
    save("visitor_recency.png")


def benchmarks() -> None:
    values = {"No-skill fraction": .2535, "Gaussian NB": .6668, "EDS rule": .8022,
              "Decision Tree": .9273, "XGBoost + Platt": .9280}
    fig, ax = plt.subplots(figsize=(7.5, 3.7))
    bars = ax.barh(list(values), list(values.values()), color=[GREY, "#a6bac4", BLUE, TEAL, NAVY])
    for bar, value in zip(bars, values.values()):
        ax.text(value + .012, bar.get_y() + bar.get_height()/2, f"{value:.3f}", va="center", fontsize=9)
    ax.set_xlim(0, 1.08)
    ax.set_xlabel("Test average precision (PR-AUC), shared 430-row Ghost/Active test")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", color="#e4e8eb", zorder=0)
    ax.set_axisbelow(True)
    save("benchmark_pr_auc.png")


def ablation() -> None:
    labels = ["Full feature set", "Named components removed", "Observation-only"]
    values = [.9280, .9089, .6072]
    fig, ax = plt.subplots(figsize=(7.5, 3.0))
    bars = ax.barh(labels[::-1], values[::-1], color=["#df8e50", TEAL, NAVY])
    for bar, value in zip(bars, values[::-1]):
        ax.text(value + .015, bar.get_y()+bar.get_height()/2, f"{value:.3f}", va="center", fontsize=9)
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Test PR-AUC; removing baseline history changes the task signal")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", color="#e4e8eb")
    ax.set_axisbelow(True)
    save("ablation_pr_auc.png")


def architecture() -> None:
    fig, ax = plt.subplots(figsize=(9, 2.7))
    boxes = [(0.0, "Retailrocket\nevents.csv"), (1.2, "Preprocess\nand labels"),
             (2.4, "Analyses\nand models"), (3.6, "FastAPI\nseven routes"),
             (4.8, "Next.js\nresearch UI")]
    for x, label in boxes:
        rect = plt.Rectangle((x, .2), 1.0, .65, facecolor="#e9f4f7", edgecolor=BLUE, lw=1.3)
        ax.add_patch(rect)
        ax.text(x+.5, .525, label, ha="center", va="center", fontsize=9, color=NAVY)
    for x in [1.0, 2.2, 3.4, 4.6]:
        ax.annotate("", xy=(x+.18, .525), xytext=(x+.02, .525), arrowprops=dict(arrowstyle="->", color=NAVY, lw=1.6))
    ax.set_xlim(-.05, 5.85)
    ax.set_ylim(0, 1.1)
    ax.axis("off")
    save("architecture.png")


design(); cohort(); recency(); benchmarks(); ablation(); architecture()
forecast = ROOT / "data/processed/forecasting/forecast.png"
if forecast.exists():
    shutil.copyfile(forecast, OUT / "weekly_forecast.png")
dashboard = ROOT / "data/processed/browser_smoke/1366-dashboard.png"
if dashboard.exists():
    shutil.copyfile(dashboard, OUT / "dashboard_real.png")
print(f"Wrote {len(list(OUT.glob('*.png')))} figures to {OUT}")
