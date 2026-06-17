from __future__ import annotations

import pandas as pd

from pipeline_utils import (
    add_validation,
    clean_text,
    ensure_schemas,
    get_engine,
    read_schema_tables,
    to_bool,
    to_date,
    to_int,
    to_num,
    parse_percent,
    write_df,
)


def build_stg_customers(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["customer_id"] = to_int(df["customer_id"])
    out["country"] = clean_text(df["country"], title=True)
    out["age_range"] = clean_text(df["age_range"])
    out["signup_date"] = to_date(df["signup_date"])
    copy_metadata(out, df)
    return add_validation(out, [
        ("invalid customer_id", out["customer_id"].isna()),
        ("missing country", out["country"].isna()),
        ("invalid signup_date", pd.isna(out["signup_date"])),
    ])


def build_stg_products(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["product_id"] = to_int(df["product_id"])
    out["product_name"] = clean_text(df["product_name"])
    out["category"] = clean_text(df["category"], title=True)
    out["brand"] = clean_text(df["brand"], title=True)
    out["color"] = clean_text(df["color"], title=True)
    out["size"] = clean_text(df["size"], upper=True)
    out["catalog_price"] = to_num(df["catalog_price"])
    out["cost_price"] = to_num(df["cost_price"])
    out["gender"] = clean_text(df["gender"], title=True)
    copy_metadata(out, df)
    return add_validation(out, [
        ("invalid product_id", out["product_id"].isna()),
        ("missing product_name", out["product_name"].isna()),
        ("catalog_price <= 0", out["catalog_price"].isna() | (out["catalog_price"] <= 0)),
        ("cost_price < 0", out["cost_price"].isna() | (out["cost_price"] < 0)),
        ("cost_price > catalog_price", out["cost_price"] > out["catalog_price"]),
    ])


def build_stg_sales(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["sale_id"] = to_int(df["sale_id"])
    out["channel"] = clean_text(df["channel"])
    out["is_discounted"] = to_bool(df["discounted"])
    out["total_amount"] = to_num(df["total_amount"])
    out["sale_date"] = to_date(df["sale_date"])
    out["customer_id"] = to_int(df["customer_id"])
    out["country"] = clean_text(df["country"], title=True)
    copy_metadata(out, df)
    return add_validation(out, [
        ("invalid sale_id", out["sale_id"].isna()),
        ("missing channel", out["channel"].isna()),
        ("invalid discounted", out["is_discounted"].isna()),
        ("total_amount < 0", out["total_amount"].isna() | (out["total_amount"] < 0)),
        ("invalid sale_date", pd.isna(out["sale_date"])),
        ("invalid customer_id", out["customer_id"].isna()),
        ("missing country", out["country"].isna()),
    ])


def build_stg_salesitems(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["item_id"] = to_int(df["item_id"])
    out["sale_id"] = to_int(df["sale_id"])
    out["product_id"] = to_int(df["product_id"])
    out["quantity"] = to_int(df["quantity"])
    out["original_price"] = to_num(df["original_price"])
    out["unit_price"] = to_num(df["unit_price"])
    out["discount_applied"] = to_num(df["discount_applied"])
    out["discount_percent"] = parse_percent(df["discount_percent"])
    out["is_discounted"] = to_bool(df["discounted"])
    out["item_total"] = to_num(df["item_total"])
    out["sale_date"] = to_date(df["sale_date"])
    out["channel"] = clean_text(df["channel"])
    out["channel_campaigns"] = clean_text(df["channel_campaigns"])
    copy_metadata(out, df)
    return add_validation(out, [
        ("invalid item_id", out["item_id"].isna()),
        ("invalid sale_id", out["sale_id"].isna()),
        ("invalid product_id", out["product_id"].isna()),
        ("quantity <= 0", out["quantity"].isna() | (out["quantity"] <= 0)),
        ("original_price < 0", out["original_price"].isna() | (out["original_price"] < 0)),
        ("unit_price < 0", out["unit_price"].isna() | (out["unit_price"] < 0)),
        ("discount_applied < 0", out["discount_applied"].isna() | (out["discount_applied"] < 0)),
        ("invalid discount_percent", out["discount_percent"].isna()),
        ("invalid discounted", out["is_discounted"].isna()),
        ("item_total < 0", out["item_total"].isna() | (out["item_total"] < 0)),
        ("invalid sale_date", pd.isna(out["sale_date"])),
    ])


def build_stg_stock(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["country"] = clean_text(df["country"], title=True)
    out["product_id"] = to_int(df["product_id"])
    out["stock_quantity"] = to_int(df["stock_quantity"])
    copy_metadata(out, df)
    return add_validation(out, [
        ("missing country", out["country"].isna()),
        ("invalid product_id", out["product_id"].isna()),
        ("stock_quantity < 0", out["stock_quantity"].isna() | (out["stock_quantity"] < 0)),
    ])


def build_stg_campaigns(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["campaign_id"] = to_int(df["campaign_id"])
    out["campaign_name"] = clean_text(df["campaign_name"])
    out["start_date"] = to_date(df["start_date"])
    out["end_date"] = to_date(df["end_date"])
    out["channel"] = clean_text(df["channel"])
    out["discount_type"] = clean_text(df["discount_type"], title=True)
    out["discount_value_raw"] = clean_text(df["discount_value"])
    numeric_value = to_num(df["discount_value"].astype(str).str.replace("%", "", regex=False))
    out["discount_percent_value"] = numeric_value.where(out["discount_type"].eq("Percentage")) / 100
    out["discount_amount_value"] = numeric_value.where(out["discount_type"].eq("Fixed"))
    copy_metadata(out, df)
    return add_validation(out, [
        ("invalid campaign_id", out["campaign_id"].isna()),
        ("missing campaign_name", out["campaign_name"].isna()),
        ("invalid start_date", pd.isna(out["start_date"])),
        ("invalid end_date", pd.isna(out["end_date"])),
        ("start_date > end_date", pd.to_datetime(out["start_date"]) > pd.to_datetime(out["end_date"])),
        ("invalid discount_type", ~out["discount_type"].isin(["Percentage", "Fixed"])),
        ("invalid discount_value", numeric_value.isna()),
    ])


def build_stg_channels(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["channel"] = clean_text(df["channel"])
    out["description"] = clean_text(df["description"])
    copy_metadata(out, df)
    return add_validation(out, [("missing channel", out["channel"].isna())])


def copy_metadata(out: pd.DataFrame, src: pd.DataFrame) -> None:
    for col in ["source_file", "loaded_at", "batch_id"]:
        out[col] = src[col] if col in src.columns else pd.NA


def build_staging() -> None:
    engine = get_engine()
    ensure_schemas(engine)
    raw = read_schema_tables(engine, "raw", ["customers", "products", "sales", "salesitems", "stock", "campaigns", "channels"])
    staging = {
        "stg_customers": build_stg_customers(raw["customers"]),
        "stg_products": build_stg_products(raw["products"]),
        "stg_sales": build_stg_sales(raw["sales"]),
        "stg_salesitems": build_stg_salesitems(raw["salesitems"]),
        "stg_stock": build_stg_stock(raw["stock"]),
        "stg_campaigns": build_stg_campaigns(raw["campaigns"]),
        "stg_channels": build_stg_channels(raw["channels"]),
    }
    for name, df in staging.items():
        write_df(engine, df, "staging", name)
        print(f"  staging.{name}: {len(df):,} rows, valid={int(df['is_valid'].sum()):,}")


def main() -> None:
    build_staging()


if __name__ == "__main__":
    main()
