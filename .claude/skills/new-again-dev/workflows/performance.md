# Performance

Budgets with `tools/bench.py` (3,000 customers, 100,000 washes ≈ 10 years), on a
dev machine with ~5× headroom for old shop PCs:

| Action | Budget | Last measured (2026-11-20) |
| --- | --- | --- |
| Open 客戶資料 (3,000 rows) | < 150 ms | 99 ms |
| Type in search (filter) | < 100 ms | 80 ms |
| Open 營收報表 / switch to year | < 100 ms | 37 / 43 ms |
| Startup | < 1 s | 0.64 s |
| Data: list all customers + last visit | < 30 ms | 14 ms |

Rules: fill tables with `fill_table` (`fit_rows=False` for one-line rows; it
pauses column auto-size); header `setResizeContentsPrecision` samples rows;
debounce typing (200 ms); pages refresh when shown, load once at startup;
report lists are capped (`ReportPage.RECORD_LIMIT`); per-customer and report
queries must stay index-only.
