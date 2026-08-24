"""
core/desktop_session/target_resolver.py — Desktop Target Resolver
==================================================================
Categorizes desktop action targets into:
1. APPLICATION (validated executable/shortcut on disk)
2. URL (validated web URL)
3. FILE (validated filesystem path)
4. WINDOWS_SETTINGS (ms-settings URI)
5. UNKNOWN (unresolved; fails cleanly without ShellExecute errors)

Never appends .url to arbitrary targets.
Never calls os.startfile on unverified application targets.
"""

import os
import re
import sys
import shutil
import logging
from enum import Enum
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

log = logging.getLogger("helios.desktop_session.target_resolver")


class TargetCategory(str, Enum):
    APPLICATION = "APPLICATION"
    URL = "URL"
    FILE = "FILE"
    WINDOWS_SETTINGS = "WINDOWS_SETTINGS"
    UNKNOWN = "UNKNOWN"


# Deterministic Application Registry
DETERMINISTIC_APP_REGISTRY: Dict[str, list] = {
    "chrome": ["chrome.exe", r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"],
    "google chrome": ["chrome.exe", r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"],
    "edge": ["msedge.exe", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"],
    "microsoft edge": ["msedge.exe", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"],
    "firefox": ["firefox.exe", r"C:\Program Files\Mozilla Firefox\firefox.exe"],
    "mozilla firefox": ["firefox.exe", r"C:\Program Files\Mozilla Firefox\firefox.exe"],
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "calc": ["calc.exe"],
    "cmd": ["cmd.exe"],
    "command prompt": ["cmd.exe"],
    "powershell": ["powershell.exe"],
    "paint": ["mspaint.exe"],
    "mspaint": ["mspaint.exe"],
    "explorer": ["explorer.exe"],
    "file explorer": ["explorer.exe"],
    "settings": ["ms-settings:"],
    "display settings": ["ms-settings:display"],
    "display": ["ms-settings:display"],
    "sound": ["ms-settings:sound"],
    "wifi": ["ms-settings:network-wifi"],
    "bluetooth": ["ms-settings:bluetooth"],
}


class TargetResolver:
    """Resolves semantic desktop action targets into validated Windows targets."""

    @classmethod
    def resolve_target(cls, target_str: str) -> Tuple[TargetCategory, Optional[str], str]:
        """
        Categorize and resolve a target string.
        Returns: (category, resolved_executable_or_uri_or_path, details)
        """
        clean_target = (target_str or "").strip()
        lower_target = clean_target.lower()

        if not clean_target:
            return TargetCategory.UNKNOWN, None, "Empty target provided."

        # Never process .url generated arbitrarily
        if lower_target.endswith(".url") and not os.path.exists(clean_target):
            log.warning("TargetResolver: Rejected fake/missing .url target '%s'", clean_target)
            return TargetCategory.UNKNOWN, None, f"Target '{clean_target}' is an invalid or missing URL shortcut."

        # 1. WINDOWS SETTINGS CATEGORY
        if lower_target in ("settings", "windows settings", "display settings", "display", "sound", "wifi", "bluetooth"):
            uri = DETERMINISTIC_APP_REGISTRY.get(lower_target, ["ms-settings:"])[0]
            return TargetCategory.WINDOWS_SETTINGS, uri, f"Resolved Windows Settings URI '{uri}'"

        if lower_target.startswith("ms-settings:"):
            return TargetCategory.WINDOWS_SETTINGS, clean_target, f"Windows Settings URI '{clean_target}'"

        # 2. URL CATEGORY
        if cls.is_valid_url(clean_target):
            url = clean_target if clean_target.startswith(("http://", "https://")) else f"https://{clean_target}"
            return TargetCategory.URL, url, f"Resolved web URL '{url}'"

        # 3. FILE CATEGORY
        if (os.path.isabs(clean_target) or "/" in clean_target or "\\" in clean_target) and Path(clean_target).exists():
            return TargetCategory.FILE, str(Path(clean_target).resolve()), f"Resolved existing file path '{clean_target}'"

        # 4. APPLICATION CATEGORY (Deterministic Registry & System PATH)
        if lower_target in DETERMINISTIC_APP_REGISTRY:
            for candidate in DETERMINISTIC_APP_REGISTRY[lower_target]:
                if candidate.startswith("ms-settings:"):
                    return TargetCategory.WINDOWS_SETTINGS, candidate, f"Resolved Settings URI '{candidate}'"
                if shutil.which(candidate) or (os.sep in candidate and Path(candidate).exists()):
                    return TargetCategory.APPLICATION, candidate, f"Resolved application '{candidate}' via registry"

        # General System PATH Check (e.g. "notepad", "chrome", "calc")
        sys_exe = shutil.which(clean_target) or shutil.which(f"{clean_target}.exe")
        if sys_exe:
            return TargetCategory.APPLICATION, sys_exe, f"Resolved executable on PATH '{sys_exe}'"

        # Windows Start Menu / Desktop Shortcut Search (.lnk ONLY, must exist)
        lnk_path = cls._find_verified_shortcut(lower_target)
        if lnk_path:
            return TargetCategory.APPLICATION, lnk_path, f"Resolved verified shortcut '{lnk_path}'"

        # UNKNOWN / UNRESOLVED
        log.warning("TargetResolver: Could not resolve target '%s' to any valid application, file, or URL.", clean_target)
        return TargetCategory.UNKNOWN, None, f"Could not resolve target '{clean_target}'. Application or file is not installed or does not exist."

    @classmethod
    def is_valid_url(cls, text: str) -> bool:
        """Check if string is a valid URL or domain target."""
        clean = text.lower().strip()
        if clean.startswith(("http://", "https://")):
            return True
        # Common domain patterns (e.g. amazon.in, google.com, www.croma.com)
        domain_pattern = r"^(www\.)?[a-zA-Z0-9-]+\.(com|in|org|net|co\.in|gov|edu)(/[^\s]*)?$"
        return bool(re.match(domain_pattern, clean))

    @classmethod
    def _find_verified_shortcut(cls, query: str) -> Optional[str]:
        """Search Desktop and Start Menu for existing .lnk shortcuts matching query."""
        search_dirs = [
            Path.home() / "Desktop",
            Path(os.environ.get("PUBLIC", r"C:\Users\Public")) / "Desktop",
            Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu",
            Path(os.environ.get("ALLUSERSPROFILE", r"C:\ProgramData")) / "Microsoft" / "Windows" / "Start Menu",
        ]
        words = query.lower().split()
        candidates = []
        for d in search_dirs:
            if not d.is_dir():
                continue
            try:
                for lnk in d.rglob("*.lnk"):
                    name_lower = lnk.stem.lower()
                    if all(w in name_lower for w in words):
                        candidates.append((len(name_lower), str(lnk)))
            except Exception:
                pass
        if candidates:
            candidates.sort(key=lambda x: x[0])
            return candidates[0][1]
        return None
