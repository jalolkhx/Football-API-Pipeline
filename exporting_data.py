import os
import pandas as pd
import urllib.parse
from datetime import datetime, timezone

from sqlalchemy import create_engine, event, text, types

from catching_data import (
    get_standings,
    get_top_scorers,
    get_top_assists
)

# =========================
# SQL SERVER CONFIG (ENV)
# =========================
SQL_SERVER = os.getenv(r"SQL_SERVER")
SQL_DATABASE = os.getenv("SQL_DATABASE")
SQL_USERNAME = os.getenv("SQL_USERNAME")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")
SQL_DRIVER = os.getenv("SQL_DRIVER", "ODBC Driver 17 for SQL Server")
SQL_SCHEMA = os.getenv("SQL_SCHEMA", "dbo")

# =========================
# ENGINE
# =========================
conn_str = (
    f"DRIVER={{{SQL_DRIVER}}};"
    f"SERVER={SQL_SERVER};"
    f"DATABASE={SQL_DATABASE};"
    f"UID={SQL_USERNAME};"
    f"PWD={SQL_PASSWORD};"
    "TrustServerCertificate=yes;"
)

engine = create_engine(
    f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(conn_str)}"
)

@event.listens_for(engine, "before_cursor_execute")
def enable_fast_executemany(conn, cursor, statement, parameters, context, executemany):
    if executemany:
        cursor.fast_executemany = True

# =========================
# EXPORT
# =========================
def overwrite(df: pd.DataFrame, table: str):
    if "exported_at" not in df.columns:
        df = df.copy()
        df["exported_at"] = datetime.now(timezone.utc)
    else:
        df = df.copy()
        # if timezone-aware series, convert to UTC then drop tz
        try:
            if pd.api.types.is_datetime64tz_dtype(df["exported_at"]):
                df["exported_at"] = df["exported_at"].dt.tz_convert("UTC").dt.tz_localize(None)
            else:
                # if naive, ensure it's datetime type
                df["exported_at"] = pd.to_datetime(df["exported_at"])
        except Exception:
            # fallback: coerce to datetime
            df["exported_at"] = pd.to_datetime(df["exported_at"])

    # 2) Drop existing table if it exists (this avoids any rowversion/timestamp columns)
    drop_sql = f"IF OBJECT_ID('{SQL_SCHEMA}.{table}', 'U') IS NOT NULL DROP TABLE {SQL_SCHEMA}.{table};"
    with engine.begin() as conn:
        conn.execute(text(drop_sql))

        # 3) Write DataFrame to SQL with explicit dtype for exported_at
        df.to_sql(
            name=table,
            con=conn,
            schema=SQL_SCHEMA,
            if_exists="replace",   # table was dropped but keep 'replace' for safety
            index=False,
            method="multi",
            dtype={"exported_at": types.DateTime()}  # DATETIME on SQL Server
        )

    print(f"[INFO] Wrote table {SQL_SCHEMA}.{table} ({len(df)} rows)")

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    overwrite(get_standings(), "epl_standings")
    overwrite(get_top_scorers(), "epl_top_scorers")
    overwrite(get_top_assists(), "epl_top_assists")

    print("SQL Server tables updated.")
