# Instagram Highlight Personal Archiver

A local Python toolkit for backing up and restoring Instagram highlight/story media that I own or have permission to handle.

It uses a dedicated Chrome profile, manual authentication, Playwright, and desktop automation. Passwords, cookies, browser sessions, downloaded media, and other local data are intentionally excluded from the repository.

## Quick start — Windows

From the repository root, double-click:

```text
CLICK_TO_RUN_INSTAGRAM_TOOLKIT.bat
```

The launcher can set up dependencies, detect highlights, calibrate restore controls, preview restore order, run a restore, and resume from a selected item.

For step-by-step instructions, see [`EASY_RUN_GUIDE.md`](EASY_RUN_GUIDE.md).

## What it does

### Highlight archive workflow

`ig_highlight_downloader.py`

- Opens or connects to a dedicated Chrome profile.
- Keeps Instagram login manual.
- Validates the current Instagram profile page.
- Detects highlight links from the selected profile.
- Keeps browser/session data and downloaded media outside Git.

### Story restore workflow

`ig_story_restore_easyload.py`

- Selects an ordered local media folder.
- Restores files in numeric filename order.
- Uses calibrated screen-vision matching for browser-extension controls.
- Supports dry runs before performing clicks.
- Supports resume controls with `--start-at` and `--limit`.
- Keeps PyAutoGUI failsafe and manual fallback controls available.

## Manual setup

```bash
python -m venv .venv
```

Windows:

```bat
.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

## Common commands

Detect highlights from the current profile:

```bash
python ig_highlight_downloader.py
```

Open a specific profile first:

```bash
python ig_highlight_downloader.py --profile username
```

Calibrate restore controls:

```bash
python ig_story_restore_easyload.py --calibrate
```

Preview restore order:

```bash
python ig_story_restore_easyload.py --choose-folder --dry-run
```

Run the restore workflow:

```bash
python ig_story_restore_easyload.py --choose-folder
```

Resume from a later item:

```bash
python ig_story_restore_easyload.py --choose-folder --start-at 10 --limit 5
```

## Repository guide

| Path | Purpose |
|---|---|
| `CLICK_TO_RUN_INSTAGRAM_TOOLKIT.bat` | Windows launcher for the normal workflow |
| `EASY_RUN_GUIDE.md` | Plain-English usage guide |
| `ig_highlight_downloader.py` | Highlight/profile detection workflow |
| `ig_story_restore_easyload.py` | Ordered story restore helper |
| `requirements.txt` | Python dependencies |
| `.gitignore` | Excludes browser data, media, local configuration, and caches |
| `RESPONSIBLE_USE.md` | Intended-use and safety boundaries |

## Status

| Area | Status |
|---|---|
| Dedicated Chrome profile | Complete |
| Manual-login workflow | Complete |
| Highlight detection | Complete |
| Ordered restore | Complete |
| Vision-assisted calibration/clicks | Complete |
| Dry-run preview | Complete |
| Resume controls | Complete |
| Windows launcher | Complete |
| Official API/data-export integration | Not implemented |
| Packaged desktop application | Not implemented |

## Requirements

- Python 3.10+
- Google Chrome
- Playwright
- PyAutoGUI
- Pyperclip
- Pillow
- OpenCV Python

The restore side is primarily Windows-focused because it interacts with the desktop browser and Windows file-selection flow.

## Responsible use

This project does not automate Instagram login, verification, CAPTCHA handling, or account-security decisions. It is intended for local archival/restoration of content I control or have permission to use.

Instagram's official data-export tools remain the safest official route for downloading account data.

## Safety

- Do not commit downloaded media.
- Do not commit browser profiles, cookies, sessions, caches, or local storage.
- Do not commit local calibration/configuration data.
- Use dry-run mode before restoring a new folder.
- Keep the PyAutoGUI failsafe enabled.
- Stop the workflow if the browser UI no longer matches the calibrated controls.

## Tech stack

Python · Playwright · Chrome DevTools Protocol · PyAutoGUI · OpenCV · Pillow · Tkinter

## License

MIT
