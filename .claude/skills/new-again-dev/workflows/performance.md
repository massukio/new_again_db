# Performance

Measure on the target: `python tools/profile_ui.py --customers 3000 --washes 100000`
**on the Windows test PC** (it is 5-10x slower than a Mac; the owner noticed lag
that Mac numbers did not show). `tools/bench.py` gives data-layer timings.

Budgets on the Windows test VM (2026-11-20 measurements, before → after the
model/view rewrite):

| Action (3,000 customers / 100k washes) | Budget | Windows now (was) |
| --- | --- | --- |
| Type in search (filter) | < 100 ms | 63 ms (349) |
| ESC / clear search | < 100 ms | 63 ms (271) |
| Save a charge (incl. disk sync) | < 150 ms | 102 ms (304) |
| Switch tab and back | < 200 ms | 127 ms (425) |
| Resize window (full restyle) | < 1 s | 645 ms (1,004) |
| Startup (window shown) | < 1 s | 586 ms |

Rules:
- The customer list is a `QTableView` + `CustomerModel` (only visible rows are
  drawn). Never go back to per-cell `QTableWidgetItem`s for big lists: 12,000
  items per keystroke was the Windows lag. Bold columns via the delegate, column
  widths via `fit_columns()` (measures a dozen longest strings).
- `refresh(force=False)` on tab switches skips the reload when the search and
  `conn.total_changes` are unchanged.
- Restyling (`setStyleSheet`) costs ~0.5 s on Windows: only when the base font size
  really changes; maximized windows use the screen size so start-up restyles once.
- Saving costs ~0.1 s on Windows because of the durable disk sync (synchronous
  FULL) — keep it: losing a charge on power loss is worse.
- Smaller tables (客戶資訊, reports) may use `fill_table`; style rows only inside
  `fill_table(decorate=...)`. `tests/test_perf.py` guards the 3,000-row list.
- Search debounce 120 ms.
- The list loads at most `CustomersPage.MAX_ROWS` (3,000) rows; beyond that the
  header says 「只顯示前 3,000 筆…請輸入車牌或電話查詢」 (count via SQL). With the
  816,917-row fake 2025-03 database restored: list 37 ms, search 62–97 ms.
