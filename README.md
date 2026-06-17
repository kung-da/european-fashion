# Fashion Store Analytics

Project phân tích dữ liệu bán hàng thời trang từ Kaggle dataset **European Fashion Store Multitable Dataset**.

Stack giai đoạn đầu:

- PostgreSQL: lưu dữ liệu `raw`, `staging`, `dwh`, `mart`
- pgAdmin: quản trị database bằng giao diện web
- Jupyter Notebook: EDA, load CSV, phân tích dữ liệu bằng Python
- Python: `pandas`, `sqlalchemy`, `psycopg2`, visualization libraries

## Folder Structure

```text
.
├── data
│   ├── raw
│   └── processed
├── notebooks
│   └── 01_postgres_connection_example.ipynb
├── reports
├── sql
│   ├── init
│   │   └── 01_create_schemas.sql
│   ├── staging
│   ├── dwh
│   └── mart
├── src
├── .env
├── Dockerfile
├── docker-compose.yml
├── README.md
└── requirements.txt
```

## Giải Thích Docker Compose

`postgres`

- Chạy PostgreSQL 16.
- Tạo database `fashion_dw`.
- User/password mặc định: `postgres/postgres`.
- Mount `./data` vào container tại `/data` để có thể import CSV.
- Mount `./sql/init` vào `/docker-entrypoint-initdb.d` để tự tạo schema khi database khởi tạo lần đầu.

`pgadmin`

- Chạy pgAdmin 4.
- Truy cập tại `http://localhost:5050`.
- Dùng để xem schema, table, query dữ liệu PostgreSQL.

`jupyter`

- Build từ `Dockerfile`.
- Cài thư viện từ `requirements.txt`.
- Mount toàn bộ project vào `/app`.
- Truy cập tại `http://localhost:8888`.
- Kết nối PostgreSQL bằng hostname service `postgres`.
- Database URL trong container:

```text
postgresql+psycopg2://postgres:postgres@postgres:5432/fashion_dw
```

## Cài Đặt

1. Cài Docker Desktop cho Windows.
2. Mở Docker Desktop và đảm bảo Docker Engine đang chạy.
3. Mở terminal tại thư mục project.

## Chạy Project

```bash
docker compose up -d --build
```

Kiểm tra container:

```bash
docker compose ps
```

Xem log nếu cần:

```bash
docker compose logs -f postgres
docker compose logs -f jupyter
```

## Truy Cập pgAdmin

Mở trình duyệt:

```text
http://localhost:5050
```

Đăng nhập:

```text
Email: admin@admin.com
Password: admin
```

Tạo server mới trong pgAdmin:

- Click **Add New Server**
- Tab **General**
  - Name: `Fashion PostgreSQL`
- Tab **Connection**
  - Host name/address: `postgres`
  - Port: `5432`
  - Maintenance database: `fashion_dw`
  - Username: `postgres`
  - Password: `postgres`
- Click **Save**

## Truy Cập Jupyter Notebook

Mở trình duyệt:

```text
http://localhost:8888
```

Notebook mẫu:

```text
notebooks/01_postgres_connection_example.ipynb
```

Ví dụ code kết nối PostgreSQL trong Jupyter:

```python
import pandas as pd
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+psycopg2://postgres:postgres@postgres:5432/fashion_dw"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT current_database(), current_user;"))
    print(result.fetchone())

schemas = pd.read_sql(
    """
    SELECT schema_name
    FROM information_schema.schemata
    WHERE schema_name IN ('raw', 'staging', 'dwh', 'mart')
    ORDER BY schema_name;
    """,
    engine,
)

schemas
```

## Chuẩn Bị Dữ Liệu CSV

Đặt các file CSV từ Kaggle vào:

```text
data/raw
```

Ví dụ:

```text
data/raw/customers.csv
data/raw/sales.csv
data/raw/sales_items.csv
data/raw/products.csv
data/raw/stock.csv
data/raw/campaigns.csv
data/raw/channels.csv
```

## Stop Container

```bash
docker compose down
```

## Reset Volume PostgreSQL

Khi muốn xóa toàn bộ dữ liệu PostgreSQL và chạy lại init SQL từ đầu:

```bash
docker compose down -v
docker compose up -d --build
```

Lưu ý: lệnh `down -v` sẽ xóa volume database.

## Test Kết Nối PostgreSQL Bằng Terminal

Test từ container PostgreSQL:

```bash
docker exec -it fashion_postgres psql -U postgres -d fashion_dw -c "SELECT current_database(), current_user;"
```

Test schema đã được tạo:

```bash
docker exec -it fashion_postgres psql -U postgres -d fashion_dw -c "\dn"
```
