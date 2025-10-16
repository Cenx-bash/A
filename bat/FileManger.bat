@echo off
setlocal enabledelayedexpansion

:: -----------------------
:: FileGarden - Simple, auditable batch file manager
:: - Safe backups are stored in a visible folder FileGarden_Backup
:: - Actions logged in FileGarden_Log.txt
:: - Type "banana" at prompt to view the action log
:: -----------------------

:: Configuration (change if you want)
set "ROOT=%~dp0"
set "BACKUP_DIR=%ROOT%FileGarden_Backup"
set "LOG_FILE=%ROOT%FileGarden_Log.txt"
set "CLIP_FILE=%ROOT%FileGarden_clip.txt"

:: Ensure backup folder and log exist
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
if not exist "%LOG_FILE%" echo [FileGarden log created on %date% %time%] > "%LOG_FILE%"

:: Clipboard-like variables (for copy/paste)
set "CLIP_MODE="   :: "COPY" or "CUT"
set "CLIP_SRC="

:: Helpers
:Log
rem usage: call :Log action file
set "timestamp=%date% %time%"
echo [%timestamp%] %~1 %~2 >> "%LOG_FILE%"
goto :eof

:MakeBackup
rem usage: call :MakeBackup fullpath
set "src=%~1"
if exist "%src%" (
  set "fname=%~nx1"
  set "ts=%date:~10,4%-%date:~4,2%-%date:~7,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%"
  rem sanitize spaces in timestamp for filename
  set "ts=!ts: =_!"
  set "dest=%BACKUP_DIR%\!ts!_!fname!"
  copy /Y "%src%" "%dest%" >nul 2>&1
  if exist "%dest%" (
    call :Log "BACKUP_CREATED" "%dest%"
  ) else (
    call :Log "BACKUP_FAILED" "%src%"
  )
) else (
  echo File not found to backup: "%src%"
)
goto :eof

:ListDir
set "cdpath=%~1"
if "%cdpath%"=="" set "cdpath=."
echo.
echo Directory: %cdpath%
echo -------------------------
dir "%cdpath%" /A:-D /B
echo -------------------------
goto :eof

:ShowHelp
echo.
echo FileGarden - commands:
echo   ls                 - list files in current folder
echo   cd <folder>        - change directory
echo   copy <file>        - stage a file for copy
echo   cut <file>         - stage a file for move (cut)
echo   paste              - paste the staged file into current folder
echo   copyto <file> <dest> - immediate copy file to dest (and backup)
echo   move <file> <dest> - immediate move file to dest (and backup)
echo   del <file>         - delete file (creates backup first)
echo   rename <old> <new> - rename file (creates backup first)
echo   edit <file>        - open file in Notepad (backs it up before editing)
echo   log                - show action log
echo   banana             - show action log (alias)
echo   help               - show this help
echo   exit               - quit FileGarden
echo.
goto :eof

:: Start in script folder
pushd "%ROOT%" >nul 2>&1
:MainLoop
set /p "cmd=FileGarden:%CD%> "
if /i "%cmd%"=="" goto :MainLoop

:: Allow quick banana to show log
if /i "%cmd%"=="banana" goto :ShowLog

for /f "tokens=1* delims= " %%A in ("%cmd%") do (
  set "verb=%%A"
  set "rest=%%B"
)

