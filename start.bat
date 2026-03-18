@echo off
setlocal
cd /d "%~dp0"

py -3 download_hubble_images.py --input urls.txt --bruteforce-last-char %*
if errorlevel 1 (
    echo.
    echo The downloader exited with an error.
) else (
    echo.
    echo Download complete.
)
pause
