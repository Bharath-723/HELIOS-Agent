"""HELIOS - Notes Manager: create, read, list, search, summarize notes"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

NOTES_DIR = Path(os.getenv("NOTES_DIR", "data/notes"))
NOTES_DIR.mkdir(parents=True, exist_ok=True)
INDEX = NOTES_DIR / ".index.json"

def _load_index():
    return json.loads(INDEX.read_text()) if INDEX.exists() else {}

def _save_index(idx):
    INDEX.write_text(json.dumps(idx, indent=2, ensure_ascii=False))

class NotesManager:
    def __init__(self, llm):
        self.llm = llm
        self.idx = _load_index()

    def create(self, title: str, content: str = "") -> str:
        ts = datetime.now()
        slug = title.lower().replace(" ", "_")[:40]
        fname = f"{ts.strftime('%Y%m%d_%H%M%S')}_{slug}.md"
        fpath = NOTES_DIR / fname
        fpath.write_text(f"# {title}\n\n**Created:** {ts.strftime('%Y-%m-%d %H:%M')}\n\n---\n\n{content}\n", encoding="utf-8")
        self.idx[fname] = {"title": title, "created": ts.isoformat(), "filepath": str(fpath)}
        _save_index(self.idx)
        return f"Note '{title}' saved as {fname}"

    def read(self, title: str) -> str:
        path = NOTES_DIR / title
        if not path.exists():
            for fn, m in self.idx.items():
                if title.lower() in m["title"].lower():
                    path = Path(m["filepath"]); break
        return path.read_text(encoding="utf-8") if path.exists() else f"Note '{title}' not found."

    def list_notes(self) -> str:
        if not self.idx:
            return "No notes yet. Create one with: 'create a note about...'"
        lines = ["Your Notes:\n"]
        for fn, m in sorted(self.idx.items(), key=lambda x: x[1]["created"], reverse=True):
            lines.append(f"  • {m['title']} — {m['created'][:10]}")
        return "\n".join(lines)

    def search(self, query: str) -> str:
        results = []
        for fn in NOTES_DIR.glob("*.md"):
            if query.lower() in fn.read_text(encoding="utf-8").lower():
                results.append(self.idx.get(fn.name, {}).get("title", fn.stem))
        if not results:
            return f"No notes found containing '{query}'."
        return f"Found {len(results)} note(s):\n" + "\n".join(f"  • {r}" for r in results)

    def summarize(self, title: str) -> str:
        content = self.read(title)
        if "not found" in content:
            return content
        resp = self.llm.chat(f"Summarize in 3-5 bullet points:\n\n{content}")
        return f"Summary:\n\n{resp.content}"
