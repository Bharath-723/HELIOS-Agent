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
    "chrome":                  r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google chrome":           r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox":                 r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "mozilla firefox":         r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "edge":                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "microsoft edge":          r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "vlc":                     r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "vlc media player":        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "notepad":                 "notepad.exe",
    "calculator":              "calc.exe",
    "calc":                    "calc.exe",
    "paint":                   "mspaint.exe",
    "ms paint":                "mspaint.exe",
    "cmd":                     "cmd.exe",
    "command prompt":          "cmd.exe",
    "powershell":              "powershell.exe",
    "taskmanager":             "taskmgr.exe",
    "task manager":            "taskmgr.exe",
    "vscode":                  os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    "vs code":                 os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    "visual studio code":      os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
    "word":                    r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "microsoft word":          r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel":                   r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "microsoft excel":         r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint":              r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
    "microsoft powerpoint":    r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
    "spotify":                 os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
    "teams":                   os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Teams\current\Teams.exe"),
    "microsoft teams":         os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Teams\current\Teams.exe"),
    "discord":                 os.path.expandvars(r"%LOCALAPPDATA%\Discord\Update.exe"),
    "zoom":                    os.path.expandvars(r"%APPDATA%\Zoom\bin\Zoom.exe"),
    "obs":                     r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
    "obs studio":              r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
    "notepad++":               r"C:\Program Files\Notepad++\notepad++.exe",
    "7zip":                    r"C:\Program Files\7-Zip\7zFM.exe",
    "7-zip":                   r"C:\Program Files\7-Zip\7zFM.exe",
    "winrar":                  r"C:\Program Files\WinRAR\WinRAR.exe",
    "radeon software":         os.path.expandvars(r"%PROGRAMFILES%\AMD\CNext\CNext\RadeonSoftware.exe"),
    "amd software":            os.path.expandvars(r"%PROGRAMFILES%\AMD\CNext\CNext\RadeonSoftware.exe"),
    "amd radeon software":     os.path.expandvars(r"%PROGRAMFILES%\AMD\CNext\CNext\RadeonSoftware.exe"),
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
            filter_name = re.sub(r'[^a-zA-Z0-9.\-_ ]', '', words[0]).strip()
            if not filter_name:
                log.warning("search_file: filter_name became empty after sanitization")
                return results[:20]
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
            try:
                clean_sanitized = re.sub(r'[^a-zA-Z0-9.\-_ ]', '', clean).strip()
                if not clean_sanitized:
                    return results[:10]
                paths_str = ", ".join(f"'$env:USERPROFILE\\{f}'" for f in USER_FOLDERS)
                ps = (
                    f"Get-ChildItem -Path {paths_str} -Recurse -Directory "
                    "-ErrorAction SilentlyContinue "
                    f"-Filter '*{clean_sanitized}*' | "
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

    # ── File Operations & Manipulation ───────────────────────────────────────
    def _resolve_file_path(self, query: str) -> Path | None:
        if not query:
            return None
        p = Path(query)
        if p.exists():
            return p
        matches = self.search_file(query)
        if matches:
            return Path(matches[0])
        return None

    def _resolve_target_dir(self, dest: str) -> Path:
        d_lower = dest.lower().strip() if dest else ""
        home = Path.home()
        targets = {
            "desktop": home / "Desktop",
            "downloads": home / "Downloads",
            "documents": home / "Documents",
            "pictures": home / "Pictures",
            "videos": home / "Videos",
            "music": home / "Music",
            "c:\\users": Path("C:/Users"),
            "users": Path("C:/Users"),
        }
        if d_lower in targets:
            return targets[d_lower]
        p = Path(dest) if dest else home / "Desktop"
        if p.exists():
            return p
        p.mkdir(parents=True, exist_ok=True)
        return p

    def move_file(self, src: str, dest: str = "") -> str:
        """Move or cut/paste a file/folder to a target directory or new path."""
        try:
            src_path = self._resolve_file_path(src)
            if not src_path or not src_path.exists():
                return f"Source file '{src}' not found on PC."

            dest_path = self._resolve_target_dir(dest)
            import shutil
            final_dest = shutil.move(str(src_path), str(dest_path))
            log.info("move_file: moved %s to %s", src_path, final_dest)
            return f"📁 Moved '{src_path.name}' to '{final_dest}' successfully!"
        except Exception as exc:
            log.error("move_file error: %s", exc, exc_info=True)
            return f"Could not move file: {exc}"

    def copy_file(self, src: str, dest: str = "") -> str:
        """Copy a file/folder to a target directory."""
        try:
            src_path = self._resolve_file_path(src)
            if not src_path or not src_path.exists():
                return f"Source file '{src}' not found on PC."

            dest_path = self._resolve_target_dir(dest)
            import shutil
            if src_path.is_dir():
                final_dest = shutil.copytree(str(src_path), str(dest_path / src_path.name), dirs_exist_ok=True)
            else:
                final_dest = shutil.copy2(str(src_path), str(dest_path))
            log.info("copy_file: copied %s to %s", src_path, final_dest)
            return f"📋 Copied '{src_path.name}' to '{final_dest}' successfully!"
        except Exception as exc:
            log.error("copy_file error: %s", exc, exc_info=True)
            return f"Could not copy file: {exc}"

    def rename_file(self, src: str, new_name: str) -> str:
        """Rename a file or folder."""
        try:
            src_path = self._resolve_file_path(src)
            if not src_path or not src_path.exists():
                return f"File '{src}' not found."

            clean_new = Path(new_name).name
            target = src_path.parent / clean_new
            src_path.rename(target)
            log.info("rename_file: renamed %s to %s", src_path, target)
            return f"✏ Renamed '{src_path.name}' to '{target.name}' successfully!"
        except Exception as exc:
            log.error("rename_file error: %s", exc, exc_info=True)
            return f"Could not rename file: {exc}"

    def delete_file(self, path_str: str) -> str:
        """Delete a file or folder safely."""
        try:
            src_path = self._resolve_file_path(path_str)
            if not src_path or not src_path.exists():
                return f"File '{path_str}' not found."

            if src_path.is_dir():
                import shutil
                shutil.rmtree(str(src_path))
            else:
                src_path.unlink()
            log.info("delete_file: deleted %s", src_path)
            return f"🗑 Deleted '{src_path.name}' successfully!"
        except Exception as exc:
            log.error("delete_file error: %s", exc, exc_info=True)
            return f"Could not delete file: {exc}"

    def deep_file_search(self, query: str, auto_play: bool = False) -> str:
        """
        Deep recursive filesystem search across all accessible Windows drives and user folders.
        Finds files by keywords (e.g. 'spiderman movie downloaded a year ago').
        If auto_play is True or prompt contains play/watch, automatically opens/plays the movie!
        """
        try:
            # Strip punctuation first
            raw_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', query.lower())
            stop_words = {
                "i", "downloaded", "a", "year", "ago", "movie", "video", "film", "file",
                "where", "is", "got", "saved", "save", "it", "search", "find", "for", "me",
                "can", "you", "if", "found", "kindly", "play", "the", "open", "watch", "run",
                "but", "dont", "don't", "know", "even", "by", "searching", "in", "explorer",
                "also", "not", "visible", "show", "tell", "location", "path"
            }
            tokens = [t.strip() for t in raw_clean.split() if len(t.strip()) > 1 and t.strip() not in stop_words]

            if not tokens:
                # Fallback to key nouns in query
                tokens = [t.strip() for t in raw_clean.split() if len(t.strip()) > 2]

            log.info("deep_file_search | tokens=%s raw_query='%s'", tokens, query)

            home = Path.home()
            search_roots = []
            for f in ["Downloads", "Videos", "Desktop", "Documents", "Pictures", "Music"]:
                if (home / f).is_dir():
                    search_roots.append(home / f)

            for letter in ["C", "D", "E", "F"]:
                drive_p = Path(f"{letter}:/")
                if drive_p.is_dir() and drive_p not in search_roots:
                    search_roots.append(drive_p)

            results: list[Path] = []
            for root in search_roots:
                if len(results) >= 20:
                    break
                matched = _safe_rglob(root, words=tokens, max_results=10)
                for item in matched:
                    if item not in results:
                        results.append(item)

            # If multi-token match returned empty, try single best token
            if not results and tokens:
                best_tokens = sorted(tokens, key=len, reverse=True)
                for t in best_tokens:
                    for root in search_roots:
                        if len(results) >= 20:
                            break
                        matched = _safe_rglob(root, words=[t], max_results=10)
                        for item in matched:
                            if item not in results:
                                results.append(item)

            if not results:
                return f"🔍 **Deep Search Complete**: No files matching '{' '.join(tokens)}' found on your computer."

            should_play = auto_play or any(kw in query.lower() for kw in ("play", "watch", "open", "launch", "run"))

            video_matches = [p for p in results if p.suffix.lower() in VIDEO_EXTS]
            chosen = video_matches[0] if video_matches else results[0]

            msg = f"🔍 **Deep Search Result**:\nFound {len(results)} matching file(s):\n"
            msg += "\n".join(f"  • **{p.name}**\n    `{p.absolute()}`" for p in results[:5])

            if should_play and chosen:
                try:
                    os.startfile(str(chosen))
                    msg += f"\n\n🎬 **Playing file now**: `{chosen.name}`"
                    log.info("deep_file_search: playing movie file %s", chosen)
                except Exception as exc:
                    msg += f"\n\n⚠ Could not auto-play file: {exc}"

            return msg
        except Exception as exc:
            log.error("deep_file_search error: %s", exc, exc_info=True)
            return f"Deep search error: {exc}"

    # ── App control ───────────────────────────────────────────────────────────

    @staticmethod
    def _find_shortcut(query: str) -> str | None:
        """
        Search Desktop and Start Menu for a .lnk shortcut whose name
        contains all words from `query`.  Returns the full .lnk path or None.
        Searches: user Desktop, public Desktop, user Start Menu, all-users
        Start Menu.
        """
        words = query.lower().split()
        search_dirs = [
            Path.home() / "Desktop",
            Path(os.environ.get("PUBLIC", r"C:\Users\Public")) / "Desktop",
            Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu",
            Path(os.environ.get("ALLUSERSPROFILE", r"C:\ProgramData"))
            / "Microsoft" / "Windows" / "Start Menu",
        ]
        candidates: list[tuple[int, str]] = []   # (match_score, path)
        for d in search_dirs:
            if not d.is_dir():
                continue
            try:
                for lnk in d.rglob("*.lnk"):
                    name_lower = lnk.stem.lower()
                    if all(w in name_lower for w in words):
                        # Prefer shorter / more specific names
                        candidates.append((len(name_lower), str(lnk)))
            except Exception:
                pass
        if candidates:
            candidates.sort(key=lambda x: x[0])
            return candidates[0][1]
        return None

    @staticmethod
    def _find_uwp_app(query: str) -> str | None:
        """
        Query Windows Store / UWP apps via PowerShell Get-StartApps.
        Returns the AppID string suitable for Start-Process, or None.
        """
        try:
            words = query.lower().split()
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-StartApps | Select-Object Name,AppID | ConvertTo-Json -Compress"],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode != 0 or not r.stdout.strip():
                return None
            import json
            items = json.loads(r.stdout)
            if isinstance(items, dict):   # single result
                items = [items]
            candidates: list[tuple[int, str]] = []
            for item in items:
                name  = (item.get("Name") or "").lower()
                appid = item.get("AppID") or ""
                if not appid:
                    continue
                if all(w in name for w in words):
                    candidates.append((len(name), appid))
            if candidates:
                candidates.sort(key=lambda x: x[0])
                return candidates[0][1]
            # ── Fallback: best partial-word overlap ───────────────────────
            # Score = number of query words found in app name (desc), then
            # name length (asc).  Minimum: the first query word must hit.
            best_score, best_id = 0, None
            anchor = words[0] if words else ""
            for item in items:
                name  = (item.get("Name") or "").lower()
                appid = item.get("AppID") or ""
                if not appid or not anchor:
                    continue
                if anchor not in name:
                    continue
                score = sum(1 for w in words if w in name)
                if score > best_score:
                    best_score = score
                    best_id    = appid
            return best_id   # None if nothing matched anchor
        except Exception as exc:
            log.debug("_find_uwp_app error: %s", exc)
        return None

    def open_app(self, app: str) -> str:
        """
        Launch an application or target using TargetResolver execution categorization pipeline.
        Categories:
          1. APPLICATION: Validated executable / shortcut on disk.
          2. URL: Validated web URL.
          3. FILE: Validated existing filesystem path.
          4. WINDOWS SETTINGS: ms-settings URI.
          5. UNKNOWN: Fails cleanly without launching ShellExecute / missing shortcut popups.
        """
        try:
            key = app.lower().strip()

            # ── 1. Explorer special handling ──────────────────────────────
            if key in ("explorer", "file explorer", "my computer", "this pc", "windows explorer"):
                return self.open_explorer()

            # ── 2. Target Resolver Categorization & Resolution ────────────
            from core.desktop_session.target_resolver import TargetResolver, TargetCategory
            cat, resolved, details = TargetResolver.resolve_target(app)

            log.info("[DESKTOP EXEC] Action: OPEN_APPLICATION | Target: '%s' | Category: %s | Resolved: '%s' | Details: %s",
                     app, cat.value, resolved, details)

            if cat == TargetCategory.WINDOWS_SETTINGS:
                import os
                os.startfile(resolved or "ms-settings:")
                return f"Opened Windows Settings ({app})."

            elif cat == TargetCategory.URL:
                return self.open_website(resolved)

            elif cat == TargetCategory.FILE:
                import os
                os.startfile(resolved)
                return f"Opened file '{app}'."

            elif cat == TargetCategory.APPLICATION and resolved:
                if resolved.endswith(".lnk"):
                    import os
                    os.startfile(resolved)
                    return f"Opened {app} via shortcut."
                else:
                    subprocess.Popen([resolved])
                    return f"Opened {app}."

            elif cat == TargetCategory.UNKNOWN:
                log.warning("open_app: Target '%s' could not be resolved. Aborting launch to prevent missing shortcut errors.", app)
                return (
                    f"Could not find or launch '{app}'.\n"
                    f"Make sure the application is installed on your system.\n"
                    f"Tip: Try specifying the exact application name (e.g. 'Chrome', 'Notepad', 'Settings')."
                )

            return f"Opened {app}."
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
                # If site contains a space and is not a scheme-prefixed URL, treat as a search query
                if " " in clean_site and not clean_site.startswith(("http://", "https://")):
                    clean_query = query.strip()
                    full_query = f"{clean_site} {clean_query}" if clean_query else clean_site
                    url = f"https://www.google.com/search?q={urllib.parse.quote(full_query)}"
                    query = ""
                else:
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