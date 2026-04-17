"""
HELIOS - Desktop Agent
Fixes:
  - safe_rglob: skips reparse points / junctions (CrossDevice etc.) that cause errors
  - list_folder: lists files inside a specific folder
  - search_in_file: grep-like text search inside a file
  - Multiple result disambiguation support (returns all matches, agent decides)
"""

import os
import re
import time
import subprocess
import webbrowser
import urllib.parse
from pathlib import Path
import psutil
import pyautogui

pyautogui.PAUSE = 0.4
pyautogui.FAILSAFE = True

# Directories to completely skip
SKIP_DIRS = {
    "windows", "system32", "syswow64", "winsxs", "$recycle.bin",
    "programdata", "appdata", "node_modules", ".git", "__pycache__", "venv",
    "program files", "program files (x86)", "mingw64", "mingw32", "usr",
    "tcl8.6", "tzdata", "git", "perl", "ruby", "java", "jdk",
    # Windows cross-device / phone sync folders that cause junction errors
    "crossdevice", "phone link", "onedrive",
}

USER_FOLDERS = ["Desktop", "Downloads", "Documents", "Music", "Pictures", "Videos"]

VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"}
AUDIO_EXTS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"}

APP_MAP = {
    "chrome":        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox":       r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "edge":          r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "vlc":           r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "notepad":       "notepad.exe",
    "explorer":      "explorer.exe",
    "file explorer": "explorer.exe",
    "calculator":    "calc.exe",
    "paint":         "mspaint.exe",
    "cmd":           "cmd.exe",
    "powershell":    "powershell.exe",
    "taskmanager":   "taskmgr.exe",
    "task manager":  "taskmgr.exe",
    "vscode":        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    "vs code":       os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    "word":          r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel":         r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint":    r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
    "spotify":       os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
}

KILL_MAP = {
    "vscode":        ["code.exe"],
    "vs code":       ["code.exe"],
    "chrome":        ["chrome.exe"],
    "firefox":       ["firefox.exe"],
    "edge":          ["msedge.exe"],
    "notepad":       ["notepad.exe"],
    "vlc":           ["vlc.exe"],
    "spotify":       ["spotify.exe"],
    "excel":         ["EXCEL.EXE", "excel.exe"],
    "word":          ["WINWORD.EXE", "winword.exe"],
    "powerpoint":    ["POWERPNT.EXE"],
    "teams":         ["Teams.exe"],
    "zoom":          ["Zoom.exe"],
    "discord":       ["Discord.exe"],
    "taskmanager":   ["Taskmgr.exe"],
    "task manager":  ["Taskmgr.exe"],
    "paint":         ["mspaint.exe"],
}

WEBSITES = {
    "youtube":   "https://www.youtube.com",
    "gmail":     "https://mail.google.com",
    "google":    "https://www.google.com",
    "github":    "https://www.github.com",
    "linkedin":  "https://www.linkedin.com",
    "instagram": "https://www.instagram.com",
    "whatsapp":  "https://web.whatsapp.com",
    "netflix":   "https://www.netflix.com",
    "twitter":   "https://www.twitter.com",
    "facebook":  "https://www.facebook.com",
    "spotify":   "https://open.spotify.com",
    "bookmyshow":"https://in.bookmyshow.com",
    "paytm":     "https://movies.paytm.com",
}


def _should_skip_dir(p: Path) -> bool:
    """Return True if this directory should be skipped entirely."""
    name = p.name.lower()
    if any(skip in name for skip in SKIP_DIRS):
        return True
    # Skip Windows reparse points / junctions / symlinks to avoid CrossDevice errors
    try:
        if p.is_symlink():
            return True
        # os.stat with follow_symlinks=False to detect reparse points
        st = os.stat(p, follow_symlinks=False)
        import stat as stat_mod
        if stat_mod.S_ISLNK(st.st_mode):
            return True
    except Exception:
        return True
    return False


def _safe_iterdir(directory: Path):
    """Yield children of directory, silently skipping any that error."""
    try:
        for child in directory.iterdir():
            yield child
    except (PermissionError, OSError):
        return


