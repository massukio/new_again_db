# Experience log (append at the bottom)

Format: `## YYYY-MM-DD — title` then What happened / Cause / Rule.

## 2026-11-20 — Old app deleted the database file
- What happened: `_pre_check_database` called `os.remove(database.db)` when the
  plate_info table was missing.
- Rule: never delete user data; set unreadable files aside (`open_database`). Promoted.

## 2026-11-20 — Windows keeps a failed sqlite connection's file locked
- What happened: moving an unreadable db aside raised WinError 32 on Windows only.
- Cause: the first PRAGMA raised before the try/close block.
- Rule: wrap every statement after `sqlite3.connect` in the guarded block and
  close the connection before moving files. Tests must also pass on Windows.

## 2026-11-20 — Rows were identified by parsing table text
- Old code split "★ ABC-1234" and the formatted phone back into keys.
- Rule: keep the row id in the table (UserRole); never parse display text.

## 2026-11-20 — Filtered list lost columns
- Old search results dropped last-visit and VIP. Rule: one query (`list_customers`)
  for both the full list and filtered results.

## 2026-11-20 — Lessons carried over from autorepair_db
- See that repo's `knowledge/lessons.md` (table fill O(n²), offscreen modal hangs,
  wrap-label heights, Windows VM automation, .bat CRLF/ASCII, executescript commits).
