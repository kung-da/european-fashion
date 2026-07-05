import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
from pipeline_utils import get_engine

def run_checks():
    engine = get_engine()
    
    with engine.connect() as conn:
        # 1. Check duplicate rows in Dimensions (Natural Keys)
        print("--- DIMENSION DUPLICATE CHECK ---")
        dim_checks = {
            "dim_customer": "customer_id",
            "dim_product": "product_id",
            "dim_date": "full_date",
            "dim_geography": "country",
            "dim_channel": "channel_name",
            "dim_campaign": "campaign_id"
        }
        for table, key in dim_checks.items():
            query = f"""
            SELECT {key}, COUNT(*) as cnt 
            FROM dwh.{table} 
            GROUP BY {key} 
            HAVING COUNT(*) > 1
            """
            dups = conn.execute(text(query)).fetchall()
            print(f"{table}: {len(dups)} duplicate keys found.")
            
        # 2. Check duplicate rows in Facts (Degenerate dimensions / primary keys)
        print("\n--- FACT DUPLICATE CHECK ---")
        fact_checks = {
            "fact_sales": "item_id",
            "fact_order": "sale_id",
            "fact_inventory": "snapshot_date_key, product_key, geography_key",
            "fact_customer_activity": "activity_date_key, customer_key"
        }
        for table, keys in fact_checks.items():
            query = f"""
            SELECT {keys}, COUNT(*) as cnt 
            FROM dwh.{table} 
            GROUP BY {keys} 
            HAVING COUNT(*) > 1
            """
            dups = conn.execute(text(query)).fetchall()
            print(f"{table}: {len(dups)} duplicate keys found.")

        # 3. Check Fan-out (Data duplication caused by Joins)
        print("\n--- JOIN FAN-OUT CHECK ---")
        base_count = conn.execute(text("SELECT COUNT(*) FROM dwh.fact_sales")).scalar()
        
        # Massive join query
        complex_join = """
        SELECT COUNT(*)
        FROM dwh.fact_sales fs
        JOIN dwh.dim_date d ON fs.sale_date_key = d.date_key
        JOIN dwh.dim_customer c ON fs.customer_key = c.customer_key
        JOIN dwh.dim_product p ON fs.product_key = p.product_key
        JOIN dwh.dim_customer c2 ON fs.customer_key = c2.customer_key
        JOIN dwh.dim_geography g ON c2.geography_key = g.geography_key
        JOIN dwh.dim_channel ch ON fs.channel_key = ch.channel_key
        LEFT JOIN dwh.dim_campaign cam ON fs.campaign_key = cam.campaign_key
        """
        join_count = conn.execute(text(complex_join)).scalar()
        
        print(f"Base fact_sales rows: {base_count}")
        print(f"Joined with ALL dimensions rows: {join_count}")
        if base_count == join_count:
            print("=> NO FAN-OUT: Joins are perfectly 1:N. No row redundancy created.")
        else:
            print(f"=> FAN-OUT DETECTED: Added {join_count - base_count} redundant rows.")

        # 4. Complex Query joining multiple facts via conformed dimensions
        print("\n--- COMPLEX CROSS-FACT CONFORMED JOIN ---")
        conformed_query = """
        WITH daily_sales AS (
            SELECT 
                fs.sale_date_key,
                fs.product_key,
                c.geography_key,
                SUM(fs.quantity) as sold_qty
            FROM dwh.fact_sales fs
            JOIN dwh.dim_customer c ON fs.customer_key = c.customer_key
            GROUP BY fs.sale_date_key, fs.product_key, c.geography_key
        ),
        daily_inventory AS (
            SELECT 
                fi.snapshot_date_key,
                fi.product_key,
                fi.geography_key,
                MAX(fi.stock_quantity) as stock_qty
            FROM dwh.fact_inventory fi
            GROUP BY fi.snapshot_date_key, fi.product_key, fi.geography_key
        )
        SELECT 
            d.full_date,
            p.product_name,
            g.country,
            COALESCE(ds.sold_qty, 0) as sold_qty,
            COALESCE(di.stock_qty, 0) as stock_qty
        FROM dwh.dim_date d
        CROSS JOIN dwh.dim_product p
        CROSS JOIN dwh.dim_geography g
        LEFT JOIN daily_sales ds 
            ON d.date_key = ds.sale_date_key 
            AND p.product_key = ds.product_key 
            AND g.geography_key = ds.geography_key
        LEFT JOIN daily_inventory di 
            ON d.date_key = di.snapshot_date_key 
            AND p.product_key = di.product_key 
            AND g.geography_key = di.geography_key
        WHERE ds.sold_qty IS NOT NULL OR di.stock_qty IS NOT NULL
        LIMIT 5;
        """
        res = conn.execute(text(conformed_query)).fetchall()
        print(f"Multi-fact join sample (5 rows):")
        for r in res:
            print(f"  {r[0]} | {str(r[1])[:20]:20s} | {str(r[2]):10s} | Sold: {int(r[3] or 0):3d} | Stock: {int(r[4] or 0):3d}")

if __name__ == "__main__":
    run_checks()
