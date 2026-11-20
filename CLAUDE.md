# 再新洗車資料庫 (New Again Car Wash Database)

Offline Windows desktop app for an **elderly car wash owner**: customer plates
and phones, wash spending, earnings reports, backup/restore. PyQt5 + SQLite,
one portable exe built with PyInstaller.

**Start with the maintainer skill: `.claude/skills/new-again-dev/SKILL.md`.**
It routes to architecture, design rules, workflows, owner decisions and the
experience log, and ends every task with a retrospective that keeps it current.

## Critical constraints (summary — details in the skill)
- DO NOT change the search / add / edit / delete flow — the owner has memorized it.
- Big UI, Traditional Chinese, no dropdowns, no popups for routine actions
  (fading Toast), no money on the main screen.
- Never lose data: never delete a database file; stay compatible with every old
  database and backup (.db and .sql).
- Every file/folder the app creates has a Chinese name (`再新洗車資料/洗車資料.db` …).

## Commands
```bash
pip install -r requirements.txt
NEWAGAIN_DATA_DIR=/tmp/cw python start.py
python -m pytest -q -p no:cacheprovider tests
build_exe.bat            # on Windows -> dist\再新洗車資料庫.exe
```
