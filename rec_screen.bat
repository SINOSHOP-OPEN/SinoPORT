@echo off
REM ============================================================
REM  SINOPORT screen recorder - ffmpeg gdigrab, 1080p60
REM
REM  Start: double click this file.
REM  Stop : press CTRL+C in this window, then answer Y.
REM
REM  Output: D:\SinoSir\SinoPORT\recordings
REM  D: free space re-checked 2026-10-19 17:25 = 9.3 GB (>= 8 GB
REM  red line F), so recording goes back to D:.
REM ============================================================
setlocal
set "OUTDIR=D:\SinoSir\SinoPORT\recordings"

if not exist "%OUTDIR%" mkdir "%OUTDIR%"
if errorlevel 1 goto NODIR

cd /d "%OUTDIR%"

REM safe timestamp YYYYMMDD_HHMMSS.  wmic is blacklisted on this
REM machine, so use PowerShell.  No colon in the file name.
set "TS="
for /f "usebackq delims=" %%a in (`powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"`) do set "TS=%%a"

if not defined TS set "TS=untitled"

echo ============================================================
echo   SINOPORT SCREEN RECORDER
echo ============================================================
echo.
echo   output dir : %OUTDIR%
echo   file name  : SINOPORT_take_%TS%.mp4
echo   resolution : 1920x1080
echo   frame rate : 60 fps
echo   codec      : h264 / yuv420p  crf 20
echo.
echo   THIS WINDOW KEEPS RECORDING.
echo   Run your demo in ANOTHER window.
echo   When finished, come back HERE and press CTRL+C, answer Y.
echo.
echo   Starting in 3 seconds...
echo.

ping -n 4 127.0.0.1 >nul

ffmpeg -hide_banner -f gdigrab -framerate 60 -i desktop -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p "SINOPORT_take_%TS%.mp4"

echo.
echo   Recording stopped.
goto END

:NODIR
echo   ERROR: cannot create output folder
echo      %OUTDIR%
echo   Check the drive, then retry.

:END
endlocal
