from __future__ import annotations

from datetime import datetime

import pandas as pd

from pipeline_utils import ensure_schemas, get_engine, read_schema_tables, write_df


RAW_TABLES = ["customers", "products", "sales", "salesitems", "stock", "campaigns", "channels"]
STG_TABLES = ["stg_customers", "stg_products", "stg_sales", "stg_salesitems", "stg_stock", "stg_campaigns", "stg_channels"]
DWH_TABLES = ["dim_customer", "dim_product", "dim_geography", "dim_channel", "dim_campaign", "fact_order", "fact_sales", "fact_inventory", "fact_customer_activity"]


def sample_values(values: pd.Series, limit: int = 5) -> str:
    vals = values.dropna().astype(str).drop_duplicates().head(limit).tolist()
    return ", ".join(vals)


def issue(layer: str, table: str, rule: str, count: int, samples: str = "", severity: str = "Warning") -> dict:
    return {
        "layer_name": layer,
        "table_name": table,
        "rule_name": rule,
        "issue_count": int(count),
        "sample_values": samples,
        "severity": severity,
        "checked_at": datetime.now(),
    }


def add_issue(issues: list[dict], layer: str, table: str, rule: str, mask: pd.Series, sample_col: pd.Series, severity: str = "Warning") -> None:
    count = int(mask.fillna(False).sum())
    if count:
        issues.append(issue(layer, table, rule, count, sample_values(sample_col[mask.fillna(False)]), severity))


def duplicate_issues(issues: list[dict], layer: str, table: str, df: pd.DataFrame, keys: list[str]) -> None:
    mask = df.duplicated(keys, keep=False)
    add_issue(issues, layer, table, f"duplicate key: {' + '.join(keys)}", mask, df[keys].astype(str).agg(":".join, axis=1))


def run_data_quality(write_all: bool = False) -> pd.DataFrame:
    engine = get_engine()
    ensure_schemas(engine)
    raw = read_schema_tables(engine, "raw", RAW_TABLES)
    stg = read_schema_tables(engine, "staging", STG_TABLES)
    dwh = read_schema_tables(engine, "dwh", DWH_TABLES)
    issues: list[dict] = []

    duplicate_issues(issues, "raw", "customers", raw["customers"], ["customer_id"])
    duplicate_issues(issues, "raw", "products", raw["products"], ["product_id"])
    duplicate_issues(issues, "raw", "sales", raw["sales"], ["sale_id"])
    duplicate_issues(issues, "raw", "salesitems", raw["salesitems"], ["item_id"])
    duplicate_issues(issues, "raw", "campaigns", raw["campaigns"], ["campaign_id"])
    duplicate_issues(issues, "raw", "stock", raw["stock"], ["product_id", "country"])

    optional_missing_columns = {
        ("stg_campaigns", "discount_amount_value"),
        ("stg_campaigns", "discount_percent_value"),
        ("stg_channels", "description"),
    }
    for table, df in stg.items():
        add_issue(issues, "staging", table, "invalid rows", ~df["is_valid"].fillna(False), df.get("validation_errors", pd.Series(dtype=str)))
        for col in df.columns:
            if col in ["validation_errors"]:
                continue
            if (table, col) in optional_missing_columns:
                continue
            add_issue(issues, "staging", table, f"missing value: {col}", df[col].isna(), df[col])

    add_issue(
        issues,
        "staging",
        "stg_sales",
        "customer_id not found in stg_customers",
        ~stg["stg_sales"]["customer_id"].isin(stg["stg_customers"]["customer_id"]),
        stg["stg_sales"]["customer_id"],
    )
    add_issue(
        issues,
        "staging",
        "stg_salesitems",
        "sale_id not found in stg_sales",
        ~stg["stg_salesitems"]["sale_id"].isin(stg["stg_sales"]["sale_id"]),
        stg["stg_salesitems"]["sale_id"],
    )
    add_issue(
        issues,
        "staging",
        "stg_salesitems",
        "product_id not found in stg_products",
        ~stg["stg_salesitems"]["product_id"].isin(stg["stg_products"]["product_id"]),
        stg["stg_salesitems"]["product_id"],
    )
    add_issue(
        issues,
        "staging",
        "stg_stock",
        "product_id not found in stg_products",
        ~stg["stg_stock"]["product_id"].isin(stg["stg_products"]["product_id"]),
        stg["stg_stock"]["product_id"],
    )

    rec = stg["stg_sales"][["sale_id", "total_amount"]].merge(
        stg["stg_salesitems"].groupby("sale_id", as_index=False)["item_total"].sum().rename(columns={"item_total": "sum_item_total"}),
        on="sale_id",
        how="left",
    )
    rec["amount_diff"] = rec["total_amount"].fillna(0) - rec["sum_item_total"].fillna(0)
    add_issue(issues, "staging", "sales_vs_salesitems", "total_amount differs from sum item_total", rec["amount_diff"].abs() > 0.01, rec["sale_id"].astype(str) + " diff=" + rec["amount_diff"].round(2).astype(str))

    expected_fact_sales = len(stg["stg_salesitems"][stg["stg_salesitems"]["is_valid"].fillna(False)])
    actual_fact_sales = len(dwh["fact_sales"])
    if expected_fact_sales != actual_fact_sales:
        issues.append(issue("dwh", "fact_sales", "row count differs from valid stg_salesitems", abs(expected_fact_sales - actual_fact_sales), f"expected={expected_fact_sales}, actual={actual_fact_sales}"))

    expected_fact_order = len(stg["stg_sales"][stg["stg_sales"]["is_valid"].fillna(False)])
    actual_fact_order = len(dwh["fact_order"])
    if expected_fact_order != actual_fact_order:
        issues.append(issue("dwh", "fact_order", "row count differs from valid stg_sales", abs(expected_fact_order - actual_fact_order), f"expected={expected_fact_order}, actual={actual_fact_order}"))

    for table in ["fact_order", "fact_sales", "fact_inventory", "fact_customer_activity"]:
        df = dwh[table]
        fk_cols = [c for c in df.columns if c.endswith("_key") and c not in [table.replace("fact_", "") + "_key"]]
        for col in fk_cols:
            if table == "fact_sales" and col == "campaign_key":
                continue
            add_issue(issues, "dwh", table, f"FK null: {col}", df[col].isna(), df[col])

    if "campaign_key" in dwh["fact_sales"].columns:
        add_issue(
            issues,
            "dwh",
            "fact_sales",
            "unmapped campaign_key allowed by design",
            dwh["fact_sales"]["campaign_key"].isna(),
            dwh["fact_sales"]["sale_id"],
            severity="Info",
        )

    for table, cols in {
        "fact_order": ["total_amount", "order_count"],
        "fact_sales": ["quantity", "net_amount", "gross_amount", "cost_amount"],
        "fact_inventory": ["stock_quantity", "stock_value_at_cost"],
    }.items():
        df = dwh[table]
        for col in cols:
            add_issue(issues, "dwh", table, f"negative measure: {col}", df[col] < 0, df[col])

    dq = pd.DataFrame(issues)
    if dq.empty:
        dq = pd.DataFrame(columns=["issue_id", "layer_name", "table_name", "rule_name", "issue_count", "sample_values", "severity", "checked_at"])
    dq = dq[dq["issue_count"].gt(0)] if not write_all and not dq.empty else dq
    if "issue_id" not in dq.columns:
        dq.insert(0, "issue_id", range(1, len(dq) + 1))
    write_df(engine, dq, "staging", "data_quality_issues")
    write_quality_markdown(dq)
    print(f"  staging.data_quality_issues: {len(dq):,} rows")
    return dq


