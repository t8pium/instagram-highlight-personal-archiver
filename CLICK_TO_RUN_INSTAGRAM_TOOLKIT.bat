@echo off
setlocal EnableExtensions EnableDelayedExpansion

title Instagram Highlight Toolkit - Easy Launcher
cd /d "%~dp0"

set "VENV_DIR=%CD%\.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "SETUP_MARKER=%VENV_DIR%\.instagram_toolkit_setup_done"
set "CHROME_PROFILE_DIR=%LOCALAPPDATA%\ChromeIGDebug"

:menu
cls
echo ============================================================
echo  Instagram Highlight Personal Archiver - Easy Launcher
echo ============================================================
echo.
echo  This menu runs the existing Python tools for you.
echo  Login stays manual. Use only content you own or have permission to handle.
echo.
echo  1. Setup / update dependencies
echo  2. Archive highlights from the current Instagram profile
echo  3. Archive highlights from a username or profile URL
echo  4. Restore: calibrate EasyLoad/Insta Uploader buttons
echo  5. Restore: choose folder and preview order only
echo  6. Restore: choose folder and run
echo  7. Restore: resume from a specific item
echo  8. Open the easy run guide
echo  9. Open dedicated Chrome login profile folder
echo  10. Reset dedicated Chrome login profile
echo  11. Open login-only Chrome ^(no automation^)
echo  0. Exit
echo.
set /p ACTION=Choose an option: 

if "%ACTION%"=="1" goto do_setup
if "%ACTION%"=="2" goto downloader_current
if "%ACTION%"=="3" goto downloader_profile
if "%ACTION%"=="4" goto restore_calibrate
if "%ACTION%"=="5" goto restore_preview
if "%ACTION%"=="6" goto restore_run
if "%ACTION%"=="7" goto restore_resume
if "%ACTION%"=="8" goto open_guide
if "%ACTION%"=="9" goto open_chrome_profile
if "%ACTION%"=="10" goto reset_chrome_profile
if "%ACTION%"=="11" goto open_login_only_chrome
if "%ACTION%"=="0" goto exit_launcher

echo.
echo Unknown option.
pause
goto menu

:do_setup
call :setup
goto after_action

:downloader_current
call :ensure_setup || goto after_action
echo.
echo Starting highlight archive. A dedicated Chrome profile may open.
echo Log in manually if needed, then follow the prompts in this window.
echo Output folder: %CD%\downloads
echo.
echo Running command:
echo "%VENV_PY%" "ig_highlight_downloader.py" --chrome-user-data-dir "%CHROME_PROFILE_DIR%" --archive --output "downloads"
echo.
"%VENV_PY%" "ig_highlight_downloader.py" --chrome-user-data-dir "%CHROME_PROFILE_DIR%" --archive --output "downloads"
set "LAST_EXIT=%ERRORLEVEL%"
echo.
echo Archive command finished with exit code: %LAST_EXIT%
if not "%LAST_EXIT%"=="0" echo If this failed, copy the error text above and send it to ChatGPT.
goto after_action

:downloader_profile
call :ensure_setup || goto after_action
echo.
set /p PROFILE=Enter Instagram username, @handle, or full profile URL: 
if "%PROFILE%"=="" goto menu
echo.
echo Output folder: %CD%\downloads
echo Running command:
echo "%VENV_PY%" "ig_highlight_downloader.py" --chrome-user-data-dir "%CHROME_PROFILE_DIR%" --profile "%PROFILE%" --archive --output "downloads"
echo.
"%VENV_PY%" "ig_highlight_downloader.py" --chrome-user-data-dir "%CHROME_PROFILE_DIR%" --profile "%PROFILE%" --archive --output "downloads"
set "LAST_EXIT=%ERRORLEVEL%"
echo.
echo Archive command finished with exit code: %LAST_EXIT%
if not "%LAST_EXIT%"=="0" echo If this failed, copy the error text above and send it to ChatGPT.
goto after_action

:restore_calibrate
call :ensure_setup || goto after_action
echo.
echo Open the EasyLoad/Insta Uploader extension page before calibrating.
echo You will hover over each button and press Enter when asked.
echo.
"%VENV_PY%" "ig_story_restore_easyload.py" --calibrate
goto after_action

:restore_preview
call :ensure_setup || goto after_action
echo.
echo Choose the folder. This only previews order and clicks nothing.
echo.
"%VENV_PY%" "ig_story_restore_easyload.py" --choose-folder --dry-run
goto after_action

:restore_run
call :ensure_setup || goto after_action
echo.
echo Choose the ordered story folder. Keep the uploader page in front when the run starts.
echo Emergency stop: move the mouse to the top-left corner or press Ctrl+C.
echo.
"%VENV_PY%" "ig_story_restore_easyload.py" --choose-folder
goto after_action

