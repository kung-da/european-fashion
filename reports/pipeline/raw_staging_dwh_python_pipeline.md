# Raw, Staging and DWH Python Pipeline

## Kiến trúc

```text
CSV files -> raw PostgreSQL tables -> staging PostgreSQL tables -> dwh Star Schema -> BI queries
```

Transform cho staging, DWH và data quality được viết bằng Python/pandas. PostgreSQL đóng vai trò lưu trữ raw, staging, dwh và mart.

## Vì sao dùng Python

- Dataset nhỏ, chưa cần Spark.
- pandas đủ tốt cho cast kiểu dữ liệu, validation, lookup key và tính measure.
- Sinh viên Data Analyst/Data Engineer dễ đọc, dễ debug.
- Chạy được trên Windows hoặc trong container Jupyter.

## Scripts

| File | Vai trò |
|---|---|
| `src/load_raw_csv.py` | Load CSV vào schema `raw` |
| `src/build_staging.py` | Clean/cast raw thành staging tables |
| `src/build_dwh.py` | Build dimensions và facts bằng pandas |
| `src/run_data_quality.py` | Chạy DQ checks bằng pandas |
| `src/run_pipeline.py` | Orchestrator chạy toàn bộ pipeline |
| `src/pipeline_utils.py` | Helper functions dùng chung |

## Tables

Raw:

- `raw.customers`
- `raw.products`
- `raw.sales`
- `raw.salesitems`
- `raw.stock`
- `raw.campaigns`
- `raw.channels`

Staging:

- `staging.stg_customers`
- `staging.stg_products`
- `staging.stg_sales`
- `staging.stg_salesitems`
- `staging.stg_stock`
- `staging.stg_campaigns`
- `staging.stg_channels`
- `staging.data_quality_issues`

DWH:

- `dwh.dim_date`
- `dwh.dim_geography`
- `dwh.dim_channel`
- `dwh.dim_customer`
- `dwh.dim_product`
- `dwh.dim_campaign`
- `dwh.fact_order`
- `dwh.fact_sales`
- `dwh.fact_inventory`
- `dwh.fact_customer_activity`

## Thứ tự chạy

```bash
docker compose up -d
docker exec fashion_jupyter python src/run_pipeline.py
```

Hoặc chạy từng bước:

```bash
docker exec fashion_jupyter python src/load_raw_csv.py
docker exec fashion_jupyter python src/build_staging.py
docker exec fashion_jupyter python src/build_dwh.py
docker exec fashion_jupyter python src/run_data_quality.py
```

## Test SQL

Connection:

```bash
docker exec fashion_postgres psql -U postgres -d fashion_dw -c "SELECT current_database(), current_user;"
```

Row count:

```bash
docker exec fashion_postgres psql -U postgres -d fashion_dw -c "SELECT 'dim_customer' AS table_name, COUNT(*) FROM dwh.dim_customer UNION ALL SELECT 'dim_product', COUNT(*) FROM dwh.dim_product UNION ALL SELECT 'fact_order', COUNT(*) FROM dwh.fact_order UNION ALL SELECT 'fact_sales', COUNT(*) FROM dwh.fact_sales UNION ALL SELECT 'fact_inventory', COUNT(*) FROM dwh.fact_inventory;"
```

KPI:

```bash
docker exec fashion_postgres psql -U postgres -d fashion_dw -c "SELECT SUM(total_amount) AS revenue, SUM(order_count) AS orders, SUM(total_amount) / NULLIF(SUM(order_count), 0) AS aov FROM dwh.fact_order;"
```

Data quality:

```bash
docker exec fashion_postgres psql -U postgres -d fashion_dw -c "SELECT table_name, rule_name, issue_count FROM staging.data_quality_issues ORDER BY issue_count DESC;"
```

## Data Quality Checks

- Duplicate natural keys
- Missing values
- Invalid staging rows
- Relationship mismatches
- Sales header vs sales item reconciliation
- DWH fact row count reconciliation
- DWH FK null checks
- Negative measure checks

## Hướng phát triển tiếp

- Thêm mart views cho dashboard.
- Thêm incremental load theo `batch_id`.
- Thêm SCD Type 2 cho product/customer nếu có dữ liệu lịch sử.
- Thêm threshold inventory để tạo cảnh báo low stock.

## Test result mới nhất

Pipeline đã chạy thành công trong container:

```bash
docker exec fashion_jupyter python src/run_pipeline.py
```

Row count chính:

| Table | Rows |
|---|---:|
| `dwh.dim_customer` | 1,000 |
| `dwh.dim_product` | 500 |
| `dwh.fact_order` | 905 |
| `dwh.fact_sales` | 2,253 |
| `dwh.fact_inventory` | 1,000 |

KPI smoke test:

| KPI | Value |
|---|---:|
| Revenue | 324,236.66 |
| Orders | 905 |
| AOV | 358.27 |

Data quality issues nổi bật:

| Table | Rule | Issue Count |
|---|---|---:|
| `fact_sales` | `unmapped campaign_key allowed by design` | 2,170 |

Data quality audit hiện ghi cả rule pass:

| Status | Rules | Issue Count |
|---|---:|---:|
| `PASS` | 115 | 0 |
| `INFO` | 1 | 2,170 |
| `WARN` | 0 | 0 |
| `FAIL` | 0 | 0 |

Ghi chú: `campaign_key` null là thông tin theo dõi, không phải lỗi hard-fail, vì nhiều dòng sales item không map được sang campaign theo `channel_campaigns` và campaign date range.
