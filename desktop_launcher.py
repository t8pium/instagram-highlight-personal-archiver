#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

ROOT = Path(__file__).resolve().parent
SETTINGS = ROOT / "launcher_settings.json"
VENV_PY = ROOT / ".venv" / "Scripts" / "python.exe"

DEFAULTS = {
    "profile": "",
    "restore_folder": "",
    "chrome_folder": str(Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "ChromeIGDebug"),
    "start_at": "1",
    "limit": "",
    "post_wait": "60-70",
}


def load_settings() -> dict:
    if SETTINGS.exists():
        try:
            data = json.loads(SETTINGS.read_text(encoding="utf-8"))
            out = dict(DEFAULTS)
            out.update({k: str(v) for k, v in data.items() if k in out})
            return out
        except Exception:
            pass
    return dict(DEFAULTS)


def find_chrome_exe() -> str:
    candidates = [
        Path(os.environ.get("PROGRAMFILES", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    return shutil.which("chrome") or shutil.which("chrome.exe") or ""


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Instagram Toolkit Launcher")
        self.geometry("880x660")
        self.minsize(800, 600)
        data = load_settings()
        self.profile = tk.StringVar(value=data["profile"])
        self.restore_folder = tk.StringVar(value=data["restore_folder"])
        self.chrome_folder = tk.StringVar(value=data["chrome_folder"])
        self.start_at = tk.StringVar(value=data["start_at"])
        self.limit = tk.StringVar(value=data["limit"])
        self.post_wait = tk.StringVar(value=data["post_wait"])
        self.status = tk.StringVar(value="Ready. Use Setup first if this is your first run.")
        self.build()
        self.protocol("WM_DELETE_WINDOW", self.close)

    def build(self) -> None:
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Instagram Toolkit Launcher", font=("Segoe UI", 20, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(frame, text="Simple control panel for setup, saved profile, saved folders, highlight archiving, restore, resume, and login fixes.").grid(row=1, column=0, sticky="w", pady=(4, 14))

        settings = ttk.LabelFrame(frame, text="Settings")
        settings.grid(row=2, column=0, sticky="ew")
        settings.columnconfigure(1, weight=1)
        self.entry_row(settings, 0, "Username / @handle / profile URL", self.profile)
        self.entry_row(settings, 1, "Restore folder", self.restore_folder, self.pick_restore)
        self.entry_row(settings, 2, "Chrome profile folder", self.chrome_folder, self.pick_chrome)

        resume = ttk.Frame(settings)
        resume.grid(row=3, column=1, sticky="w", padx=8, pady=8)
        ttk.Label(settings, text="Resume controls").grid(row=3, column=0, sticky="w", padx=8, pady=8)
        for label, var, width in [("Start at", self.start_at, 8), ("Limit", self.limit, 8), ("Post wait", self.post_wait, 10)]:
            ttk.Label(resume, text=label).pack(side="left")
            ttk.Entry(resume, textvariable=var, width=width).pack(side="left", padx=(6, 14))
        ttk.Button(settings, text="Save", command=self.save).grid(row=3, column=2, padx=8, pady=8)

        actions = ttk.LabelFrame(frame, text="Actions")
        actions.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)
        left = ttk.Frame(actions, padding=8)
        right = ttk.Frame(actions, padding=8)
        left.grid(row=0, column=0, sticky="nsew")
        right.grid(row=0, column=1, sticky="nsew")
        left.columnconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        ttk.Button(left, text="Setup / repair environment", command=self.setup).grid(row=0, column=0, sticky="ew", pady=4)
        ttk.Button(left, text="Archive highlights from current profile", command=self.detect_current).grid(row=1, column=0, sticky="ew", pady=4)
        ttk.Button(left, text="Archive highlights from saved profile", command=self.detect_saved).grid(row=2, column=0, sticky="ew", pady=4)
        ttk.Button(left, text="Open login-only Chrome (no automation)", command=self.open_login_only_chrome).grid(row=3, column=0, sticky="ew", pady=(16, 4))
        ttk.Button(left, text="Open Chrome login profile folder", command=self.open_chrome_profile).grid(row=4, column=0, sticky="ew", pady=4)
        ttk.Button(left, text="Reset Chrome login profile", command=self.reset_chrome_profile).grid(row=5, column=0, sticky="ew", pady=4)
        ttk.Button(left, text="Open repo folder", command=lambda: self.open_folder(ROOT)).grid(row=6, column=0, sticky="ew", pady=4)

        ttk.Button(right, text="Calibrate restore buttons", command=self.calibrate).grid(row=0, column=0, sticky="ew", pady=4)
        ttk.Button(right, text="Preview restore order", command=self.preview).grid(row=1, column=0, sticky="ew", pady=4)
        ttk.Button(right, text="Run restore", command=self.restore).grid(row=2, column=0, sticky="ew", pady=4)
        ttk.Button(right, text="Resume restore", command=self.resume).grid(row=3, column=0, sticky="ew", pady=4)
        ttk.Button(right, text="Open restore folder", command=self.open_restore).grid(row=4, column=0, sticky="ew", pady=(16, 4))

        ttk.Label(frame, text="Archive buttons save files into the repo's downloads folder. If a command fails, the command window now stays open so you can read the error.", wraplength=840).grid(row=4, column=0, sticky="w", pady=(14, 6))
        ttk.Label(frame, text="If Instagram shows a broken verification page, close the tool's Chrome window, reset the Chrome login profile, then use login-only Chrome. After login works, close that Chrome window and archive again.", wraplength=840).grid(row=5, column=0, sticky="w", pady=(0, 6))
        ttk.Label(frame, textvariable=self.status).grid(row=6, column=0, sticky="w")

    def entry_row(self, parent, row, label, var, browse=None):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=8)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", padx=8, pady=8)
        if browse:
            ttk.Button(parent, text="Browse", command=browse).grid(row=row, column=2, padx=8, pady=8)

    def save(self):
        data = {
            "profile": self.profile.get().strip(),
            "restore_folder": self.restore_folder.get().strip(),
            "chrome_folder": self.chrome_folder.get().strip(),
            "start_at": self.start_at.get().strip() or "1",
            "limit": self.limit.get().strip(),
            "post_wait": self.post_wait.get().strip() or "60-70",
        }
        SETTINGS.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.status.set("Saved launcher settings.")

    def pick_restore(self):
        value = filedialog.askdirectory(title="Choose restore folder", initialdir=self.restore_folder.get() or str(Path.home()))
        if value:
            self.restore_folder.set(value)
            self.save()

    def pick_chrome(self):
        value = filedialog.askdirectory(title="Choose Chrome profile folder", initialdir=self.chrome_folder.get() or str(Path.home()))
        if value:
            self.chrome_folder.set(value)
            self.save()

    def open_folder(self, path: Path):
        path.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(str(path))
        else:
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(path)])

    def chrome_profile_path(self) -> Path:
        return Path(self.chrome_folder.get().strip() or DEFAULTS["chrome_folder"])

    def open_login_only_chrome(self):
        self.save()
        chrome = find_chrome_exe()
        if not chrome:
            messagebox.showerror("Chrome not found", "Could not find Google Chrome. Install Chrome or set the Chrome path manually in the script.")
            return
        profile_dir = self.chrome_profile_path()
        profile_dir.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.Popen([
                chrome,
                f"--user-data-dir={profile_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                "https://www.instagram.com/",
            ])
        except Exception as exc:
            messagebox.showerror("Could not open Chrome", str(exc))
            return
        self.status.set("Opened login-only Chrome without automation.")
        messagebox.showinfo(
            "Login-only Chrome opened",
            "Use this Chrome window to log in manually.\n\n"
            "When Instagram is fully logged in and the challenge is cleared, close this Chrome window.\n\n"
            "Then run archive again from the launcher.",
        )

    def open_chrome_profile(self):
        self.save()
        self.open_folder(self.chrome_profile_path())
        self.status.set("Opened dedicated Chrome login profile folder.")

    def reset_chrome_profile(self):
        self.save()
        path = self.chrome_profile_path()
        if not path.exists():
            messagebox.showinfo("Nothing to reset", f"This folder does not exist yet:\n\n{path}")
            return
        ok = messagebox.askyesno(
            "Reset dedicated Chrome profile?",
            "Close the toolkit Chrome window first.\n\n"
            "This will rename the dedicated toolkit Chrome profile folder so Instagram starts with a fresh login profile next time.\n\n"
            "It does not touch your normal Chrome or Brave profile.\n\n"
            f"Folder:\n{path}\n\nContinue?",
        )
        if not ok:
            return
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = path.with_name(f"{path.name}_old_{stamp}")
        try:
            path.rename(backup)
        except PermissionError:
            messagebox.showerror("Could not reset", "The folder is probably still open in Chrome. Close every toolkit Chrome window, then try again.")
            return
        except Exception as exc:
            messagebox.showerror("Could not reset", f"Failed to rename the folder:\n\n{exc}")
            return
        self.status.set(f"Reset complete. Old profile renamed to {backup.name}")
        messagebox.showinfo("Reset complete", f"Old profile renamed to:\n\n{backup}\n\nUse login-only Chrome next, then run archive again.")

    def open_restore(self):
        folder = self.restore_folder.get().strip()
        if not folder:
            messagebox.showinfo("Folder needed", "Choose a restore folder first.")
            return
        self.open_folder(Path(folder))

    def ready(self) -> bool:
        if VENV_PY.exists():
            return True
        messagebox.showinfo("Setup needed", "Run Setup / repair environment first.")
        return False

    def launch(self, args, title):
        self.save()
        command = subprocess.list2cmdline([str(x) for x in args])
        if os.name == "nt":
            subprocess.Popen(["cmd.exe", "/k", command], cwd=str(ROOT))
        else:
            subprocess.Popen(command, shell=True, cwd=str(ROOT))
        self.status.set(f"Opened: {title}. The command window will stay open if it errors.")

    def setup(self):
        self.launch([str(ROOT / "CLICK_TO_RUN_INSTAGRAM_TOOLKIT.bat")], "setup/menu")

    def downloader_base(self):
        return [
            str(VENV_PY),
            str(ROOT / "ig_highlight_downloader.py"),
            "--chrome-user-data-dir",
            self.chrome_folder.get().strip(),
            "--archive",
            "--output",
            "downloads",
        ]

    def detect_current(self):
        if self.ready():
            self.launch(self.downloader_base(), "current profile archive")

    def detect_saved(self):
        if not self.ready():
            return
        profile = self.profile.get().strip()
        if not profile:
            messagebox.showinfo("Profile needed", "Enter a username, @handle, or profile URL first.")
            return
        self.launch(self.downloader_base() + ["--profile", profile], "saved profile archive")

    def restore_base(self):
        folder = self.restore_folder.get().strip()
        if not folder:
            messagebox.showinfo("Folder needed", "Choose a restore folder first.")
            return None
        return [str(VENV_PY), str(ROOT / "ig_story_restore_easyload.py"), "--source", folder]

    def calibrate(self):
        if self.ready():
            self.launch([str(VENV_PY), str(ROOT / "ig_story_restore_easyload.py"), "--calibrate"], "calibration")

    def preview(self):
        if not self.ready():
            return
        base = self.restore_base()
        if base:
            self.launch(base + ["--dry-run"], "preview")

    def restore(self):
        if not self.ready():
            return
        base = self.restore_base()
        if base:
            self.launch(base + ["--post-wait", self.post_wait.get().strip() or "60-70"], "restore")

    def resume(self):
        if not self.ready():
            return
        base = self.restore_base()
        if not base:
            return
        args = base + ["--start-at", self.start_at.get().strip() or "1", "--post-wait", self.post_wait.get().strip() or "60-70"]
        if self.limit.get().strip():
            args += ["--limit", self.limit.get().strip()]
        self.launch(args, "resume")

    def close(self):
        self.save()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
