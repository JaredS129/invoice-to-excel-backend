@echo off
echo Building Invoice Processing API executable...

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Run PyInstaller
python -m PyInstaller invoice-api.spec --clean

echo.
echo Build complete! Executable located at: dist\invoice-api.exe
