# Architecture

## Goal

Build a Snowflake-native framework where datasets are onboarded through metadata.

## Layers

| Layer | Purpose |
|---|---|
| Storage/stage | Files land under `raw/<dataset>/YYYY/MM/DD/<run_id>/` |
| Control | Config, file state, run logs, DQ rules, AI suggestions |
| Bronze | Raw loaded tables with file lineage |
| Silver | Cleansed/conformed views or tables |
| Gold | Published analytics/data products |
| Governance | Tags, classification, policy audit, SLA metadata |

## Control flow

1. `SP_DISCOVER_FILES(P_DAYS_BACK)` reads enabled datasets from `CFG_DATASET` and lists files under each stage path.
2. New files are inserted into `FILE_CONTROL` with status `NEW`.
3. `SP_CREATE_OR_EVOLVE_TARGETS()` creates target tables if missing.
4. `SP_INGEST_FILES(P_MAX_RETRIES)` loads `NEW` and retryable files into target tables.
5. Failed files are moved to `FAILED_RETRYABLE` or `FAILED_FINAL`.
6. `SP_RUN_DQ_RULES()` executes active SQL-based DQ rules.
7. `SP_AI_SUGGEST_DQ_RULES()` generates AI suggestions for rule review.
8. Streamlit reads monitoring views for operational visibility.

## Why full file path matters

A file name alone is not safe because the same name can land under multiple folders/runs. This framework tracks `FILE_PATH`, not just `FILE_NAME`.

## Starter implementation note

The default target table stores `RAW_RECORD VARIANT` plus file lineage columns. This is safe for a generic starter project. For enterprise production, extend `SP_CREATE_OR_EVOLVE_TARGETS` to infer typed columns from Parquet and extend `SP_INGEST_FILES` for typed projection or `MERGE` behavior.
