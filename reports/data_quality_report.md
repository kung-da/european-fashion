# Data Quality Report

## Summary

| Metric | Value |
|---|---:|
| Total records in issue table | 1 |
| Warning issue count | 0 |
| Informational count | 2,170 |

## Issues

| severity | layer_name | table_name | rule_name                               | issue_count | sample_values             |
| -------- | ---------- | ---------- | --------------------------------------- | ----------- | ------------------------- |
| Info     | dwh        | fact_sales | unmapped campaign_key allowed by design | 2170        | 658, 336, 1255, 331, 1079 |

## Notes

- `campaign_key` null in `fact_sales` is informational because campaign mapping is intentionally nullable.
- `discount_percent_value` and `discount_amount_value` are mutually exclusive in campaign data, depending on `discount_type`.
