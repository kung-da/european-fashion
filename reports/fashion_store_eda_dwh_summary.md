# Fashion Store EDA DWH Summary

Dataset is ready for Star Schema after staging validation and reconciliation.

## Key Results

- Tables: 7
- Sales orders: 905
- Sales line items: 2,253
- Products: 500
- Customers: 1,000
- Reconciliation rate: 100.00%
- Duplicate key rows: 0
- Relationship checks with issues: 0
- Invalid rule total count: 77

## Design Conclusion

- `salesitems` is the main source for `fact_sales`.
- `sales` should stay separate as `fact_order` to calculate orders and AOV at the right grain.
- `stock` needs a generated `snapshot_date_key` because the source has no inventory date.
- `dim_channel` should be built from the union of channels, sales, salesitems and campaigns.
- `campaign_key` in `fact_sales` should be nullable because not every line item maps to a campaign.

## Dashboard Readiness

- Executive Sales Overview: ready.
- Product Performance: ready.
- Customer Analytics: ready.
- Inventory Monitoring: ready with generated `snapshot_date_key`.
- Channel & Campaign Analytics: partially ready because campaign mapping is sparse.
