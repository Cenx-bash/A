@echo off
setlocal enabledelayedexpansion

title A Little Surprise
echo.
echo   ♥  Hello — a small, safe surprise  ♥
echo.

:: Show initial message (use `n newline escape in PowerShell string)
powershell -NoProfile -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show(\"I love you ❤️`n`nThis is a little surprise. Sit tight for 5 minutes.\",\"A Message For You\")"

:: Total seconds for 5 minutes
set /a total=300

:: Minute-by-minute updates (5,4,3,2,1)
for /l %%m in (5,-1,1) do (
  set /a secs=%%m*60
  rem use delayed expansion to get the runtime value of secs
  echo Waiting %%m minute(s) — !secs! seconds remaining...
  timeout /t 60 /nobreak >nul
)

:: Final 60-second countdown (prints seconds left)
echo Final 60-second countdown begins now.
for /l %%i in (60,-1,1) do (
  <nul set /p ="Countdown: %%i s... "
  timeout /t 1 /nobreak >nul
  echo.
)

:: Pre-shutdown message (PowerShell string uses `n for newline)
powershell -NoProfile -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show(\"Okay — shutting down in 60 seconds.`n`nIf you need to cancel, run: shutdown -a\",\"Goodbye\")"

:: Initiate shutdown (60 seconds)
shutdown /s /t 60 /c "Shutting down in 60 seconds."

echo.
echo Shutdown initiated (60 seconds).
echo.

:: Build reminder script (one-time at next logon)
set "scriptFolder=%~dp0"
set "reminder=%scriptFolder%reminder_open_folder.bat"

(
  echo @echo off
  echo powershell -NoProfile -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show(\"Reminder: If you want to remove the surprise files, please delete them manually in the folder:`n`n%scriptFolder%\",\"Cleanup Reminder\")"
  echo start "" "explorer.exe" "%scriptFolder%"
  echo schtasks /Delete /TN "LoveScriptReminder" /F >nul 2^>^1
  echo exit /b
) > "%reminder%"

:: Create scheduled task to run reminder on next logon
schtasks /Create /SC ONLOGON /TN "LoveScriptReminder" /TR "\"%reminder%\"" /F >nul 2>&1
if %errorlevel% EQU 0 (
  echo A one-time reminder has been scheduled for next logon to help you clean up.
) else (
  echo Could not schedule reminder. You can manually delete the files later: %scriptFolder%
)

echo.
echo Done. Script finished. The reminder batch is: "%reminder%"
pause
endlocal
