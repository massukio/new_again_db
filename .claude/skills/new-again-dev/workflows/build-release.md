# Build, test on Windows, release

- Identity in `app/config.py`: `APP_NAME 再新洗車資料庫`, `APP_VERSION` (2.0.0 =
  first release of this design), author Sukio Lin, created 2025, MIT.
- `build_exe.bat` (CRLF, ASCII only): pip install → pytest → `tools/make_icon.py`
  → PyInstaller → `dist\再新洗車資料庫.exe`.
- Icon: source of truth is `assets/icon_source.png` (owner-generated teal car +
  water drops). `make_icon.py` crops the rounded square, makes the corners
  transparent and writes `assets/app.ico` (16–256 px) + `app.png` (build outputs,
  gitignored). To change the icon, replace the source image (adjust
  `CORNER_RATIO` if the new art has different corners) and rebuild.
- Windows test machine: credentials from the owner / env vars, never in the
  repo. Same proven loop as autorepair_db (`COPYFILE_DISABLE=1 tar`, scp, build,
  `schtasks /IT` to launch in the desktop session, `PrintWindow` screenshots,
  UTF-16LE PowerShell scripts for Chinese paths; retry flaky SSH).
- Upgrade test before every release: new exe + an OLD `database.db` in a folder
  with Chinese characters and spaces → launch → `再新洗車資料/洗車資料.db` exists,
  row counts and totals unchanged, `自動備份/` created.
- Users upgrade by replacing the exe; the old `database.db` is adopted automatically.

- Upload: `tar` WITHOUT `--exclude='*.db'` (the legacy fixtures are needed by the
  tests). cmd gotcha: `if exist X rmdir ... & mkdir ...` runs mkdir only inside the
  if — split it. Give scp an absolute `C:/Users/<user>/...` path.
- Release zip: make it on Windows with .NET `ZipFile.CreateFromDirectory(..., UTF8)`
  (Chinese exe name keeps the UTF-8 flag); deliver `dist/再新洗車資料庫_<version>.zip`.

## Manual screenshots (tools/make_manual.py) — run on Windows

- Offscreen Qt on Windows has NO system fonts unless told where they are:
  `$env:QT_QPA_PLATFORM="offscreen"; $env:QT_QPA_FONTDIR="C:\Windows\Fonts"`.
  The windows platform over SSH (session 0) works but its screen is 1024×768, so
  windows are squeezed — use offscreen + QT_QPA_FONTDIR (1280×900 pictures).
- Point the data dir env var at an EMPTY folder with a natural Chinese path
  (e.g. `C:\汽車保養資料庫\汽車保養資料`): the 備份/還原 picture shows it. Delete it after.
- Copy the PNGs back into the repo (they are committed) and build: the spec bundles
  `assets/manual`. Check a running exe: `%TEMP%\_MEI*\assets\manual` holds the files.
- VM automation: injected mouse/keys do nothing while the VM's desktop session is
  disconnected (PrintWindow still works). In PowerShell, `$null` passed to a string
  parameter becomes "" — use `[NullString]::Value` (e.g. `FindWindow`).

## Release zip (owner rule, 2026-11-25)

`build_exe.bat` ends with `tools/make_release.py`, which writes
`dist/<APP_NAME>_<APP_VERSION>.zip` = ONE folder `<APP_NAME>_<APP_VERSION>/` with exactly
two files: the exe and `使用說明書.html` (the in-app manual as a single file, pictures
embedded as data URIs, opens in any browser). It verifies the zip and fails the build
otherwise; Python's zipfile sets the UTF-8 flag for the Chinese names. Deliver that
zip as built — do not hand-pack zips in PowerShell any more (older notes above).
`test_release_zip_is_one_folder_with_exe_and_manual` guards the layout.
