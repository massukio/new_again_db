# Design system: easy and elegant, not fancy

Shared with autorepair_db (same `style.py` / `widgets.py`; accent colour here is
the carwash teal `#0E6E84`). Owner direction: "no need to be fancy, but easy
and elegant"; remove anything too hard for an elder.

## The memorized flow (do not change)

- Main screen: list on the left, action buttons on the right
  (＋ 新增資料, 修改資料, 刪除資料 | 記錄消費, 客戶資訊), search under the list:
  車牌查詢 (前半 — 後半) / 電話查詢, filtering while typing.
- Enter moves to the next box; ESC clears the search and focuses 前半.
- 新增資料 stays open after saving (clears itself) to enter the next car.
  Same plate + same phone → refused; same plate + other phone → ask
  (要新增 / 不要 → clears). Edit: plate that belongs to another row → refused.
- 記錄消費: type chips (一般洗車/精緻洗車/美容/其他) + amount + optional note,
  dated today; Enter amount → note → save; ESC closes.
- 客戶資訊 on button or double-click: totals, history, ★ VIP toggle,
  delete a mistaken wash.

## Elder UX rules (from the owner, keep them)

- Big everything; nothing important below the base size; search boxes extra big.
- No dropdowns — toggle buttons / pill switches (`Segmented`, chips).
- No confirmation popups for routine actions — `Toast` fading message.
  Destructive actions (delete) DO confirm with explicit verbs (確定刪除 / 不要刪除).
- No money on the main screen.
- No jargon; Traditional Chinese; no hidden features or submenus.
- Forgiveness: ESC clears, duplicates allow retry, mistakes can be deleted.
- Consistency: green = add/save/confirm, teal = navigation & 記錄消費,
  red outline = delete.
- Dialogs never exceed the screen (`fit_to_screen`), buttons pinned outside scroll areas.

## Components

`Card`, `Tile`, `Segmented`, `button(role)` (primary, action, big, bigdanger,
danger, link, item, brand, nav, seg), `label(role)` (cardtitle, field, muted,
hint, plate, badge, toast, toastwarn, dash, info …), `Toast`, `BrandGrid`
(wrapping logo chips, click again to clear), `make_table` + `fill_table`
(`fit_rows=False` for one-line rows), `sized()` for every fixed pixel size.

## Check every UI change

`tools/screenshot.py` at 1070×540, 1280×760, 1920×1040, 800×480 + dialogs; then
the real exe on Windows (fonts render smaller there; the offscreen renderer
pretends the screen is 800×600, so dialogs look cramped in screenshots only).
