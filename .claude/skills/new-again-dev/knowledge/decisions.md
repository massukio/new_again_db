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
