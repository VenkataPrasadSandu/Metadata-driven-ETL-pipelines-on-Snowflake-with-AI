from __future__ import annotations

import os

import pandas as pd
import snowflake.connector
import streamlit as st
from dotenv import load_dotenv

st.set_page_config(page_title="Snowflake AI Metadata ETL", layout="wide")


def connect():
    load_dotenv()
    kwargs = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "role": os.getenv("SNOWFLAKE_ROLE"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "database": os.getenv("SNOWFLAKE_DATABASE", "AI_ETL_DEV"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "CONTROL"),
        "authenticator": os.getenv("SNOWFLAKE_AUTHENTICATOR", "snowflake"),
    }
    return snowflake.connector.connect(**{k: v for k, v in kwargs.items() if v})


@st.cache_data(ttl=60)
def query(sql: str) -> pd.DataFrame:
    with connect() as conn:
        return pd.read_sql(sql, conn)


st.title("Snowflake AI Metadata ETL Control Tower")
st.caption("Discovery, ingestion, retry, DQ, AI suggestions, and operational health")

try:
    health = query("SELECT * FROM CONTROL.VW_DATASET_HEALTH ORDER BY DATASET_NAME")
    failed = query("SELECT * FROM CONTROL.VW_FAILED_FILES ORDER BY UPDATED_AT DESC")
    runs = query("SELECT * FROM CONTROL.VW_RUN_SUMMARY ORDER BY STARTED_AT DESC LIMIT 50")
    dq = query("SELECT * FROM CONTROL.VW_DQ_SCORECARD ORDER BY DATASET_NAME, RULE_NAME")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Datasets", len(health))
    c2.metric("Failed Final", int(health.get("FAILED_FINAL_FILES", pd.Series(dtype=int)).sum() or 0))
    c3.metric("Retryable", int(health.get("RETRYABLE_FILES", pd.Series(dtype=int)).sum() or 0))
    c4.metric("Recent Runs", len(runs))

    tabs = st.tabs(["Dataset Health", "Run Summary", "Failed Files", "DQ Scorecard", "AI Suggestions"])

    with tabs[0]:
        st.dataframe(health, use_container_width=True, hide_index=True)

    with tabs[1]:
        st.dataframe(runs, use_container_width=True, hide_index=True)

    with tabs[2]:
        st.dataframe(failed, use_container_width=True, hide_index=True)

    with tabs[3]:
        st.dataframe(dq, use_container_width=True, hide_index=True)

    with tabs[4]:
        ai = query("""
            SELECT DATASET_NAME, SUGGESTION_TYPE, MODEL_NAME, APPROVED, CREATED_AT, RESPONSE_TEXT
            FROM CONTROL.AI_SUGGESTION_LOG
            ORDER BY CREATED_AT DESC
            LIMIT 100
        """)
        st.dataframe(ai, use_container_width=True, hide_index=True)

except Exception as exc:
    st.error("Could not load control tower data. Check Snowflake credentials and deployed objects.")
    st.exception(exc)
