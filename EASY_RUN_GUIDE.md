# Easy run guide

This is the simple way to use the toolkit on Windows without typing Python commands into Command Prompt.

## Main way to run

Double-click this file from the repo root:

```text
CLICK_TO_RUN_INSTAGRAM_TOOLKIT.bat
```

The launcher gives you a menu for setup, highlight detection, restore calibration, restore preview, normal restore, and resume.

## First-time setup

1. Double-click `CLICK_TO_RUN_INSTAGRAM_TOOLKIT.bat`.
2. Choose `1. Setup / update dependencies`.
3. Wait for the installer output to finish.
4. Return to the launcher menu.

The setup creates `.venv`, installs `requirements.txt`, and installs Playwright Chromium support. The `.venv` folder stays local and is ignored by Git.

## Downloader / highlight detection

Use this when you want the tool to open/connect to the dedicated Chrome profile and detect highlight links.

### Use the Instagram profile already open in Chrome

Choose:

```text
2. Downloader: detect highlights from the current Instagram profile
```

Then follow the prompts. Login is manual in the Chrome window.

### Open a specific profile

Choose:

```text
3. Downloader: open a username or profile URL, then detect highlights
```

You can enter any of these forms:

```text
username
@username
https://www.instagram.com/username/
```

## Restore / uploader helper

Use this when you already have ordered story media in a local folder and want to step through the EasyLoad/Insta Uploader extension flow.

### Calibrate first

Choose:

```text
4. Restore: calibrate EasyLoad/Insta Uploader buttons
```

The tool asks you to hover over the center of each button, then press Enter. It saves local calibration files that are ignored by Git.

### Preview before restoring

Choose:

```text
5. Restore: choose folder and preview order only
```

This opens a folder picker, lists the restore order, and clicks nothing.

### Run the restore flow

Choose:

```text
6. Restore: choose folder and run
```

Keep the EasyLoad/Insta Uploader page in front before the run starts.

Emergency stop options:

- Move the mouse to the top-left corner.
- Press `Ctrl+C` in the launcher window.

### Resume a partial restore

Choose:

```text
7. Restore: resume from a specific item
```

Enter the starting item number. You can also set a limit if you only want to process a few files.

## What still stays manual

- Instagram login
- Security checks
- CAPTCHA or verification prompts
- Choosing the correct profile/account/page
- Making sure you own or have permission to handle the content

## Old command-line method

The Python scripts still work directly if needed:

```bash
python ig_highlight_downloader.py
python ig_highlight_downloader.py --profile username
python ig_story_restore_easyload.py --calibrate
python ig_story_restore_easyload.py --choose-folder
python ig_story_restore_easyload.py --choose-folder --dry-run
```
