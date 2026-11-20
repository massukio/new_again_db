# Design system: easy and elegant, not fancy

Shared with autorepair_db (same `style.py` / `widgets.py`; accent colour here is
the carwash teal `#0E6E84`). Owner direction: "no need to be fancy, but easy
and elegant"; remove anything too hard for an elder.

## The memorized flow (do not change)

- Main job: find a plate and read its phone number to call the customer, so
  plate and phone are bold and large; 備註 is a narrow last column.
- Main screen (owner-approved layout, 2026-11-20):
  left card = header row [共 N 筆 · toast · ＋ 新增 | 修改 | 刪除 | 客戶資訊], the list
  (車牌號碼, 電話號碼, 上次來店 sized to content; 備註 takes what is left), search
  under the list; right card = 記錄消費 for the selected car: plate badge, service
  item chips (wrap like words, multi-select, ＋ 新增項目 / 管理項目, right-click to
  rename/delete), 金額, 備註, 儲存消費. A search that finds exactly one car selects
  it, so "look up the phone, then charge" is one flow. Search under the list:
  車牌查詢 (前半 — 後半) / 電話查詢, filtering while typing.
- Enter moves to the next box; ESC clears the search and focuses 前半.
- 新增資料 stays open after saving (clears itself) to enter the next car.
  Same plate + same phone → refused; same plate + other phone → ask
  (加這個號碼 / 不要 → keeps the typing, focuses the phone). Edit: plate that belongs
  to another row → refused. ESC: add = clear (close when empty), edit = back out.
- After any dialog or tab switch the cursor goes back to the search box.
- 記錄消費 (panel): chips + amount (required) + optional note, dated today;
  Enter amount → note → save; after saving the panel clears and the cursor
  returns to the search box.
- 客戶資訊 on button or double-click: totals, history, all phone numbers,
  delete a mistaken wash. (No VIP / ★ — removed by the owner.)

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

## Visible state (mandatory)

- Selected table row: solid accent background, white bold text (`::item:selected`);
  hover tint on rows. Anything the user must click first (a row) needs a visible
  confirmation of what is selected (carwash: 「目前選擇」 box).
- Keyboard focus: amber ring on every focusable button; inputs show an accent border.
- No hidden Enter behaviour: `button()` turns off autoDefault; dialogs that want
  Enter to save handle it in `keyPressEvent`; message boxes default to the safe button.
- Test it: `tests/test_ui.py` style tests click, press Enter/ESC and assert the
  visible state, not only the data.
