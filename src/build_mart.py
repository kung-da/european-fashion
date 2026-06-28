"""Build mart views for BI and Machine Learning.

Creates mart.daily_demand -- a daily aggregate of fact_sales joined with
dimensions, used by the Demand Forecasting notebook and BI dashboards.
"""
from __future__ import annotations

from pipeline_utils import ensure_schemas, get_engine
from sqlalchemy import text


DAILY_DEMAND_VIEW = """
CREATE OR REPLACE VIEW mart.daily_demand AS
SELECT
    d.full_date,
    d.day_of_week,
    d.day_name,
    d.is_weekend,
    d.week_of_year,
    d.month_number,
    d.quarter_number,
    d.year_number,
    p.category,
    g.country,
    ch.channel_name,
    SUM(fs.quantity)                                              AS daily_quantity,
    SUM(fs.net_amount)                                            AS daily_revenue,
    SUM(fs.discount_amount)                                       AS daily_discount_amount,
    COUNT(DISTINCT fs.sale_id)                                    AS daily_orders,
    COUNT(fs.sales_key)                                           AS daily_line_items,
    AVG(fs.discount_percent)                                      AS avg_discount_percent,
    MAX(CASE WHEN fs.is_discounted THEN 1 ELSE 0 END)            AS has_discount,
    MAX(CASE WHEN fs.campaign_key IS NOT NULL THEN 1 ELSE 0 END) AS has_campaign
FROM dwh.fact_sales   fs
JOIN dwh.dim_date      d  ON fs.sale_date_key = d.date_key
JOIN dwh.dim_product   p  ON fs.product_key   = p.product_key
JOIN dwh.dim_geography g  ON fs.geography_key = g.geography_key
JOIN dwh.dim_channel   ch ON fs.channel_key   = ch.channel_key
GROUP BY
    d.full_date, d.day_of_week, d.day_name, d.is_weekend,
    d.week_of_year, d.month_number, d.quarter_number, d.year_number,
    p.category, g.country, ch.channel_name
"""


def build_mart() -> None:
    engine = get_engine()
    ensure_schemas(engine)
    with engine.begin() as conn:
        conn.execute(text(DAILY_DEMAND_VIEW))
    print("  mart.daily_demand view created/replaced")


def main() -> None:
    build_mart()


if __name__ == "__main__":
    main()
