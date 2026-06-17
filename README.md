# Fashion Store Analytics

Project phan tich du lieu ban hang thoi trang tu **European Fashion Store Multitable Dataset**.

Pipeline chinh:

```text
CSV files -> raw -> staging -> dwh -> BI/dashboard
```

Cong nghe:

- PostgreSQL 16: luu `raw`, `staging`, `dwh`, `mart`
- Python/pandas: EDA, transform staging, build DWH, data quality
- Docker Desktop: chay PostgreSQL, pgAdmin, Jupyter

## Quick Start

```bash
docker compose up -d --build
docker exec fashion_jupyter python src/run_pipeline.py
```

Mo cong cu:

```text
pgAdmin: http://localhost:5050
Jupyter: http://localhost:8888
```

Dang nhap pgAdmin:

```text
Email: admin@admin.com
Password: admin
```

Ket noi PostgreSQL trong pgAdmin:

```text
Host: postgres
Port: 5432
Database: fashion_dw
Username: postgres
Password: postgres
```

## Project Structure

```text
.
|-- data/
|   `-- raw/                         # CSV source files
|
|-- notebooks/
|   |-- 01_postgres_connection_example.ipynb
|   `-- 02_eda_dwh_readiness.ipynb
|
|-- reports/
|   |-- data_quality/
|   |   `-- data_quality_report.md
|   |-- dwh/
|   |   `-- fashion_store_dwh_design.md
|   |-- eda/
|   |   |-- fashion_store_eda_dwh_results.xlsx
|   |   |-- fashion_store_eda_dwh_results_from_notebook.xlsx
|   |   `-- fashion_store_eda_dwh_summary.md
|   |-- pipeline/
|   |   `-- raw_staging_dwh_python_pipeline.md
|   `-- project_structure.md
|
|-- scripts/
|   `-- generate_eda_dwh_assets.py
|
|-- sql/
|   `-- init/
|       `-- 01_create_schemas.sql
|
|-- src/
|   |-- load_raw_csv.py              # CSV -> raw
|   |-- build_staging.py             # raw -> staging
|   |-- build_dwh.py                 # staging -> dwh
|   |-- run_data_quality.py          # DQ checks -> report/table
|   |-- run_pipeline.py              # orchestrator
|   `-- pipeline_utils.py
|
|-- docker-compose.yml
|-- Dockerfile
|-- requirements.txt
`-- README.md
```

## Folder Roles

| Folder | Vai tro |
|---|---|
| `data/raw` | Chua 7 file CSV goc tu Kaggle |
| `src` | Python pipeline chinh |
| `scripts` | Script sinh EDA notebook/report |
| `notebooks` | Notebook EDA va notebook test ket noi |
| `reports/eda` | Ket qua EDA |
| `reports/dwh` | Tai lieu thiet ke Star Schema |
| `reports/pipeline` | Tai lieu pipeline Raw -> Staging -> DWH |
| `reports/data_quality` | Bao cao data quality |
| `sql/init` | SQL init schema khi PostgreSQL tao DB lan dau |

## Pipeline Commands

Chay tat ca:

```bash
docker exec fashion_jupyter python src/run_pipeline.py
```

Chay tung buoc:

```bash
docker exec fashion_jupyter python src/load_raw_csv.py
docker exec fashion_jupyter python src/build_staging.py
docker exec fashion_jupyter python src/build_dwh.py
docker exec fashion_jupyter python src/run_data_quality.py
```

Bo qua raw load:

```bash
docker exec fashion_jupyter python src/run_pipeline.py --skip-raw
```

## EDA Commands

Sinh lai EDA report va notebook:

```bash
docker exec fashion_jupyter python scripts/generate_eda_dwh_assets.py
```

Chay notebook EDA:

```bash
docker exec fashion_jupyter jupyter nbconvert --to notebook --execute --inplace notebooks/02_eda_dwh_readiness.ipynb
```

## Database Tables

Raw:

```text
raw.customers
raw.products
raw.sales
raw.salesitems
raw.stock
raw.campaigns
raw.channels
```

Staging:

```text
staging.stg_customers
staging.stg_products
staging.stg_sales
staging.stg_salesitems
staging.stg_stock
staging.stg_campaigns
staging.stg_channels
staging.data_quality_issues
```

DWH:

```text
dwh.dim_date
dwh.dim_geography
dwh.dim_channel
dwh.dim_customer
dwh.dim_product
dwh.dim_campaign
dwh.fact_order
dwh.fact_sales
dwh.fact_inventory
dwh.fact_customer_activity
```

## Test Queries

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
docker exec fashion_postgres psql -U postgres -d fashion_dw -c "SELECT status, severity, table_name, rule_name, issue_count FROM staging.data_quality_issues ORDER BY status, issue_count DESC;"
```

## Important Reports

| Report | Path |
|---|---|
| Project structure | `reports/project_structure.md` |
| Data quality | `reports/data_quality/data_quality_report.md` |
| DWH design | `reports/dwh/fashion_store_dwh_design.md` |
| EDA summary | `reports/eda/fashion_store_eda_dwh_summary.md` |
| EDA Excel | `reports/eda/fashion_store_eda_dwh_results.xlsx` |
| Pipeline summary | `reports/pipeline/raw_staging_dwh_python_pipeline.md` |

## Stop / Reset

Stop:

```bash
docker compose down
```

Reset database volume:

```bash
docker compose down -v
docker compose up -d --build
docker exec fashion_jupyter python src/run_pipeline.py
```
