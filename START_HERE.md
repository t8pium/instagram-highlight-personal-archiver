# Start here

This repo has two tools, plus two easy run layers.

## Easiest normal method

Double-click this file from the repo root:

```text
CLICK_TO_RUN_INSTAGRAM_TOOLKIT.bat
```

Then choose:

```text
2. Archive highlights from the current Instagram profile
3. Archive highlights from a username or profile URL
```

Saved output goes under:

```text
downloads
```

## Desktop app-style launcher

The repo also has a GUI control panel:

```text
desktop_launcher.py
```

It has buttons for setup, highlight archiving, login-only Chrome, Chrome profile reset, calibration, preview, restore, and resume.

Full instructions are in [`DESKTOP_LAUNCHER_GUIDE.md`](DESKTOP_LAUNCHER_GUIDE.md).

## Manual command-line method

Detect only:

```bash
python ig_highlight_downloader.py
```

Archive current profile:

```bash
python ig_highlight_downloader.py --archive --output downloads
```

Archive a target profile:

```bash
python ig_highlight_downloader.py --profile username --archive --output downloads
```

Limit a test run:

```bash
python ig_highlight_downloader.py --profile username --archive --highlight-limit 1 --max-items-per-highlight 20
```

## Restore workflow

Calibrate first:

```bash
python ig_story_restore_easyload.py --calibrate
```

Then choose a folder:

```bash
python ig_story_restore_easyload.py --choose-folder
```

Preview without clicking anything:

```bash
python ig_story_restore_easyload.py --choose-folder --dry-run
```

## Notes

- Login is manual in Chrome.
- Keep local media, browser profiles, sessions, and output out of GitHub.
- Use this only for content you own or have permission to handle.