def _safe_rglob(root: Path, max_results: int = 20):
    """
    Safe recursive file search that:
    - Skips symlinks/junctions (fixes CrossDevice error)
    - Skips known system directories
    - Stops when max_results reached
    Uses an explicit stack instead of rglob() to maintain full control.
    """
    results = []
    stack = [root]
    while stack and len(results) < max_results:
        current = stack.pop()
        for child in _safe_iterdir(current):
            if len(results) >= max_results:
                break
            if child.is_dir(follow_symlinks=False):
                if not _should_skip_dir(child):
                    stack.append(child)
            elif child.is_file(follow_symlinks=False):
                results.append(child)
    return results


class DesktopAgent:

    # ── File Search ────────────────────────────────────────────────────────
    def search_file(self, query: str) -> list:
        """Search for files in user folders. Returns list of matching paths."""
        clean = re.sub(
            r'\b(open|play|find|search|for|the|file|movie|song|music|'
            r'video|on|my|pc|drive|computer|from|in|list)\b',
            '', query.lower()).strip()

        # Extension-based queries
        ext_map = {
            "video": list(VIDEO_EXTS), "videos": list(VIDEO_EXTS),
            "audio": list(AUDIO_EXTS), "music":  list(AUDIO_EXTS),
            "mp4": [".mp4"], "mkv": [".mkv"], "avi": [".avi"],
            "mp3": [".mp3"], "wav": [".wav"], "txt": [".txt"],
            "pdf": [".pdf"], "doc": [".doc", ".docx"],
            "img": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
        }
        exts  = []
        words = []
        for word in clean.split():
            if word in ext_map:
                exts.extend(ext_map[word])
            elif word.startswith("."):
                exts.append(word)
            elif len(word) > 1:
                words.append(word)

        if not words and not exts:
            return []

        results = []
        home = Path.home()

        # Search standard user folders first (fast, safe)
        search_roots = [home / f for f in USER_FOLDERS if (home / f).exists()]

        for root_dir in search_roots:
            all_files = _safe_rglob(root_dir, max_results=200)
            for item in all_files:
                name_lower = item.name.lower()
                if exts and not any(name_lower.endswith(e) for e in exts):
                    continue
                if words and not all(w in name_lower for w in words):
                    continue
                path_str = str(item)
                if path_str not in results:
                    results.append(path_str)
            if len(results) >= 20:
                break

        if results:
            return results[:20]

        # PowerShell fallback — searches USERPROFILE, avoids junctions
        if words:
            filter_name = words[0]
            try:
                ps = (
                    f"Get-ChildItem -Path $env:USERPROFILE -Recurse "
                    f"-ErrorAction SilentlyContinue "
                    f"-Filter '*{filter_name}*' | "
                    f"Where-Object {{ !$_.Attributes.HasFlag([System.IO.FileAttributes]::ReparsePoint) }} | "
                    f"Select-Object -First 15 -ExpandProperty FullName")
                r = subprocess.run(["powershell", "-Command", ps],
                                   capture_output=True, text=True, timeout=25)
                ps_results = [l.strip() for l in r.stdout.splitlines()
                              if l.strip()]
                # Filter by extension if needed
                if exts:
                    ps_results = [p for p in ps_results
                                  if any(p.lower().endswith(e) for e in exts)]
                results.extend(ps_results)
            except Exception:
                pass

        return results[:20]

    def search_folder(self, query: str) -> list:
        """Search for directories in user home tree."""
        clean = re.sub(
            r'\b(open|find|search|for|the|folder|directory|named|called|in)\b',
            '', query.lower()).strip()
        if not clean:
            return []

        words = [w for w in clean.split() if len(w) > 1]
        results = []
        home = Path.home()

        # Walk user home with safe traversal
        stack = [home]
        while stack and len(results) < 10:
            current = stack.pop()
            for child in _safe_iterdir(current):
                if child.is_dir(follow_symlinks=False):
                    if _should_skip_dir(child):
                        continue
                    if all(w in child.name.lower() for w in words):
                        results.append(str(child))
                    stack.append(child)
                if len(results) >= 10:
                    break

        if not results:
            # PowerShell fallback
            try:
                ps = (
                    f"Get-ChildItem -Path $env:USERPROFILE -Recurse -Directory "
                    f"-ErrorAction SilentlyContinue "
                    f"-Filter '*{clean}*' | "
                    f"Where-Object {{ !$_.Attributes.HasFlag([System.IO.FileAttributes]::ReparsePoint) }} | "
                    f"Select-Object -First 5 -ExpandProperty FullName")
                r = subprocess.run(["powershell", "-Command", ps],
                                   capture_output=True, text=True, timeout=20)
                results = [l.strip() for l in r.stdout.splitlines() if l.strip()]
            except Exception:
                pass

        return results[:10]

    def list_folder_contents(self, location: str) -> list:
        """List files inside a specific known folder (Downloads, Desktop, etc.)."""
        from modules.agent_locations import LOCATIONS  # avoid circular import
        # Accept both known names and raw paths
        folder = LOCATIONS.get(location.lower())
        if folder is None:
            # Try as a literal path
            folder = Path(location)
        if not folder.exists() or not folder.is_dir():
            return []
        items = []
        for child in _safe_iterdir(folder):
            if child.is_file(follow_symlinks=False):
                items.append(str(child))
        return sorted(items)[:50]

    def search_in_file(self, filepath: str, keyword: str) -> str:
        """Search for a keyword inside a text file and return matching lines."""
        p = Path(filepath)
        if not p.exists():
            return f"File not found: {filepath}"
        if not p.is_file():
            return f"Not a file: {filepath}"
        # Only read text files
        text_exts = {".txt", ".md", ".py", ".js", ".ts", ".html", ".css",
                     ".json", ".csv", ".log", ".xml", ".yaml", ".yml",
                     ".ini", ".cfg", ".bat", ".sh", ".java", ".c", ".cpp",
                     ".h", ".cs", ".rb", ".go", ".rs"}
        if p.suffix.lower() not in text_exts:
            return f"Cannot search inside '{p.name}' — not a text file."
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            return f"Could not read file: {e}"

        lines = content.splitlines()
        kw_lower = keyword.lower()
        matches = []
        for i, line in enumerate(lines, 1):
            if kw_lower in line.lower():
                matches.append(f"  Line {i}: {line.rstrip()}")

        if not matches:
            return (f"No occurrences of '{keyword}' found in {p.name}.\n"
                    f"Total lines searched: {len(lines)}")
        return (f"Found {len(matches)} occurrence(s) of '{keyword}' in {p.name}:\n"
                + "\n".join(matches[:30])
                + (f"\n  ... and {len(matches)-30} more" if len(matches) > 30 else ""))

    def play_media(self, query: str) -> str:
        """Find and play a media file. Returns ambiguity info if multiple found."""
        results = self.search_file(query)
        media = [r for r in results
                 if Path(r).suffix.lower() in VIDEO_EXTS | AUDIO_EXTS]
        targets = media if media else results

        if not targets:
            return (f"No media file found matching '{query}'.\n"
                    f"Make sure the file is in Desktop, Downloads, Documents, "
                    f"Music, Pictures, or Videos.")

        # Return all matches so agent can handle disambiguation
        return targets

    def open_explorer_search(self, query: str) -> str:
        folders = self.search_folder(query)
        if folders:
            try:
                subprocess.Popen(["explorer.exe", folders[0]])
            except Exception:
                pass
            result = f"Opened: {folders[0]}"
            if len(folders) > 1:
                result += "\n\nOther matches:\n" + "\n".join(
                    f"  • {f}" for f in folders[1:5])
            return result

        files = self.search_file(query)
        if files:
            parent = str(Path(files[0]).parent)
            try:
                subprocess.Popen(["explorer.exe", parent])
            except Exception:
                pass
            return (f"Opened Explorer at: {parent}\n"
                    f"Files matching '{query}':\n" +
                    "\n".join(f"  • {Path(f).name}" for f in files[:5]))

        try:
            subprocess.Popen(["explorer.exe"])
        except Exception:
            pass
        return f"No folder/file named '{query}' found. File Explorer opened."

    # ── App Control ────────────────────────────────────────────────────────
    def open_app(self, app: str) -> str:
        key = app.lower().strip()
        exe = APP_MAP.get(key)
        if exe and Path(exe).exists():
            subprocess.Popen([exe])
            return f"Opened {app}."
        try:
            subprocess.Popen(key, shell=True)
            return f"Launched {app}."
        except Exception as e:
            return f"Could not open '{app}': {e}"

    def kill_app(self, app: str) -> str:
        key = app.lower().strip()
        targets = KILL_MAP.get(key, [app, app + ".exe"])
        killed = []
        for proc in psutil.process_iter(["name", "pid"]):
            try:
                pname = proc.info["name"]
                if (any(t.lower() == pname.lower() for t in targets) or
                        key in pname.lower()):
                    proc.kill()
                    killed.append(pname)
            except Exception:
                pass
        if killed:
            return f"Closed: {', '.join(set(killed))}"
        try:
            r = subprocess.run(["taskkill", "/F", "/IM", f"{app}.exe"],
                               capture_output=True, text=True)
            if r.returncode == 0:
                return f"Closed {app}."
        except Exception:
            pass
        return f"No running process found for '{app}'."

    def open_website(self, site: str) -> str:
        url = WEBSITES.get(site.lower(), f"https://www.{site}.com")
        webbrowser.open(url)
        return f"Opened: {url}"

    def open_url(self, url: str) -> str:
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)
        return f"Opened: {url}"

    def search_google(self, query: str) -> str:
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        return f"Searching Google for: {query}"

    def search_youtube(self, query: str) -> str:
        url = (f"https://www.youtube.com/results?"
               f"search_query={urllib.parse.quote(query)}")
        webbrowser.open(url)
        return f"Searching YouTube for: {query}"

    # ── Volume ─────────────────────────────────────────────────────────────
    def volume_up(self, steps: int = 5) -> str:
        for _ in range(steps):
            pyautogui.press("volumeup")
        return "Volume increased."

    def volume_down(self, steps: int = 5) -> str:
        for _ in range(steps):
            pyautogui.press("volumedown")
        return "Volume decreased."

    def mute(self) -> str:
        pyautogui.press("volumemute")
        return "Volume toggled mute/unmute."

    # ── Screenshot ─────────────────────────────────────────────────────────
    def screenshot(self) -> str:
        path = str(Path.home() / "Desktop" / f"helios_{int(time.time())}.png")
        img = pyautogui.screenshot()
        img.save(path)
        return f"Screenshot saved to Desktop: {Path(path).name}"

    # ── System ─────────────────────────────────────────────────────────────
    def lock_screen(self) -> str:
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
        return "Screen locked."

    def shutdown(self, delay: int = 0) -> str:
        subprocess.run(["shutdown", "/s", "/t", str(delay)])
        return f"Shutting down in {delay} seconds."

    def restart(self, delay: int = 0) -> str:
        subprocess.run(["shutdown", "/r", "/t", str(delay)])
        return f"Restarting in {delay} seconds."

    def sleep(self) -> str:
        subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
        return "Going to sleep..."

    def battery_status(self) -> str:
        b = psutil.sensors_battery()
        if not b:
            return "No battery detected (desktop PC)."
        status = "charging" if b.power_plugged else "discharging"
        secs = b.secsleft
        if secs < 0 or secs > 86400 * 30:
            time_str = "calculating..."
        else:
            h, m = divmod(int(secs) // 60, 60)
            time_str = f"{h}h {m}m remaining"
        return f"Battery: {b.percent:.0f}%\nStatus: {status}\nTime: {time_str}"

    def disk_space(self) -> str:
        lines = ["Disk Space:"]
        for p in psutil.disk_partitions():
            try:
                u = psutil.disk_usage(p.mountpoint)
                lines.append(
                    f"  {p.device}  "
                    f"{u.free//(1024**3)}GB free / {u.total//(1024**3)}GB "
                    f"({u.percent}% used)")
            except Exception:
                pass
        return "\n".join(lines)

    def running_apps(self) -> str:
        seen, names = set(), []
        skip = {"svchost.exe", "RuntimeBroker.exe", "conhost.exe",
                "csrss.exe", "lsass.exe", "services.exe", "System"}
        for p in psutil.process_iter(["name"]):
            try:
                n = p.info["name"]
                if n and n not in skip and n not in seen:
                    seen.add(n)
                    names.append(n.replace(".exe", ""))
            except Exception:
                pass
        names.sort()
        return "Running apps:\n" + "\n".join(f"  • {n}" for n in names[:30])

    def ip_address(self) -> str:
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        lines = [f"Hostname: {hostname}", f"Local IP: {local_ip}"]
        for iface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == 2:
                    lines.append(f"  {iface}: {addr.address}")
        return "\n".join(lines)

    def empty_recycle(self) -> str:
        subprocess.run(
            ["powershell", "-Command",
             "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
            timeout=15)
        return "Recycle Bin emptied."
