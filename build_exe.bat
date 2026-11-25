@echo off
cd /d %~dp0
echo === Install build requirements ===
python -m pip install -r requirements.txt || goto :error
echo === Run tests ===
python -m pytest -q -p no:cacheprovider tests || goto :error
echo === Make icon ===
python tools\make_icon.py || goto :error
echo === Build exe ===
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
python -m PyInstaller --noconfirm new_again_db.spec || goto :error
echo === Pack release zip (exe + manual) ===
python tools\make_release.py || goto :error
echo.
echo Build OK. The exe and the release zip are in the dist folder.
exit /b 0
:error
echo BUILD FAILED
exit /b 1
