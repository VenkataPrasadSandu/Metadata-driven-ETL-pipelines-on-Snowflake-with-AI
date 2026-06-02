from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console

console = Console()

REQUIRED_FIELDS = {
    "dataset_name",
    "landing_subpath",
    "target_database",
    "target_schema",
    "target_table",
    "stage_name",
    "file_format_name",
    "file_type",
    "load_mode",
}

VALID_LOAD_MODES = {"APPEND", "MERGE", "FULL_REFRESH"}
VALID_FILE_TYPES = {"PARQUET", "CSV", "JSON"}


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def validate_dataset(ds: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_FIELDS - set(ds.keys()))
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")

    name = str(ds.get("dataset_name", "<unknown>")).upper()

    load_mode = str(ds.get("load_mode", "")).upper()
    if load_mode and load_mode not in VALID_LOAD_MODES:
        errors.append(f"{name}: invalid load_mode {load_mode}; expected {sorted(VALID_LOAD_MODES)}")

    file_type = str(ds.get("file_type", "")).upper()
    if file_type and file_type not in VALID_FILE_TYPES:
        errors.append(f"{name}: invalid file_type {file_type}; expected {sorted(VALID_FILE_TYPES)}")

    if ds.get("primary_keys") is not None and not isinstance(ds.get("primary_keys"), list):
        errors.append(f"{name}: primary_keys must be a list")

    if ds.get("partition_keys") is not None and not isinstance(ds.get("partition_keys"), list):
        errors.append(f"{name}: partition_keys must be a list")

    return errors


def validate_config(path: str | Path) -> list[str]:
    cfg = load_yaml(path)
    datasets = cfg.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        return ["config must contain a non-empty datasets list"]

    errors: list[str] = []
    seen: set[str] = set()
    for ds in datasets:
        if not isinstance(ds, dict):
            errors.append("each dataset entry must be an object")
            continue
        name = str(ds.get("dataset_name", "")).upper()
        if not name:
            errors.append("dataset_name cannot be blank")
        elif name in seen:
            errors.append(f"duplicate dataset_name: {name}")
        seen.add(name)
        errors.extend(validate_dataset(ds))
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate metadata-driven ETL dataset config")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    errors = validate_config(args.config)
    if errors:
        console.print("[bold red]Config validation failed[/bold red]")
        for err in errors:
            console.print(f"- {err}")
        raise SystemExit(1)

    console.print("[bold green]Config validation passed[/bold green]")


if __name__ == "__main__":
    main()
