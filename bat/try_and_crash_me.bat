@echo off
setlocal enabledelayedexpansion

:: Controlled Google opener
set /p count="How many times would you like to open Google? (max 50): "
if "%count%"=="" (
  echo No number entered. Exiting.
  goto :eof
)

rem ensure numeric
for /f "delims=0123456789" %%a in ("%count%") do (
  echo Invalid number entered. Please enter digits only.
  goto :eof
)

set /a num=%count% 2>nul
if %num% lss 1 (
  echo Enter a positive number.
  goto :eof
)
if %num% gtr 5000 (
  echo Requested number %num% exceeds safe limit (50). Aborting.
  goto :eof
)

echo Opening https://www.google.com %num% time(s). Press Ctrl+C to stop.
for /l %%i in (1,1,%num%) do (
  start "" "https://www.google.com"
  timeout /t 1 >nul
)

echo Done.
endlocal
