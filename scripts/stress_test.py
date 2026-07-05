import sys
from pathlib import Path
import time
import concurrent.futures
from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
from pipeline_utils import get_engine

COMPLEX_QUERIES = [
    # Query 1: Heavy aggregation with multiple joins
    """
    SELECT 
        d.year_number,
        d.month_number,
        p.category,
        g.country,
        SUM(fs.gross_amount) as total_gross,
        SUM(fs.discount_amount) as total_discount,
        SUM(fs.net_amount) as total_net,
        SUM(fs.gross_profit) as total_profit
    FROM dwh.fact_sales fs
    JOIN dwh.dim_date d ON fs.sale_date_key = d.date_key
    JOIN dwh.dim_product p ON fs.product_key = p.product_key
    JOIN dwh.dim_geography g ON fs.geography_key = g.geography_key
    GROUP BY d.year_number, d.month_number, p.category, g.country
    ORDER BY total_net DESC;
    """,
    # Query 2: Window functions and ranking
    """
    WITH ranked_sales AS (
        SELECT 
            c.customer_id,
            d.year_number,
            d.month_number,
            SUM(fs.net_amount) as customer_revenue,
            RANK() OVER (PARTITION BY d.year_number, d.month_number ORDER BY SUM(fs.net_amount) DESC) as revenue_rank
        FROM dwh.fact_sales fs
        JOIN dwh.dim_date d ON fs.sale_date_key = d.date_key
        JOIN dwh.dim_customer c ON fs.customer_key = c.customer_key
        GROUP BY c.customer_id, d.year_number, d.month_number
    )
    SELECT * FROM ranked_sales WHERE revenue_rank <= 10;
    """,
    # Query 3: Comparing sales with inventory
    """
    SELECT 
        p.product_id,
        p.product_name,
        g.country,
        SUM(fs.quantity) as total_sold,
        MAX(fi.stock_quantity) as current_stock,
        (MAX(fi.stock_quantity) - SUM(fs.quantity)) as stock_diff
    FROM dwh.fact_sales fs
    JOIN dwh.dim_product p ON fs.product_key = p.product_key
    JOIN dwh.dim_geography g ON fs.geography_key = g.geography_key
    LEFT JOIN dwh.fact_inventory fi ON p.product_key = fi.product_key AND g.geography_key = fi.geography_key
    GROUP BY p.product_id, p.product_name, g.country
    HAVING (MAX(fi.stock_quantity) - SUM(fs.quantity)) < 10
    ORDER BY stock_diff ASC;
    """
]

def run_query(engine, query_id, query_sql):
    start_time = time.time()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query_sql)).fetchall()
            row_count = len(result)
        end_time = time.time()
        return {"status": "success", "duration": end_time - start_time, "rows": row_count, "query_id": query_id}
    except Exception as e:
        end_time = time.time()
        return {"status": "error", "duration": end_time - start_time, "error": str(e), "query_id": query_id}

def main():
    engine = get_engine()
    
    # Configuration
    NUM_WORKERS = 20
    TOTAL_REQUESTS = 100
    
    print(f"Starting Stress Test: {TOTAL_REQUESTS} requests across {NUM_WORKERS} workers...")
    
    start_test = time.time()
    results = []
    
    # We will just round-robin the complex queries
    queries_to_run = [(i, COMPLEX_QUERIES[i % len(COMPLEX_QUERIES)]) for i in range(TOTAL_REQUESTS)]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = [executor.submit(run_query, engine, q_id, q_sql) for q_id, q_sql in queries_to_run]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            results.append(res)
            # print(f"Query {res['query_id']} completed in {res['duration']:.4f}s with status {res['status']}")

    end_test = time.time()
    
    total_duration = end_test - start_test
    successes = [r for r in results if r["status"] == "success"]
    errors = [r for r in results if r["status"] == "error"]
    
    durations = [r["duration"] for r in successes]
    if durations:
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        min_duration = min(durations)
        durations.sort()
        p95_duration = durations[int(len(durations) * 0.95)]
    else:
        avg_duration = max_duration = min_duration = p95_duration = 0

    print("\\n" + "="*40)
    print("STRESS TEST RESULTS")
    print("="*40)
    print(f"Total Requests  : {TOTAL_REQUESTS}")
    print(f"Concurrency     : {NUM_WORKERS}")
    print(f"Total Time      : {total_duration:.4f} seconds")
    print(f"Throughput      : {TOTAL_REQUESTS / total_duration:.2f} queries/sec")
    print(f"Successful      : {len(successes)}")
    print(f"Errors          : {len(errors)}")
    print("-" * 40)
    print(f"Min Latency     : {min_duration:.4f} seconds")
    print(f"Max Latency     : {max_duration:.4f} seconds")
    print(f"Avg Latency     : {avg_duration:.4f} seconds")
    print(f"P95 Latency     : {p95_duration:.4f} seconds")
    print("="*40)
    
    if errors:
        print("Sample errors:")
        for e in errors[:3]:
            print(f" - {e['error']}")

if __name__ == "__main__":
    main()
