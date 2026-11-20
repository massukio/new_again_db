---
name: new-again-dev
description: Maintain and extend 再新洗車資料庫 (new_again_db), the offline PyQt5 + SQLite Windows app an elderly car wash owner uses to keep customer plates/phones, wash spending and earnings. Use for ANY task on this repo - bug fixes, features, UI, database, performance, building the Windows exe - and always finish with the retrospective that keeps this skill up to date.
---

# 再新洗車資料庫 — maintainer skill (single entry point)

This file is the **only entry point**; details live in the nested files. Read
what the task needs, but always do steps 1 and 4.

## 0. The app in 30 seconds

- Offline Windows desktop app, one portable exe (`再新洗車資料庫.exe`, PyInstaller onefile).
- User: an elderly car wash owner who has **memorized the search / add / edit /
  delete flow**. Never change that flow (see `reference/design-system.md`).
- Data: customers = plate (two halves, e.g. ABC-1234) + phone + note + optional
  brand; wash records = plate + amount + date + service items/note.
- Pages: 客戶資料 (main: list + search on the left, 記錄消費 panel with editable
  service-item chips on the right) · 營收報表 · 備份/還原 · 設定. Dialogs:
  新增/修改資料, 客戶資訊, 管理服務項目.
- Data folder `再新洗車資料/` next to the exe (`洗車資料.db`, `自動備份/`, `錯誤紀錄.log`).
- Sister project with the same architecture and design system: `autorepair_db`
  (汽車保養資料庫). Improvements usually apply to both.

## 1. Before you start (always)

1. Read `knowledge/lessons.md` and `knowledge/decisions.md`.
2. Run the tests: `python -m pytest -q -p no:cacheprovider tests`.

## 2. Route to the right guide

| Your task | Read |
| --- | --- |
| Where does code live, data model, compatibility | `reference/architecture.md` |
| Any UI change | `reference/design-system.md` |
| Run, screenshots, fake data, tests | `workflows/develop.md` |
| Add / change a feature | `workflows/feature.md` |
| Fix a bug | `workflows/bugfix.md` |
| Change the database or backup/restore | `workflows/data-changes.md` |
| Lists, queries, "it is slow" | `workflows/performance.md` |
| Build the exe, test on Windows, release | `workflows/build-release.md` |
| Finishing ANY task | `workflows/retro.md` (mandatory) |

## 3. Non-negotiable rules

- **Never lose data.** Never delete a database file (an unreadable one is set
  aside as `無法開啟的資料_<time>.db`). Keep the schema compatible with old app
  versions; old `.db` and `.sql` backups must always restore.
- **Keep the memorized flow** and the elder UX rules (`reference/design-system.md`).
- **No money on the main screen** — only in 營收報表 and 客戶資訊.
- **Every file/folder the app creates has a Chinese name.**
- **Must not lag** with years of data — run `tools/bench.py` after touching
  queries or tables.
- **Verify on Windows** before calling a release done. No secrets in the repo.

## 4. Finish with the retrospective (always)

Do `workflows/retro.md`: make every skill file true again, add lessons, record
owner decisions. A task is not done until the skill matches the code.
