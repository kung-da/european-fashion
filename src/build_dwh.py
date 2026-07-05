from __future__ import annotations

from datetime import date

import pandas as pd

from pipeline_utils import ensure_schemas, get_engine, read_schema_tables, write_df


STAGING_TABLES = ["stg_customers", "stg_products", "stg_sales", "stg_salesitems", "stg_stock", "stg_campaigns", "stg_channels"]


def valid(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["is_valid"].fillna(False)].copy()


def yyyymmdd(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, errors="coerce").dt.strftime("%Y%m%d").astype("Int64")


def build_dim_date(stg: dict[str, pd.DataFrame]) -> pd.DataFrame:
    dates = pd.concat(
        [
            pd.to_datetime(stg["stg_customers"]["signup_date"], errors="coerce"),
            pd.to_datetime(stg["stg_sales"]["sale_date"], errors="coerce"),
            pd.to_datetime(stg["stg_salesitems"]["sale_date"], errors="coerce"),
            pd.to_datetime(stg["stg_campaigns"]["start_date"], errors="coerce"),
            pd.to_datetime(stg["stg_campaigns"]["end_date"], errors="coerce"),
            pd.Series([pd.Timestamp(date.today())]),
        ],
        ignore_index=True,
    ).dropna()
    calendar = pd.DataFrame({"full_date": pd.date_range(dates.min(), dates.max(), freq="D")})
    calendar["date_key"] = calendar["full_date"].dt.strftime("%Y%m%d").astype(int)
    calendar["day_of_week"] = calendar["full_date"].dt.isocalendar().day.astype(int)
    calendar["day_name"] = calendar["full_date"].dt.day_name()
    calendar["day_of_month"] = calendar["full_date"].dt.day.astype(int)
    calendar["week_of_year"] = calendar["full_date"].dt.isocalendar().week.astype(int)
    calendar["month_number"] = calendar["full_date"].dt.month.astype(int)
    calendar["month_name"] = calendar["full_date"].dt.month_name()
    calendar["quarter_number"] = calendar["full_date"].dt.quarter.astype(int)
    calendar["year_number"] = calendar["full_date"].dt.year.astype(int)
    calendar["is_weekend"] = calendar["day_of_week"].isin([6, 7])
    calendar["full_date"] = calendar["full_date"].dt.date
    return calendar[
        [
            "date_key",
            "full_date",
            "day_of_week",
            "day_name",
            "day_of_month",
            "week_of_year",
            "month_number",
            "month_name",
            "quarter_number",
            "year_number",
            "is_weekend",
        ]
    ]


def build_dim_geography(stg: dict[str, pd.DataFrame]) -> pd.DataFrame:
    countries = pd.concat(
        [stg["stg_customers"]["country"], stg["stg_sales"]["country"], stg["stg_stock"]["country"]],
        ignore_index=True,
    ).dropna().drop_duplicates().sort_values().reset_index(drop=True)
    return pd.DataFrame({"geography_key": range(1, len(countries) + 1), "country": countries, "region": "Europe"})


def build_dim_channel(stg: dict[str, pd.DataFrame]) -> pd.DataFrame:
    channels = pd.concat(
        [
            stg["stg_channels"][["channel", "description"]].assign(in_sales=True, in_campaign=False),
            stg["stg_sales"][["channel"]].assign(description=pd.NA, in_sales=True, in_campaign=False),
            stg["stg_salesitems"][["channel"]].assign(description=pd.NA, in_sales=True, in_campaign=False),
            stg["stg_campaigns"][["channel"]].assign(description=pd.NA, in_sales=False, in_campaign=True),
        ],
        ignore_index=True,
    ).dropna(subset=["channel"])
    grouped = channels.groupby("channel", as_index=False).agg(
        channel_description=("description", lambda x: next((v for v in x if pd.notna(v)), pd.NA)),
        in_sales=("in_sales", "max"),
        in_campaign=("in_campaign", "max"),
    )
    grouped["channel_key"] = range(1, len(grouped) + 1)
    grouped["channel_type"] = grouped.apply(lambda r: "Sales" if r["in_sales"] else "Marketing" if r["in_campaign"] else "Unknown", axis=1)
    grouped = grouped.rename(columns={"channel": "channel_name"})
    return grouped[["channel_key", "channel_name", "channel_description", "channel_type"]]


