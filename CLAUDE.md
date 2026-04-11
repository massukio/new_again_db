# 再新洗車資料庫 (New Again Car Wash Database)

## What This App Is
A desktop app for **elderly car wash operators** to record customer license plate info, phone numbers, wash spending, and business analytics. The users have minimal PC experience — every design decision must prioritize simplicity and large readable UI.

## Critical UX Constraints
- **DO NOT change the search/create/edit/delete flow** — elders have memorized it
- **All fonts and buttons must be large** — configurable via menu → 調整字體大小
- **Traditional Chinese UI** throughout
- **Standalone app** — no server, no network. SQLite DB file lives next to the executable.
- **No dropdowns** — use toggle buttons instead (elder-friendly)
- **No unnecessary confirmation popups** — use auto-fading status flash instead
- **No sensitive money info on main screen** — earnings only visible in dedicated report page
- **Dialogs auto-size to screen resolution** — use `_size_to_screen()` pattern
- **Enter key navigates field-by-field**, ESC clears and refocuses
- **Brand selection is optional**, wash record is optional — never force input

## Tech Stack
- Python 3.13+, PyQt5 5.15, SQLite3
- PyInstaller for standalone .exe packaging
- uv for dependency management

## How to Run
```bash
pip3 install uv            # Install uv if not present
uv venv                    # Create venv
uv pip install -e ".[dev]" # Install all deps from pyproject.toml
uv run python start.py     # Launch the app
```

## How to Build Standalone
```bash
uv run pyinstaller new_again_db.spec
# Output: dist/new_again_db (or dist/new_again_db.exe on Windows)
```

## How to Test
```bash
uv run pytest tests/ -v
```

## Architecture
```
start.py                    → Entry point, launches MainWindow maximized
bootstrap.py                → Auto-setup: pip→uv→venv→deps
core/application.py         → MainWindow: signal wiring + delegation only
core/logger.py              → Rotating file loggers (logs/ directory)
ui/main_ui.py               → QLayout-based UI setup (no absolute positioning)
ui/add_plate_dialog.py      → Add/edit plate dialog with brand selector
ui/table_view_handler.py    → Table data binding, filtering, visit stats
ui/wash_record_dialog.py    → Wash type selector + amount input
ui/earnings_page.py         → Earnings report (day/week/month/year)
ui/customer_dashboard.py    → Per-plate spending/visit dashboard + VIP toggle
ui/styles.py                → All stylesheet generation (single source of truth)
ui/font_size_dialog.py      → Font size adjustment dialog
config/constants.py         → Paths (APP_DIR-relative), app constants
config/config_manager.py    → Font config load/save (config.json)
config/brands.py            → Car brand list + logo file paths
database/database.py        → All SQLite operations (context manager pattern)
database/initialize_db.py   → Schema creation + migration
utils/helpers.py            → Phone formatting, plate validation
assets/brands/              → Car brand logo PNGs (20+ brands)
```

## Database Schema

### plate_info
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `part1` TEXT NOT NULL — first half of plate (e.g., "ABC")
- `part2` TEXT NOT NULL — second half of plate (e.g., "1234")
- `phone_number` TEXT NOT NULL
- `note` TEXT
- `brand` TEXT DEFAULT '' — car brand (optional)
- `vip` INTEGER DEFAULT 0 — VIP flag
- UNIQUE(part1, part2, phone_number)

### wash_records
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `plate_part1` TEXT NOT NULL
- `plate_part2` TEXT NOT NULL
- `amount` INTEGER NOT NULL
- `wash_date` TEXT NOT NULL (YYYY-MM-DD)
- `note` TEXT DEFAULT ''
- `created_at` TEXT DEFAULT (datetime('now', 'localtime'))

Plates are always stored UPPERCASE. Phone numbers stored raw, displayed formatted.

## Key Conventions
- All DB operations use `with get_connection() as conn:` context manager
- Styles centralized in `ui/styles.py` — don't inline stylesheets
- Font sizes come from `config.json`, loaded via `config/config_manager.py`
- `constants.py` computes `APP_DIR` to work for both dev and PyInstaller
- `config/brands.py` uses `sys._MEIPASS` for PyInstaller asset paths
- When adding new modules, update `hiddenimports` in `new_again_db.spec`
- Dialogs use `_size_to_screen(w_ratio, h_ratio)` for screen-relative sizing
- Use `_SearchModeProxy` in main_ui.py (replaces QComboBox for elder usability)
- Status messages use `_show_status()` with auto-hide timer, NOT QMessageBox

## Common Pitfalls
- PyInstaller won't auto-detect new file imports → add to `hiddenimports`
- File paths must use `APP_DIR` from constants, not relative paths
- Don't break the existing search/add flow — test manually with elders in mind
- `QDesktopWidget` is deprecated in Qt6 — if migrating, use `QScreen`
- Table plate text may have "★ " VIP prefix — always `.replace("★ ", "")` before parsing
- Brand logos referenced by `BRAND_ICONS` dict — check file exists before loading
- Old databases need `migrate_database()` for new columns (brand, vip, wash_records table)
- Don't show money/earnings on main screen — sensitive business data
- Don't add confirmation popups for routine actions — elders don't want extra clicks
