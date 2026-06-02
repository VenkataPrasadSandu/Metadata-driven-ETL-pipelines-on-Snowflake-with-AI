from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    customer_path = ROOT / "sample_data/raw/customer/2026/06/01/run_001/customer.parquet"
    claims_path = ROOT / "sample_data/raw/claims/2026/06/01/run_001/claims.parquet"
    customer_path.parent.mkdir(parents=True, exist_ok=True)
    claims_path.parent.mkdir(parents=True, exist_ok=True)

    pd.DataFrame([
        {"CUSTOMER_ID": 1, "CUSTOMER_NAME": "Acme Health", "STATUS": "ACTIVE"},
        {"CUSTOMER_ID": 2, "CUSTOMER_NAME": "Northwind", "STATUS": "ACTIVE"},
    ]).to_parquet(customer_path, index=False)

    pd.DataFrame([
        {"CLAIM_ID": "C100", "CUSTOMER_ID": 1, "CLAIM_AMOUNT": 125.50, "STATUS": "PAID"},
        {"CLAIM_ID": "C101", "CUSTOMER_ID": 2, "CLAIM_AMOUNT": 220.00, "STATUS": "PENDING"},
    ]).to_parquet(claims_path, index=False)

    print(f"Wrote {customer_path}")
    print(f"Wrote {claims_path}")
    print("\nSnowflake PUT commands:")
    print("PUT file://sample_data/raw/customer/2026/06/01/run_001/customer.parquet @AI_ETL_DEV.CONTROL.STG_RAW/raw/customer/2026/06/01/run_001 AUTO_COMPRESS=FALSE;")
    print("PUT file://sample_data/raw/claims/2026/06/01/run_001/claims.parquet @AI_ETL_DEV.CONTROL.STG_RAW/raw/claims/2026/06/01/run_001 AUTO_COMPRESS=FALSE;")


if __name__ == "__main__":
    main()
