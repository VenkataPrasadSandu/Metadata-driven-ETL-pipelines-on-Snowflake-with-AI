# Extending

## Add a dataset

Add a row in `config/datasets.sample.yml`, then run:

```bash
python -m metadata_etl.config_loader --config config/datasets.sample.yml --apply
```

## Add typed schema evolution

Extend `SP_CREATE_OR_EVOLVE_TARGETS` to:

1. Read representative Parquet files.
2. Infer column names/data types.
3. Compare with `INFORMATION_SCHEMA.COLUMNS`.
4. Generate `ALTER TABLE ADD COLUMN` statements.
5. Store DDL in `CONTROL.DDL_HISTORY`.

## Add MERGE mode

For upsert datasets:

1. Load file into temp staging table.
2. Build dynamic `ON` condition from `PRIMARY_KEYS`.
3. Execute `MERGE INTO target USING staging`.
4. Mark file loaded only after merge succeeds.

## Add classification

Add a `CONTROL.COLUMN_CLASSIFICATION` table and tag columns based on enterprise policy. Use Snowflake tags, masking policies, and row access policies for sensitive data.
