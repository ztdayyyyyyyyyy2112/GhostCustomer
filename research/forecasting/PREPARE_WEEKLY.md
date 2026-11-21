# BE-10 Mature weekly series

The module prepares dated ghost-rate counts from the data owner's **already approved** operational labels. It does not define ghost, fit a forecasting model or publish a research artifact to the API. Standard-library Python only; no extra runtime dependency.

From the repository root:

```bash
python -m research.forecasting.prepare_weekly --labels data/processed/customer_labels.csv --output-dir data/processed/weekly-series --observed-through 2015-09-14 --data-mode real --label-version APPROVED_VERSION
python -m pytest research/forecasting/tests/test_prepare_weekly.py -q
```

Replace the observation boundary and version with the actual metadata. Dates denote 00:00 UTC. CSV columns must be exactly `visitorid,snapshot_date,label_end,label_status,target_ghost`. `snapshot_date` uses the Monday weekly T grid. Label end must be later than T. Known statuses active/ghost/recovered/inactive have targets 0/1 consistent with ghost; unknown/candidate require a blank target. IDs remain strings. One visitor may appear at multiple dates but not twice at one T. Future labels at different horizons must produce separate series.

Outputs are weekly_rates.csv and weekly_rates_metadata.json, including input SHA256, observation boundary, mode, label version, counts/exclusions and gaps. The denominator excludes unknown/candidate. A complete bin is excluded if its label horizon has not matured. This prevents short follow-up from becoming a zero or an artificially low rate. Nothing interpolates missing weeks.

The prior exploratory audit lists 8–12 eligible weekly T dates for several scenarios. These are feasibility counts, not final ghost rates, and are too few to assume reliable ARIMA estimation. Assess the actual resulting series before selecting D-06. Repeated users across weeks also induce dependence. `real` records declared provenance, not independent approval; input hashes and E-02/E-06 must be reviewed.

Acceptance: synthetic tests verify censoring boundaries, denominator, missing weeks, repeated users, invalid labels and metadata. Real-data acceptance remains pending Lâm's labels and D-02/D-03 approval. Plot the resulting dated rates in the accompanying notebook only after valid input exists.
