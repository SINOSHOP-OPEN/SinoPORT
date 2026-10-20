@echo off
REM ============================================================
REM  SINOPORT  burn subtitles onto recorded screen footage
REM
REM  Usage:
REM    A) put ONE raw mp4 in this folder, double click this file
REM    B) drag an mp4 onto this file
REM  Output: <input>_sub.mp4
REM
REM  Pure ASCII + CRLF. No chcp (it breaks cmd read offset).
REM ============================================================
setlocal
cd /d "%~dp0"

set "SRT=SINOPORT_demo.srt"
set "IN=%~1"

if not exist "%SRT%" goto NOSRT

if "%IN%"=="" goto PICK

if not exist "%IN%" goto NOIN

goto RUN

:PICK
set "IN="
for %%f in (*.mp4) do (
    echo %%f | find /i "_sub.mp4" >nul || set "IN=%%f"
)
if "%IN%"=="" goto NOMP4
goto RUN

:RUN
echo ============================================================
echo   SINOPORT SUBTITLE BURNER
echo ============================================================
echo.
echo   input    : %IN%
echo   subtitle : %SRT%
echo.
echo   Burning, please wait...
echo.

ffmpeg -hide_banner -y -i "%IN%" -vf "subtitles=%SRT%:force_style='FontName=Microsoft YaHei,FontSize=26,PrimaryColour=&H00FFFFFF,OutlineColour=&HC0000000,BorderStyle=3,Outline=3,Shadow=1,MarginV=44,Alignment=2'" -c:a copy "%IN:.mp4=_sub.mp4"

if errorlevel 1 goto FFERR

echo.
echo   DONE -> %IN:.mp4=_sub.mp4
goto END

:NOSRT
echo   ERROR: subtitle file not found  ->  %SRT%
goto END

:NOIN
echo   ERROR: input file not found  ->  %IN%
goto END

:NOMP4
echo   ERROR: no mp4 found in this folder.
echo   Put your recorded mp4 here, or drag it onto this file.
goto END

:FFERR
echo.
echo   ERROR: ffmpeg failed. Check the file name and retry.
goto END

:END
endlocal
