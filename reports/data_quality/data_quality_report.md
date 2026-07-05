# Data Quality Report

## Summary

| Metric | Value |
|---|---:|
| Total records in issue table | 113 |
| PASS rules | 112 |
| WARN rules | 0 |
| FAIL rules | 0 |
| INFO rules | 1 |
| Warning issue count | 0 |
| Informational count | 2,170 |

## Issues

| status | severity | layer_name | table_name             | rule_name                                | issue_count | sample_values              |
| ------ | -------- | ---------- | ---------------------- | ---------------------------------------- | ----------- | -------------------------- |
| INFO   | Info     | dwh        | fact_sales             | unmapped campaign_key allowed by design  | 2170        | 658, 336, 1255, 331, 1079  |
| PASS   | Warning  | raw        | customers              | duplicate key: customer_id               | 0           |                            |
| PASS   | Warning  | raw        | products               | duplicate key: product_id                | 0           |                            |
| PASS   | Warning  | raw        | sales                  | duplicate key: sale_id                   | 0           |                            |
| PASS   | Warning  | raw        | salesitems             | duplicate key: item_id                   | 0           |                            |
| PASS   | Warning  | raw        | campaigns              | duplicate key: campaign_id               | 0           |                            |
| PASS   | Warning  | raw        | stock                  | duplicate key: product_id + country      | 0           |                            |
| PASS   | Warning  | staging    | stg_customers          | invalid rows                             | 0           |                            |
| PASS   | Warning  | staging    | stg_customers          | missing value: customer_id               | 0           |                            |
| PASS   | Warning  | staging    | stg_customers          | missing value: country                   | 0           |                            |
| PASS   | Warning  | staging    | stg_customers          | missing value: age_range                 | 0           |                            |
| PASS   | Warning  | staging    | stg_customers          | missing value: signup_date               | 0           |                            |
| PASS   | Warning  | staging    | stg_customers          | missing value: source_file               | 0           |                            |
| PASS   | Warning  | staging    | stg_customers          | missing value: loaded_at                 | 0           |                            |
| PASS   | Warning  | staging    | stg_customers          | missing value: batch_id                  | 0           |                            |
| PASS   | Warning  | staging    | stg_customers          | missing value: is_valid                  | 0           |                            |
| PASS   | Warning  | staging    | stg_products           | invalid rows                             | 0           |                            |
| PASS   | Warning  | staging    | stg_products           | missing value: product_id                | 0           |                            |
| PASS   | Warning  | staging    | stg_products           | missing value: product_name              | 0           |                            |
| PASS   | Warning  | staging    | stg_products           | missing value: category                  | 0           |                            |
| PASS   | Warning  | staging    | stg_products           | missing value: brand                     | 0           |                            |
| PASS   | Warning  | staging    | stg_products           | missing value: color                     | 0           |                            |
| PASS   | Warning  | staging    | stg_products           | missing value: size                      | 0           |                            |
| PASS   | Warning  | staging    | stg_products           | missing value: catalog_price             | 0           |                            |
| PASS   | Warning  | staging    | stg_products           | missing value: cost_price                | 0           |                            |
| PASS   | Warning  | staging    | stg_products           | missing value: gender                    | 0           |                            |
| PASS   | Warning  | staging    | stg_products           | missing value: source_file               | 0           |                            |
| PASS   | Warning  | staging    | stg_products           | missing value: loaded_at                 | 0           |                            |
| PASS   | Warning  | staging    | stg_products           | missing value: batch_id                  | 0           |                            |
| PASS   | Warning  | staging    | stg_products           | missing value: is_valid                  | 0           |                            |
| PASS   | Warning  | staging    | stg_sales              | invalid rows                             | 0           |                            |
| PASS   | Warning  | staging    | stg_sales              | missing value: sale_id                   | 0           |                            |
| PASS   | Warning  | staging    | stg_sales              | missing value: channel                   | 0           |                            |
| PASS   | Warning  | staging    | stg_sales              | missing value: is_discounted             | 0           |                            |
| PASS   | Warning  | staging    | stg_sales              | missing value: total_amount              | 0           |                            |
| PASS   | Warning  | staging    | stg_sales              | missing value: sale_date                 | 0           |                            |
| PASS   | Warning  | staging    | stg_sales              | missing value: customer_id               | 0           |                            |
| PASS   | Warning  | staging    | stg_sales              | missing value: country                   | 0           |                            |
| PASS   | Warning  | staging    | stg_sales              | missing value: source_file               | 0           |                            |
| PASS   | Warning  | staging    | stg_sales              | missing value: loaded_at                 | 0           |                            |
| PASS   | Warning  | staging    | stg_sales              | missing value: batch_id                  | 0           |                            |
| PASS   | Warning  | staging    | stg_sales              | missing value: is_valid                  | 0           |                            |
| PASS   | Warning  | staging    | stg_salesitems         | invalid rows                             | 0           |                            |
| PASS   | Warning  | staging    | stg_salesitems         | missing value: item_id                   | 0           |                            |
| PASS   | Warning  | staging    | stg_salesitems         | missing value: sale_id                   | 0           |                            |
| PASS   | Warning  | staging    | stg_salesitems         | missing value: product_id                | 0           |                            |
| PASS   | Warning  | staging    | stg_salesitems         | missing value: quantity                  | 0           |                            |
| PASS   | Warning  | staging    | stg_salesitems         | missing value: original_price            | 0           |                            |
| PASS   | Warning  | staging    | stg_salesitems         | missing value: unit_price                | 0           |                            |
| PASS   | Warning  | staging    | stg_salesitems         | missing value: discount_applied          | 0           |                            |
| PASS   | Warning  | staging    | stg_salesitems         | missing value: discount_percent          | 0           |                            |
| PASS   | Warning  | staging    | stg_salesitems         | missing value: is_discounted             | 0           |                            |
| PASS   | Warning  | staging    | stg_salesitems         | missing value: item_total                | 0           |                            |
| PASS   | Warning  | staging    | stg_salesitems         | missing value: sale_date                 | 0           |                            |
| PASS   | Warning  | staging    | stg_salesitems         | missing value: channel                   | 0           |                            |
| PASS   | Warning  | staging    | stg_salesitems         | missing value: channel_campaigns         | 0           |                            |
| PASS   | Warning  | staging    | stg_salesitems         | missing value: source_file               | 0           |                            |
| PASS   | Warning  | staging    | stg_salesitems         | missing value: loaded_at                 | 0           |                            |
| PASS   | Warning  | staging    | stg_salesitems         | missing value: batch_id                  | 0           |                            |
| PASS   | Warning  | staging    | stg_salesitems         | missing value: is_valid                  | 0           |                            |
| PASS   | Warning  | staging    | stg_stock              | invalid rows                             | 0           |                            |
| PASS   | Warning  | staging    | stg_stock              | missing value: country                   | 0           |                            |
| PASS   | Warning  | staging    | stg_stock              | missing value: product_id                | 0           |                            |
| PASS   | Warning  | staging    | stg_stock              | missing value: stock_quantity            | 0           |                            |
| PASS   | Warning  | staging    | stg_stock              | missing value: source_file               | 0           |                            |
| PASS   | Warning  | staging    | stg_stock              | missing value: loaded_at                 | 0           |                            |
| PASS   | Warning  | staging    | stg_stock              | missing value: batch_id                  | 0           |                            |
| PASS   | Warning  | staging    | stg_stock              | missing value: is_valid                  | 0           |                            |
| PASS   | Warning  | staging    | stg_campaigns          | invalid rows                             | 0           |                            |
| PASS   | Warning  | staging    | stg_campaigns          | missing value: campaign_id               | 0           |                            |
| PASS   | Warning  | staging    | stg_campaigns          | missing value: campaign_name             | 0           |                            |
| PASS   | Warning  | staging    | stg_campaigns          | missing value: start_date                | 0           |                            |
| PASS   | Warning  | staging    | stg_campaigns          | missing value: end_date                  | 0           |                            |
| PASS   | Warning  | staging    | stg_campaigns          | missing value: channel                   | 0           |                            |
| PASS   | Warning  | staging    | stg_campaigns          | missing value: discount_type             | 0           |                            |
| PASS   | Warning  | staging    | stg_campaigns          | missing value: discount_value_raw        | 0           |                            |
| PASS   | Warning  | staging    | stg_campaigns          | missing value: source_file               | 0           |                            |
| PASS   | Warning  | staging    | stg_campaigns          | missing value: loaded_at                 | 0           |                            |
| PASS   | Warning  | staging    | stg_campaigns          | missing value: batch_id                  | 0           |                            |
| PASS   | Warning  | staging    | stg_campaigns          | missing value: is_valid                  | 0           |                            |
| PASS   | Warning  | staging    | stg_channels           | invalid rows                             | 0           |                            |
| PASS   | Warning  | staging    | stg_channels           | missing value: channel                   | 0           |                            |
| PASS   | Warning  | staging    | stg_channels           | missing value: source_file               | 0           |                            |
| PASS   | Warning  | staging    | stg_channels           | missing value: loaded_at                 | 0           |                            |
| PASS   | Warning  | staging    | stg_channels           | missing value: batch_id                  | 0           |                            |
| PASS   | Warning  | staging    | stg_channels           | missing value: is_valid                  | 0           |                            |
| PASS   | Warning  | staging    | stg_sales              | customer_id not found in stg_customers   | 0           |                            |
| PASS   | Warning  | staging    | stg_salesitems         | sale_id not found in stg_sales           | 0           |                            |
| PASS   | Warning  | staging    | stg_salesitems         | product_id not found in stg_products     | 0           |                            |
| PASS   | Warning  | staging    | stg_stock              | product_id not found in stg_products     | 0           |                            |
| PASS   | Warning  | staging    | sales_vs_salesitems    | total_amount differs from sum item_total | 0           |                            |
| PASS   | Warning  | dwh        | fact_sales             | row count equals valid stg_salesitems    | 0           | expected=2253, actual=2253 |
| PASS   | Warning  | dwh        | fact_order             | row count equals valid stg_sales         | 0           | expected=905, actual=905   |
| PASS   | Warning  | dwh        | fact_order             | FK null: sale_date_key                   | 0           |                            |
| PASS   | Warning  | dwh        | fact_order             | FK null: customer_key                    | 0           |                            |
| PASS   | Warning  | dwh        | fact_order             | FK null: channel_key                     | 0           |                            |
| PASS   | Warning  | dwh        | fact_sales             | FK null: sale_date_key                   | 0           |                            |
| PASS   | Warning  | dwh        | fact_sales             | FK null: customer_key                    | 0           |                            |
| PASS   | Warning  | dwh        | fact_sales             | FK null: product_key                     | 0           |                            |
| PASS   | Warning  | dwh        | fact_sales             | FK null: channel_key                     | 0           |                            |
| PASS   | Warning  | dwh        | fact_inventory         | FK null: snapshot_date_key               | 0           |                            |
| PASS   | Warning  | dwh        | fact_inventory         | FK null: product_key                     | 0           |                            |
| PASS   | Warning  | dwh        | fact_inventory         | FK null: geography_key                   | 0           |                            |
| PASS   | Warning  | dwh        | fact_customer_activity | FK null: activity_date_key               | 0           |                            |
| PASS   | Warning  | dwh        | fact_customer_activity | FK null: customer_key                    | 0           |                            |
| PASS   | Warning  | dwh        | fact_order             | negative measure: total_amount           | 0           |                            |
| PASS   | Warning  | dwh        | fact_order             | negative measure: order_count            | 0           |                            |
| PASS   | Warning  | dwh        | fact_sales             | negative measure: quantity               | 0           |                            |
| PASS   | Warning  | dwh        | fact_sales             | negative measure: net_amount             | 0           |                            |
| PASS   | Warning  | dwh        | fact_sales             | negative measure: gross_amount           | 0           |                            |
| PASS   | Warning  | dwh        | fact_sales             | negative measure: cost_amount            | 0           |                            |
| PASS   | Warning  | dwh        | fact_inventory         | negative measure: stock_quantity         | 0           |                            |
| PASS   | Warning  | dwh        | fact_inventory         | negative measure: stock_value_at_cost    | 0           |                            |

## Notes

- `campaign_key` null in `fact_sales` is informational because campaign mapping is intentionally nullable.
- `discount_percent_value` and `discount_amount_value` are mutually exclusive in campaign data, depending on `discount_type`.
