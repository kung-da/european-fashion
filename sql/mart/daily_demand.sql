-- mart.daily_demand
-- Aggregate fact_sales with dimensions for BI dashboards and ML forecasting.
-- Used by notebooks/05_demand_forecasting.ipynb and src/build_mart.py.

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
JOIN dwh.dim_customer  c  ON fs.customer_key  = c.customer_key
JOIN dwh.dim_geography g  ON c.geography_key  = g.geography_key
JOIN dwh.dim_channel   ch ON fs.channel_key   = ch.channel_key
GROUP BY
    d.full_date, d.day_of_week, d.day_name, d.is_weekend,
    d.week_of_year, d.month_number, d.quarter_number, d.year_number,
    p.category, g.country, ch.channel_name;
