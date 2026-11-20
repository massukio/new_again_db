# Architecture (keep this file true)

```
start.py               excepthook -> 錯誤紀錄.log, single-instance QLockFile, open_database
                       (sets unreadable files aside), daily auto backup, MainWindow
app/config.py          APP_* identity (version, author, MIT), Chinese file names, legacy
                       database.db adoption, UI scaling constants, WASH_TYPES
app/db.py              Database: customers, wash records, reports, backup_to (VACUUM INTO),
                       check_backup_file / restore_from (.db any version or old .sql dump),
                       open_database; helpers clean_part / clean_phone / format_phone
app/backup.py          daily auto backup + before-restore safety copies (pruned)
app/brands.py          brand list + logo paths (assets/brands/*.png)
app/ui/main_window.py  header (icon, name, tabs), page stack, window-size font scaling
app/ui/customers.py    CustomersPage (main: list, header actions, search), ChargePanel
                       (記錄消費: ChipFlow service items + amount + note), CustomerDialog
                       (add/edit), CustomerInfoDialog, BrandGrid, FlowLayout/ChipFlow, Toast
app/ui/items.py        service item flows (add / rename / delete / reorder) + manager dialog
                       (same file shape as autorepair_db's items.py)
app/ui/pages.py        ReportPage, BackupPage, SettingsPage (字體大小, 服務項目 ItemManager, 關於)
app/ui/widgets.py      shared widgets (Card, Tile, Segmented, fill_table, messages ...) -
                       same file as in autorepair_db
app/ui/style.py        palette (teal accent), stylesheet, sized() scaling registry
tools/                 make_icon.py, screenshot.py, make_fake_data.py, bench.py
tests/test_db.py       data layer incl. every old schema, .sql dump restore, file moves
new_again_db.spec      PyInstaller (exe 再新洗車資料庫.exe, bundles assets/brands + icon)
build_exe.bat          Windows: pip install -> pytest -> make_icon -> PyInstaller (CRLF, ASCII)
```

## Data model (schema version 2 — deliberately the same tables as old versions)

```
plate_info(id, part1, part2, phone_number, note NULL, brand '', vip 0,
           UNIQUE(part1, part2, phone_number))        -- one row per plate+phone
                                                      -- vip: kept for old apps, unused (owner removed VIP)
wash_records(id, plate_part1, plate_part2, amount INT, wash_date 'YYYY-MM-DD',
             note '一般洗車 - 額外備註', created_at)     -- linked by plate text
settings(key, value)                                   -- new in 2.0; old apps ignore it
services(id, name UNIQUE, sort_order, active)          -- new in 2.0: service item chips,
                                                          seeded once from the shop's price-list
                                                          names (config.DEFAULT_SERVICES); soft delete
idx_wash_plate (plate_part1, plate_part2, wash_date, amount)   covering: per-customer
idx_wash_day   (wash_date, amount, plate_part1, plate_part2)   covering: reports
```

- Plates: halves upper-case A-Z/0-9, max 4 each (`clean_part`). Phones stored as
  digits (`clean_phone`), shown as 0912-345-678 (`format_phone`).
- A plate may have several phones (several rows). Wash records belong to the
  plate, not to a row. Editing a plate moves its wash records along, unless
  another row still uses the old plate. Deleting a customer keeps its wash
  records (earnings stay correct).
- UI tracks rows by `plate_info.id` (table UserRole), never by parsing cell text.
- A wash's note = chosen service names joined with 「、」 plus 「 - 備註」 — the same
  text format old versions wrote, so reports and old apps read it unchanged. No
  prices are stored for services (owner: "不需要價格，只要項目"); amount is typed.

## Compatibility (why the schema did not change)

Every old version and its backup format — real backup files of each, made by the
old code itself, live in `tests/fixtures/legacy/` (regenerate with
`tools/make_legacy_backups.py <clone with history>`), tested by
`tests/test_legacy_backups.py`:

| Version | plate_info | wash_records | backups |
| --- | --- | --- | --- |
| 2025-03-02 first (`fa742e1`) | no `note`, UNIQUE(part1, part2) | – | copy of database.db* |
| 2025-03-02 (`5f1c239`) | + note, UNIQUE(part1, part2) | – | copy of database.db* |
| 2025-08 main (`18177f9`) | UNIQUE(part1, part2, phone_number) | – | .db copy or .sql dump |
| 2026-04 v1.1 (`21ad8ae`) | + brand, vip | yes | .db copy or .sql dump |

\* the very first commits offered a ".json" backup that copied a file the app never
wrote - no real JSON backup can exist, so JSON is not supported.

`_create_schema` upgrades any of them in place: ADD COLUMN note/brand/vip, and if
the table still has UNIQUE(part1, part2) it is rebuilt (`_rebuild_plate_info`, one
transaction, ids kept) so a plate can have several phones. Tables are otherwise
unchanged, so a 2.0 backup still opens in v1.x apps. Restore decides by CONTENT,
never by file name or extension (the picker shows all files): SQLite header →
database; text with CREATE TABLE plate_info → old `.sql` dump, loaded into a temp
database with ATTACH/DETACH/load_extension denied, validated, then copied.

## Files and names

`config.data_dir()`: `NEWAGAIN_DATA_DIR` env → `<exe dir>/再新洗車資料` if writable →
`%LOCALAPPDATA%/再新洗車資料庫/再新洗車資料`. Inside: `洗車資料.db`,
`自動備份/自動備份_YYYYMMDD.db` (30 kept), `還原前備份_…db` (10 kept),
`錯誤紀錄.log`, `使用中.lock`. Manual backups default to `再新洗車備份_…db`.
Old versions kept `database.db` next to the exe: `_adopt_legacy_database` renames
it (with its `-journal`) into the data folder; if that fails `db_path()` keeps
using the old file. Old `config.json` / `logs/` are ignored, not deleted.
