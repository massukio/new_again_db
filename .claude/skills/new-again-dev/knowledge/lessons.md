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

## 2026-11-20 — State the user cannot see (owner: "I click the table but see nothing selected")
- Cause: the stylesheet styled `QTableWidget::item` (padding, border) but had no
  `::item:selected` rule, so Qt drew only a faint tint. Related, found by review:
  styled buttons draw no focus ring; QDialog buttons are `autoDefault`, so Enter
  "clicked" whatever had focus (a brand chip, the VIP toggle, 取消); confirmation
  boxes defaulted to the destructive button (確定刪除 / 確定還原).
- Rules (promoted to design-system.md): every interactive state needs an explicit,
  strong style — `::item:selected` (solid accent + white bold), `:hover`,
  `QPushButton:focus` amber ring (placed last in the stylesheet so it wins);
  `button()` sets `setAutoDefault(False)`; message boxes default to the SAFE
  choice; dialogs set an explicit default/focus (e.g. 客戶資訊 → 關閉).

## 2026-11-20 — PyQt5 aborts on exceptions inside Qt callbacks
- What happened: test run ended with "Fatal Python error: Aborted".
- Cause: an exception in a slot/event handler with no `sys.excepthook` → PyQt5 calls
  qFatal. (The app's `start.py` installs a hook that logs to 錯誤紀錄.log.)
- Rule: tests install a hook that records such exceptions and fails the test
  (`tests/conftest.py`); stop timers before closing the database in fixtures.

## 2026-11-20 — Space on the main screen
- What happened: adding the 記錄消費 panel squeezed the list (clipped header buttons,
  cut phone numbers) and a fixed-column chip grid clipped long service names.
- Rule: size the important columns to content and let the least important one
  (備註) stretch; drop titles the tab already shows; use a flow layout for chips of
  very different lengths (`ChipFlow`). Check 1070×540 and 1280×760 every time.
