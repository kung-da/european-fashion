# Fashion Store Analytics

Project phan tich du lieu ban hang thoi trang tu dataset **European Fashion Store Multitable Dataset**. Project dung PostgreSQL lam kho luu tru `raw`, `staging`, `dwh`, `mart`; Python/pandas xu ly EDA, staging, DWH va data quality.

## 1. Kien Truc

```text
CSV files
  -> raw PostgreSQL tables
  -> staging PostgreSQL tables
  -> dwh Star Schema
  -> BI / dashboard queries
```

Ly do dung Python:

- Dataset nho, chua can Spark.
- pandas du tot de cast kieu du lieu, validate, lookup surrogate key va tinh measures.
- De chay tren Windows bang Docker Desktop.
- De doc va phu hop cho project Data Analyst/Data Engineer.

## 2. Cau Truc Thu Muc

```text
.
|-- data
|   `-- raw
|-- notebooks
|   |-- 01_postgres_connection_example.ipynb
|   `-- 02_eda_dwh_readiness.ipynb
|-- reports
|   |-- data_quality_report.md
|   |-- fashion_store_dwh_design.md
|   |-- fashion_store_eda_dwh_results.xlsx
|   |-- fashion_store_eda_dwh_results_from_notebook.xlsx
|   |-- fashion_store_eda_dwh_summary.md
|   |-- project_structure.md
|   `-- raw_staging_dwh_python_pipeline.md
|-- scripts
|   `-- generate_eda_dwh_assets.py
|-- sql
|   `-- init
|       `-- 01_create_schemas.sql
|-- src
|   |-- build_dwh.py
|   |-- build_staging.py
|   |-- load_raw_csv.py
|   |-- pipeline_utils.py
|   |-- run_data_quality.py
|   `-- run_pipeline.py
|-- .env
|-- docker-compose.yml
|-- Dockerfile
|-- README.md
`-- requirements.txt
```

## 3. Docker Services

`postgres`

- PostgreSQL 16.
- Database: `fashion_dw`.
- User/password: `postgres/postgres`.
- Port: `5432`.

`pgadmin`

- URL: `http://localhost:5050`.
- Email/password: `admin@admin.com/admin`.

`jupyter`

- URL: `http://localhost:8888`.
- Mount toan bo project vao `/app`.
- Ket noi PostgreSQL bang hostname Docker: `postgres`.

## 4. Chay Docker

```bash
docker compose up -d --build
```

Kiem tra container:

```bash
docker compose ps
```

Test PostgreSQL:

```bash
docker exec fashion_postgres psql -U postgres -d fashion_dw -c "SELECT current_database(), current_user;"
```

## 5. Chay Pipeline Python

Chay toan bo pipeline:

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

Bo qua raw load neu muon giu raw hien tai:

```bash
docker exec fashion_jupyter python src/run_pipeline.py --skip-raw
```

## 6. Chay EDA

Sinh lai notebook/report EDA:

```bash
docker exec fashion_jupyter python scripts/generate_eda_dwh_assets.py
```

Chay notebook EDA:

```bash
docker exec fashion_jupyter jupyter nbconvert --to notebook --execute --inplace notebooks/02_eda_dwh_readiness.ipynb
```

Output EDA:

- `reports/fashion_store_eda_dwh_results.xlsx`
- `reports/fashion_store_eda_dwh_results_from_notebook.xlsx`
- `reports/fashion_store_eda_dwh_summary.md`

## 7. Bang Du Lieu

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

## 8. Test Sau Khi Load

Row count DWH:

```bash
docker exec fashion_postgres psql -U postgres -d fashion_dw -c "SELECT 'dim_customer' AS table_name, COUNT(*) FROM dwh.dim_customer UNION ALL SELECT 'dim_product', COUNT(*) FROM dwh.dim_product UNION ALL SELECT 'fact_order', COUNT(*) FROM dwh.fact_order UNION ALL SELECT 'fact_sales', COUNT(*) FROM dwh.fact_sales UNION ALL SELECT 'fact_inventory', COUNT(*) FROM dwh.fact_inventory;"
```

KPI revenue/orders/AOV:

```bash
docker exec fashion_postgres psql -U postgres -d fashion_dw -c "SELECT SUM(total_amount) AS revenue, SUM(order_count) AS orders, SUM(total_amount) / NULLIF(SUM(order_count), 0) AS aov FROM dwh.fact_order;"
```

Data quality:

```bash
docker exec fashion_postgres psql -U postgres -d fashion_dw -c "SELECT severity, table_name, rule_name, issue_count FROM staging.data_quality_issues ORDER BY severity, issue_count DESC;"
```

## 9. Bao Cao

- DWH design: `reports/fashion_store_dwh_design.md`
- EDA summary: `reports/fashion_store_eda_dwh_summary.md`
- Pipeline summary: `reports/raw_staging_dwh_python_pipeline.md`
- Data quality report: `reports/data_quality_report.md`

## 10. Stop / Reset

Stop container:

```bash
docker compose down
```

Reset database volume:

```bash
docker compose down -v
docker compose up -d --build
docker exec fashion_jupyter python src/run_pipeline.py
```
