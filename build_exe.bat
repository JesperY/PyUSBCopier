@echo off
echo Cleaning up old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist USBBackup.spec del USBBackup.spec

echo Checking for icon file...
if not exist src\resources mkdir src\resources

echo Icon file check completed.

echo Creating PyInstaller spec file...
pyinstaller --name=USBBackup --clean --windowed --icon=src\resources\icon.ico --hidden-import=PyQt6 --hidden-import=PyQt6.QtCore --hidden-import=PyQt6.QtGui --hidden-import=PyQt6.QtWidgets --add-data "src\resources;src\resources" --hidden-import=win32api --hidden-import=win32file src\main.py

echo Building executable...
pyinstaller USBBackup.spec

echo Build complete. Executable is in dist folder.

echo.
if %ERRORLEVEL% EQU 0 (
    echo Build completed successfully!
    echo Application executable is located at: dist\USBBackup.exe
) else (
    echo Build failed with error code %ERRORLEVEL%
)

echo.