def build_dim_customer(stg: dict[str, pd.DataFrame], dims: dict[str, pd.DataFrame]) -> pd.DataFrame:
    c = valid(stg["stg_customers"]).drop_duplicates("customer_id").copy()
    c = c.merge(dims["dim_geography"][["geography_key", "country"]], on="country", how="left")
    c["customer_key"] = range(1, len(c) + 1)
    c["signup_date_key"] = yyyymmdd(c["signup_date"])
    c["effective_from"] = date(1900, 1, 1)
    c["effective_to"] = date(9999, 12, 31)
    c["is_current"] = True
    return c[["customer_key", "customer_id", "geography_key", "age_range", "signup_date", "signup_date_key", "effective_from", "effective_to", "is_current"]]


def build_dim_product(stg: dict[str, pd.DataFrame]) -> pd.DataFrame:
    p = valid(stg["stg_products"]).drop_duplicates("product_id").copy()
    p["product_key"] = range(1, len(p) + 1)
    p["effective_from"] = date(1900, 1, 1)
    p["effective_to"] = date(9999, 12, 31)
    p["is_current"] = True
    return p[["product_key", "product_id", "product_name", "category", "brand", "color", "size", "gender", "catalog_price", "cost_price", "effective_from", "effective_to", "is_current"]]


def build_dim_campaign(stg: dict[str, pd.DataFrame], dims: dict[str, pd.DataFrame]) -> pd.DataFrame:
    c = valid(stg["stg_campaigns"]).drop_duplicates("campaign_id").copy()
    c = c.merge(dims["dim_channel"][["channel_key", "channel_name"]], left_on="channel", right_on="channel_name", how="left")
    c["campaign_key"] = range(1, len(c) + 1)
    c["start_date_key"] = yyyymmdd(c["start_date"])
    c["end_date_key"] = yyyymmdd(c["end_date"])
    c = c.rename(columns={"channel": "channel_name_src"})
    c["channel_name"] = c["channel_name"].fillna(c["channel_name_src"])
    return c[
        [
            "campaign_key",
            "campaign_id",
            "campaign_name",
            "channel_key",
            "start_date",
            "end_date",
            "start_date_key",
            "end_date_key",
            "discount_type",
            "discount_value_raw",
            "discount_percent_value",
            "discount_amount_value",
        ]
    ]


def build_fact_order(stg: dict[str, pd.DataFrame], dims: dict[str, pd.DataFrame]) -> pd.DataFrame:
    s = valid(stg["stg_sales"]).copy()
    line_counts = valid(stg["stg_salesitems"]).groupby("sale_id").size().rename("line_item_count").reset_index()
    f = s.merge(line_counts, on="sale_id", how="left")
    f = f.merge(dims["dim_customer"][["customer_key", "customer_id"]], on="customer_id", how="inner")
    f = f.merge(dims["dim_channel"][["channel_key", "channel_name"]], left_on="channel", right_on="channel_name", how="inner")
    f["order_key"] = range(1, len(f) + 1)
    f["sale_date_key"] = yyyymmdd(f["sale_date"])
    f["order_count"] = 1
    f["line_item_count"] = f["line_item_count"].fillna(0).astype(int)
    return f[["order_key", "sale_id", "sale_date_key", "customer_key", "channel_key", "order_count", "line_item_count", "total_amount", "is_discounted"]]


def map_campaign(row: pd.Series, campaigns: pd.DataFrame):
    if pd.isna(row.get("channel_campaigns")):
        return pd.NA
    key = str(row["channel_campaigns"]).lower()
    sale_date = pd.to_datetime(row["sale_date"])
    candidates = campaigns[
        ((campaigns["campaign_name"].str.lower() == key) | (campaigns["channel_name"].str.lower() == key))
        & (pd.to_datetime(campaigns["start_date"]) <= sale_date)
        & (pd.to_datetime(campaigns["end_date"]) >= sale_date)
    ]
    if candidates.empty:
        return pd.NA
    return candidates.iloc[0]["campaign_key"]


