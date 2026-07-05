from pipeline_utils import get_engine
import pandas as pd

engine = get_engine()

# 1. Check if dim_campaign has channel_name
df_campaign = pd.read_sql("SELECT * FROM dwh.dim_campaign LIMIT 1", engine)
print("dim_campaign columns:", df_campaign.columns.tolist())

# 2. Check if fact_sales.channel_key matches dim_campaign.channel_key
query = """
SELECT fs.sales_key, fs.channel_key as sale_channel, dc.channel_key as camp_channel 
FROM dwh.fact_sales fs
JOIN dwh.dim_campaign dc ON fs.campaign_key = dc.campaign_key
WHERE fs.channel_key != dc.channel_key
"""
mismatch = pd.read_sql(query, engine)
print(f"\nMismatches between sale channel and campaign channel: {len(mismatch)}")

# 3. What percentage of sales have a campaign?
query_pct = """
SELECT 
    COUNT(campaign_key) as camp_sales, 
    COUNT(*) as total_sales
FROM dwh.fact_sales
"""
pct = pd.read_sql(query_pct, engine)
print(f"\nSales with campaign: {pct['camp_sales'][0]} / {pct['total_sales'][0]}")
