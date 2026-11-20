# Build, test on Windows, release

- Identity in `app/config.py`: `APP_NAME 再新洗車資料庫`, `APP_VERSION` (2.0.0 =
  first release of this design), author Sukio Lin, created 2025, MIT.
- `build_exe.bat` (CRLF, ASCII only): pip install → pytest → `tools/make_icon.py`
  (generated 「洗」 icon; app.ico/app.png are build outputs, gitignored) →
  PyInstaller → `dist\再新洗車資料庫.exe`.
- Windows test machine: credentials from the owner / env vars, never in the
  repo. Same proven loop as autorepair_db (`COPYFILE_DISABLE=1 tar`, scp, build,
  `schtasks /IT` to launch in the desktop session, `PrintWindow` screenshots,
  UTF-16LE PowerShell scripts for Chinese paths; retry flaky SSH).
- Upgrade test before every release: new exe + an OLD `database.db` in a folder
  with Chinese characters and spaces → launch → `再新洗車資料/洗車資料.db` exists,
  row counts and totals unchanged, `自動備份/` created.
- Users upgrade by replacing the exe; the old `database.db` is adopted automatically.
