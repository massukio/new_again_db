# Fix a bug

1. Reproduce: failing test in `tests/test_db.py`, or an offscreen script driving the widget.
2. Ask for `再新洗車資料/錯誤紀錄.log` from the shop if available.
3. Fix the root cause; search for the same pattern elsewhere.
4. If it could have touched shop data: think about existing databases and backups.
5. Verify (tests, screenshots, Windows), then add the lesson to `knowledge/lessons.md`.