def write_quality_markdown(dq: pd.DataFrame) -> None:
    report_path = get_report_path()
    if dq.empty:
        body = "# Data Quality Report\n\nNo data quality issues recorded.\n"
    else:
        ordered = dq.sort_values(["severity", "issue_count"], ascending=[True, False])
        table = dataframe_to_markdown(ordered[["severity", "layer_name", "table_name", "rule_name", "issue_count", "sample_values"]])
        warning_count = int(ordered[ordered["severity"].ne("Info")]["issue_count"].sum())
        info_count = int(ordered[ordered["severity"].eq("Info")]["issue_count"].sum())
        body = f"""# Data Quality Report

## Summary

| Metric | Value |
|---|---:|
| Total records in issue table | {len(ordered):,} |
| Warning issue count | {warning_count:,} |
| Informational count | {info_count:,} |

## Issues

{table}

## Notes

- `campaign_key` null in `fact_sales` is informational because campaign mapping is intentionally nullable.
- `discount_percent_value` and `discount_amount_value` are mutually exclusive in campaign data, depending on `discount_type`.
"""
    report_path.write_text(body, encoding="utf-8")


def get_report_path():
    from pipeline_utils import ROOT_DIR

    report_dir = ROOT_DIR / "reports"
    report_dir.mkdir(exist_ok=True)
    return report_dir / "data_quality_report.md"


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._"
    rendered = df.fillna("").astype(str)
    headers = list(rendered.columns)
    rows = rendered.values.tolist()
    widths = [len(h) for h in headers]
    for row in rows:
        widths = [max(widths[i], len(row[i])) for i in range(len(headers))]

    def fmt(values: list[str]) -> str:
        return "| " + " | ".join(values[i].ljust(widths[i]) for i in range(len(values))) + " |"

    lines = [fmt(headers), "| " + " | ".join("-" * w for w in widths) + " |"]
    lines.extend(fmt(row) for row in rows)
    return "\n".join(lines)


def main() -> None:
    dq = run_data_quality()
    if dq.empty:
        print("No data quality issues recorded.")
    else:
        print(dq[["table_name", "rule_name", "issue_count"]].sort_values("issue_count", ascending=False).to_string(index=False))


if __name__ == "__main__":
    main()
