from __future__ import annotations

import os

import snowflake.connector
from dotenv import load_dotenv


def connect():
    load_dotenv()
    kwargs = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "role": os.getenv("SNOWFLAKE_ROLE"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "database": os.getenv("SNOWFLAKE_DATABASE"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA"),
        "authenticator": os.getenv("SNOWFLAKE_AUTHENTICATOR", "snowflake"),
    }
    kwargs = {k: v for k, v in kwargs.items() if v}
    required = ["account", "user", "role", "warehouse", "database", "schema"]
    missing = [k for k in required if k not in kwargs]
    if missing:
        raise RuntimeError(f"Missing Snowflake environment variables: {missing}")
    return snowflake.connector.connect(**kwargs)
