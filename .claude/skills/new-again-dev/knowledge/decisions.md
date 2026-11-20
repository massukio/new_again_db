# Owner decisions (ask before changing)

- 2025 — Offline single-exe app for an elderly car wash owner; Traditional Chinese.
- 2025 — Do not change the search/add/edit/delete flow; no dropdowns; no routine
  popups (fading status); no money on the main screen; big everything.
- 2026-11-20 — Redesign on branch `refactor/autorepair-design` (from
  `feat/business-intelligence-expansion`), same design system as autorepair_db:
  "no need to be fancy, but easy and elegant". Features too hard for elders may be
  removed or simplified (brand grid wraps instead of scrolling; report uses
  今日/本週/本月/今年 + prev/next instead of date dropdowns; 3-value font dialog →
  小/中/大/特大 + auto-scaling; backup always .db, no format question).
- 2026-11-20 — Daily auto backup, Chinese names for every file/folder the app creates.
- 2026-11-20 — Must restore data from old versions (.db and .sql backups, all old schemas).
- 2026-11-20 — Version 2.0.0 for the redesign; MIT; author Sukio Lin; created 2025.
- 2026-11-20 — Main use: look up a plate to read the phone number and call the
  customer; add/edit plates with phones. A plate can have several numbers; numbers
  change or expire. → phone as prominent as the plate, newest number first,
  「目前選擇」 box shows plate + phone large, 修改資料 = change number, 刪除資料 on a
  row = remove only that number (history stays with the plate).
- 2026-11-20 — 備註 is rarely used in real life: narrow last column (full text on
  hover and in 客戶資訊), "no need such big room".
- 2026-11-20 — Duplicate-plate question answered 「不要」 keeps the typed data and
  focuses the phone box (old app cleared everything). ESC in 修改資料 backs out.
- 2026-11-20 — Icon: white car with three water drops on a teal rounded square
  (owner generated it; `assets/icon_source.png`), replacing the 「洗」 placeholder.
- 2026-11-20 — 「目前選擇」 box removed (redundant with the highlighted row). Main
  screen: actions in the list header, right column = 記錄消費 panel so a phone
  lookup and the charge happen together. Services = editable items from the shop's
  price list, NO prices or car sizes ("不需要價格，只要項目就好"); amount is typed.
- 2026-11-20 — No VIP feature (★ mark, 設為 VIP) — "不用這種功能". The vip column stays in
  the database only so old app versions keep working; nothing reads or writes it.
- 2026-11-20 — Restore must consume any backup that follows one of our schemas,
  whatever the file name. All files the app creates have Chinese names.
