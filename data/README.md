# Data pipeline inputs and outputs

`data/raw/events.csv` is the only required raw table. Download Retailrocket dataset version 2 from [Kaggle](https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset), save it at that path, and verify it against the SHA-256 in `data/config/pipeline.json` before running any stage. The source page lists CC BY-NC-SA 4.0. Attribute the source; do not redistribute the raw file, and review the non-commercial and share-alike terms before sharing derived outputs.

The pipeline expects Python 3.12. Install the pinned libraries in `data/scripts/requirements.txt`, then run from the repository root:

```powershell
python -m pip install -r data/scripts/requirements.txt
python -m data.scripts.run_pipeline --config data/config/pipeline.json --mode audit_compat
```

Raw data, processed Parquet/CSV/JSON, manifests and customer detail files live under ignored `data/raw/` and `data/processed/`; never add them to Git. Tracked mock data lives only under `data/mock/` and each row has `is_synthetic=true`.

The runner produces the primary clean/session/week/cohort/feature/label/customer/overview/descriptive artifacts. The local manifest also tracks supplementary E-02 window/session sensitivity and customer detail files. A consolidated script to regenerate those supplementary outputs is still pending. The default scenario is a **proposed audit setting**, not an approved scientific decision. See `docs/data_go_no_go.md` before using outputs in a report or model.
