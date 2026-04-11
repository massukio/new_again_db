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

## Modifying the Database Schema
1. Edit `database/initialize_db.py` with the new schema
2. For existing users: the app will need a migration path — check if table exists and ALTER TABLE as needed in `_pre_check_database()` in `application.py`
3. Update the relevant functions in `database/database.py`
4. Update tests in `tests/test_database.py`

## Building the Standalone App
```bash
# Ensure all dependencies installed
pip install -r requirement.txt
# Build
pyinstaller new_again_db.spec
# Output in dist/
```
Test the built executable by running it directly — verify DB creates next to the exe.

## Running Tests
```bash
pytest tests/ -v
```

## Elder UX Principles (MUST FOLLOW)
- **Big everything**: fonts ≥ 20px for buttons, ≥ 25px for tables, ≥ 30px for inputs
- **Simple flow**: search (type to filter) → add/edit/delete. No extra steps.
- **No jargon**: all UI text in Traditional Chinese, simple words
- **Forgiveness**: ESC clears search, duplicate warnings allow retry, delete requires confirmation
- **Consistency**: same colors for same actions across all dialogs
- **No hidden features**: everything the user needs is visible, not in submenus

## Common Pitfalls
- Always use `APP_DIR` from `config/constants.py` for file paths
- Always use `with get_connection() as conn:` for DB operations
- Update `new_again_db.spec` hiddenimports when adding new modules
- Test on the target elder user's screen resolution (usually 1920x1080)
- The app starts maximized — ensure layout works at full screen
