# Project Structure

Muc tieu cua cau truc moi la tach ro **source data**, **code pipeline**, **notebook**, va **bao cao dau ra**.

## Recommended Layout

```text
.
|-- data/
|   `-- raw/
|       |-- dataset_fashion_store_campaigns.csv
|       |-- dataset_fashion_store_channels.csv
|       |-- dataset_fashion_store_customers.csv
|       |-- dataset_fashion_store_products.csv
|       |-- dataset_fashion_store_sales.csv
|       |-- dataset_fashion_store_salesitems.csv
|       `-- dataset_fashion_store_stock.csv
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
|   |-- load_raw_csv.py
|   |-- build_staging.py
|   |-- build_dwh.py
|   |-- run_data_quality.py
|   |-- run_pipeline.py
|   `-- pipeline_utils.py
|
|-- docker-compose.yml
|-- Dockerfile
|-- requirements.txt
`-- README.md
```

## Folder Meaning

| Folder | Noi dung | Co nen sua tay? |
|---|---|---|
| `data/raw` | CSV goc | Co, khi thay dataset |
| `src` | Pipeline Python chinh | Co |
| `scripts` | Script sinh artifact EDA | Co |
| `notebooks` | Notebook de xem/phan tich | Co |
| `reports/eda` | Output EDA | Thuong khong, sinh lai bang script |
| `reports/dwh` | Tai lieu thiet ke DWH | Co |
| `reports/pipeline` | Tai lieu pipeline | Co |
| `reports/data_quality` | Output data quality | Thuong khong, sinh lai bang pipeline |
| `sql/init` | SQL tao schema ban dau | It sua |

## Execution Flow

```text
src/run_pipeline.py
  1. src/load_raw_csv.py
  2. src/build_staging.py
  3. src/build_dwh.py
  4. src/run_data_quality.py
```

## Report Flow

```text
scripts/generate_eda_dwh_assets.py
  -> notebooks/02_eda_dwh_readiness.ipynb
  -> reports/eda/fashion_store_eda_dwh_results.xlsx
  -> reports/eda/fashion_store_eda_dwh_summary.md

src/run_data_quality.py
  -> staging.data_quality_issues
  -> reports/data_quality/data_quality_report.md
```

## Files Removed From Main Level

Report files are grouped under:

- `reports/eda`
- `reports/dwh`
- `reports/pipeline`
- `reports/data_quality`

This keeps the project root focused on runtime configuration and entry points.
