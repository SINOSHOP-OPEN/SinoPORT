@echo off
setlocal
cd /d "%~dp0"

set "FCEXE=%LOCALAPPDATA%\Programs\FreeCAD 1.1\bin\freecadcmd.exe"
set "SCRIPT=src\model\build_pyramid_r6.py"

echo ============================================================
echo   SinoPORT  FILMING RUN  -  FreeCAD live build
echo ============================================================
echo.

if not exist "%FCEXE%" goto NOFCAE

if not exist "%SCRIPT%" goto NOSCRIPT

echo   exe    : %FCEXE%
echo   script : %SCRIPT%
echo.
echo ------------------------------------------------------------
echo   HOW TO CUT  --  READ BEFORE PRESSING ANY KEY
echo.
echo   Watch the screen. When this exact line shows up:
echo.
echo       building foam ...
echo.
echo   press  Ctrl+C  IMMEDIATELY.
echo   cmd then asks:  Terminate batch job  Y/N
echo   type  Y  and press ENTER.
echo.
echo   WHY: at that moment all 15 PASS lines are already done.
echo   Running further costs about 9 min 41 s with no new output.
echo ------------------------------------------------------------
echo.

"%FCEXE%" "%SCRIPT%"

echo.
echo === run ended ===
goto END

:NOSCRIPT
echo   ERROR: script not found
echo      %SCRIPT%
goto END

:NOFCAE
echo   ERROR: FreeCAD not found at
echo      %FCEXE%
echo   Fix the path in this file, then double click again.
goto END

:END
endlocal
