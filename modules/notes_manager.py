"""HELIOS - Notes Manager: create, read, list, search, summarize notes"""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

log = logging.getLogger("helios.notes_manager")

# Resolve absolute path relative to project root
NOTES_DIR = Path(os.getenv("NOTES_DIR", Path(__file__).parent.parent / "data" / "notes"))
try:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
except Exception as exc:
    log.error("Failed to create notes directory %s: %s", NOTES_DIR, exc, exc_info=True)

INDEX = NOTES_DIR / ".index.json"

def _load_index():
    if not INDEX.exists():
        return {}
    try:
        return json.loads(INDEX.read_text(encoding="utf-8"))
    except Exception as exc:
        log.error("Failed to load notes index: %s", exc, exc_info=True)
        return {}

def _save_index(idx):
    try:
        INDEX.write_text(json.dumps(idx, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        log.error("Failed to save notes index: %s", exc, exc_info=True)

class NotesManager:
    def __init__(self, llm):
        self.llm = llm
        self.idx = _load_index()
        log.info("NotesManager initialized with %d index entries.", len(self.idx))

    def create(self, title: str, content: str = "") -> str:
        log.info("create note called: title='%s'", title)
        try:
            ts = datetime.now()
            slug = title.lower().replace(" ", "_")[:40]
            fname = f"{ts.strftime('%Y%m%d_%H%M%S')}_{slug}.md"
            fpath = NOTES_DIR / fname
            
            note_content = f"# {title}\n\n**Created:** {ts.strftime('%Y-%m-%d %H:%M')}\n\n---\n\n{content}\n"
            fpath.write_text(note_content, encoding="utf-8")
            
            self.idx[fname] = {"title": title, "created": ts.isoformat(), "filepath": str(fpath)}
            _save_index(self.idx)
            
            log.info("Successfully created note: %s", fname)
            return f"Note '{title}' saved as {fname}"
        except Exception as exc:
            log.error("Error creating note: %s", exc, exc_info=True)
            return f"Failed to create note: {exc}"

    def read(self, title: str) -> str:
        log.info("read note called: title='%s'", title)
        try:
            path = NOTES_DIR / title
            if not path.exists():
                for fn, m in self.idx.items():
                    if title.lower() in m["title"].lower():
                        path = Path(m["filepath"])
                        break
            if path.exists():
                return path.read_text(encoding="utf-8")
            
            log.warning("Note not found: %s", title)
            return f"Note '{title}' not found."
        except Exception as exc:
            log.error("Error reading note: %s", exc, exc_info=True)
            return f"Failed to read note: {exc}"

    def list_notes(self) -> str:
        log.info("list_notes called")
        try:
            if not self.idx:
                return "No notes yet. Create one with: 'create a note about...'"
            lines = ["Your Notes:\n"]
            for fn, m in sorted(self.idx.items(), key=lambda x: x[1]["created"], reverse=True):
                lines.append(f"  • {m['title']} — {m['created'][:10]}")
            return "\n".join(lines)
        except Exception as exc:
            log.error("Error listing notes: %s", exc, exc_info=True)
            return f"Failed to list notes: {exc}"

    def search(self, query: str) -> str:
        log.info("search note called: query='%s'", query)
        try:
            results = []
            for fn in NOTES_DIR.glob("*.md"):
                try:
                    if query.lower() in fn.read_text(encoding="utf-8").lower():
                        results.append(self.idx.get(fn.name, {}).get("title", fn.stem))
                except Exception as file_exc:
                    log.warning("Could not read note file during search %s: %s", fn, file_exc)
            if not results:
                return f"No notes found containing '{query}'."
            return f"Found {len(results)} note(s):\n" + "\n".join(f"  • {r}" for r in results)
        except Exception as exc:
            log.error("Error searching notes: %s", exc, exc_info=True)
            return f"Failed to search notes: {exc}"

    def summarize(self, title: str) -> str:
        log.info("summarize note called: title='%s'", title)
        try:
            content = self.read(title)
            if "not found" in content:
                return content
            resp = self.llm.chat(f"Summarize in 3-5 bullet points:\n\n{content}")
            return f"Summary:\n\n{resp.content}"
        except Exception as exc:
            log.error("Error summarizing note: %s", exc, exc_info=True)
            return f"Failed to summarize note: {exc}"
