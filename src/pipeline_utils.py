from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data" / "raw"

TABLE_FILES = {
    "customers": "dataset_fashion_store_customers.csv",
    "products": "dataset_fashion_store_products.csv",
    "sales": "dataset_fashion_store_sales.csv",
    "salesitems": "dataset_fashion_store_salesitems.csv",
    "stock": "dataset_fashion_store_stock.csv",
    "campaigns": "dataset_fashion_store_campaigns.csv",
    "channels": "dataset_fashion_store_channels.csv",
}


def get_database_url() -> str:
    load_dotenv(ROOT_DIR / ".env")
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "fashion_dw")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


def get_engine():
    return create_engine(get_database_url())


def ensure_schemas(engine) -> None:
    with engine.begin() as conn:
        for schema in ["raw", "staging", "dwh", "mart"]:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))


def read_csv_tables() -> dict[str, pd.DataFrame]:
    tables = {}
    missing = []
    for name, file_name in TABLE_FILES.items():
        path = RAW_DIR / file_name
        if not path.exists():
            missing.append(str(path))
            continue
        tables[name] = pd.read_csv(path, dtype=str, keep_default_na=False)
    if missing:
        raise FileNotFoundError("Missing CSV files:\n" + "\n".join(missing))
    return tables


def read_schema_tables(engine, schema: str, names: list[str]) -> dict[str, pd.DataFrame]:
    tables = {}
    for name in names:
        tables[name] = pd.read_sql_table(name, engine, schema=schema)
    return tables


def write_df(engine, df: pd.DataFrame, schema: str, table: str, if_exists: str = "replace") -> None:
    if if_exists == "replace":
        with engine.begin() as conn:
            relkind = conn.execute(
                text(
                    """
                    SELECT c.relkind
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = :schema AND c.relname = :table
                    """
                ),
                {"schema": schema, "table": table},
            ).scalar()
            if relkind in ("r", "p", "f"):
                conn.execute(text(f'DROP TABLE IF EXISTS "{schema}"."{table}" CASCADE'))
            elif relkind in ("v", "m"):
                conn.execute(text(f'DROP VIEW IF EXISTS "{schema}"."{table}" CASCADE'))
        if_exists = "fail"
    df.to_sql(table, engine, schema=schema, if_exists=if_exists, index=False, method="multi", chunksize=1000)


def clean_text(series: pd.Series, title: bool = False, upper: bool = False) -> pd.Series:
    s = series.fillna("").astype(str).str.strip()
    if title:
        s = s.str.title()
    if upper:
        s = s.str.upper()
    return s.replace("", pd.NA)


def to_int(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").astype("Int64")


def to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def to_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.date


def to_bool(series: pd.Series) -> pd.Series:
    s = series.fillna("").astype(str).str.strip().str.lower()
    return s.map({"1": True, "true": True, "t": True, "yes": True, "0": False, "false": False, "f": False, "no": False})


def parse_percent(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.fillna("").astype(str).str.replace("%", "", regex=False).str.strip(), errors="coerce") / 100


def add_validation(df: pd.DataFrame, rules: list[tuple[str, pd.Series]]) -> pd.DataFrame:
    errors = pd.Series([""] * len(df), index=df.index, dtype="object")
    is_valid = pd.Series([True] * len(df), index=df.index)
    for message, invalid_mask in rules:
        mask = invalid_mask.fillna(True)
        is_valid &= ~mask
        errors = errors.mask(mask, errors.where(errors.eq(""), errors + "; ") + message)
    df["is_valid"] = is_valid
    df["validation_errors"] = errors
    return df


def date_key(series: pd.Series) -> pd.Series:
    dt = pd.to_datetime(series, errors="coerce")
    return (dt.dt.strftime("%Y%m%d")).astype("float").astype("Int64")


def print_row_counts(engine) -> None:
    tables = [
        ("raw", "customers"), ("raw", "products"), ("raw", "sales"), ("raw", "salesitems"),
        ("raw", "stock"), ("raw", "campaigns"), ("raw", "channels"),
        ("staging", "stg_customers"), ("staging", "stg_products"), ("staging", "stg_sales"),
        ("staging", "stg_salesitems"), ("staging", "stg_stock"), ("staging", "stg_campaigns"),
        ("staging", "stg_channels"),
        ("dwh", "dim_customer"), ("dwh", "dim_product"), ("dwh", "dim_date"),
        ("dwh", "dim_geography"), ("dwh", "dim_channel"), ("dwh", "dim_campaign"),
        ("dwh", "fact_order"), ("dwh", "fact_sales"), ("dwh", "fact_inventory"),
        ("dwh", "fact_customer_activity"),
    ]
    print("\nRow counts:")
    with engine.begin() as conn:
        for schema, table in tables:
            try:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {schema}.{table}")).scalar_one()
                print(f"  {schema}.{table}: {count:,}")
            except Exception:
                print(f"  {schema}.{table}: not found")


def print_kpi_smoke_test(engine) -> None:
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT
                    SUM(total_amount) AS revenue,
                    SUM(order_count) AS orders,
                    SUM(total_amount) / NULLIF(SUM(order_count), 0) AS aov
                FROM dwh.fact_order
                """
            )
        ).one()
    print("\nKPI smoke test:")
    print(f"  revenue: {row.revenue}")
    print(f"  orders: {row.orders}")
    print(f"  aov: {row.aov}")
