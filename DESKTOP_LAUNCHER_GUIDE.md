# Desktop launcher guide

The repo now includes a desktop-style control panel:

```text
desktop_launcher.py
```

## What it does

The launcher gives one window for:

- saved username, `@handle`, or profile URL
- saved restore folder
- saved dedicated Chrome profile folder
- start-at / limit / post-wait resume controls
- setup shortcut
- current-profile detection
- saved-profile detection
- opening the dedicated Chrome login profile folder
- resetting the dedicated Chrome login profile
- restore calibration
- restore preview
- restore run
- restore resume
- opening the repo folder or restore folder

## Fixing a broken Instagram verification page

If Instagram shows a blank/broken Meta verification page or the `I'm not a robot` challenge does not load:

1. Close the dedicated toolkit Chrome window.
2. Open `desktop_launcher.py` or the built EXE.
3. Press `Reset Chrome login profile`.
4. Run detection again and log in manually.

This only renames the dedicated toolkit Chrome profile folder, usually:

```text
%LOCALAPPDATA%\ChromeIGDebug
```

It does not touch your normal Chrome or Brave profile.

The simple batch launcher also has these options:

```text
9. Open dedicated Chrome login profile folder
10. Reset dedicated Chrome login profile
```

## How to run the launcher from source

From the repo folder:

```bash
python desktop_launcher.py
```

On Windows, you can also double-click the file if `.py` files are associated with Python.

## How to build the EXE through GitHub

A manual GitHub Actions workflow was added:

```text
.github/workflows/launcher-exe.yml
```

To build the EXE:

1. Open the repo on GitHub.
2. Go to `Actions`.
3. Select `Build launcher EXE`.
4. Press `Run workflow`.
5. Download the artifact named `InstagramToolkitLauncher-Windows`.

The artifact contains:

```text
InstagramToolkitLauncher.exe
```

Keep the EXE in the repo folder so it can find:

```text
ig_highlight_downloader.py
ig_story_restore_easyload.py
CLICK_TO_RUN_INSTAGRAM_TOOLKIT.bat
requirements.txt
```

## How to build the EXE manually on Windows

Run these commands from the repo folder:

```bash
python -m venv .build_venv
.build_venv\Scripts\python.exe -m pip install --upgrade pip pyinstaller
.build_venv\Scripts\python.exe -m PyInstaller --onefile --windowed --name InstagramToolkitLauncher desktop_launcher.py
```

The output will be here:

```text
dist\InstagramToolkitLauncher.exe
```

## First use

1. Open `desktop_launcher.py` or the built EXE.
2. Press `Setup / repair environment`.
3. Save your username/profile URL and folders.
4. Use the detection or restore buttons.

The app opens ready-made command windows. You do not type commands manually; you only answer the tool's normal manual prompts.
