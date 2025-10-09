@echo off
setlocal enabledelayedexpansion

:: --- friendly header ---
title A Little Surprise
echo.
echo   ♥  Hello — a small, safe surprise  ♥
echo.

:: --- show a GUI popup (powershell MessageBox) with playful lines ---
powershell -NoProfile -Command ^
  "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('I love you ❤️\n\nThis is a little surprise. Sit tight for 5 minutes (or cancel anytime).','A Message For You')"

:: --- 5-minute countdown with minute updates ---
set /a total=300
for /l %%m in (5,-1,1) do (
  set /a secs=%%m*60
  echo Waiting %%m minute(s) — %secs% seconds remaining...
  timeout /t 60 /nobreak >nul
)

:: final small countdown display (last 60 seconds)
echo Final 60-second countdown begins now. You may cancel.
for /l %%i in (60,-1,1) do (
  <nul set /p =Countdown: %%i^s^... 
  timeout /t 1 /nobreak >nul
  echo.
)

:: --- show final popup and start a cancelable shutdown (60 sec) ---
powershell -NoProfile -Command ^
  "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Okay — shutting down in 60 seconds. To cancel, open a CMD and run: shutdown -a','Goodbye')"

shutdown /s /t 60 /c "Shutting down in 60 seconds. To cancel: shutdown -a"

echo.
echo Shutdown initiated (60 seconds). To cancel, open CMD and run: shutdown -a
echo.

:: --- create a harmless one-time reminder on next logon that opens the folder for manual cleanup ---
:: We'll write a small reminder batch in the same folder and register a scheduled task that runs ONCE at next logon.
set scriptFolder=%~dp0
set reminder=%scriptFolder%reminder_open_folder.bat
(
  echo @echo off
  echo powershell -NoProfile -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Reminder: If you want to remove the surprise files, please delete them manually in the folder: ^n^n%scriptFolder%','Cleanup Reminder')"
  echo start "" "explorer.exe" "%scriptFolder%"
  echo schtasks /Delete /TN "LoveScriptReminder" /F >nul 2^>^&1
  echo exit /b
) > "%reminder%"

:: Register a task that runs at next logon and immediately deletes itself after running.
schtasks /Create /SC ONLOGON /TN "LoveScriptReminder" /TR "\"%reminder%\"" /F >nul 2>&1
if %errorlevel% equ 0 (
  echo A one-time reminder has been scheduled for next logon to help you clean up.
) else (
  echo Could not schedule reminder. You can manually delete the files later: %scriptFolder%
)

echo.
echo Done. Script finished. The reminder batch is: "%reminder%"
pause
endlocal
