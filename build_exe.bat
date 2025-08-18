@echo off
echo Building new_again_db executable...
echo.

REM Remove existing dist directory
if exist dist rmdir /s /q dist

REM Build the executable
pyinstaller new_again_db.spec

echo.
echo Build completed successfully!
echo Executable location: dist\new_again_db.exe
echo.

pause