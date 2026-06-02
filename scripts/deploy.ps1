$ErrorActionPreference = "Stop"
python -m metadata_etl.deploy_sql --sql-dir sql
python -m metadata_etl.validate_config --config config/datasets.sample.yml
python -m metadata_etl.config_loader --config config/datasets.sample.yml --apply
Write-Host "Deployment complete. Run: python -m metadata_etl.run_pipeline --days-back 7 --max-retries 3"
