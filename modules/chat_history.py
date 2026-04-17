"""HELIOS - Chat History: save/load conversations by session"""
import json
from datetime import datetime
from pathlib import Path

HIST_DIR = Path("data/chat_history")
HIST_DIR.mkdir(parents=True, exist_ok=True)
INDEX = HIST_DIR / "index.json"


def _load_idx():
    if not INDEX.exists():
        return []
    return json.loads(INDEX.read_text(encoding="utf-8"))


def _save_idx(sessions):
    INDEX.write_text(json.dumps(sessions, indent=2, ensure_ascii=False), encoding="utf-8")


class ChatHistory:
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.messages = []
        sessions = _load_idx()
        sessions.insert(0, {
            "id": self.session_id,
            "started": datetime.now().isoformat(),
            "title": f"Session {datetime.now().strftime('%b %d, %H:%M')}",
            "preview": "", "message_count": 0,
        })
        _save_idx(sessions)

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content,
                               "time": datetime.now().isoformat()})
        (HIST_DIR / f"{self.session_id}.json").write_text(
            json.dumps(self.messages, indent=2, ensure_ascii=False),
            encoding="utf-8")
        sessions = _load_idx()
        for s in sessions:
            if s["id"] == self.session_id:
                if role == "user" and not s["preview"]:
                    s["title"] = content[:40] + ("..." if len(content) > 40 else "")
                    s["preview"] = content[:80]
                s["message_count"] = len(self.messages)
                break
        _save_idx(sessions)

    def get_all(self) -> list:
        return _load_idx()[:20]

    def load(self, session_id: str) -> list:
        f = HIST_DIR / f"{session_id}.json"
        if not f.exists():
            return []
        return json.loads(f.read_text(encoding="utf-8"))

    def delete(self, session_id: str):
        f = HIST_DIR / f"{session_id}.json"
        if f.exists():
            f.unlink()
        _save_idx([s for s in _load_idx() if s["id"] != session_id])

    def clear_all(self):
        for f in HIST_DIR.glob("*.json"):
            f.unlink()
