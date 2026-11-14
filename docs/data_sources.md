# Data source and provenance

## Retailrocket events

| Field | Value |
|---|---|
| Canonical source | [Retailrocket recommender system dataset](https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset), Kaggle dataset version 2 |
| Dataset license | CC BY-NC-SA 4.0, as listed on the Kaggle source page; attribution and non-commercial/share-alike conditions apply |
| Downloaded | 2026-11-14; `events.csv` retrieved from a public mirror and verified against the canonical source's audited hash |
| Local raw file | `data/raw/events.csv` (ignored by Git) |
| Bytes / rows | 94,237,913 / 2,756,101 |
| SHA-256 | `3745aa83238b1e6d44d8fda209807899f420084398f94ddf745f3cbcfecbf9e7` |
| Retrieval mirror | [RetailRocket-Recommender-Data on Hugging Face](https://huggingface.co/datasets/DanielKiani/RetailRocket-Recommender-Data); mirror is a transport source, not the licensing authority |

The source page describes three files: `events.csv`, item properties, and the category tree. This project uses only `events.csv`; item properties and category tree are not required by the current event-count/session research questions. Adding either requires a documented research reason and a new provenance record. The raw file is never committed. Because the license is non-commercial and share-alike, obtain the course team's review before distributing derived data or artifacts outside the project.

## Source field dictionary

| Source field | Raw type | Meaning and handling |
|---|---|---|
| `timestamp` | integer, Unix milliseconds | Event time; parse as UTC with millisecond units. Never interpret as seconds or local time. |
| `visitorid` | integer | Anonymous browser/device visitor identifier; preserve as int64. It is not a verified person or account. |
| `event` | string/category | `view`, `addtocart`, or `transaction`; normalize case/whitespace, fail on unknown values. |
| `itemid` | integer | Item identifier; preserve as int64, do not use the raw identifier as a model feature. |
| `transactionid` | nullable integer | Present for transaction rows and empty for non-transaction rows; preserve nullable integer semantics. |

E-00 reports 2,756,101 rows, 1,407,580 visitor IDs, 2,664,312 views, 69,332 add-to-carts, 22,457 transactions, 460 exact duplicate excess rows, and 2,733,644 empty transaction IDs. The pipeline keeps and flags duplicates rather than deleting them. The event mix is highly view-heavy; count purchases separately from carts.

## Reproduction and change control

Run `python -m data.scripts.run_pipeline --config data/config/pipeline.json --mode audit_compat`. The runner verifies the configured byte count, row count, header and SHA-256 before processing. Any hash mismatch is a hard stop. Every output manifest records the input hash, config hash, code revision, package versions, row counts and output hashes. A changed raw file or scientific parameter requires a new `data_version`; do not overwrite a frozen version.
