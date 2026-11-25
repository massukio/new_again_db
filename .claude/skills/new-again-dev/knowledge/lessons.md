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

## 2026-11-20 — "It feels laggy" on Windows, fast on the Mac
- What happened: the owner felt lag; Mac profiling showed nothing alarming.
- Cause: Windows (VM) runs Qt 5-10x slower: QTableWidget with 12,000 items rebuilt
  per keystroke/save/tab switch (~0.3 s), and a full restyle (~1 s) right after
  start-up when the window maximized.
- Rule: profile interactions ON WINDOWS with `tools/profile_ui.py`; model/view for
  big lists; skip refreshes when nothing changed; avoid restyles. Promoted to
  `workflows/performance.md`.

## 2026-11-20 — Selected chips must not change size
- A ✓ prefix and bold on selected chips made them wider, so wrapped chips jumped
  to another line. Rule: show selection by colour only (both apps).

## 2026-11-20 — "Restores old backups" must be proven with REAL old backups
- What happened: tests used hand-written old schemas and missed the two very first
  versions (no note column; one phone per plate). Restoring them would have failed.
- Rule: generate fixtures by running each old version's own code from git
  (`tools/make_legacy_backups.py`), test restore under any file name, and test
  the upgraded data is fully usable (second phone, wash, edit).
- Early commits (fa742e1, 5f1c239) shipped a database.db with fake data
  (816,919 / 100,002 rows): never reuse a committed database as a fixture; it was
  useful locally as a stress test and exposed the need for `MAX_ROWS`.

## 2026-11-20 — Never commit database files; rewriting history safely
- Early commits contained database.db (fake data, 44 MB). Removal = history rewrite.
- How it was done safely: work in a separate `git clone --mirror`; fetch unpushed
  branches into it first so they are rewritten consistently; snapshot every
  branch's file list + commit count; `git filter-repo --path database.db
  --invert-paths`; verify 0 objects left and identical files per branch; push
  `refs/heads/*` with --force; verify from a fresh clone; never touch the owner's
  working clone with uncommitted work. `.gitignore` already excludes *.db.
- Branch names: `x/y` cannot coexist with a branch named `x`.

## 2026-11-24 — 2.0.1 pre-release review (two independent reviewers + sister-app findings)
- Restore: ids in the restored data can mean other cars. The charge panel kept the
  typed amount/chips/note and the reselected row could be another plate → 儲存消費
  could charge the wrong car. Rule: after a restore, `invalidate()` the list, clear
  the selection and `charge.set_customer(None)`; never rely on `total_changes`.
- The "skip unchanged refresh" key must include today's date (「N天前」 changes at
  midnight while the data does not).
- `backup_to` checks the new copy BEFORE `os.replace`: a bad copy must never replace
  an older good backup. An hourly auto-backup failure is shown once, then logged.
- Ported from autorepair_db: UNC paths in sqlite URIs (`file:////server/...`),
  `glob.escape` in rotation, restore failing half way puts the safety copy back,
  overwrite question when `.db` is appended, message if no data folder.
- Enter on a focused button in 新增/修改資料 now presses that button (取消 used to save).
- The save toast showed money on the main screen (owner rule) — removed.
- `.gitignore` had `*.db` with no exception, so the legacy `.db` fixtures were never
  committed (fresh clones and the Windows build failed `test_legacy_backups`), and
  `.pytest_cache/再新洗車資料/` was one line, so neither was ignored. Fixed; don't
  exclude `*.db` when uploading the source tree for a build.

## 2026-11-25 — 使用說明 (in-app manual) for both apps
- Owner asked for a Chinese manual with a table of contents, Taiwanese spoken
  style and highlighted screenshots, packed into the program. Built as
  `app/ui/manual.py` + `assets/manual/` + `tools/make_manual.py` (same in both apps).
- Making the screenshots found real UI bugs: the new header button squeezed the
  program name (now hidden only when there is no room, tabs slightly tighter);
  in 修改資料 the phone box got narrower than a phone number (the hint
  label shares the row) and hid the first digit → `PhoneEdit` minimum width from font metrics.
- Highlight boxes must only cover what is visible: clip to the window and to
  every scroll-area viewport on the way (`rect_of`), or boxes point at nothing.
- The first Windows build failed in a test: `ItemGrid.changeEvent` used
  `QTimer.singleShot(0, lambda ...)`; if the window was deleted before it fired,
  it touched deleted chips (RuntimeError). Rule: a deferred call on a widget uses a
  QTimer OWNED by that widget (dies with it), never a bare lambda singleShot.
  A "1 passed, 1 error" seen once on the Mac was this same flaky crash, not tooling noise
  — never wave off an intermittent error; reproduce it (`sip.delete` the parent).
- Tests that depend on the real font size must call `apply_font_size()` after
  resizing: the window's resize timer has not run yet in a test.

## 2026-11-25 — Release zip layout
- Owner: each zip must be one folder holding the exe and the manual html only. The
  hand-made zips held a bare exe, and old zips sat next to new ones in dist/ and in the
  VM test folders, which looked like "a zip inside the zip". Rule: the build makes the
  zip (`tools/make_release.py`), and check the zip's contents before reporting.
