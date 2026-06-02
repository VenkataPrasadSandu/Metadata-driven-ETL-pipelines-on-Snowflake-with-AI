from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console

from metadata_etl.connection import connect
from metadata_etl.validate_config import validate_config

console = Console()


def load_config(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def upsert_dataset(cur, ds: dict[str, Any]) -> None:
    sql = """
    MERGE INTO CONTROL.CFG_DATASET T
    USING (
        SELECT
            %(dataset_name)s AS DATASET_NAME,
            %(description)s AS DESCRIPTION,
            %(domain)s AS DOMAIN,
            %(owner_email)s AS OWNER_EMAIL,
            %(enabled)s AS ENABLED,
            %(landing_subpath)s AS LANDING_SUBPATH,
            %(stage_name)s AS STAGE_NAME,
            %(file_format_name)s AS FILE_FORMAT_NAME,
            %(file_type)s AS FILE_TYPE,
            %(target_database)s AS TARGET_DATABASE,
            %(target_schema)s AS TARGET_SCHEMA,
            %(target_table)s AS TARGET_TABLE,
            %(load_mode)s AS LOAD_MODE,
            PARSE_JSON(%(primary_keys)s) AS PRIMARY_KEYS,
            PARSE_JSON(%(partition_keys)s) AS PARTITION_KEYS,
            %(expected_arrival_cron)s AS EXPECTED_ARRIVAL_CRON,
            %(freshness_sla_minutes)s AS FRESHNESS_SLA_MINUTES,
            %(schema_evolution)s AS SCHEMA_EVOLUTION,
            %(dq_enabled)s AS DQ_ENABLED,
            PARSE_JSON(%(tags)s) AS TAGS
    ) S
    ON T.DATASET_NAME = S.DATASET_NAME
    WHEN MATCHED THEN UPDATE SET
        DESCRIPTION = S.DESCRIPTION,
        DOMAIN = S.DOMAIN,
        OWNER_EMAIL = S.OWNER_EMAIL,
        ENABLED = S.ENABLED,
        LANDING_SUBPATH = S.LANDING_SUBPATH,
        STAGE_NAME = S.STAGE_NAME,
        FILE_FORMAT_NAME = S.FILE_FORMAT_NAME,
        FILE_TYPE = S.FILE_TYPE,
        TARGET_DATABASE = S.TARGET_DATABASE,
        TARGET_SCHEMA = S.TARGET_SCHEMA,
        TARGET_TABLE = S.TARGET_TABLE,
        LOAD_MODE = S.LOAD_MODE,
        PRIMARY_KEYS = S.PRIMARY_KEYS,
        PARTITION_KEYS = S.PARTITION_KEYS,
        EXPECTED_ARRIVAL_CRON = S.EXPECTED_ARRIVAL_CRON,
        FRESHNESS_SLA_MINUTES = S.FRESHNESS_SLA_MINUTES,
        SCHEMA_EVOLUTION = S.SCHEMA_EVOLUTION,
        DQ_ENABLED = S.DQ_ENABLED,
        TAGS = S.TAGS,
        UPDATED_AT = CURRENT_TIMESTAMP(),
        UPDATED_BY = CURRENT_USER()
    WHEN NOT MATCHED THEN INSERT (
        DATASET_NAME, DESCRIPTION, DOMAIN, OWNER_EMAIL, ENABLED, LANDING_SUBPATH,
        STAGE_NAME, FILE_FORMAT_NAME, FILE_TYPE, TARGET_DATABASE, TARGET_SCHEMA,
        TARGET_TABLE, LOAD_MODE, PRIMARY_KEYS, PARTITION_KEYS, EXPECTED_ARRIVAL_CRON,
        FRESHNESS_SLA_MINUTES, SCHEMA_EVOLUTION, DQ_ENABLED, TAGS
    ) VALUES (
        S.DATASET_NAME, S.DESCRIPTION, S.DOMAIN, S.OWNER_EMAIL, S.ENABLED,
        S.LANDING_SUBPATH, S.STAGE_NAME, S.FILE_FORMAT_NAME, S.FILE_TYPE,
        S.TARGET_DATABASE, S.TARGET_SCHEMA, S.TARGET_TABLE, S.LOAD_MODE,
        S.PRIMARY_KEYS, S.PARTITION_KEYS, S.EXPECTED_ARRIVAL_CRON,
        S.FRESHNESS_SLA_MINUTES, S.SCHEMA_EVOLUTION, S.DQ_ENABLED, S.TAGS
    )
    """
    params = {
        "dataset_name": str(ds["dataset_name"]).upper(),
        "description": ds.get("description"),
        "domain": ds.get("domain"),
        "owner_email": ds.get("owner") or ds.get("owner_email"),
        "enabled": bool(ds.get("enabled", True)),
        "landing_subpath": ds["landing_subpath"].strip("/"),
        "stage_name": ds["stage_name"],
        "file_format_name": ds["file_format_name"],
        "file_type": str(ds.get("file_type", "PARQUET")).upper(),
        "target_database": ds["target_database"],
        "target_schema": ds["target_schema"],
        "target_table": ds["target_table"],
        "load_mode": str(ds.get("load_mode", "APPEND")).upper(),
        "primary_keys": json.dumps(ds.get("primary_keys", [])),
        "partition_keys": json.dumps(ds.get("partition_keys", [])),
        "expected_arrival_cron": ds.get("expected_arrival_cron"),
        "freshness_sla_minutes": ds.get("freshness_sla_minutes"),
        "schema_evolution": bool(ds.get("schema_evolution", True)),
        "dq_enabled": bool(ds.get("dq_enabled", True)),
        "tags": json.dumps(ds.get("tags", {})),
    }
    cur.execute(sql, params)


def main() -> None:
    parser = argparse.ArgumentParser(description="Load YAML metadata into CONTROL.CFG_DATASET")
    parser.add_argument("--config", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    errors = validate_config(args.config)
    if errors:
        for e in errors:
            console.print(f"[red]- {e}[/red]")
        raise SystemExit(1)

    cfg = load_config(args.config)
    datasets = cfg["datasets"]
    console.print(f"Validated {len(datasets)} dataset(s)")
    if not args.apply:
        console.print("Dry run only. Add --apply to load metadata.")
        return

    with connect() as conn:
        cur = conn.cursor()
        try:
            for ds in datasets:
                upsert_dataset(cur, ds)
                console.print(f"Upserted {str(ds['dataset_name']).upper()}")
        finally:
            cur.close()


if __name__ == "__main__":
    main()
