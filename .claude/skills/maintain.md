---
name: maintain
description: Guide for maintaining, developing, and building the 再新洗車資料庫 elder car wash app
---

# Maintenance & Development Guide

## Adding a New Feature/Button
1. Add the widget in `ui/main_ui.py` inside the appropriate layout section
2. Connect the signal in `core/application.py` `_connect_signals()`
3. Implement the handler method in `core/application.py`
4. If it needs styling, add an object name and CSS rule in `ui/styles.py`
5. Write a test in `tests/`
6. Update `new_again_db.spec` `hiddenimports` if you added a new module

## Adding a New Dialog
1. Create `ui/new_dialog.py` following the pattern in `wash_record_dialog.py`
2. Use `_size_to_screen(w_ratio, h_ratio)` for screen-relative sizing
3. Apply style with `build_dialog_stylesheet()` from `ui/styles.py`
4. Use `_show_status()` for feedback, NOT `QMessageBox` (no extra clicks for elders)
5. Add Enter key navigation: field1 → field2 → ... → accept
6. ESC should clear or close

## Modifying the Database Schema
1. Edit `database/initialize_db.py`:
   - Add column to `CREATE TABLE` for fresh installs
   - Add `ALTER TABLE` in `migrate_database()` for existing users
2. Update the relevant functions in `database/database.py`
3. Update tests in `tests/test_database.py` and `tests/test_backward_compat.py`

## Building the Standalone App
```bash
uv run pyinstaller new_again_db.spec
# Output in dist/new_again_db (Mac) or dist/new_again_db.exe (Windows)
```
Test the built executable — verify DB creates next to the exe, brand logos load.

## Running Tests
```bash
uv run pytest tests/ -v
```

## Elder UX Principles (MUST FOLLOW)
- **Big everything**: fonts ≥ 20px for buttons, ≥ 25px for tables, ≥ 30px for inputs
- **Simple flow**: search (type to filter) → add/edit/delete. No extra steps.
- **No dropdowns**: use toggle buttons instead (easier to tap and see)
- **No confirmation popups** for routine actions — use auto-fading status flash
- **No sensitive info on main screen** — earnings only in dedicated report page
- **No jargon**: all UI text in Traditional Chinese, simple words
- **Forgiveness**: ESC clears search, duplicate warnings allow retry, delete requires confirmation
- **Consistency**: same colors for same actions across all dialogs
- **No hidden features**: everything the user needs is visible, not in submenus
- **Screen-relative sizing**: dialogs auto-size to resolution via `_size_to_screen()`
- **VIP star prefix**: always strip "★ " before parsing plate text from table

## Adding a New Car Brand
1. Download logo PNG to `assets/brands/`
2. Add entry to `config/brands.py` BRANDS list: `("BrandName", "filename.png")`
3. That's it — BrandSelector auto-builds from the list

## Common Pitfalls
- Always use `APP_DIR` from `config/constants.py` for file paths
- Always use `with get_connection() as conn:` for DB operations
- `config/brands.py` uses `sys._MEIPASS` for PyInstaller — don't use `__file__` for asset paths
- Update `new_again_db.spec` hiddenimports when adding new modules
- Test on the target elder user's screen resolution (usually 1920x1080)
- The app starts maximized — ensure layout works at full screen
- Table plate text may have "★ " VIP prefix — strip it before split('-')
