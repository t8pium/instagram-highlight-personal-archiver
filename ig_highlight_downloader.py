"""Browser-Assisted Instagram Highlight Backup Tool.

Public-safe entry point for a local personal archival workflow.

This repository intentionally does not include downloaded media, browser
profiles, cookies, cache files, or personal session data. Use this project only
for content you own or have permission to archive.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
import argparse
import hashlib
import json
import mimetypes
import os
import re
import subprocess
import time
import urllib.request

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


BLOCKED_PROFILE_PATHS = {
    "accounts",
    "explore",
    "reels",
    "stories",
    "direct",
    "p",
    "reel",
    "tv",
    "about",
    "developer",
}

MEDIA_HOST_MARKERS = (
    "cdninstagram.com",
    "fbcdn.net",
    "scontent",
    "instagram.f",
)

IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
}


def find_chrome_exe() -> str:
    """Return a likely Chrome executable path on Windows, or an empty string."""
    candidates = [
        Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
    ]

    for path in candidates:
        if path.exists():
            return str(path)

    return ""


def cdp_is_alive(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1.5) as response:
            return response.status == 200
    except Exception:
        return False


def wait_for_cdp(port: int, timeout_seconds: int = 25) -> bool:
    start = time.time()

    while time.time() - start < timeout_seconds:
        if cdp_is_alive(port):
            return True
        time.sleep(0.35)

    return False


def launch_debug_chrome(chrome_path: str, user_data_dir: Path, port: int) -> None:
    user_data_dir.mkdir(parents=True, exist_ok=True)

    args = [
        chrome_path,
        "--remote-debugging-address=127.0.0.1",
        f"--remote-debugging-port={port}",
        f"--user-data-dir={str(user_data_dir)}",
        "--no-first-run",
        "--no-default-browser-check",
        "https://www.instagram.com/",
    ]

    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def normalize_profile_input(raw: str) -> str:
    raw = (raw or "").strip()

    if not raw:
        return ""

    if raw.startswith("@"):
        raw = raw[1:]

    if raw.startswith("http://") or raw.startswith("https://"):
        return raw

    raw = raw.strip("/")
    return f"https://www.instagram.com/{raw}/"


def is_instagram_profile_url(url: str) -> bool:
    """Return True for normal Instagram profile URLs."""
    if not url:
        return False

    parsed = urlparse(url)
    host = parsed.netloc.lower().replace("www.", "")
    path = parsed.path.strip("/")

    if host != "instagram.com" or not path:
        return False

    parts = path.split("/")
    first = parts[0].lower()

    if first in BLOCKED_PROFILE_PATHS:
        return False

    return len(parts) == 1


def wait_for_page_ready(page) -> None:
    try:
        page.wait_for_load_state("domcontentloaded", timeout=5000)
    except PlaywrightTimeoutError:
        pass

    page.wait_for_timeout(1000)


def wait_for_user_to_be_on_profile(page, profile_arg: str = "") -> str:
    if profile_arg:
        profile_url = normalize_profile_input(profile_arg)
        print(f"\nOpening provided profile: {profile_url}")
        page.goto(profile_url, wait_until="domcontentloaded")
        wait_for_page_ready(page)
        return profile_url

    while True:
        wait_for_page_ready(page)
        current_url = page.url

        if is_instagram_profile_url(current_url):
            print("\nUsing current Instagram profile:")
            print(current_url)
            return current_url

        print("\nYou are not on an Instagram profile page yet.")
        print("Go to the profile you want in Chrome, then return here.")
        print("Example: https://www.instagram.com/username/")
        input("\nPress ENTER after you are on the correct profile page... ")


def detect_highlight_links(page) -> list[dict[str, str]]:
    script = r"""
    () => {
      const anchors = Array.from(document.querySelectorAll('a[href*="/stories/highlights/"]'));
      const seen = new Set();
      const out = [];

      for (const anchor of anchors) {
        const href = anchor.href || "";
        const match = href.match(/\/stories\/highlights\/(\d+)/);
        if (!match || seen.has(match[1])) continue;
        seen.add(match[1]);

        out.push({
          id: match[1],
          href,
          label: (anchor.innerText || anchor.getAttribute("aria-label") || anchor.getAttribute("title") || match[1]).trim()
        });
      }

      return out;
    }
    """
    return page.evaluate(script)


def profile_slug_from_url(profile_url: str) -> str:
    parsed = urlparse(profile_url)
    slug = parsed.path.strip("/").split("/")[0] if parsed.path else "profile"
    return safe_name(slug or "profile")


def safe_name(value: str, fallback: str = "item") -> str:
    value = (value or "").strip()
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"[^A-Za-z0-9._@-]+", "_", value)
    value = value.strip("._-")
    return value[:80] or fallback


def is_likely_instagram_media_url(url: str) -> bool:
    if not url or url.startswith("blob:") or url.startswith("data:"):
        return False
    lower = url.lower()
    return any(marker in lower for marker in MEDIA_HOST_MARKERS)


def normalize_download_key(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.netloc}{parsed.path}"


def extension_for_url(url: str, content_type: str = "") -> str:
    content_type = (content_type or "").split(";", 1)[0].strip().lower()
    if content_type in CONTENT_TYPE_EXTENSIONS:
        return CONTENT_TYPE_EXTENSIONS[content_type]

    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".webm", ".mov"}:
        return ".jpg" if suffix == ".jpeg" else suffix

    guessed = mimetypes.guess_extension(content_type) if content_type else ""
    return guessed or ".bin"


def short_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8", errors="ignore")).hexdigest()[:10]


def collect_visible_media_candidates(page) -> list[dict]:
    """Return visible, large media elements from the current story view.

    This intentionally relies on what is visible in the normal browser instead
    of private APIs. For videos, Instagram may expose only a blob: URL in the DOM;
    network video responses are used as a fallback for those.
    """
    script = r"""
    () => {
      const out = [];
      const elements = Array.from(document.querySelectorAll('img, video, source'));
      for (const el of elements) {
        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        const visible =
          rect.width >= 160 &&
          rect.height >= 160 &&
          rect.bottom > 0 &&
          rect.right > 0 &&
          rect.top < window.innerHeight &&
          rect.left < window.innerWidth &&
          style.visibility !== 'hidden' &&
          style.display !== 'none' &&
          Number(style.opacity || 1) > 0.05;
        if (!visible) continue;

        const tag = el.tagName.toLowerCase();
        let url = el.currentSrc || el.src || el.getAttribute('src') || '';
        if (!url && el.srcset) {
          const parts = el.srcset.split(',').map(x => x.trim().split(/\s+/)[0]).filter(Boolean);
          url = parts[parts.length - 1] || '';
        }

        out.push({
          url,
          tag,
          width: Math.round(rect.width),
          height: Math.round(rect.height),
          area: Math.round(rect.width * rect.height),
          natural_width: Math.round(el.naturalWidth || el.videoWidth || rect.width),
          natural_height: Math.round(el.naturalHeight || el.videoHeight || rect.height),
          alt: el.alt || '',
          is_blob: String(url).startsWith('blob:')
        });
      }
      return out.sort((a, b) => b.area - a.area).slice(0, 16);
    }
    """
    try:
        return page.evaluate(script) or []
    except Exception as exc:
        print(f"    Could not inspect visible media: {exc}")
        return []


def download_url(context, url: str, destination: Path, content_type_hint: str = "") -> tuple[bool, str]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        response = context.request.get(url, timeout=60000)
    except Exception as exc:
        return False, f"request failed: {exc}"

    try:
        if response.status >= 400:
            return False, f"HTTP {response.status}"
        body = response.body()
        if not body:
            return False, "empty response"
        destination.write_bytes(body)
        return True, f"saved {len(body):,} bytes"
    except Exception as exc:
        return False, f"save failed: {exc}"


def make_media_recorder():
    media_responses: list[dict] = []

    def on_response(response) -> None:
        try:
            url = response.url
            headers = response.headers or {}
            content_type = headers.get("content-type", "").split(";", 1)[0].lower()
            length_raw = headers.get("content-length", "0") or "0"
            try:
                content_length = int(length_raw)
            except ValueError:
                content_length = 0

            if not is_likely_instagram_media_url(url):
                return
            if content_type not in IMAGE_TYPES and content_type not in VIDEO_TYPES:
                return

            # Keep video responses aggressively. Keep only non-tiny images from
            # network, because small images are often avatars/UI. Visible DOM
            # image collection handles story images more reliably.
            if content_type in IMAGE_TYPES and 0 < content_length < 35000:
                return

            media_responses.append(
                {
                    "url": url,
                    "content_type": content_type,
                    "content_length": content_length,
                    "time": time.time(),
                }
            )
        except Exception:
            return

    return media_responses, on_response


def current_story_fingerprint(page) -> str:
    candidates = collect_visible_media_candidates(page)
    bits = [page.url]
    for item in candidates[:4]:
        bits.append(str(item.get("url", "")))
        bits.append(str(item.get("area", "")))
    return short_hash("|".join(bits))


def build_current_item_candidates(page, media_responses: list[dict], downloaded_keys: set[str]) -> list[dict]:
    out: list[dict] = []
    visible = collect_visible_media_candidates(page)
    now = time.time()

    for item in visible:
        url = item.get("url") or ""
        tag = item.get("tag") or ""
        area = int(item.get("area") or 0)
        if area < 50000:
            continue
        if is_likely_instagram_media_url(url):
            out.append(
                {
                    "url": url,
                    "content_type": "video/mp4" if tag == "video" else "image/jpeg",
                    "source": "visible_dom",
                    "area": area,
                }
            )

    has_visible_video = any((item.get("tag") == "video" or item.get("is_blob")) and int(item.get("area") or 0) >= 50000 for item in visible)
    if has_visible_video:
        recent_videos = [
            item
            for item in media_responses
            if item.get("content_type") in VIDEO_TYPES and now - float(item.get("time") or 0) <= 35
        ]
        for item in recent_videos[-6:]:
            out.append({**item, "source": "recent_network_video"})

    deduped: list[dict] = []
    local_seen: set[str] = set()
    for item in out:
        url = item.get("url") or ""
        key = normalize_download_key(url)
        if not key or key in downloaded_keys or key in local_seen:
            continue
        local_seen.add(key)
        deduped.append(item)

    # Prefer videos first, then largest visible images.
    deduped.sort(key=lambda item: (0 if str(item.get("content_type", "")).startswith("video/") else 1, -int(item.get("area") or 0)))
    return deduped


def archive_highlight(page, context, highlight: dict, profile_dir: Path, args, media_responses: list[dict], downloaded_keys: set[str]) -> dict:
    label = safe_name(highlight.get("label") or highlight.get("id") or "highlight")
    highlight_dir = profile_dir / f"{label}_{highlight.get('id', '')}".strip("_")
    highlight_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 72)
    print(f"Archiving highlight: {highlight.get('label') or highlight.get('id')}")
    print(highlight.get("href"))
    print(f"Output folder: {highlight_dir}")
    print("=" * 72)

    page.goto(highlight["href"], wait_until="domcontentloaded")
    page.wait_for_timeout(int(float(args.story_settle) * 1000))

    saved_items: list[dict] = []
    stale_steps = 0
    last_fingerprint = ""

    for story_index in range(1, int(args.max_items_per_highlight) + 1):
        page.wait_for_timeout(int(float(args.story_settle) * 1000))

        fingerprint = current_story_fingerprint(page)
        candidates = build_current_item_candidates(page, media_responses, downloaded_keys)
        saved_this_step = 0

        for candidate in candidates:
            url = candidate["url"]
            key = normalize_download_key(url)
            content_type = candidate.get("content_type", "")
            ext = extension_for_url(url, content_type)
            filename = f"{len(saved_items) + 1:03d}_{candidate.get('source', 'media')}_{short_hash(url)}{ext}"
            destination = highlight_dir / filename
            ok, message = download_url(context, url, destination, content_type)
            if ok:
                downloaded_keys.add(key)
                saved_this_step += 1
                record = {
                    "file": str(destination.relative_to(profile_dir.parent)),
                    "highlight_id": highlight.get("id"),
                    "highlight_label": highlight.get("label"),
                    "source_url": url,
                    "content_type": content_type,
                    "source": candidate.get("source"),
                    "story_step": story_index,
                }
                saved_items.append(record)
                print(f"  saved {filename} ({candidate.get('source')})")
            else:
                print(f"  skipped candidate: {message}")

        if saved_this_step == 0 and fingerprint == last_fingerprint:
            stale_steps += 1
        else:
            stale_steps = 0
        last_fingerprint = fingerprint

        if stale_steps >= 3:
            print("  no new visible media after several steps; moving to next highlight")
            break

        try:
            page.keyboard.press("ArrowRight")
        except Exception:
            pass
        page.wait_for_timeout(int(float(args.between_stories) * 1000))

        # If Instagram has closed the story viewer or left the stories area, stop.
        if "/stories/" not in (page.url or "") and story_index > 1:
            break

    manifest_path = highlight_dir / "manifest.json"
    manifest_path.write_text(json.dumps(saved_items, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Finished highlight. Saved {len(saved_items)} file(s).")
    return {"highlight": highlight, "folder": str(highlight_dir), "saved_count": len(saved_items), "items": saved_items}


def archive_highlights(page, context, profile_url: str, highlights: list[dict], args, media_responses: list[dict]) -> None:
    output_root = Path(args.output).expanduser().resolve()
    profile_dir = output_root / profile_slug_from_url(profile_url)
    profile_dir.mkdir(parents=True, exist_ok=True)
    downloaded_keys: set[str] = set()
    archive_results: list[dict] = []

    selected = highlights[: int(args.highlight_limit)] if args.highlight_limit else highlights
    print(f"\nArchive mode enabled. Saving into: {profile_dir}")
    print(f"Selected {len(selected)} highlight(s) out of {len(highlights)} detected.")

    for index, highlight in enumerate(selected, start=1):
        print(f"\n[{index}/{len(selected)}]")
        result = archive_highlight(page, context, highlight, profile_dir, args, media_responses, downloaded_keys)
        archive_results.append(result)
        page.wait_for_timeout(1000)

    archive_manifest = {
        "profile_url": profile_url,
        "output_folder": str(profile_dir),
        "highlight_count": len(selected),
        "total_saved": sum(item["saved_count"] for item in archive_results),
        "highlights": archive_results,
    }
    manifest_path = profile_dir / "archive_manifest.json"
    manifest_path.write_text(json.dumps(archive_manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "=" * 72)
    print("Archive complete.")
    print(f"Saved files: {archive_manifest['total_saved']}")
    print(f"Manifest: {manifest_path}")
    print("=" * 72)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Browser-assisted Instagram highlight backup workflow for personal archival."
    )
    parser.add_argument("--profile", default="", help="Optional Instagram username or profile URL.")
    parser.add_argument("--port", type=int, default=9222, help="Chrome remote debugging port.")
    parser.add_argument("--chrome-path", default="", help="Optional path to chrome.exe.")
    parser.add_argument(
        "--chrome-user-data-dir",
        default=str(Path(os.environ.get("LOCALAPPDATA", ".")) / "ChromeIGDebug"),
        help="Dedicated Chrome profile folder for this workflow.",
    )
    parser.add_argument("--archive", action="store_true", help="Open each detected highlight and save visible story media into --output.")
    parser.add_argument("--output", default="downloads", help="Archive output folder. Default: downloads")
    parser.add_argument("--highlight-limit", type=int, default=0, help="Only archive the first N highlights. 0 means all.")
    parser.add_argument("--max-items-per-highlight", type=int, default=120, help="Safety cap for story steps per highlight.")
    parser.add_argument("--story-settle", type=float, default=2.0, help="Seconds to wait for each story item to load before capture.")
    parser.add_argument("--between-stories", type=float, default=0.8, help="Seconds to wait after pressing ArrowRight.")
    args = parser.parse_args()

    chrome_path = args.chrome_path or find_chrome_exe()
    if not chrome_path:
        raise SystemExit("Could not find Google Chrome. Use --chrome-path to point to chrome.exe.")

    user_data_dir = Path(args.chrome_user_data_dir)

    if not cdp_is_alive(args.port):
        print("\nStarting dedicated Chrome for Instagram backup workflow...")
        print(f"Chrome profile folder: {user_data_dir}")
        launch_debug_chrome(chrome_path, user_data_dir, args.port)

    if not wait_for_cdp(args.port):
        raise SystemExit("Chrome started, but the debug port did not open. Try --port 9223.")

    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{args.port}")
        if not browser.contexts:
            raise SystemExit("Connected to Chrome, but no browser context was found.")

        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        media_responses, on_response = make_media_recorder()
        page.on("response", on_response)

        if "instagram.com" not in (page.url or ""):
            page.goto("https://www.instagram.com/", wait_until="domcontentloaded")

        print("\nLog into Instagram manually in the Chrome window if needed.")
        input("Press ENTER after login is done... ")

        profile_url = wait_for_user_to_be_on_profile(page, args.profile)
        highlights = detect_highlight_links(page)

        print(f"\nDetected {len(highlights)} highlight link(s).")
        for index, highlight in enumerate(highlights, start=1):
            print(f"{index:02d}. {highlight.get('label') or highlight['id']} | {highlight['href']}")

        if args.archive:
            if not highlights:
                print("\nNo highlights detected, so there is nothing to archive.")
            else:
                archive_highlights(page, context, profile_url, highlights, args, media_responses)
        else:
            print("\nDetection only. Add --archive to save highlight media into the downloads folder.")

        print("\nKeep downloaded media, browser data, and local output outside version control.")


if __name__ == "__main__":
    main()
