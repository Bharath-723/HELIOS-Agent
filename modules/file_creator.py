"""HELIOS - File Creator: create files with content at specific locations"""
import os
import subprocess
from pathlib import Path

LOCATIONS = {
    "desktop":   Path.home() / "Desktop",
    "documents": Path.home() / "Documents",
    "downloads": Path.home() / "Downloads",
    "home":      Path.home(),
}

class FileCreator:
    def create_file(self, name: str, location: str = "desktop",
                    content: str = "", open_after: bool = True) -> str:
        folder = LOCATIONS.get(location.lower(), Path.home() / "Desktop")
        folder.mkdir(parents=True, exist_ok=True)
        if not Path(name).suffix:
            name += ".txt"
        path = folder / name
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        result = f"File created: {path.name}\nLocation: {path}"
        if content:
            result += f"\nContent: {content[:60]}{'...' if len(content)>60 else ''}"
        if open_after:
            try:
                os.startfile(str(path))
                result += "\nOpened in default editor."
            except Exception:
                subprocess.Popen(["notepad.exe", str(path)])
        return result

    def create_in_notepad(self, name: str, location: str = "desktop",
                          content: str = "") -> str:
        folder = LOCATIONS.get(location.lower(), Path.home() / "Desktop")
        folder.mkdir(parents=True, exist_ok=True)
        if not Path(name).suffix:
            name += ".txt"
        path = folder / name
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        subprocess.Popen(["notepad.exe", str(path)])
        return (f"File '{path.name}' created on {location}.\n"
                f"Content: {content}\nOpened in Notepad.")