def build_fact_sales(stg: dict[str, pd.DataFrame], dims: dict[str, pd.DataFrame]) -> pd.DataFrame:
    si = valid(stg["stg_salesitems"]).copy()
    s = valid(stg["stg_sales"])[["sale_id", "customer_id"]]
    f = si.merge(s, on="sale_id", how="inner")
    f = f.merge(dims["dim_customer"][["customer_key", "customer_id"]], on="customer_id", how="inner")
    f = f.merge(dims["dim_product"][["product_key", "product_id", "cost_price"]], on="product_id", how="inner")
    f = f.merge(dims["dim_channel"][["channel_key", "channel_name"]], left_on="channel", right_on="channel_name", how="inner")
    
    # Merge dim_campaign with dim_channel to provide channel_name to map_campaign
    c_df = dims["dim_campaign"].merge(dims["dim_channel"][["channel_key", "channel_name"]], on="channel_key", how="left")
    f["campaign_key"] = f.apply(lambda r: map_campaign(r, c_df), axis=1).astype("Int64")
    f["sales_key"] = range(1, len(f) + 1)
    f["sale_date_key"] = yyyymmdd(f["sale_date"])
    f["gross_amount"] = f["quantity"].astype(float) * f["original_price"].astype(float)
    f["net_amount"] = f["item_total"].astype(float)
    f["discount_amount"] = f["gross_amount"] - f["net_amount"]
    f["cost_amount"] = f["quantity"].astype(float) * f["cost_price"].astype(float)
    f["gross_profit"] = f["net_amount"] - f["cost_amount"]
    return f[
        [
            "sales_key",
            "item_id",
            "sale_id",
            "sale_date_key",
            "customer_key",
            "product_key",
            "channel_key",
            "campaign_key",
            "quantity",
            "original_price",
            "unit_price",
            "gross_amount",
            "net_amount",
            "discount_amount",
            "discount_percent",
            "cost_amount",
            "gross_profit",
            "is_discounted",
        ]
    ]


def build_fact_inventory(stg: dict[str, pd.DataFrame], dims: dict[str, pd.DataFrame]) -> pd.DataFrame:
    st = valid(stg["stg_stock"]).copy()
    f = st.merge(dims["dim_product"][["product_key", "product_id", "catalog_price", "cost_price"]], on="product_id", how="inner")
    f = f.merge(dims["dim_geography"][["geography_key", "country"]], on="country", how="inner")
    f["inventory_key"] = range(1, len(f) + 1)
    f["snapshot_date_key"] = int(pd.Timestamp(date.today()).strftime("%Y%m%d"))
    f["stock_value_at_cost"] = f["stock_quantity"].astype(float) * f["cost_price"].astype(float)
    f["stock_value_at_catalog"] = f["stock_quantity"].astype(float) * f["catalog_price"].astype(float)
    return f[["inventory_key", "snapshot_date_key", "product_key", "geography_key", "stock_quantity", "stock_value_at_cost", "stock_value_at_catalog"]]


def build_fact_customer_activity(stg: dict[str, pd.DataFrame], dims: dict[str, pd.DataFrame]) -> pd.DataFrame:
    customers = valid(stg["stg_customers"])[["customer_id", "signup_date"]].copy()
    signup = customers.rename(columns={"signup_date": "activity_date"})
    signup["signup_count"] = 1
    signup["order_count"] = 0
    signup["revenue_amount"] = 0.0
    sales = valid(stg["stg_sales"]).groupby(["customer_id", "sale_date"], as_index=False).agg(order_count=("sale_id", "count"), revenue_amount=("total_amount", "sum"))
    sales = sales.rename(columns={"sale_date": "activity_date"})
    sales["signup_count"] = 0
    activity = pd.concat([signup, sales], ignore_index=True)
    activity = activity.groupby(["customer_id", "activity_date"], as_index=False).agg(signup_count=("signup_count", "sum"), order_count=("order_count", "sum"), revenue_amount=("revenue_amount", "sum"))
    activity = activity.merge(dims["dim_customer"][["customer_key", "customer_id"]], on="customer_id", how="inner")
    activity["customer_activity_key"] = range(1, len(activity) + 1)
    activity["activity_date_key"] = yyyymmdd(activity["activity_date"])
    return activity[["customer_activity_key", "activity_date_key", "customer_key", "signup_count", "order_count", "revenue_amount"]]


def build_dwh() -> None:
    engine = get_engine()
    ensure_schemas(engine)
    stg = read_schema_tables(engine, "staging", STAGING_TABLES)
    dims = {}
    dims["dim_date"] = build_dim_date(stg)
    dims["dim_geography"] = build_dim_geography(stg)
    dims["dim_channel"] = build_dim_channel(stg)
    dims["dim_customer"] = build_dim_customer(stg, dims)
    dims["dim_product"] = build_dim_product(stg)
    dims["dim_campaign"] = build_dim_campaign(stg, dims)
    facts = {
        "fact_order": build_fact_order(stg, dims),
        "fact_sales": build_fact_sales(stg, dims),
        "fact_inventory": build_fact_inventory(stg, dims),
        "fact_customer_activity": build_fact_customer_activity(stg, dims),
    }
    for name, df in {**dims, **facts}.items():
        write_df(engine, df, "dwh", name)
        print(f"  dwh.{name}: {len(df):,} rows")


def main() -> None:
    build_dwh()


if __name__ == "__main__":
    main()
