# 再新洗車資料庫 (New Again Car Wash Database)

## What This App Is
A desktop app for **elderly car wash operators** to record customer license plate info, phone numbers, and notes. The users have minimal PC experience — every design decision must prioritize simplicity and large readable UI.

## Critical UX Constraints
- **DO NOT change the search/create/edit/delete flow** — elders have memorized it
- **All fonts and buttons must be large** — configurable via menu → 調整字體大小
- **Traditional Chinese UI** throughout
- **Standalone app** — no server, no network. SQLite DB file lives next to the executable.

## Tech Stack
- Python 3.12+, PyQt5 5.15, SQLite3
- PyInstaller for standalone .exe packaging

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
core/application.py         → MainWindow: signal wiring + delegation only
core/logger.py              → Rotating file loggers (logs/ directory)
ui/main_ui.py               → QLayout-based UI setup (no absolute positioning)
ui/add_plate_dialog.py      → Add/edit plate dialog with validation
ui/table_view_handler.py    → Table data binding, filtering, CRUD delegation
ui/styles.py                → All stylesheet generation (single source of truth)
ui/font_size_dialog.py      → Font size adjustment dialog
config/constants.py         → Paths (APP_DIR-relative), app constants
config/config_manager.py    → Font config load/save (config.json)
database/database.py        → All SQLite operations (context manager pattern)
database/initialize_db.py   → Schema creation
utils/helpers.py            → Phone formatting, plate validation
```

## Database Schema
Single table `plate_info`:
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `part1` TEXT NOT NULL — first half of plate (e.g., "ABC")
- `part2` TEXT NOT NULL — second half of plate (e.g., "1234")
- `phone_number` TEXT NOT NULL
- `note` TEXT
- UNIQUE(part1, part2, phone_number)

Plates are always stored UPPERCASE. Phone numbers stored raw, displayed formatted.

## Key Conventions
- All DB operations use `with get_connection() as conn:` context manager
- Styles centralized in `ui/styles.py` — don't inline stylesheets
- Font sizes come from `config.json`, loaded via `config/config_manager.py`
- `constants.py` computes `APP_DIR` to work for both dev and PyInstaller
- When adding new modules, update `hiddenimports` in `new_again_db.spec`

## Common Pitfalls
- PyInstaller won't auto-detect new file imports → add to `hiddenimports`
- File paths must use `APP_DIR` from constants, not relative paths
- Don't break the existing search/add flow — test manually with elders in mind
- `QDesktopWidget` is deprecated in Qt6 — if migrating, use `QScreen`
