#!/usr/bin/env python3
"""Browser-assisted Instagram Story restoration through EasyLoad/Insta Uploader.

This local helper restores ordered story media through a normal browser
extension UI. It is intended for personal archival restoration of content you
own or have permission to publish. It does not automate login, verification,
CAPTCHA, account checks, or Instagram security decisions.

Typical flow per file:
1. Click Add to stories.
2. Paste the local file path into the Windows file picker.
3. Click Next.
4. Click Publish now.
5. Click OK.
6. Wait 60-70 seconds before the next file.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DEFAULT_SOURCE = "downloads"
CONFIG_FILE = "ig_story_restore_easyload_vision_config.json"
TEMPLATE_DIR = "ig_story_restore_easyload_templates"

SUPPORTED_EXTENSIONS = {
    ".mp4", ".mov", ".m4v", ".webm",
    ".jpg", ".jpeg", ".png", ".webp", ".gif",
    ".tif", ".tiff", ".heic", ".heif",
}

BUTTON_ORDER = ["add_to_stories", "next", "publish_now", "ok"]
BUTTON_LABELS = {
    "add_to_stories": "Add to stories",
    "next": "Next",
    "publish_now": "Publish now",
    "ok": "OK",
}


@dataclass
class ButtonResult:
    status: str
    method: str


def lazy_import_gui():
    try:
        import pyautogui  # type: ignore
        import pyperclip  # type: ignore
    except ImportError as exc:
        print("\nMissing dependency.")
        print("Install with:")
        print("  py -m pip install pyautogui pyperclip pillow opencv-python")
        raise SystemExit(1) from exc

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.08
    return pyautogui, pyperclip


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def config_path() -> Path:
    return script_dir() / CONFIG_FILE


def template_dir() -> Path:
    return script_dir() / TEMPLATE_DIR


def load_config() -> Dict:
    path = config_path()
    if not path.exists():
        return {"buttons": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"buttons": {}}


def save_config(config: Dict) -> None:
    config_path().write_text(json.dumps(config, indent=2), encoding="utf-8")


def parse_wait_range(value: str) -> Tuple[float, float]:
    value = str(value).strip()
    if not value:
        raise argparse.ArgumentTypeError("Wait value cannot be empty.")

    if "-" in value:
        left, right = value.split("-", 1)
    elif "," in value:
        left, right = value.split(",", 1)
    else:
        seconds = float(value)
        if seconds < 0:
            raise argparse.ArgumentTypeError("Wait value cannot be negative.")
        return seconds, seconds

    a = float(left.strip())
    b = float(right.strip())
    if a < 0 or b < 0:
        raise argparse.ArgumentTypeError("Wait value cannot be negative.")
    if b < a:
        a, b = b, a
    return a, b


def sleep_range(wait_range: Tuple[float, float], label: str) -> None:
    seconds = random.uniform(wait_range[0], wait_range[1])
    print(f"    {label}: {seconds:.1f}s")
    time.sleep(seconds)


def numeric_sort_key(path: Path):
    match = re.match(r"^\s*(\d+)", path.name)
    if match:
        return (0, int(match.group(1)), path.name.lower())
    return (1, 10**9, path.name.lower())


def collect_files(source: Path) -> List[Path]:
    if not source.exists():
        raise FileNotFoundError(f"Source folder does not exist: {source}")
    if not source.is_dir():
        raise NotADirectoryError(f"Source is not a folder: {source}")

    files = [
        path for path in source.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(files, key=numeric_sort_key)


def choose_source_folder(initial_dir: str = DEFAULT_SOURCE) -> Optional[Path]:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as exc:
        print("Could not open the folder picker because tkinter is unavailable.")
        print("Use --source instead, for example:")
        print(r'  py ig_story_restore_easyload.py --source "C:\path\to\folder"')
        print(f"Details: {exc}")
        return None

    initial_path = Path(initial_dir).expanduser()
    if not initial_path.exists():
        initial_path = Path.home()

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    selected = filedialog.askdirectory(
        title="Choose the ordered story folder to restore",
        initialdir=str(initial_path),
        mustexist=True,
    )
    root.destroy()

    return Path(selected) if selected else None


def apply_start_limit(files: List[Path], start_at: int, limit: Optional[int]) -> List[Path]:
    if start_at < 1:
        raise ValueError("--start-at is 1-based, so it must be 1 or higher.")
    selected = files[start_at - 1:]
    if limit is not None:
        selected = selected[:max(0, limit)]
    return selected


def print_order(files: List[Path], original_count: Optional[int] = None) -> None:
    total = original_count if original_count is not None else len(files)
    if not files:
        print("No supported files found.")
        return
    print(f"Restore order ({len(files)} selected / {total} total):")
    for index, path in enumerate(files, 1):
        print(f"  {index:03d}. {path.name}")


def clamp_region(left: int, top: int, width: int, height: int, screen_w: int, screen_h: int):
    left = max(0, min(left, screen_w - 1))
    top = max(0, min(top, screen_h - 1))
    width = max(1, min(width, screen_w - left))
    height = max(1, min(height, screen_h - top))
    return left, top, width, height


def calibrate_button(button_name: str, args, config: Dict) -> None:
    pyautogui, _ = lazy_import_gui()
    label = BUTTON_LABELS[button_name]

    print("\n" + "=" * 70)
    print(f"Calibrating: {label}")
    print("=" * 70)
    print(f"1. Put the EasyLoad/Insta Uploader page where '{label}' is visible.")
    print(f"2. Hover over the CENTER of the '{label}' button.")
    print("3. Press Enter here in the terminal.")
    input("> ")

    x, y = pyautogui.position()
    screen_w, screen_h = pyautogui.size()
    width = int(args.template_width)
    height = int(args.template_height)
    region = clamp_region(int(x - width / 2), int(y - height / 2), width, height, screen_w, screen_h)

    template_dir().mkdir(parents=True, exist_ok=True)
    template_path = template_dir() / f"{button_name}.png"
    screenshot = pyautogui.screenshot(region=region)
    screenshot.save(template_path)

    config.setdefault("buttons", {})[button_name] = {
        "label": label,
        "x": int(x),
        "y": int(y),
        "template": str(template_path),
        "template_width": width,
        "template_height": height,
    }
    save_config(config)
    print(f"Saved fallback coordinate: ({x}, {y})")
    print(f"Saved screen template: {template_path}")


def calibrate(args) -> None:
    config = load_config()
    if args.calibrate_button:
        buttons = [args.calibrate_button]
    elif args.calibrate_add_only:
        buttons = ["add_to_stories"]
    elif args.calibrate_next_only:
        buttons = ["next"]
    elif args.calibrate_publish_only:
        buttons = ["publish_now"]
    elif args.calibrate_ok_only:
        buttons = ["ok"]
    else:
        buttons = BUTTON_ORDER

    for button in buttons:
        calibrate_button(button, args, config)

    print("\nCalibration complete.")
    print(f"Config saved to: {config_path()}")


def get_button_config(config: Dict, button_name: str) -> Dict:
    button_cfg = config.get("buttons", {}).get(button_name)
    if not button_cfg:
        raise RuntimeError(
            f"Missing calibration for '{BUTTON_LABELS[button_name]}'. "
            f"Run: py {Path(sys.argv[0]).name} --calibrate"
        )
    return button_cfg


def locate_button(button_name: str, args, config: Dict):
    pyautogui, _ = lazy_import_gui()
    button_cfg = get_button_config(config, button_name)
    template_path = Path(button_cfg["template"])
    if not template_path.exists():
        raise RuntimeError(f"Template missing for '{BUTTON_LABELS[button_name]}': {template_path}")

    confidence = float(args.ok_confidence) if button_name == "ok" and args.ok_confidence else float(args.confidence)
    locate_kwargs = {"confidence": confidence, "grayscale": bool(args.grayscale)}

    if args.search_near_saved:
        x = int(button_cfg["x"])
        y = int(button_cfg["y"])
        screen_w, screen_h = pyautogui.size()
        region = clamp_region(
            x - int(args.search_radius_x),
            y - int(args.search_radius_y),
            int(args.search_radius_x) * 2,
            int(args.search_radius_y) * 2,
            screen_w,
            screen_h,
        )
        locate_kwargs["region"] = region

    try:
        return pyautogui.locateCenterOnScreen(str(template_path), **locate_kwargs)
    except Exception as exc:
        message = str(exc)
        exc_name = exc.__class__.__name__
        if "ImageNotFoundException" in exc_name or "Could not locate the image" in message or "highest confidence" in message:
            return None
        if "confidence" in message.lower() or "opencv" in message.lower():
            print("\nImage matching with confidence needs OpenCV.")
            print("Install with: py -m pip install opencv-python")
        raise


def click_saved_fallback(button_name: str, config: Dict) -> None:
    pyautogui, _ = lazy_import_gui()
    button_cfg = get_button_config(config, button_name)
    pyautogui.click(int(button_cfg["x"]), int(button_cfg["y"]))


def wait_for_button_and_click(button_name: str, args, config: Dict, timeout: float, reason: str) -> ButtonResult:
    pyautogui, _ = lazy_import_gui()
    label = BUTTON_LABELS[button_name]
    start = time.time()
    last_print = 0.0

    print(f"    waiting for '{label}' ({reason})...")

    while True:
        if time.time() - start > timeout:
            print(f"\nCould not find '{label}' after {timeout:.0f}s.")
            if args.non_interactive:
                return ButtonResult("quit", "timeout")

            print("Options:")
            print("  Enter = scan again")
            print("  f     = click saved fallback coordinate")
            print("  m     = I clicked it manually; continue")
            print("  s     = skip this file")
            print("  q     = quit")
            choice = input("> ").strip().lower()

            if choice == "":
                start = time.time()
                continue
            if choice == "f":
                click_saved_fallback(button_name, config)
                return ButtonResult("clicked", "fallback")
            if choice == "m":
                return ButtonResult("clicked", "manual")
            if choice == "s":
                return ButtonResult("skip", "manual")
            if choice == "q":
                return ButtonResult("quit", "manual")
            print("Unknown choice.")
            continue

        center = locate_button(button_name, args, config)
        if center:
            pyautogui.click(center.x, center.y)
            print(f"    clicked '{label}' via screen match at ({center.x}, {center.y})")
            return ButtonResult("clicked", "vision")

        now = time.time()
        if now - last_print > 5:
            print(f"      still scanning... {now - start:.0f}s")
            last_print = now
        time.sleep(float(args.scan_interval))


def paste_file_into_dialog(file_path: Path, args) -> None:
    pyautogui, pyperclip = lazy_import_gui()
    full_path = str(file_path)
    print(f"    pasting file path: {full_path}")
    time.sleep(float(args.file_dialog_wait))

    if not args.no_alt_n:
        pyautogui.hotkey("alt", "n")
        time.sleep(0.15)

    pyperclip.copy(full_path)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.08)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.12)
    pyautogui.press("enter")


def upload_one_file(file_path: Path, index: int, total: int, args, config: Dict) -> str:
    print("\n" + "-" * 70)
    print(f"{index:03d}/{total:03d} restoring {file_path.name}")
    print("-" * 70)

    if args.confirm_each:
        response = input("Press Enter to restore this file, s to skip, q to quit: ").strip().lower()
        if response == "s":
            return "skip"
        if response == "q":
            return "quit"

    result = wait_for_button_and_click("add_to_stories", args, config, float(args.add_timeout), "open file picker")
    if result.status != "clicked":
        return result.status

    paste_file_into_dialog(file_path, args)

    if args.preview_wait > 0:
        print(f"    minimum preview wait: {args.preview_wait:.1f}s")
        time.sleep(float(args.preview_wait))

    result = wait_for_button_and_click("next", args, config, float(args.next_timeout), "move to publishing screen")
    if result.status != "clicked":
        return result.status

    if args.after_next_wait > 0:
        print(f"    after-next wait: {args.after_next_wait:.1f}s")
        time.sleep(float(args.after_next_wait))

    result = wait_for_button_and_click("publish_now", args, config, float(args.publish_timeout), "start publishing")
    if result.status != "clicked":
        return result.status

    if args.after_publish_wait > 0:
        print(f"    after-publish minimum wait: {args.after_publish_wait:.1f}s")
        time.sleep(float(args.after_publish_wait))

    result = wait_for_button_and_click("ok", args, config, float(args.ok_timeout), "confirm published story")
    if result.status != "clicked":
        return result.status

    return "uploaded"


def run_upload(args) -> None:
    if args.choose_folder:
        chosen = choose_source_folder(args.source)
        if chosen is None:
            print("No folder selected. Exiting.")
            return
        source = chosen
        print(f"Selected source folder: {source}")
    else:
        source = Path(args.source).expanduser()

    all_files = collect_files(source)
    selected_files = apply_start_limit(all_files, int(args.start_at), args.limit)

    if args.list or args.dry_run:
        print_order(selected_files, original_count=len(all_files))
        if args.dry_run:
            print("\nDry run only. Nothing clicked or restored.")
        return

    if not selected_files:
        print("No files selected.")
        return

    config = load_config()
    for button in BUTTON_ORDER:
        get_button_config(config, button)

    print_order(selected_files, original_count=len(all_files))
    print("\nStarting in 5 seconds. Put the EasyLoad/Insta Uploader page in front.")
    print("Emergency stop: move mouse to top-left corner, or press Ctrl+C.")
    time.sleep(5)

    post_wait_range = parse_wait_range(args.post_wait)
    uploaded = 0
    skipped = 0

    try:
        for index, file_path in enumerate(selected_files, 1):
            status = upload_one_file(file_path, index, len(selected_files), args, config)
            if status == "uploaded":
                uploaded += 1
                if index < len(selected_files):
                    sleep_range(post_wait_range, label="after OK wait before next file")
            elif status == "skip":
                skipped += 1
                print(f"Skipped: {file_path.name}")
            elif status == "quit":
                print("Stopped by user.")
                break
            else:
                print(f"Stopped with status: {status}")
                break
    except KeyboardInterrupt:
        print("\nStopped by Ctrl+C.")
    finally:
        print("\nSummary:")
        print(f"  Restored: {uploaded}")
        print(f"  Skipped:  {skipped}")
        print(f"  Selected: {len(selected_files)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Restore ordered local story media through EasyLoad/Insta Uploader using screen vision."
    )
    parser.add_argument("--source", default=DEFAULT_SOURCE, help=f"Folder containing ordered story files. Default: {DEFAULT_SOURCE}")
    parser.add_argument("--choose-folder", action="store_true", help="Open a Windows folder picker before listing/restoring.")
    parser.add_argument("--list", action="store_true", help="List restore order and exit.")
    parser.add_argument("--dry-run", action="store_true", help="List restore order without clicking.")
    parser.add_argument("--start-at", type=int, default=1, help="1-based file position to start from.")
    parser.add_argument("--limit", type=int, default=None, help="Only process this many files.")
    parser.add_argument("--confirm-each", action="store_true", help="Ask before each file.")

    parser.add_argument("--calibrate", action="store_true", help="Calibrate all four buttons.")
    parser.add_argument("--calibrate-button", choices=BUTTON_ORDER, help="Calibrate one button.")
    parser.add_argument("--calibrate-add-only", action="store_true", help="Calibrate only Add to stories.")
    parser.add_argument("--calibrate-next-only", action="store_true", help="Calibrate only Next.")
    parser.add_argument("--calibrate-publish-only", action="store_true", help="Calibrate only Publish now.")
    parser.add_argument("--calibrate-ok-only", action="store_true", help="Calibrate only OK.")
    parser.add_argument("--template-width", type=int, default=110, help="Width of button screenshot template.")
    parser.add_argument("--template-height", type=int, default=45, help="Height of button screenshot template.")

    parser.add_argument("--confidence", type=float, default=0.82, help="Template match confidence, e.g. 0.75-0.92.")
    parser.add_argument("--ok-confidence", type=float, default=None, help="Optional separate confidence for OK.")
    parser.add_argument("--scan-interval", type=float, default=0.50, help="Seconds between screen scans.")
    parser.add_argument("--grayscale", action="store_true", default=True, help="Use grayscale matching.")
    parser.add_argument("--no-grayscale", dest="grayscale", action="store_false", help="Disable grayscale matching.")
    parser.add_argument("--search-near-saved", action="store_true", default=True, help="Scan near saved coordinates. Default: on.")
    parser.add_argument("--scan-whole-screen", dest="search_near_saved", action="store_false", help="Scan the whole screen.")
    parser.add_argument("--search-radius-x", type=int, default=260, help="X radius for near-saved search.")
    parser.add_argument("--search-radius-y", type=int, default=160, help="Y radius for near-saved search.")
    parser.add_argument("--non-interactive", action="store_true", help="Quit instead of prompting when a button cannot be found.")

    parser.add_argument("--file-dialog-wait", type=float, default=1.0, help="Wait after Add before pasting path.")
    parser.add_argument("--preview-wait", type=float, default=1.5, help="Wait after selecting file before scanning for Next.")
    parser.add_argument("--after-next-wait", type=float, default=0.5, help="Wait after Next before Publish.")
    parser.add_argument("--after-publish-wait", type=float, default=1.0, help="Wait after Publish before OK.")
    parser.add_argument("--post-wait", default="60-70", help="Wait after OK before next file. Examples: 60, 60-70.")

    parser.add_argument("--add-timeout", type=float, default=90, help="Max seconds to wait for Add to stories.")
    parser.add_argument("--next-timeout", type=float, default=120, help="Max seconds to wait for Next.")
    parser.add_argument("--publish-timeout", type=float, default=120, help="Max seconds to wait for Publish now.")
    parser.add_argument("--ok-timeout", type=float, default=240, help="Max seconds to wait for OK after publishing.")
    parser.add_argument("--no-alt-n", action="store_true", help="Do not press Alt+N before pasting into file picker.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    needs_calibration = (
        args.calibrate
        or args.calibrate_button
        or args.calibrate_add_only
        or args.calibrate_next_only
        or args.calibrate_publish_only
        or args.calibrate_ok_only
    )
    if needs_calibration:
        calibrate(args)
    else:
        run_upload(args)


if __name__ == "__main__":
    main()
