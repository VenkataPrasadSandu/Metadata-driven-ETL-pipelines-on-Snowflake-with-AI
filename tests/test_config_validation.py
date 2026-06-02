from pathlib import Path

from metadata_etl.validate_config import validate_config


def test_sample_config_valid():
    root = Path(__file__).resolve().parents[1]
    errors = validate_config(root / "config" / "datasets.sample.yml")
    assert errors == []