:: Process commands
if /i "%verb%"=="help" goto :ShowHelp
if /i "%verb%"=="ls" (
  call :ListDir "%CD%"
  goto :MainLoop
)
if /i "%verb%"=="cd" (
  if "%rest%"=="" (
    echo Current: %CD%
  ) else (
    pushd "%rest%" 2>nul || (echo Cannot change to "%rest%")
  )
  goto :MainLoop
)
if /i "%verb%"=="copy" (
  if "%rest%"=="" (echo Usage: copy filename & goto :MainLoop)
  if exist "%rest%" (
    set "CLIP_MODE=COPY"
    for %%F in ("%rest%") do set "CLIP_SRC=%%~fF"
    echo Staged for copy: %CLIP_SRC%
  ) else echo File not found: "%rest%"
  goto :MainLoop
)
if /i "%verb%"=="cut" (
  if "%rest%"=="" (echo Usage: cut filename & goto :MainLoop)
  if exist "%rest%" (
    set "CLIP_MODE=CUT"
    for %%F in ("%rest%") do set "CLIP_SRC=%%~fF"
    echo Staged for move (cut): %CLIP_SRC%
  ) else echo File not found: "%rest%"
  goto :MainLoop
)
if /i "%verb%"=="paste" (
  if "%CLIP_MODE%"=="" (echo Nothing is staged. Use copy or cut first.& goto :MainLoop)
  if "%CLIP_SRC%"=="" (echo Staged source missing.& goto :MainLoop)
  rem compute destination filename (same name in current dir)
  for %%F in ("%CLIP_SRC%") do set "SRCNAME=%%~nxF"
  set "DEST=%CD%\%SRCNAME%"
  rem backup original file before overwriting/pasting
  if exist "%DEST%" (
    call :MakeBackup "%DEST%"
  )
  rem for CUT: move; for COPY: copy
  if /i "%CLIP_MODE%"=="CUT" (
    rem backup the source before moving
    call :MakeBackup "%CLIP_SRC%"
    move /Y "%CLIP_SRC%" "%DEST%" >nul 2>&1
    if exist "%DEST%" (
      echo Moved "%CLIP_SRC%" -> "%DEST%"
      call :Log "MOVE" "%CLIP_SRC% -> %DEST%"
    ) else (
      echo Move failed.
    )
  ) else (
    copy /Y "%CLIP_SRC%" "%DEST%" >nul 2>&1
    if exist "%DEST%" (
      echo Copied "%CLIP_SRC%" -> "%DEST%"
      call :Log "COPY" "%CLIP_SRC% -> %DEST%"
      rem also create backup of the source (so we have an original snapshot)
      call :MakeBackup "%CLIP_SRC%"
    ) else (
      echo Copy failed.
    )
  )
  rem clear clipboard staging for CUT (so you can't accidentally reuse)
  if /i "%CLIP_MODE%"=="CUT" set "CLIP_MODE=" & set "CLIP_SRC="
  goto :MainLoop
)

if /i "%verb%"=="copyto" (
  rem syntax: copyto source dest
  for /f "tokens=1,2*" %%X in ("%rest%") do (
    set "srcFile=%%X"
    set "destPath=%%Y%%Z"
  )
  if "%srcFile%"=="" (echo Usage: copyto source dest & goto :MainLoop)
  if not exist "%srcFile%" (echo Source not found: "%srcFile%" & goto :MainLoop)
  rem ensure dest directory exists
  for %%D in ("%destPath%") do set "destDir=%%~dpD"
  if not exist "%destDir%" mkdir "%destDir%"
  rem backup destination if exists
  if exist "%destPath%" call :MakeBackup "%destPath%"
  copy /Y "%srcFile%" "%destPath%" >nul 2>&1
  if exist "%destPath%" (
    echo Copied "%srcFile%" -> "%destPath%"
    call :Log "COPYTO" "%srcFile% -> %destPath%"
    call :MakeBackup "%srcFile%"
  ) else echo Copy failed.
  goto :MainLoop
)

if /i "%verb%"=="move" (
  rem syntax: move source dest
  for /f "tokens=1,2*" %%X in ("%rest%") do (
    set "srcFile=%%X"
    set "destPath=%%Y%%Z"
  )
  if "%srcFile%"=="" (echo Usage: move source dest & goto :MainLoop)
  if not exist "%srcFile%" (echo Source not found: "%srcFile%" & goto :MainLoop)
  for %%D in ("%destPath%") do set "destDir=%%~dpD"
  if not exist "%destDir%" mkdir "%destDir%"
  call :MakeBackup "%srcFile%"
  move /Y "%srcFile%" "%destPath%" >nul 2>&1
  if exist "%destPath%" (
    echo Moved "%srcFile%" -> "%destPath%"
    call :Log "MOVE" "%srcFile% -> %destPath%"
  ) else echo Move failed.
  goto :MainLoop
)

if /i "%verb%"=="del" (
  if "%rest%"=="" (echo Usage: del filename & goto :MainLoop)
  if exist "%rest%" (
    call :MakeBackup "%rest%"
    del /F /Q "%rest%" >nul 2>&1
    if not exist "%rest%" (
      echo Deleted "%rest%"
      call :Log "DELETE" "%rest%"
    ) else (
      echo Deletion failed: "%rest%"
    )
  ) else echo File not found: "%rest%"
  goto :MainLoop
)

if /i "%verb%"=="rename" (
  rem usage: rename oldname newname
  for /f "tokens=1,2*" %%X in ("%rest%") do (
    set "old=%%X"
    set "new=%%Y%%Z"
  )
  if "%old%"=="" (echo Usage: rename oldname newname & goto :MainLoop)
  if not exist "%old%" (echo File not found: "%old%" & goto :MainLoop)
  call :MakeBackup "%old%"
  ren "%old%" "%new%" >nul 2>&1
  if exist "%new%" (
    echo Renamed "%old%" -> "%new%"
    call :Log "RENAME" "%old% -> %new%"
  ) else echo Rename failed.
  goto :MainLoop
)

if /i "%verb%"=="edit" (
  if "%rest%"=="" (echo Usage: edit filename & goto :MainLoop)
  if exist "%rest%" (
    call :MakeBackup "%rest%"
    start "" notepad "%rest%"
    call :Log "EDIT" "%rest%"
  ) else (
    echo File not found: "%rest%"
  )
  goto :MainLoop
)

if /i "%verb%"=="log" (
  type "%LOG_FILE%"
  goto :MainLoop
)

if /i "%verb%"=="exit" (
  popd >nul 2>&1
  echo Goodbye.
  goto :EOF
)

echo Unknown command: %verb%. Type help for a list of commands.
goto :MainLoop
