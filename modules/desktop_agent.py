"""
HELIOS - Desktop Agent  (production-stable)
Python 3.10 compatible.

Key guarantees:
  - _safe_iterdir     : never raises; silently skips PermissionError / OSError
  - _should_skip_dir  : reparse-point detection via FILE_ATTRIBUTE_REPARSE_POINT
                        (ctypes, no follow_symlinks kwarg needed → 3.10 safe)
  - _safe_rglob       : explicit stack, stops early, never touches junctions
  - search_file       : user folders only, then PowerShell fallback
  - open_app("explorer") / open_app("file explorer") → os.startfile("explorer")
  - Every public method is wrapped in a top-level try/except → no crash reaches UI
"""

import os
import re
import stat
import time
import ctypes
import logging
import subprocess
import webbrowser
import urllib.parse
from pathlib import Path
from typing import List

import psutil
import pyautogui

# ── Logger ────────────────────────────────────────────────────────────────────
log = logging.getLogger("helios.desktop")

pyautogui.PAUSE    = 0.4
pyautogui.FAILSAFE = True

# ── Windows FILE_ATTRIBUTE_REPARSE_POINT flag ─────────────────────────────────
_FILE_ATTR_REPARSE = 0x400          # junction / symlink on Windows

# ── Directories to skip during recursive search ───────────────────────────────
SKIP_NAMES: set = {
    # Windows system
    "windows", "system32", "syswow64", "winsxs", "$recycle.bin",
    "programdata", "program files", "program files (x86)",
    # Dev / package dirs
    "appdata", "node_modules", ".git", "__pycache__", "venv", ".venv",
    "mingw64", "mingw32", "usr", "tcl8.6", "tzdata",
    "git", "perl", "ruby", "java", "jdk",
    # Windows phone-sync / cross-device junctions that always error
    "crossdevice", "phone link", "onedrive", "icloudphotos",
}

USER_FOLDERS: List[str] = [
    "Desktop", "Downloads", "Documents", "Music", "Pictures", "Videos"
]

VIDEO_EXTS: set = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"}
AUDIO_EXTS: set = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"}

# ── App → executable map ──────────────────────────────────────────────────────
APP_MAP: dict = {
    "chrome":         r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox":        r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "edge":           r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "vlc":            r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "notepad":        "notepad.exe",
    "calculator":     "calc.exe",
    "paint":          "mspaint.exe",
    "cmd":            "cmd.exe",
    "powershell":     "powershell.exe",
    "taskmanager":    "taskmgr.exe",
    "task manager":   "taskmgr.exe",
    "vscode":         os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    "vs code":        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    "word":           r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel":          r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint":     r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
    "spotify":        os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
    # Explorer handled specially — do NOT put "explorer.exe" here
}

# ── Process-kill map ──────────────────────────────────────────────────────────
KILL_MAP: dict = {
    "vscode":       ["code.exe"],
    "vs code":      ["code.exe"],
    "chrome":       ["chrome.exe"],
    "firefox":      ["firefox.exe"],
    "edge":         ["msedge.exe"],
    "notepad":      ["notepad.exe"],
    "vlc":          ["vlc.exe"],
    "spotify":      ["Spotify.exe"],
    "excel":        ["EXCEL.EXE"],
    "word":         ["WINWORD.EXE"],
    "powerpoint":   ["POWERPNT.EXE"],
    "teams":        ["Teams.exe"],
    "zoom":         ["Zoom.exe"],
    "discord":      ["Discord.exe"],
    "taskmanager":  ["Taskmgr.exe"],
    "task manager": ["Taskmgr.exe"],
    "paint":        ["mspaint.exe"],
    "explorer":     ["explorer.exe"],
}

