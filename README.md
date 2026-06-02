# Snowflake AI Metadata-Driven ETL Framework

A GitHub-ready end-to-end project for building **metadata-driven ETL pipelines on Snowflake with AI assistance**.

The goal is simple: onboard datasets by changing metadata rows, not by creating a brand-new pipeline every time.

```text
External Storage / Stage
        ↓
SP_DISCOVER_FILES → CONTROL.FILE_CONTROL
        ↓
SP_CREATE_OR_EVOLVE_TARGETS
        ↓
SP_INGEST_FILES → BRONZE / ICEBERG target tables
        ↓
SP_RUN_DQ_RULES
        ↓
Streamlit Control Tower + AI suggestions using Snowflake Cortex
```

## What is included

| Area | Included |
|---|---|
| Metadata tables | `CFG_DATASET`, `FILE_CONTROL`, `INGEST_LOG`, `DQ_RULE`, `DQ_RESULT`, `AI_SUGGESTION_LOG`, `DDL_HISTORY` |
| Stored procedures | Discovery, target creation/evolution starter, ingestion, DQ execution, one-dataset run, full wrapper run, AI DQ suggestion |
| AI | Snowflake Cortex prompt to suggest DQ rules from target metadata/sample data |
| Orchestration | Snowflake Task with CRON schedule |
| UI | Streamlit control tower for runs, dataset health, failed files, DQ results, and AI suggestions |
| CI/CD | GitHub Actions Snowflake deployment pattern |
| Python utilities | Config validation, config loader, SQL deployer, pipeline runner |
| Docs | Architecture, runbook, extension guide |

## Repo structure

```text
snowflake-ai-metadata-etl/
├── app/streamlit_app.py
├── config/datasets.sample.yml
├── config/prompts.yml
├── diagrams/architecture.mmd
├── docs/architecture.md
├── docs/runbook.md
├── docs/extending.md
├── scripts/deploy.sh
├── scripts/deploy.ps1
├── scripts/generate_sample_data.py
├── sql/00_create_roles_warehouses.sql
├── sql/01_create_database_schemas.sql
├── sql/02_create_file_formats_stages.sql
├── sql/03_metadata_tables.sql
├── sql/04_stored_procedures.sql
├── sql/05_monitoring_views.sql
├── sql/06_tasks.sql
├── sql/07_seed_sample_config.sql
├── src/metadata_etl/config_loader.py
├── src/metadata_etl/deploy_sql.py
├── src/metadata_etl/run_pipeline.py
├── src/metadata_etl/validate_config.py
├── tests/test_config_validation.py
├── .github/workflows/deploy.yml
├── .env.example
├── requirements.txt
└── snowflake.yml
```

## Quick start

### 1. Create Python environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in:

```bash
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ROLE=SYSADMIN
SNOWFLAKE_WAREHOUSE=ETL_WH
SNOWFLAKE_DATABASE=AI_ETL_DEV
SNOWFLAKE_SCHEMA=CONTROL
SNOWFLAKE_AUTHENTICATOR=snowflake
```

For production, use key-pair auth, OAuth, or a secrets manager instead of password auth.

### 3. Deploy objects

```bash
bash scripts/deploy.sh
```

Or manually:

```bash
python -m metadata_etl.deploy_sql --sql-dir sql
python -m metadata_etl.validate_config --config config/datasets.sample.yml
python -m metadata_etl.config_loader --config config/datasets.sample.yml --apply
```

### 4. Upload sample data

```bash
python scripts/generate_sample_data.py
```

The script prints Snowflake `PUT` commands for the generated Parquet files.

### 5. Run pipeline

```bash
python -m metadata_etl.run_pipeline --days-back 7 --max-retries 3
```

SQL equivalent:

```sql
CALL CONTROL.SP_PROCESS_CHANGED_DATASETS(7, 3);
```

### 6. Run UI

```bash
streamlit run app/streamlit_app.py
```

## Main metadata design

### `CONTROL.CFG_DATASET`

One row per dataset. Example fields:

| Column | Purpose |
|---|---|
| `DATASET_NAME` | Logical dataset, for example `CUSTOMER`, `CLAIMS`, `SLSDA`, `INVDA` |
| `LANDING_SUBPATH` | Stage folder, for example `raw/customer` |
| `STAGE_NAME` | Snowflake stage object, for example `CONTROL.STG_RAW` |
| `TARGET_DATABASE` | Target database |
| `TARGET_SCHEMA` | Target schema, for example `BRONZE` |
| `TARGET_TABLE` | Target table |
| `LOAD_MODE` | `APPEND`, `MERGE`, or `FULL_REFRESH` |
| `PRIMARY_KEYS` | JSON array of key columns |
| `PARTITION_KEYS` | JSON array of partition columns |
| `SCHEMA_EVOLUTION` | Whether auto DDL evolution is enabled |
| `DQ_ENABLED` | Whether DQ should run |

### `CONTROL.FILE_CONTROL`

Tracks every staged file using full file path, not just file name. This avoids duplicate problems when the same file name appears in multiple folders.

Statuses:

```text
NEW
IN_PROGRESS
LOADED
FAILED_RETRYABLE
FAILED_FINAL
SKIPPED
```

### `CONTROL.INGEST_LOG`

Stores run ID, dataset, step, status, counts, query ID, error message, and timing.

## End-to-end procedure wrapper

```sql
CALL CONTROL.SP_PROCESS_CHANGED_DATASETS(7, 3);
```

This wrapper does:

1. Discover staged files changed in the last `P_DAYS_BACK` days.
2. Create target tables if missing.
3. Ingest `NEW` and retryable files.
4. Run enabled DQ rules.
5. Write observability logs.

## AI flow

```sql
CALL CONTROL.SP_AI_SUGGEST_DQ_RULES('CUSTOMER', 10);
```

The AI procedure reads target table metadata/sample rows, sends a prompt to Snowflake Cortex, and stores the output in `CONTROL.AI_SUGGESTION_LOG`. The generated rules are not automatically activated; a data engineer reviews and promotes them into `CONTROL.DQ_RULE`.

## Production hardening checklist

- Use key-pair/OAuth authentication in CI/CD.
- Use separate databases per environment: `AI_ETL_DEV`, `AI_ETL_QA`, `AI_ETL_PROD`.
- Restrict write access to `CONTROL` tables.
- Add masking policies and row access policies for PII/PHI.
- Configure Snowflake event tables for stored procedure logs.
- Add alerts for `FAILED_FINAL`, SLA misses, and critical DQ failures.
- Add MERGE mode implementation for upsert datasets.
- Add typed-table evolution if you do not want raw `VARIANT` landing tables.
- Add classification/tag propagation into Silver/Gold.

## Adapting to your existing naming

| Existing concept | Project object |
|---|---|
| `CFG_DATASET` / `DATA_INGESTION_CFG` | `CONTROL.CFG_DATASET` |
| `FILE_CONTROL` / `DATA_INGESTION_CNTL` | `CONTROL.FILE_CONTROL` |
| `INGEST_LOG` / `DATA_INGESTION_LOG` | `CONTROL.INGEST_LOG` |
| `STG_RAW` | `CONTROL.STG_RAW` |
| DDL procedure | `CONTROL.SP_CREATE_OR_EVOLVE_TARGETS` |
| Retry ingestion | `CONTROL.SP_INGEST_FILES` |
| Main wrapper | `CONTROL.SP_PROCESS_CHANGED_DATASETS` |
| AI-generated DQ suggestions | `CONTROL.SP_AI_SUGGEST_DQ_RULES` |

## License

MIT