:restore_resume
call :ensure_setup || goto after_action
echo.
set /p START_AT=Start at item number ^(default 1^): 
if "%START_AT%"=="" set "START_AT=1"
set /p LIMIT=Limit how many files ^(blank for no limit^): 
set "LIMIT_ARG="
if not "%LIMIT%"=="" set "LIMIT_ARG=--limit %LIMIT%"
echo.
"%VENV_PY%" "ig_story_restore_easyload.py" --choose-folder --start-at "%START_AT%" %LIMIT_ARG%
goto after_action

:open_guide
if exist "EASY_RUN_GUIDE.md" (
  start "" "EASY_RUN_GUIDE.md"
) else (
  echo EASY_RUN_GUIDE.md was not found.
)
goto after_action

:open_chrome_profile
if not exist "%CHROME_PROFILE_DIR%" mkdir "%CHROME_PROFILE_DIR%"
start "" "%CHROME_PROFILE_DIR%"
goto after_action

:reset_chrome_profile
echo.
echo Close the dedicated toolkit Chrome window before continuing.
echo This only resets this isolated folder:
echo   %CHROME_PROFILE_DIR%
echo It does NOT touch your normal Chrome or Brave data.
echo.
if not exist "%CHROME_PROFILE_DIR%" (
  echo Nothing to reset. The folder does not exist yet.
  goto after_action
)
set /p CONFIRM=Type RESET and press Enter to rename this profile folder: 
if /i not "%CONFIRM%"=="RESET" (
  echo Cancelled.
  goto after_action
)
set "BACKUP_DIR=%CHROME_PROFILE_DIR%_old_%RANDOM%%RANDOM%"
for %%F in ("%BACKUP_DIR%") do set "BACKUP_NAME=%%~nxF"
ren "%CHROME_PROFILE_DIR%" "!BACKUP_NAME!" 2>nul
if errorlevel 1 (
  echo.
  echo Could not reset. Chrome is probably still using the folder.
  echo Close the toolkit Chrome window and try again.
  goto after_action
)
echo.
echo Reset complete. Old folder renamed to:
echo   %BACKUP_DIR%
echo.
echo Next recommended step: choose option 11 and log in without automation.
goto after_action

:open_login_only_chrome
call :find_chrome || goto after_action
if not exist "%CHROME_PROFILE_DIR%" mkdir "%CHROME_PROFILE_DIR%"
echo.
echo Opening normal Chrome with the same dedicated profile, but without automation/debug mode.
echo Log in manually. After Instagram is fully logged in, close Chrome and run option 2 or 3.
echo.
start "" "%CHROME_EXE%" --user-data-dir="%CHROME_PROFILE_DIR%" --no-first-run --no-default-browser-check "https://www.instagram.com/"
goto after_action

:find_chrome
set "CHROME_EXE="
if exist "%PROGRAMFILES%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"
if not defined CHROME_EXE if exist "%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"
if not defined CHROME_EXE if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
if not defined CHROME_EXE for /f "delims=" %%C in ('where chrome 2^>nul') do (
  set "CHROME_EXE=%%C"
  goto found_chrome
)
:found_chrome
if not defined CHROME_EXE (
  echo Could not find Google Chrome. Install Chrome and try again.
  exit /b 1
)
exit /b 0

:after_action
echo.
echo ------------------------------------------------------------
echo Done. Review the output above for any errors or next steps.
echo ------------------------------------------------------------
pause
goto menu

:ensure_setup
if not exist "%VENV_PY%" (
  call :setup || exit /b 1
)
if not exist "%SETUP_MARKER%" (
  call :setup || exit /b 1
)
exit /b 0

:setup
echo.
echo Checking local Python environment...

if not exist "%VENV_PY%" (
  call :create_venv || exit /b 1
)

if not exist "%VENV_PY%" (
  echo Virtual environment Python was not found at:
  echo %VENV_PY%
  exit /b 1
)

echo.
echo Installing/updating Python packages...
"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 exit /b 1

"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo.
echo Installing Playwright Chromium support...
"%VENV_PY%" -m playwright install chromium
if errorlevel 1 exit /b 1

> "%SETUP_MARKER%" echo setup complete

echo.
echo Setup complete.
exit /b 0

:create_venv
where py >nul 2>&1
if not errorlevel 1 (
  echo Creating virtual environment with Python launcher...
  py -3 -m venv "%VENV_DIR%"
  if errorlevel 1 exit /b 1
  exit /b 0
)

set "BASE_PY="
for /f "delims=" %%P in ('where python 2^>nul') do (
  set "BASE_PY=%%P"
  goto create_venv_with_python
)

echo.
echo Could not find Python.
echo Install Python 3.10+ from python.org, then run this file again.
exit /b 1

:create_venv_with_python
echo Creating virtual environment with: !BASE_PY!
"!BASE_PY!" -m venv "%VENV_DIR%"
if errorlevel 1 exit /b 1
exit /b 0

:exit_launcher
endlocal
exit /b 0