WEBSITES: dict = {
    "youtube":    "https://www.youtube.com",
    "gmail":      "https://mail.google.com",
    "google":     "https://www.google.com",
    "github":     "https://www.github.com",
    "linkedin":   "https://www.linkedin.com",
    "instagram":  "https://www.instagram.com",
    "whatsapp":   "https://web.whatsapp.com",
    "netflix":    "https://www.netflix.com",
    "twitter":    "https://www.twitter.com",
    "facebook":   "https://www.facebook.com",
    "spotify":    "https://open.spotify.com",
    "bookmyshow": "https://in.bookmyshow.com",
    "paytm":      "https://movies.paytm.com",
}

# ── Extension alias map for search_file ───────────────────────────────────────
EXT_MAP: dict = {
    "video":  list(VIDEO_EXTS), "videos": list(VIDEO_EXTS),
    "audio":  list(AUDIO_EXTS), "music":  list(AUDIO_EXTS),
    "mp4":  [".mp4"],  "mkv":  [".mkv"],  "avi":  [".avi"],
    "mp3":  [".mp3"],  "wav":  [".wav"],
    "txt":  [".txt"],  "pdf":  [".pdf"],
    "doc":  [".doc", ".docx"],
    "img":  [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
    "image":[".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
}

TEXT_SEARCHABLE: set = {
    ".txt", ".md", ".py", ".js", ".ts", ".html", ".css",
    ".json", ".csv", ".log", ".xml", ".yaml", ".yml",
    ".ini", ".cfg", ".bat", ".sh", ".java", ".c", ".cpp",
    ".h", ".cs", ".rb", ".go", ".rs", ".sql",
}


# ═════════════════════════════════════════════════════════════════════════════
# LOW-LEVEL PATH UTILITIES  (Python 3.10 safe)
# ═════════════════════════════════════════════════════════════════════════════

def _is_reparse_point(p: Path) -> bool:
    """
    Detect Windows junctions / symlinks without using follow_symlinks kwarg
    on is_dir() / is_file() (added in 3.12).
    Uses GetFileAttributesW via ctypes — works on 3.10+.
    Falls back to os.stat st_mode check if ctypes fails.
    """
    try:
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(p))  # type: ignore
        if attrs == 0xFFFFFFFF:       # INVALID_FILE_ATTRIBUTES
            return False
        return bool(attrs & _FILE_ATTR_REPARSE)
    except Exception:
        pass
    # Fallback: os.lstat
    try:
        st = os.lstat(p)              # lstat never follows symlinks
        return stat.S_ISLNK(st.st_mode)
    except Exception:
        return False


def _should_skip_dir(p: Path) -> bool:
    """Return True if directory must be excluded from search."""
    name = p.name.lower()
    # Name-based exclusions
    if any(skip in name for skip in SKIP_NAMES):
        log.debug("skip (name): %s", p)
        return True
    # Reparse point (junction / symlink)
    if _is_reparse_point(p):
        log.debug("skip (reparse): %s", p)
        return True
    return False


def _safe_iterdir(directory: Path):
    """Yield Path children; silently swallow any OS error."""
    try:
        for child in directory.iterdir():
            yield child
    except (PermissionError, OSError) as exc:
        log.debug("iterdir error [%s]: %s", directory, exc)


def _safe_is_file(p: Path) -> bool:
    """is_file() without follow_symlinks kwarg — 3.10 compatible."""
    try:
        return p.is_file() and not _is_reparse_point(p)
    except Exception:
        return False


def _safe_is_dir(p: Path) -> bool:
    """is_dir() without follow_symlinks kwarg — 3.10 compatible."""
    try:
        return p.is_dir() and not _is_reparse_point(p)
    except Exception:
        return False


def _safe_rglob(root: Path, words: List[str] = None, exts: List[str] = None, max_results: int = 100) -> List[Path]:
    """
    Stack-based recursive file walk with built-in query filtering.
    Guarantees: no recursion limit, no junction traversal, no crash.
    """
    results: List[Path] = []
    stack = [root]
    while stack and len(results) < max_results:
        current = stack.pop()
        for child in _safe_iterdir(current):
            if len(results) >= max_results:
                break
            try:
                if _is_reparse_point(child):
                    continue
                if child.is_dir():
                    if not _should_skip_dir(child):
                        stack.append(child)
                elif child.is_file():
                    name_lower = child.name.lower()
                    if exts and not any(name_lower.endswith(e) for e in exts):
                        continue
                    if words and not all(w in name_lower for w in words):
                        continue
                    results.append(child)
            except (PermissionError, OSError) as exc:
                log.debug("child error [%s]: %s", child, exc)
    return results


# ═════════════════════════════════════════════════════════════════════════════
# DESKTOP AGENT
# ═════════════════════════════════════════════════════════════════════════════

class DesktopAgent:
    """
    All public methods return str (never raise).
    play_media returns list[str] | str so agent can handle disambiguation.
    """

    # ── File search ───────────────────────────────────────────────────────────
    def search_file(self, query: str) -> List[str]:
        """
        Search user folders for files matching query.
        Never crashes. Returns list of absolute path strings (may be empty).
        """
        try:
            return self._search_file_impl(query)
        except Exception as exc:
            log.error("search_file error: %s", exc, exc_info=True)
            return []

    def _search_file_impl(self, query: str) -> List[str]:
        clean = re.sub(
            r"\b(open|play|find|search|for|the|file|movie|song|music|"
            r"video|on|my|pc|drive|computer|from|in|list)\b",
            "", query.lower()
        ).strip()

        exts:  List[str] = []
        words: List[str] = []
        for token in clean.split():
            if token in EXT_MAP:
                exts.extend(EXT_MAP[token])
            elif token.startswith("."):
                exts.append(token)
            elif len(token) > 1:
                words.append(token)

        if not words and not exts:
            log.debug("search_file: empty query after cleaning '%s'", query)
            return []

        log.info("search_file | words=%s exts=%s", words, exts)

        results: List[str] = []
        home = Path.home()
        onedrive = home / "OneDrive"
        search_roots = []
        for f in USER_FOLDERS:
            if (home / f).is_dir():
                search_roots.append(home / f)
            if onedrive.is_dir() and (onedrive / f).is_dir():
                search_roots.append(onedrive / f)

        for root_dir in search_roots:
            matched_items = _safe_rglob(root_dir, words=words, exts=exts, max_results=20)
            for item in matched_items:
                path_str = str(item)
                if path_str not in results:
                    results.append(path_str)
            if len(results) >= 20:
                break

        if results:
            log.info("search_file: found %d results (Python walk)", len(results))
            return results[:20]

        # PowerShell fallback — restricted to user folders to avoid AppData loops/timeouts
        if words:
            filter_name = words[0]
            try:
                paths_str = ", ".join(f"'$env:USERPROFILE\\{f}'" for f in USER_FOLDERS)
                ps = (
                    f"Get-ChildItem -Path {paths_str} -Recurse "
                    "-ErrorAction SilentlyContinue "
                    f"-Filter '*{filter_name}*' | "
                    "Where-Object { "
                    "  !$_.Attributes.HasFlag("
                    "    [System.IO.FileAttributes]::ReparsePoint) } | "
                    "Select-Object -First 15 -ExpandProperty FullName"
                )
                r = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps],
                    capture_output=True, text=True, timeout=15,
                )
                ps_results = [
                    ln.strip() for ln in r.stdout.splitlines() if ln.strip()
                ]
                if exts:
                    ps_results = [
                        p for p in ps_results
                        if any(p.lower().endswith(e) for e in exts)
                    ]
                results.extend(ps_results)
                log.info("search_file: PowerShell found %d", len(ps_results))
            except Exception as exc:
                log.warning("PowerShell search failed: %s", exc)

        return results[:20]

    # ── Folder search ─────────────────────────────────────────────────────────
    def search_folder(self, query: str) -> List[str]:
        """Search user home tree for directories matching query."""
        try:
            return self._search_folder_impl(query)
        except Exception as exc:
            log.error("search_folder error: %s", exc, exc_info=True)
            return []

    def _search_folder_impl(self, query: str) -> List[str]:
        clean = re.sub(
            r"\b(open|find|search|for|the|folder|directory|named|called|in)\b",
            "", query.lower()
        ).strip()
        if not clean:
            return []
        words = [w for w in clean.split() if len(w) > 1]
        results: List[str] = []
        home = Path.home()
        onedrive = home / "OneDrive"
        stack = []
        for f in USER_FOLDERS:
            if (home / f).is_dir():
                stack.append(home / f)
            if onedrive.is_dir() and (onedrive / f).is_dir():
                stack.append(onedrive / f)
        while stack and len(results) < 10:
            current = stack.pop()
            for child in _safe_iterdir(current):
                try:
                    if _is_reparse_point(child):
                        continue
                    if child.is_dir():
                        if _should_skip_dir(child):
                            continue
                        if all(w in child.name.lower() for w in words):
                            results.append(str(child))
                        stack.append(child)
                except (PermissionError, OSError):
                    pass
        if not results:
            try:
                paths_str = ", ".join(f"'$env:USERPROFILE\\{f}'" for f in USER_FOLDERS)
                ps = (
                    f"Get-ChildItem -Path {paths_str} -Recurse -Directory "
                    "-ErrorAction SilentlyContinue "
                    f"-Filter '*{clean}*' | "
                    "Where-Object { "
                    "  !$_.Attributes.HasFlag("
                    "    [System.IO.FileAttributes]::ReparsePoint) } | "
                    "Select-Object -First 5 -ExpandProperty FullName"
                )
                r = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps],
                    capture_output=True, text=True, timeout=15,
                )
                results = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
            except Exception as exc:
                log.warning("folder search PowerShell failed: %s", exc)
        return results[:10]

    # ── Search inside a file ──────────────────────────────────────────────────
    def search_in_file(self, filepath: str, keyword: str) -> str:
        """Grep-like keyword search inside a text file."""
        try:
            p = Path(filepath)
            if not p.exists():
                return f"File not found: {filepath}"
            if p.suffix.lower() not in TEXT_SEARCHABLE:
                return f"'{p.name}' is not a searchable text file."
            content = p.read_text(encoding="utf-8", errors="ignore")
            lines   = content.splitlines()
            kw      = keyword.lower()
            matches = [
                f"  Line {i}: {ln.rstrip()}"
                for i, ln in enumerate(lines, 1)
                if kw in ln.lower()
            ]
            if not matches:
                return (
                    f"No occurrences of '{keyword}' found in {p.name}.\n"
                    f"({len(lines)} lines searched)"
                )
            header = f"Found {len(matches)} occurrence(s) of '{keyword}' in {p.name}:\n"
            tail   = f"\n  ... and {len(matches)-30} more" if len(matches) > 30 else ""
            return header + "\n".join(matches[:30]) + tail
        except Exception as exc:
            log.error("search_in_file error: %s", exc, exc_info=True)
            return f"Error searching file: {exc}"

    # ── Play media ────────────────────────────────────────────────────────────
    def play_media(self, query: str):
        """
        Returns list[str] of candidate paths (agent handles disambiguation),
        or str error message.
        """
        try:
            results = self.search_file(query)
            media   = [r for r in results if Path(r).suffix.lower() in VIDEO_EXTS | AUDIO_EXTS]
            targets = media if media else results
            if not targets:
                return (
                    f"No media file found matching '{query}'.\n"
                    f"Check Desktop, Downloads, Documents, Music, Pictures, or Videos."
                )
            return targets
        except Exception as exc:
            log.error("play_media error: %s", exc, exc_info=True)
            return f"Error searching for media: {exc}"

    # ── Open File Explorer ────────────────────────────────────────────────────
    def open_explorer(self, path: str = "") -> str:
        """
        Open File Explorer.
        'open file explorer' → opens My Computer / default view.
        'open file explorer at C:\\Users\\...' → opens that folder.
        Uses os.startfile which is the correct Win32 approach.
        """
        try:
            target = path.strip() if path.strip() else "explorer"
            if target == "explorer" or not Path(target).exists():
                os.startfile("explorer")           # opens default Explorer
                log.info("open_explorer: opened default Explorer")
                return "File Explorer opened."
            else:
                os.startfile(target)
                log.info("open_explorer: opened path %s", target)
                return f"File Explorer opened at: {target}"
        except Exception as exc:
            log.error("open_explorer error: %s", exc, exc_info=True)
            # Hard fallback
            try:
                subprocess.Popen(["explorer.exe"])
                return "File Explorer opened."
            except Exception as exc2:
                return f"Could not open Explorer: {exc2}"

    def open_explorer_search(self, query: str) -> str:
        """Open Explorer at the folder/file matching query."""
        try:
            folders = self.search_folder(query)
            if folders:
                os.startfile(folders[0])
                result = f"Opened Explorer at: {folders[0]}"
                if len(folders) > 1:
                    result += "\nOther matches:\n" + "\n".join(
                        f"  • {f}" for f in folders[1:5]
                    )
                return result

            files = self.search_file(query)
            if files:
                parent = str(Path(files[0]).parent)
                os.startfile(parent)
                return (
                    f"Opened Explorer at: {parent}\n"
                    + "\n".join(f"  • {Path(f).name}" for f in files[:5])
                )

            os.startfile("explorer")
            return f"'{query}' not found. Opened Explorer."
        except Exception as exc:
            log.error("open_explorer_search error: %s", exc, exc_info=True)
            return f"Error opening Explorer: {exc}"

    # ── App control ───────────────────────────────────────────────────────────
    def open_app(self, app: str) -> str:
        """Launch an application by name."""
        try:
            key = app.lower().strip()

            # ── Explorer: always use os.startfile, never Popen ────────────
            if key in ("explorer", "file explorer", "my computer",
                       "this pc", "windows explorer"):
                return self.open_explorer()

            exe = APP_MAP.get(key)
            if exe:
                exe_path = Path(exe) if not exe.endswith(".exe") or "\\" in exe else None
                if exe_path and exe_path.exists():
                    subprocess.Popen([str(exe_path)])
                    log.info("open_app: launched %s via APP_MAP", key)
                    return f"Opened {app}."
                elif exe.endswith(".exe") and "\\" not in exe:
                    # system exe like notepad.exe, calc.exe
                    subprocess.Popen(exe, shell=True)
                    log.info("open_app: launched system exe %s", exe)
                    return f"Opened {app}."

            # Try os.startfile (respects Windows file associations)
            try:
                os.startfile(key)
                log.info("open_app: startfile '%s'", key)
                return f"Launched {app}."
            except Exception:
                pass

            # Last resort: shell Popen
            subprocess.Popen(app, shell=True)
            log.info("open_app: shell Popen '%s'", app)
            return f"Launched {app}."
        except Exception as exc:
            log.error("open_app('%s') error: %s", app, exc, exc_info=True)
            return f"Could not open '{app}': {exc}"

    def kill_app(self, app: str) -> str:
        """Force-close a running application."""
        try:
            key     = app.lower().strip()
            targets = KILL_MAP.get(key, [app, app + ".exe"])
            killed  = []
            for proc in psutil.process_iter(["name", "pid"]):
                try:
                    pname = proc.info["name"] or ""
                    if (
                        any(t.lower() == pname.lower() for t in targets)
                        or key in pname.lower()
                    ):
                        proc.kill()
                        killed.append(pname)
                        log.info("kill_app: killed %s (pid %s)", pname, proc.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            if killed:
                return f"Closed: {', '.join(set(killed))}"
            # Fallback: taskkill
            r = subprocess.run(
                ["taskkill", "/F", "/IM", f"{app}.exe"],
                capture_output=True, text=True,
            )
            if r.returncode == 0:
                return f"Closed {app}."
            return f"No running process found for '{app}'."
        except Exception as exc:
            log.error("kill_app error: %s", exc, exc_info=True)
            return f"Error closing '{app}': {exc}"

    # ── Web helpers ───────────────────────────────────────────────────────────
    def open_website(self, site: str, query: str = "") -> str:
        try:
            clean_site = site.lower().strip()
            # If site matches a predefined shortcut, use it
            url = WEBSITES.get(clean_site)
            if not url:
                # Also check without common TLDs in case it matches "youtube" from "youtube.com"
                name_only = clean_site
                for tld in (".com", ".org", ".net", ".in", ".co", ".edu", ".gov"):
                    if clean_site.endswith(tld):
                        name_only = clean_site[:-len(tld)]
                        break
                url = WEBSITES.get(name_only)
                
            if not url:
                # If site already has a dot, assume it is a domain
                if "." in clean_site:
                    url = clean_site
                else:
                    url = f"{clean_site}.com"
                
                if not url.startswith("http"):
                    if not url.startswith("www."):
                        url = f"https://www.{url}"
                    else:
                        url = f"https://{url}"
            
            if query:
                clean_query = query.lower().strip()
                is_cart = any(w in clean_query for w in ("cart", "checkout", "basket"))
                is_login = any(w in clean_query for w in ("login", "sign in", "signin", "sign-in", "signup", "sign up"))
                is_account = any(w in clean_query for w in ("account", "profile", "my account"))
                
                nav_templates = {
                    "swiggy": {
                        "cart": "https://www.swiggy.com/checkout",
                        "login": "https://www.swiggy.com",
                        "account": "https://www.swiggy.com/my-account",
                    },
                    "zomato": {
                        "cart": "https://www.zomato.com/delivery",
                        "login": "https://www.zomato.com",
                        "account": "https://www.zomato.com/user",
                    },
                    "amazon": {
                        "cart": "https://www.amazon.in/gp/cart/view.html",
                        "login": "https://www.amazon.in/ap/signin",
                        "account": "https://www.amazon.in/gp/css/homepage.html",
                    },
                    "github": {
                        "cart": "https://github.com/marketplace",
                        "login": "https://github.com/login",
                        "account": "https://github.com/settings/profile",
                    }
                }
                
                name_only = clean_site
                for tld in (".com", ".org", ".net", ".in", ".co", ".edu", ".gov"):
                    if clean_site.endswith(tld):
                        name_only = clean_site[:-len(tld)]
                        break
                        
                nav_map = nav_templates.get(name_only) or nav_templates.get(clean_site)
                resolved_url = None
                if nav_map:
                    if is_cart:
                        resolved_url = nav_map.get("cart")
                    elif is_login:
                        resolved_url = nav_map.get("login")
                    elif is_account:
                        resolved_url = nav_map.get("account")
                        
                if resolved_url:
                    url = resolved_url
                else:
                    templates = {
                        "swiggy":    "https://www.swiggy.com/search?query={}",
                        "zomato":    "https://www.zomato.com/search?q={}",
                        "amazon":    "https://www.amazon.in/s?k={}",
                        "github":    "https://github.com/search?q={}",
                        "youtube":   "https://www.youtube.com/results?search_query={}",
                        "google":    "https://www.google.com/search?q={}",
                        "wikipedia": "https://en.wikipedia.org/wiki/Special:Search?search={}",
                    }
                    tmpl = templates.get(name_only) or templates.get(clean_site)
                    if tmpl:
                        url = tmpl.format(urllib.parse.quote(query))
                    else:
                        url = f"{url.rstrip('/')}/search?q={urllib.parse.quote(query)}"
                    
            webbrowser.open(url)
            log.info("open_website: %s", url)
            return f"Opened: {url}"
        except Exception as exc:
            return f"Could not open website: {exc}"

    def open_url(self, url: str) -> str:
        try:
            if not url.startswith("http"):
                url = "https://" + url
            webbrowser.open(url)
            return f"Opened: {url}"
        except Exception as exc:
            return f"Could not open URL: {exc}"

    def search_google(self, query: str) -> str:
        try:
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            webbrowser.open(url)
            return f"Searching Google for: {query}"
        except Exception as exc:
            return f"Google search error: {exc}"

    def search_youtube(self, query: str, raw_intent: str = "") -> str:
        try:
            intent = (raw_intent or query).lower().strip()
            is_play_intent = any(w in intent for w in ("play", "stream", "watch", "listen"))
            
            if is_play_intent:
                clean_query = query.lower().strip()
                for w in ("play ", "stream ", "watch ", "listen ", "play a video from ", "play a video from the search ", "play a random video from "):
                    if clean_query.startswith(w):
                        clean_query = clean_query[len(w):].strip()
                for suffix in (" on youtube", " in youtube", " youtube"):
                    if clean_query.endswith(suffix):
                        clean_query = clean_query[:-len(suffix)].strip()
                
                try:
                    import requests
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
                    search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(clean_query)}"
                    r = requests.get(search_url, headers=headers, timeout=10)
                    if r.status_code == 200:
                        matches = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', r.text)
                        if matches:
                            unique_matches = []
                            for m in matches:
                                if m not in unique_matches:
                                    unique_matches.append(m)
                            video_id = unique_matches[0]
                            video_url = f"https://www.youtube.com/watch?v={video_id}"
                            webbrowser.open(video_url)
                            return f"Playing directly on YouTube:\n  • {clean_query}\n  • URL: {video_url}"
                except Exception as e:
                    log.warning("Failed to find direct YouTube video: %s", e)
            
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            webbrowser.open(url)
            return f"Searching YouTube for: {query}"
        except Exception as exc:
            return f"YouTube search error: {exc}"

    # ── Volume / media keys ───────────────────────────────────────────────────
    def volume_up(self, steps: int = 5) -> str:
        try:
            for _ in range(max(1, min(steps, 50))):
                pyautogui.press("volumeup")
            return "Volume increased."
        except Exception as exc:
            return f"Volume error: {exc}"

    def volume_down(self, steps: int = 5) -> str:
        try:
            for _ in range(max(1, min(steps, 50))):
                pyautogui.press("volumedown")
            return "Volume decreased."
        except Exception as exc:
            return f"Volume error: {exc}"

    def mute(self) -> str:
        try:
            pyautogui.press("volumemute")
            return "Volume toggled mute/unmute."
        except Exception as exc:
            return f"Mute error: {exc}"

    # ── Screenshot ────────────────────────────────────────────────────────────
    def screenshot(self) -> str:
        try:
            path = Path.home() / "Desktop" / f"helios_{int(time.time())}.png"
            img  = pyautogui.screenshot()
            img.save(str(path))
            log.info("screenshot saved: %s", path)
            return f"Screenshot saved to Desktop: {path.name}"
        except Exception as exc:
            log.error("screenshot error: %s", exc, exc_info=True)
            return f"Screenshot failed: {exc}"

    # ── System power ──────────────────────────────────────────────────────────
    def lock_screen(self) -> str:
        try:
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
            return "Screen locked."
        except Exception as exc:
            return f"Lock error: {exc}"

    def shutdown(self, delay: int = 0) -> str:
        try:
            subprocess.run(["shutdown", "/s", "/t", str(delay)])
            return f"Shutting down in {delay} seconds."
        except Exception as exc:
            return f"Shutdown error: {exc}"

    def restart(self, delay: int = 0) -> str:
        try:
            subprocess.run(["shutdown", "/r", "/t", str(delay)])
            return f"Restarting in {delay} seconds."
        except Exception as exc:
            return f"Restart error: {exc}"

    def sleep(self) -> str:
        try:
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
            return "Going to sleep..."
        except Exception as exc:
            return f"Sleep error: {exc}"

    # ── System stats ──────────────────────────────────────────────────────────
    def battery_status(self) -> str:
        try:
            b = psutil.sensors_battery()
            if not b:
                return "No battery detected (desktop PC)."
            status = "charging" if b.power_plugged else "discharging"
            secs   = b.secsleft
            if secs < 0 or secs > 86_400 * 30:
                time_str = "calculating..."
            else:
                h, m = divmod(int(secs) // 60, 60)
                time_str = f"{h}h {m}m remaining"
            return f"Battery: {b.percent:.0f}%\nStatus: {status}\nTime: {time_str}"
        except Exception as exc:
            return f"Battery error: {exc}"

    def disk_space(self) -> str:
        try:
            lines = ["Disk Space:"]
            for part in psutil.disk_partitions():
                try:
                    u = psutil.disk_usage(part.mountpoint)
                    lines.append(
                        f"  {part.device}  "
                        f"{u.free//(1024**3)}GB free / "
                        f"{u.total//(1024**3)}GB  ({u.percent}% used)"
                    )
                except Exception:
                    pass
            return "\n".join(lines)
        except Exception as exc:
            return f"Disk space error: {exc}"

    def running_apps(self) -> str:
        try:
            skip = {
                "svchost.exe", "RuntimeBroker.exe", "conhost.exe",
                "csrss.exe", "lsass.exe", "services.exe", "System",
                "Registry", "smss.exe",
            }
            seen:  set = set()
            names: list = []
            for proc in psutil.process_iter(["name"]):
                try:
                    n = proc.info["name"]
                    if n and n not in skip and n not in seen:
                        seen.add(n)
                        names.append(n.replace(".exe", ""))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            names.sort()
            return "Running apps:\n" + "\n".join(f"  • {n}" for n in names[:35])
        except Exception as exc:
            return f"Error listing apps: {exc}"

    def ip_address(self) -> str:
        try:
            import socket
            hostname  = socket.gethostname()
            local_ip  = socket.gethostbyname(hostname)
            lines     = [f"Hostname: {hostname}", f"Local IP: {local_ip}"]
            for iface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == 2:      # AF_INET
                        lines.append(f"  {iface}: {addr.address}")
            return "\n".join(lines)
        except Exception as exc:
            return f"IP error: {exc}"

    def empty_recycle(self) -> str:
        try:
            subprocess.run(
                ["powershell", "-Command",
                 "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
                timeout=15,
            )
            return "Recycle Bin emptied."
        except Exception as exc:
            return f"Recycle error: {exc}"

    def pause_media(self) -> str:
        """Pause playback by pressing global media play/pause key."""
        try:
            pyautogui.press("playpause")
            return "Paused playback."
        except Exception as exc:
            log.error("pause_media error: %s", exc, exc_info=True)
            return f"Error pausing media: {exc}"

    def stop_media(self) -> str:
        """Stop playback by closing open YouTube windows and pressing media key."""
        try:
            import pygetwindow as gw
            closed = []
            for w in gw.getAllWindows():
                if w.title and "youtube" in w.title.lower():
                    try:
                        w.close()
                        closed.append(w.title)
                    except Exception as e:
                        log.warning("Failed to close YouTube window '%s': %s", w.title, e)
            
            # Press system-wide play/pause media key
            pyautogui.press("playpause")
            
            if closed:
                return f"Stopped playback and closed YouTube window(s): {', '.join(closed)}"
            return "Stopped playback."
        except Exception as exc:
            log.error("stop_media error: %s", exc, exc_info=True)
            return f"Error stopping media: {exc}"