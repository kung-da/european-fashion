# Project Structure

## Current Structure

```text
.
|-- data
|   `-- raw                         # Kaggle CSV files
|-- notebooks
|   |-- 01_postgres_connection_example.ipynb
|   `-- 02_eda_dwh_readiness.ipynb  # EDA notebook
|-- reports
|   |-- data_quality_report.md
|   |-- fashion_store_dwh_design.md
|   |-- fashion_store_eda_dwh_results.xlsx
|   |-- fashion_store_eda_dwh_results_from_notebook.xlsx
|   |-- fashion_store_eda_dwh_summary.md
|   |-- project_structure.md
|   `-- raw_staging_dwh_python_pipeline.md
|-- scripts
|   `-- generate_eda_dwh_assets.py  # Regenerate EDA notebook/report/Excel
|-- sql
|   `-- init
|       `-- 01_create_schemas.sql   # Docker init schemas only
|-- src
|   |-- build_dwh.py                # Build DWH dimensions/facts with pandas
|   |-- build_staging.py            # Build staging tables with pandas
|   |-- load_raw_csv.py             # Load CSV to raw schema
|   |-- pipeline_utils.py           # Shared helpers
|   |-- run_data_quality.py         # DQ checks and DQ markdown
|   `-- run_pipeline.py             # Main orchestrator
|-- docker-compose.yml
|-- Dockerfile
|-- README.md
`-- requirements.txt
```

## Kept

- Python pipeline files in `src/`.
- EDA generator in `scripts/`.
- PostgreSQL schema init SQL in `sql/init/`.
- EDA, DWH, pipeline, and data quality reports in `reports/`.

## Removed / Ignored

- Python `__pycache__` folders are generated files and should not be committed.
- SQL transform/load scripts are not needed because staging, DWH, and data quality are implemented in Python.

## Main Commands

```bash
docker exec fashion_jupyter python scripts/generate_eda_dwh_assets.py
docker exec fashion_jupyter jupyter nbconvert --to notebook --execute --inplace notebooks/02_eda_dwh_readiness.ipynb
docker exec fashion_jupyter python src/run_pipeline.py
```
