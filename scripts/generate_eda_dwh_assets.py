from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
REPORT_DIR = ROOT / "reports"
EDA_REPORT_DIR = REPORT_DIR / "eda"
NOTEBOOK_DIR = ROOT / "notebooks"

FILES = {
    "customers": "dataset_fashion_store_customers.csv",
    "products": "dataset_fashion_store_products.csv",
    "sales": "dataset_fashion_store_sales.csv",
    "salesitems": "dataset_fashion_store_salesitems.csv",
    "stock": "dataset_fashion_store_stock.csv",
    "campaigns": "dataset_fashion_store_campaigns.csv",
    "channels": "dataset_fashion_store_channels.csv",
}


def load_tables() -> dict[str, pd.DataFrame]:
    return {name: pd.read_csv(RAW_DIR / file_name) for name, file_name in FILES.items()}


def parse_percent(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace("%", "", regex=False).str.strip(), errors="coerce") / 100


def table_overview(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    roles = {
        "customers": ("customer_id", "Customer master data", "Dimension source"),
        "products": ("product_id", "Product catalog and cost", "Dimension source"),
        "sales": ("sale_id", "Order header transaction", "Fact source"),
        "salesitems": ("item_id", "Order line item transaction", "Fact source"),
        "stock": ("product_id + country", "Inventory snapshot", "Inventory snapshot source"),
        "campaigns": ("campaign_id", "Marketing campaigns", "Campaign source"),
        "channels": ("channel", "Channel lookup", "Lookup source"),
    }
    return pd.DataFrame(
        [
            {
                "Source Table": name,
                "Rows": len(df),
                "Columns": len(df.columns),
                "Primary/Natural Key Candidate": roles[name][0],
                "Business Meaning": roles[name][1],
                "DWH Role": roles[name][2],
            }
            for name, df in tables.items()
        ]
    )


def missing_values(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, df in tables.items():
        for col in df.columns:
            count = int(df[col].isna().sum())
            rate = count / len(df) if len(df) else 0
            severity = "Good" if rate == 0 else "Acceptable" if rate < 0.05 else "Need Review" if rate <= 0.30 else "Serious"
            rows.append(
                {
                    "Table": name,
                    "Column": col,
                    "Missing Count": count,
                    "Missing Rate": rate,
                    "Severity": severity,
                    "DWH Impact": "No major impact" if count == 0 else "Need Unknown member or quarantine",
                    "Action": "Keep" if count == 0 else "Review before DWH load",
                }
            )
    return pd.DataFrame(rows)


def duplicate_checks(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    checks = {
        "customers": ["customer_id"],
        "products": ["product_id"],
        "sales": ["sale_id"],
        "salesitems": ["item_id"],
        "campaigns": ["campaign_id"],
        "stock": ["product_id", "country"],
    }
    rows = []
    for name, keys in checks.items():
        df = tables[name]
        count = int(df.duplicated(keys, keep=False).sum())
        rows.append(
            {
                "Table": name,
                "Key Checked": " + ".join(keys),
                "Duplicate Count": count,
                "Duplicate Rate": count / len(df),
                "DWH Impact": "Can break grain" if count else "No issue",
                "Recommended Action": "Deduplicate/quarantine" if count else "Keep",
            }
        )
    return pd.DataFrame(rows)


def relationship_checks(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    customers, products, sales = tables["customers"], tables["products"], tables["sales"]
    items, stock, campaigns, channels = tables["salesitems"], tables["stock"], tables["campaigns"], tables["channels"]
    geography = pd.Series(pd.concat([customers["country"], sales["country"], stock["country"]]).dropna().unique())
    channel_dim = pd.Series(pd.concat([channels["channel"], sales["channel"], items["channel"], campaigns["channel"]]).dropna().unique())
    specs = [
        ("sales.customer_id -> customers.customer_id", sales["customer_id"], customers["customer_id"]),
        ("salesitems.sale_id -> sales.sale_id", items["sale_id"], sales["sale_id"]),
        ("salesitems.product_id -> products.product_id", items["product_id"], products["product_id"]),
        ("stock.product_id -> products.product_id", stock["product_id"], products["product_id"]),
        ("sales.country -> geography list", sales["country"], geography),
        ("customers.country -> geography list", customers["country"], geography),
        ("stock.country -> geography list", stock["country"], geography),
        ("sales.channel -> channel dimension", sales["channel"], channel_dim),
        ("salesitems.channel -> channel dimension", items["channel"], channel_dim),
        ("campaigns.channel -> channel dimension", campaigns["channel"], channel_dim),
    ]
    rows = []
    for rel, src, tgt in specs:
        matched = int(src.isin(set(tgt.dropna())).sum())
        rows.append(
            {
                "Relationship": rel,
                "Source Rows": len(src),
                "Matched Rows": matched,
                "Unmatched Rows": len(src) - matched,
                "Match Rate": matched / len(src),
                "Status": "OK" if matched == len(src) else "Need Review",
            }
        )
    return pd.DataFrame(rows)


def invalid_values(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    customers, products, sales = tables["customers"], tables["products"], tables["sales"]
    items, stock, campaigns = tables["salesitems"], tables["stock"], tables["campaigns"]
    channel_dim = pd.Series(pd.concat([tables["channels"]["channel"], sales["channel"], items["channel"], campaigns["channel"]]).dropna().unique())
    rows = []

    def add(table: str, rule: str, mask: pd.Series, examples: pd.Series, impact: str, action: str) -> None:
        mask = mask.fillna(False)
        count = int(mask.sum())
        rows.append(
            {
                "Table": table,
                "Rule": rule,
                "Invalid Count": count,
                "Invalid Rate": count / len(mask) if len(mask) else 0,
                "Example Values": ", ".join(examples[mask].dropna().astype(str).head(5).tolist()),
                "DWH Impact": impact if count else "No issue",
                "Action": action if count else "Keep",
            }
        )

    add("customers", "customer_id null", customers["customer_id"].isna(), customers["customer_id"], "Cannot build dim_customer", "Quarantine")
    add("customers", "signup_date invalid", pd.to_datetime(customers["signup_date"], errors="coerce").isna(), customers["signup_date"], "Bad date key", "Quarantine")
    add("customers", "country null", customers["country"].isna(), customers["country"], "Bad geography lookup", "Unknown member")
    add("products", "catalog_price <= 0", pd.to_numeric(products["catalog_price"], errors="coerce") <= 0, products["catalog_price"], "Bad product price", "Review")
    add("products", "cost_price < 0", pd.to_numeric(products["cost_price"], errors="coerce") < 0, products["cost_price"], "Bad product cost", "Review")
    add("products", "cost_price > catalog_price", pd.to_numeric(products["cost_price"], errors="coerce") > pd.to_numeric(products["catalog_price"], errors="coerce"), products["product_id"], "Bad margin", "Review")
    add("sales", "customer_id not in customers", ~sales["customer_id"].isin(customers["customer_id"]), sales["customer_id"], "Bad customer FK", "Quarantine/Unknown")
    add("sales", "total_amount < 0", pd.to_numeric(sales["total_amount"], errors="coerce") < 0, sales["total_amount"], "Bad revenue", "Quarantine")
    add("salesitems", "sale_id not in sales", ~items["sale_id"].isin(sales["sale_id"]), items["sale_id"], "Bad order FK", "Quarantine")
    add("salesitems", "product_id not in products", ~items["product_id"].isin(products["product_id"]), items["product_id"], "Bad product FK", "Quarantine/Unknown")
    add("salesitems", "quantity <= 0", pd.to_numeric(items["quantity"], errors="coerce") <= 0, items["quantity"], "Bad quantity", "Quarantine")
    expected_total = pd.to_numeric(items["quantity"], errors="coerce") * pd.to_numeric(items["unit_price"], errors="coerce")
    add("salesitems", "item_total != quantity * unit_price", (pd.to_numeric(items["item_total"], errors="coerce") - expected_total).abs() > 0.01, items["item_id"], "Bad net amount", "Flag/recalculate")
    add("stock", "product_id not in products", ~stock["product_id"].isin(products["product_id"]), stock["product_id"], "Bad product FK", "Quarantine")
    add("stock", "stock_quantity < 0", pd.to_numeric(stock["stock_quantity"], errors="coerce") < 0, stock["stock_quantity"], "Bad inventory", "Quarantine")
    add("campaigns", "start_date > end_date", pd.to_datetime(campaigns["start_date"], errors="coerce") > pd.to_datetime(campaigns["end_date"], errors="coerce"), campaigns["campaign_id"], "Bad campaign period", "Review")
    add("campaigns", "channel not in channel dimension", ~campaigns["channel"].isin(channel_dim), campaigns["channel"], "Bad channel FK", "Add channel/Unknown")
    return pd.DataFrame(rows)


def reconciliation(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    sales = tables["sales"][["sale_id", "total_amount"]].copy()
    sales["total_amount"] = pd.to_numeric(sales["total_amount"], errors="coerce")
    items = tables["salesitems"][["sale_id", "item_total"]].copy()
    items["item_total"] = pd.to_numeric(items["item_total"], errors="coerce")
    rec = sales.merge(items.groupby("sale_id", as_index=False)["item_total"].sum().rename(columns={"item_total": "sum_item_total"}), on="sale_id", how="left")
    rec["amount_diff"] = rec["total_amount"] - rec["sum_item_total"].fillna(0)
    rec["is_reconciled"] = rec["amount_diff"].abs() <= 0.01
    return rec


def fact_sales_measures(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    items = tables["salesitems"].copy()
    products = tables["products"][["product_id", "category", "brand", "cost_price"]].copy()
    df = items.merge(products, on="product_id", how="left")
    for col in ["quantity", "original_price", "unit_price", "discount_applied", "item_total", "cost_price"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["discount_percent_num"] = parse_percent(df["discount_percent"])
    df["gross_amount"] = df["quantity"] * df["original_price"]
    df["net_amount"] = df["item_total"]
    df["discount_amount"] = df["gross_amount"] - df["net_amount"]
    df["cost_amount"] = df["quantity"] * df["cost_price"]
    df["gross_profit"] = df["net_amount"] - df["cost_amount"]
    df["gross_margin"] = np.where(df["net_amount"].ne(0), df["gross_profit"] / df["net_amount"], np.nan)
    return df


def outlier_summary(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    fs = fact_sales_measures(tables)
    frames = {
        "salesitems": fs[["quantity", "original_price", "unit_price", "item_total", "discount_applied", "discount_percent_num", "gross_profit", "gross_margin"]],
        "sales": tables["sales"][["total_amount"]].apply(pd.to_numeric, errors="coerce"),
        "stock": tables["stock"][["stock_quantity"]].apply(pd.to_numeric, errors="coerce"),
    }
    rows = []
    for table, df in frames.items():
        for col in df.columns:
            x = pd.to_numeric(df[col], errors="coerce").dropna()
            if x.empty:
                continue
            q1, q3 = x.quantile(0.25), x.quantile(0.75)
            iqr = q3 - q1
            low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            outliers = int(((x < low) | (x > high)).sum())
            rows.append(
                {
                    "Table": table,
                    "Column": col,
                    "Min": x.min(),
                    "Q1": q1,
                    "Median": x.median(),
                    "Mean": x.mean(),
                    "Q3": q3,
                    "Max": x.max(),
                    "P01": x.quantile(0.01),
                    "P99": x.quantile(0.99),
                    "Outlier Count": outliers,
                    "Outlier Rate": outliers / len(x),
                    "DWH Action": "Flag only" if outliers else "Keep",
                }
            )
    return pd.DataFrame(rows)


def dwh_mapping() -> pd.DataFrame:
    rows = [
        ("customers", "customer_id", "dim_customer", "customer_id", "cast integer", "quarantine if null/duplicate"),
        ("customers", "country", "dim_geography", "country", "trim/title case", "unknown member if null"),
        ("customers", "signup_date", "dim_customer", "signup_date_key", "cast date, build YYYYMMDD", "quarantine if invalid"),
        ("products", "product_id", "dim_product", "product_id", "cast integer", "quarantine if null/duplicate"),
        ("products", "catalog_price,cost_price", "dim_product", "catalog_price,cost_price", "cast numeric", "review if negative/cost > catalog"),
        ("sales", "sale_id", "fact_order", "sale_id", "cast integer", "quarantine if null/duplicate"),
        ("sales", "customer_id,country,channel", "fact_order", "customer_key,geography_key,channel_key", "lookup surrogate keys", "quarantine/unknown if lookup fails"),
        ("salesitems", "item_id", "fact_sales", "item_id", "cast integer", "quarantine if null/duplicate"),
        ("salesitems", "discount_percent", "fact_sales", "discount_percent", "parse percent", "review invalid percent"),
        ("salesitems + products", "quantity,prices,cost_price", "fact_sales", "gross/net/cost/profit measures", "calculate with pandas", "flag amount mismatch"),
        ("stock", "product_id,country,stock_quantity", "fact_inventory", "product_key,geography_key,stock_quantity", "lookup keys, cast integer", "quarantine if negative/unmatched"),
        ("campaigns", "campaign_id,dates,discount", "dim_campaign", "campaign attributes", "parse dates/discount value", "review invalid campaign"),
    ]
    return pd.DataFrame(rows, columns=["Source Table", "Source Column", "Target Table", "Target Column", "Transform Rule", "Data Quality Rule"])


def dimension_readiness() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ("dim_date", "all date columns", "full_date", "date_key", "calendar attributes", "None", "Generate from source min/max dates"),
            ("dim_customer", "customers", "customer_id", "customer_key", "country, age_range, signup_date", "Type 1 now; Type 2 optional", "Ready"),
            ("dim_product", "products", "product_id", "product_key", "category, brand, price, cost", "Type 2 recommended for price/cost", "Ready"),
            ("dim_geography", "customers/sales/stock", "country", "geography_key", "country, region", "Type 1", "Ready"),
            ("dim_channel", "channels/sales/salesitems/campaigns", "channel_name", "channel_key", "description, channel_type", "Type 1", "Build from union sources"),
            ("dim_campaign", "campaigns", "campaign_id", "campaign_key", "campaign, dates, discount", "Type 1", "Sales item mapping may be sparse"),
        ],
        columns=["Dimension", "Source", "Natural Key", "Surrogate Key", "Important Attributes", "SCD Type", "Data Quality Notes"],
    )


def fact_readiness() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ("fact_order", "sales", "1 row / sale_id", "sale_date_key, customer_key, geography_key, channel_key", "order_count,total_amount,line_item_count,is_discounted", "Additive; AOV derived", "Ready"),
            ("fact_sales", "salesitems + sales + products", "1 row / item_id", "date/customer/product/geography/channel/campaign", "quantity,gross,net,discount,cost,profit", "Amounts additive; price/percent non-additive", "Main fact"),
            ("fact_inventory", "stock + products", "product_id + country + snapshot_date_key", "snapshot_date_key,product_key,geography_key", "stock_quantity,stock_value", "Semi-additive across date", "Needs generated snapshot_date_key"),
            ("fact_customer_activity", "customers + sales", "customer + activity_date", "activity_date_key,customer_key,geography_key", "signup_count,order_count,revenue_amount", "Additive", "Optional for cohort/activity"),
        ],
        columns=["Fact Table", "Source", "Grain", "Foreign Keys", "Measures", "Additivity", "Data Quality Notes"],
    )


def dashboard_readiness() -> pd.DataFrame:
    rows = [
        ("Total Revenue", "fact_order/fact_sales", "total_amount/net_amount", "Yes", "Use correct grain", "Ready"),
        ("Orders", "fact_order", "order_count", "Yes", "None", "Ready"),
        ("AOV", "fact_order", "total_amount/order_count", "Yes", "Avoid fact-to-fact join", "Ready"),
        ("Quantity Sold", "fact_sales", "quantity", "Yes", "None", "Ready"),
        ("Gross Profit", "fact_sales", "gross_profit", "Yes", "Cost available in products", "Ready"),
        ("Inventory Quantity", "fact_inventory", "stock_quantity", "Yes", "Semi-additive", "Filter snapshot date"),
        ("Campaign Performance", "fact_sales + dim_campaign", "campaign_key", "Partial", "Campaign mapping sparse", "Allow nullable campaign_key"),
    ]
    return pd.DataFrame(rows, columns=["KPI", "Required Fact", "Required Columns", "Can Calculate?", "Data Issue", "Recommendation"])


def write_notebook() -> None:
    cells = []

    def md(text: str) -> None:
        cells.append({"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)})

    def code(text: str) -> None:
        cells.append({"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": text.splitlines(keepends=True)})

    md(
        """# EDA DWH Readiness - Fashion Store Analytics

Notebook này kiểm tra dataset **European Fashion Store Multitable Dataset** dưới góc nhìn Data Warehouse:

- Dữ liệu có đủ sạch để load vào DWH không?
- Grain của các fact có đúng không?
- Relationship giữa các bảng có ổn không?
- Các measure revenue, profit, inventory có tính được không?
- Star Schema và dashboard có sẵn sàng chưa?

Notebook được tạo lại từ `scripts/generate_eda_dwh_assets.py`.
"""
    )
    code(
        """# 1. Import libraries
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")
pd.set_option("display.max_columns", 120)

ROOT = Path.cwd()
if not (ROOT / "data" / "raw").exists() and (ROOT.parent / "data" / "raw").exists():
    ROOT = ROOT.parent

RAW_DIR = ROOT / "data" / "raw"
REPORT_DIR = ROOT / "reports" / "eda"
REPORT_DIR.mkdir(exist_ok=True)
"""
    )
    code(
        """# 2. Load source CSV tables
FILES = {
    "customers": "dataset_fashion_store_customers.csv",
    "products": "dataset_fashion_store_products.csv",
    "sales": "dataset_fashion_store_sales.csv",
    "salesitems": "dataset_fashion_store_salesitems.csv",
    "stock": "dataset_fashion_store_stock.csv",
    "campaigns": "dataset_fashion_store_campaigns.csv",
    "channels": "dataset_fashion_store_channels.csv",
}

tables = {name: pd.read_csv(RAW_DIR / file_name) for name, file_name in FILES.items()}
{name: df.shape for name, df in tables.items()}
"""
    )
    code(
        """# 3. Helper functions
def to_num(series):
    return pd.to_numeric(series, errors="coerce")

def to_date(series):
    return pd.to_datetime(series, errors="coerce")

def parse_percent(series):
    return pd.to_numeric(series.astype(str).str.replace("%", "", regex=False).str.strip(), errors="coerce") / 100

def plot_bar(df, x, y, title, figsize=(10, 5)):
    plt.figure(figsize=figsize)
    ax = sns.barplot(data=df, x=x, y=y)
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()
    plt.show()

def plot_hist(series, title, bins=30):
    plt.figure(figsize=(9, 4))
    sns.histplot(series.dropna(), bins=bins, kde=True)
    plt.title(title)
    plt.tight_layout()
    plt.show()

def sample_values(series, mask, limit=5):
    return ", ".join(series[mask.fillna(False)].dropna().astype(str).head(limit).tolist())
"""
    )
    code(
        """# 4. Data overview
role_map = {
    "customers": ("customer_id", "Customer master data", "Dimension source"),
    "products": ("product_id", "Product catalog and cost", "Dimension source"),
    "sales": ("sale_id", "Order header transaction", "Fact source"),
    "salesitems": ("item_id", "Order line item transaction", "Fact source"),
    "stock": ("product_id + country", "Inventory snapshot", "Inventory snapshot source"),
    "campaigns": ("campaign_id", "Marketing campaigns", "Campaign source"),
    "channels": ("channel", "Channel lookup", "Lookup source"),
}

table_overview = pd.DataFrame([
    {
        "Source Table": name,
        "Rows": len(df),
        "Columns": len(df.columns),
        "Primary/Natural Key Candidate": role_map[name][0],
        "Business Meaning": role_map[name][1],
        "DWH Role": role_map[name][2],
    }
    for name, df in tables.items()
])
display(table_overview)
plot_bar(table_overview, "Source Table", "Rows", "Rows by source table")
plot_bar(table_overview, "Source Table", "Columns", "Columns by source table")

print(\"\"\"Nhận xét:
- sales là transaction ở cấp đơn hàng, phù hợp tạo fact_order.
- salesitems có grain chi tiết nhất: 1 dòng / 1 sản phẩm trong đơn hàng, phù hợp làm fact_sales chính.
- customers, products, channels, campaigns là nguồn dimension/lookup.
- stock là nguồn inventory snapshot, cần sinh snapshot_date_key vì source không có ngày tồn kho.\"\"\")
"""
    )
    code(
        """# 5. Missing values
missing_rows = []
for table, df in tables.items():
    for col in df.columns:
        count = int(df[col].isna().sum())
        rate = count / len(df) if len(df) else 0
        severity = "Good" if rate == 0 else "Acceptable" if rate < 0.05 else "Need Review" if rate <= 0.30 else "Serious"
        missing_rows.append({
            "Table": table,
            "Column": col,
            "Missing Count": count,
            "Missing Rate": rate,
            "Severity": severity,
            "DWH Impact": "No major impact" if count == 0 else "Need Unknown member or quarantine",
            "Action": "Keep" if count == 0 else "Review before DWH load",
        })
missing_values = pd.DataFrame(missing_rows)
display(missing_values.sort_values(["Missing Rate", "Missing Count"], ascending=False).head(20))

missing_pivot = missing_values.pivot(index="Table", columns="Column", values="Missing Rate").fillna(0)
plt.figure(figsize=(14, 5))
sns.heatmap(missing_pivot, cmap="Reds", annot=False)
plt.title("Missing value heatmap")
plt.tight_layout()
plt.show()
"""
    )
    code(
        """# 6. Duplicate key checks
duplicate_specs = {
    "customers": ["customer_id"],
    "products": ["product_id"],
    "sales": ["sale_id"],
    "salesitems": ["item_id"],
    "campaigns": ["campaign_id"],
    "stock": ["product_id", "country"],
}

duplicate_checks = []
for table, keys in duplicate_specs.items():
    df = tables[table]
    count = int(df.duplicated(keys, keep=False).sum())
    duplicate_checks.append({
        "Table": table,
        "Key Checked": " + ".join(keys),
        "Duplicate Count": count,
        "Duplicate Rate": count / len(df),
        "DWH Impact": "Can break fact/dimension grain" if count else "No issue",
        "Recommended Action": "Deduplicate/quarantine" if count else "Keep",
    })
duplicate_checks = pd.DataFrame(duplicate_checks)
display(duplicate_checks)
plot_bar(duplicate_checks, "Table", "Duplicate Count", "Duplicate count by table/key")
"""
    )
    code(
        """# 7. Relationship validation
customers = tables["customers"]
products = tables["products"]
sales = tables["sales"]
items = tables["salesitems"]
stock = tables["stock"]
campaigns = tables["campaigns"]
channels = tables["channels"]

geography = pd.Series(pd.concat([customers["country"], sales["country"], stock["country"]]).dropna().unique())
channel_dim = pd.Series(pd.concat([channels["channel"], sales["channel"], items["channel"], campaigns["channel"]]).dropna().unique())

relationship_specs = [
    ("sales.customer_id -> customers.customer_id", sales["customer_id"], customers["customer_id"]),
    ("salesitems.sale_id -> sales.sale_id", items["sale_id"], sales["sale_id"]),
    ("salesitems.product_id -> products.product_id", items["product_id"], products["product_id"]),
    ("stock.product_id -> products.product_id", stock["product_id"], products["product_id"]),
    ("sales.country -> geography list", sales["country"], geography),
    ("customers.country -> geography list", customers["country"], geography),
    ("stock.country -> geography list", stock["country"], geography),
    ("sales.channel -> channel dimension", sales["channel"], channel_dim),
    ("salesitems.channel -> channel dimension", items["channel"], channel_dim),
    ("campaigns.channel -> channel dimension", campaigns["channel"], channel_dim),
]

relationship_checks = []
for rel, src, tgt in relationship_specs:
    matched = int(src.isin(set(tgt.dropna())).sum())
    relationship_checks.append({
        "Relationship": rel,
        "Source Rows": len(src),
        "Matched Rows": matched,
        "Unmatched Rows": len(src) - matched,
        "Match Rate": matched / len(src),
        "Status": "OK" if matched == len(src) else "Need Review",
    })
relationship_checks = pd.DataFrame(relationship_checks)
display(relationship_checks)
plot_bar(relationship_checks, "Relationship", "Match Rate", "Relationship match rate", figsize=(13, 5))
plot_bar(relationship_checks, "Relationship", "Unmatched Rows", "Unmatched rows by relationship", figsize=(13, 5))
"""
    )
    code(
        """# 8. Grain validation
grain_validation = pd.DataFrame([
    {
        "Table": "sales",
        "Expected Grain": "1 row / sale_id",
        "Key Unique": not sales["sale_id"].duplicated().any(),
        "Null Key Count": int(sales["sale_id"].isna().sum()),
        "Notes": "Suitable for fact_order",
    },
    {
        "Table": "salesitems",
        "Expected Grain": "1 row / item_id",
        "Key Unique": not items["item_id"].duplicated().any(),
        "Null Key Count": int(items["item_id"].isna().sum()),
        "Notes": "Main source for fact_sales",
    },
    {
        "Table": "stock",
        "Expected Grain": "1 row / product_id + country + snapshot_date_key",
        "Key Unique": not stock.duplicated(["product_id", "country"]).any(),
        "Null Key Count": int(stock[["product_id", "country"]].isna().any(axis=1).sum()),
        "Notes": "Needs generated snapshot_date_key",
    },
])
display(grain_validation)

items_per_sale = items.groupby("sale_id").size().describe()
display(items_per_sale)
"""
    )
    code(
        """# 9. Invalid value checks
invalid_rows = []

def add_invalid(table, rule, mask, examples, impact, action):
    mask = mask.fillna(False)
    count = int(mask.sum())
    invalid_rows.append({
        "Table": table,
        "Rule": rule,
        "Invalid Count": count,
        "Invalid Rate": count / len(mask) if len(mask) else 0,
        "Example Values": sample_values(examples, mask),
        "DWH Impact": impact if count else "No issue",
        "Action": action if count else "Keep",
    })

add_invalid("customers", "customer_id null", customers["customer_id"].isna(), customers["customer_id"], "Cannot build dim_customer", "Quarantine")
add_invalid("customers", "signup_date invalid", to_date(customers["signup_date"]).isna(), customers["signup_date"], "Bad date key", "Quarantine")
add_invalid("customers", "country null", customers["country"].isna(), customers["country"], "Bad geography lookup", "Unknown member")
add_invalid("products", "catalog_price <= 0", to_num(products["catalog_price"]) <= 0, products["catalog_price"], "Bad price", "Review")
add_invalid("products", "cost_price < 0", to_num(products["cost_price"]) < 0, products["cost_price"], "Bad cost", "Review")
add_invalid("products", "cost_price > catalog_price", to_num(products["cost_price"]) > to_num(products["catalog_price"]), products["product_id"], "Bad margin", "Review")
add_invalid("sales", "customer_id not in customers", ~sales["customer_id"].isin(customers["customer_id"]), sales["customer_id"], "Bad customer FK", "Quarantine/Unknown")
add_invalid("sales", "total_amount < 0", to_num(sales["total_amount"]) < 0, sales["total_amount"], "Bad revenue", "Quarantine")
add_invalid("salesitems", "sale_id not in sales", ~items["sale_id"].isin(sales["sale_id"]), items["sale_id"], "Bad order FK", "Quarantine")
add_invalid("salesitems", "product_id not in products", ~items["product_id"].isin(products["product_id"]), items["product_id"], "Bad product FK", "Quarantine/Unknown")
add_invalid("salesitems", "quantity <= 0", to_num(items["quantity"]) <= 0, items["quantity"], "Bad quantity", "Quarantine")
expected_total = to_num(items["quantity"]) * to_num(items["unit_price"])
add_invalid("salesitems", "item_total != quantity * unit_price", (to_num(items["item_total"]) - expected_total).abs() > 0.01, items["item_id"], "Bad net amount", "Flag/recalculate")
add_invalid("stock", "product_id not in products", ~stock["product_id"].isin(products["product_id"]), stock["product_id"], "Bad product FK", "Quarantine")
add_invalid("stock", "stock_quantity < 0", to_num(stock["stock_quantity"]) < 0, stock["stock_quantity"], "Bad inventory", "Quarantine")
add_invalid("campaigns", "start_date > end_date", to_date(campaigns["start_date"]) > to_date(campaigns["end_date"]), campaigns["campaign_id"], "Bad campaign period", "Review")

invalid_values = pd.DataFrame(invalid_rows)
display(invalid_values.sort_values("Invalid Count", ascending=False))
plot_bar(invalid_values, "Rule", "Invalid Count", "Invalid count by rule", figsize=(14, 5))
"""
    )
    code(
        """# 10. Reconciliation checks
sales_amount = sales[["sale_id", "total_amount"]].copy()
sales_amount["total_amount"] = to_num(sales_amount["total_amount"])
item_sum = items.assign(item_total_num=to_num(items["item_total"])).groupby("sale_id", as_index=False)["item_total_num"].sum()
item_sum = item_sum.rename(columns={"item_total_num": "sum_item_total"})
reconciliation = sales_amount.merge(item_sum, on="sale_id", how="left")
reconciliation["sum_item_total"] = reconciliation["sum_item_total"].fillna(0)
reconciliation["amount_diff"] = reconciliation["total_amount"] - reconciliation["sum_item_total"]
reconciliation["is_reconciled"] = reconciliation["amount_diff"].abs() <= 0.01

rec_kpi = pd.DataFrame([{
    "Total orders": len(reconciliation),
    "Reconciled orders": int(reconciliation["is_reconciled"].sum()),
    "Unreconciled orders": int((~reconciliation["is_reconciled"]).sum()),
    "Reconciliation rate": reconciliation["is_reconciled"].mean(),
    "Total absolute difference": reconciliation["amount_diff"].abs().sum(),
}])
display(rec_kpi)
display(reconciliation.sort_values("amount_diff", key=lambda s: s.abs(), ascending=False).head(20))
plot_hist(reconciliation["amount_diff"], "Order amount_diff distribution")
"""
    )
    code(
        """# 11. Fact_sales measure readiness
fact_sales_preview = items.merge(products[["product_id", "category", "brand", "cost_price"]], on="product_id", how="left")
for col in ["quantity", "original_price", "unit_price", "discount_applied", "item_total", "cost_price"]:
    fact_sales_preview[col] = to_num(fact_sales_preview[col])
fact_sales_preview["discount_percent_num"] = parse_percent(fact_sales_preview["discount_percent"])
fact_sales_preview["gross_amount"] = fact_sales_preview["quantity"] * fact_sales_preview["original_price"]
fact_sales_preview["net_amount"] = fact_sales_preview["item_total"]
fact_sales_preview["discount_amount"] = fact_sales_preview["gross_amount"] - fact_sales_preview["net_amount"]
fact_sales_preview["cost_amount"] = fact_sales_preview["quantity"] * fact_sales_preview["cost_price"]
fact_sales_preview["gross_profit"] = fact_sales_preview["net_amount"] - fact_sales_preview["cost_amount"]
fact_sales_preview["gross_margin"] = np.where(fact_sales_preview["net_amount"].ne(0), fact_sales_preview["gross_profit"] / fact_sales_preview["net_amount"], np.nan)

category_revenue = fact_sales_preview.groupby("category", as_index=False).agg(revenue=("net_amount", "sum"), gross_profit=("gross_profit", "sum"))
display(category_revenue.sort_values("revenue", ascending=False))
plot_bar(category_revenue.sort_values("revenue", ascending=False), "category", "revenue", "Revenue by category")
plot_hist(fact_sales_preview["gross_profit"], "Gross profit distribution")
"""
    )
    code(
        """# 12. Outlier analysis
outlier_rows = []
frames = {
    "salesitems": fact_sales_preview[["quantity", "original_price", "unit_price", "item_total", "discount_applied", "discount_percent_num", "gross_profit", "gross_margin"]],
    "sales": sales[["total_amount"]].apply(to_num),
    "stock": stock[["stock_quantity"]].apply(to_num),
}

for table, df in frames.items():
    for col in df.columns:
        x = to_num(df[col]).dropna()
        if x.empty:
            continue
        q1, q3 = x.quantile(0.25), x.quantile(0.75)
        iqr = q3 - q1
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers = int(((x < low) | (x > high)).sum())
        outlier_rows.append({
            "Table": table,
            "Column": col,
            "Min": x.min(),
            "Q1": q1,
            "Median": x.median(),
            "Mean": x.mean(),
            "Q3": q3,
            "Max": x.max(),
            "P01": x.quantile(0.01),
            "P99": x.quantile(0.99),
            "Outlier Count": outliers,
            "Outlier Rate": outliers / len(x),
            "DWH Action": "Flag only" if outliers else "Keep",
        })
outlier_summary = pd.DataFrame(outlier_rows)
display(outlier_summary.sort_values("Outlier Rate", ascending=False))
"""
    )
    code(
        """# 13. DWH mapping and readiness
dwh_mapping = pd.DataFrame([
    ["customers", "customer_id", "dim_customer", "customer_id", "cast integer", "quarantine if null/duplicate"],
    ["customers", "country", "dim_geography", "country", "trim/title case", "unknown member if null"],
    ["products", "product_id", "dim_product", "product_id", "cast integer", "quarantine if null/duplicate"],
    ["sales", "sale_id", "fact_order", "sale_id", "cast integer", "quarantine if null/duplicate"],
    ["salesitems + products", "quantity,prices,cost_price", "fact_sales", "gross/net/cost/profit measures", "calculate with pandas", "flag amount mismatch"],
    ["stock", "product_id,country,stock_quantity", "fact_inventory", "product_key,geography_key,stock_quantity", "lookup keys, cast integer", "quarantine if negative/unmatched"],
], columns=["Source Table", "Source Column", "Target Table", "Target Column", "Transform Rule", "Data Quality Rule"])

dimension_readiness = pd.DataFrame([
    ["dim_date", "all date columns", "full_date", "date_key", "calendar attributes", "None", "Generate from source min/max dates"],
    ["dim_customer", "customers", "customer_id", "customer_key", "country, age_range, signup_date", "Type 1", "Ready"],
    ["dim_product", "products", "product_id", "product_key", "category, brand, price, cost", "Type 2 optional", "Ready"],
    ["dim_geography", "customers/sales/stock", "country", "geography_key", "country, region", "Type 1", "Ready"],
    ["dim_channel", "channels/sales/salesitems/campaigns", "channel_name", "channel_key", "description, channel_type", "Type 1", "Union all sources"],
    ["dim_campaign", "campaigns", "campaign_id", "campaign_key", "campaign attributes", "Type 1", "Campaign mapping sparse"],
], columns=["Dimension", "Source", "Natural Key", "Surrogate Key", "Important Attributes", "SCD Type", "Data Quality Notes"])

fact_readiness = pd.DataFrame([
    ["fact_order", "sales", "1 row / sale_id", "sale_date_key, customer_key, geography_key, channel_key", "order_count,total_amount,line_item_count", "Additive; AOV derived", "Ready"],
    ["fact_sales", "salesitems + sales + products", "1 row / item_id", "date/customer/product/geography/channel/campaign", "quantity,gross,net,discount,cost,profit", "Main additive measures", "Ready"],
    ["fact_inventory", "stock + products", "product_id + country + snapshot_date_key", "snapshot_date_key, product_key, geography_key", "stock_quantity, stock_value", "Semi-additive", "Needs snapshot_date_key"],
    ["fact_customer_activity", "customers + sales", "customer + activity_date", "activity_date_key, customer_key, geography_key", "signup_count, order_count, revenue", "Additive", "Optional"],
], columns=["Fact Table", "Source", "Grain", "Foreign Keys", "Measures", "Additivity", "Data Quality Notes"])

display(dwh_mapping)
display(dimension_readiness)
display(fact_readiness)
"""
    )
    code(
        """# 14. Dashboard readiness
dashboard_readiness = pd.DataFrame([
    ["Total Revenue", "fact_order/fact_sales", "total_amount/net_amount", "Yes", "Use correct grain", "Ready"],
    ["Orders", "fact_order", "order_count", "Yes", "None", "Ready"],
    ["AOV", "fact_order", "total_amount/order_count", "Yes", "Avoid fact-to-fact join", "Ready"],
    ["Quantity Sold", "fact_sales", "quantity", "Yes", "None", "Ready"],
    ["Gross Profit", "fact_sales", "gross_profit", "Yes", "Cost available", "Ready"],
    ["Inventory Quantity", "fact_inventory", "stock_quantity", "Yes", "Semi-additive", "Filter snapshot date"],
    ["Campaign Performance", "fact_sales + dim_campaign", "campaign_key", "Partial", "Mapping sparse", "Allow nullable campaign_key"],
], columns=["KPI", "Required Fact", "Required Columns", "Can Calculate?", "Data Issue", "Recommendation"])
display(dashboard_readiness)
"""
    )
    code(
        """# 15. Export EDA outputs to Excel
excel_path = REPORT_DIR / "fashion_store_eda_dwh_results_from_notebook.xlsx"
with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
    table_overview.to_excel(writer, sheet_name="table_overview", index=False)
    missing_values.to_excel(writer, sheet_name="missing_values", index=False)
    duplicate_checks.to_excel(writer, sheet_name="duplicate_checks", index=False)
    relationship_checks.to_excel(writer, sheet_name="relationship_checks", index=False)
    invalid_values.to_excel(writer, sheet_name="invalid_values", index=False)
    outlier_summary.to_excel(writer, sheet_name="outlier_summary", index=False)
    reconciliation.to_excel(writer, sheet_name="reconciliation", index=False)
    dwh_mapping.to_excel(writer, sheet_name="dwh_mapping", index=False)
    dimension_readiness.to_excel(writer, sheet_name="dimension_readiness", index=False)
    fact_readiness.to_excel(writer, sheet_name="fact_readiness", index=False)
    dashboard_readiness.to_excel(writer, sheet_name="dashboard_readiness", index=False)
excel_path
"""
    )
    md(
        """## Final conclusion

- Dataset đủ điều kiện triển khai DWH dạng Star Schema.
- `salesitems` là fact chính cho phân tích sales line.
- `sales` nên tách riêng thành `fact_order` để tính Orders/AOV đúng grain.
- `stock` cần `snapshot_date_key`.
- `campaign_key` nên nullable vì mapping campaign chưa bao phủ mọi dòng sales item.
- Dashboard Sales/Product/Customer/Inventory có thể làm ngay; Campaign dashboard cần rule mapping tốt hơn.
"""
    )

    nb = {
        "cells": cells,
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (NOTEBOOK_DIR / "02_eda_dwh_readiness.ipynb").write_text(json.dumps(nb, indent=2), encoding="utf-8")


def write_outputs() -> None:
    REPORT_DIR.mkdir(exist_ok=True)
    EDA_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    NOTEBOOK_DIR.mkdir(exist_ok=True)
    tables = load_tables()
    outputs = {
        "table_overview": table_overview(tables),
        "missing_values": missing_values(tables),
        "duplicate_checks": duplicate_checks(tables),
        "relationship_checks": relationship_checks(tables),
        "invalid_values": invalid_values(tables),
        "outlier_summary": outlier_summary(tables),
        "reconciliation": reconciliation(tables),
        "dwh_mapping": dwh_mapping(),
        "dimension_readiness": dimension_readiness(),
        "fact_readiness": fact_readiness(),
        "dashboard_readiness": dashboard_readiness(),
    }
    with pd.ExcelWriter(EDA_REPORT_DIR / "fashion_store_eda_dwh_results.xlsx", engine="openpyxl") as writer:
        for sheet, df in outputs.items():
            df.to_excel(writer, sheet_name=sheet[:31], index=False)

    rec = outputs["reconciliation"]
    invalid_total = int(outputs["invalid_values"]["Invalid Count"].sum())
    duplicate_total = int(outputs["duplicate_checks"]["Duplicate Count"].sum())
    rel_issues = int(outputs["relationship_checks"]["Unmatched Rows"].gt(0).sum())
    summary = f"""# Fashion Store EDA DWH Summary

Dataset is ready for Star Schema after staging validation and reconciliation.

## Key Results

- Tables: {len(tables)}
- Sales orders: {len(tables['sales']):,}
- Sales line items: {len(tables['salesitems']):,}
- Products: {len(tables['products']):,}
- Customers: {len(tables['customers']):,}
- Reconciliation rate: {rec['is_reconciled'].mean():.2%}
- Duplicate key rows: {duplicate_total:,}
- Relationship checks with issues: {rel_issues:,}
- Invalid rule total count: {invalid_total:,}

## Design Conclusion

- `salesitems` is the main source for `fact_sales`.
- `sales` should stay separate as `fact_order` to calculate orders and AOV at the right grain.
- `stock` needs a generated `snapshot_date_key` because the source has no inventory date.
- `dim_channel` should be built from the union of channels, sales, salesitems and campaigns.
- `campaign_key` in `fact_sales` should be nullable because not every line item maps to a campaign.

## Dashboard Readiness

- Executive Sales Overview: ready.
- Product Performance: ready.
- Customer Analytics: ready.
- Inventory Monitoring: ready with generated `snapshot_date_key`.
- Channel & Campaign Analytics: partially ready because campaign mapping is sparse.
"""
    (EDA_REPORT_DIR / "fashion_store_eda_dwh_summary.md").write_text(summary, encoding="utf-8")
    write_notebook()


if __name__ == "__main__":
    write_outputs()
