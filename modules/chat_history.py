"""HELIOS - Chat History: save/load conversations by session"""
import json
import logging
from datetime import datetime
from pathlib import Path

log = logging.getLogger("helios.chat_history")

# Resolve absolute path relative to project root
HIST_DIR = Path(__file__).parent.parent / "data" / "chat_history"
try:
    HIST_DIR.mkdir(parents=True, exist_ok=True)
except Exception as exc:
    log.error("Failed to create chat history directory %s: %s", HIST_DIR, exc, exc_info=True)

INDEX = HIST_DIR / "index.json"


def _load_idx():
    if not INDEX.exists():
        return []
    try:
        return json.loads(INDEX.read_text(encoding="utf-8"))
    except Exception as exc:
        log.error("Failed to load chat history index: %s", exc, exc_info=True)
        return []


def _save_idx(sessions):
    try:
        INDEX.write_text(json.dumps(sessions, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        log.error("Failed to save chat history index: %s", exc, exc_info=True)


class ChatHistory:
    def __init__(self):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.messages = []
        log.info("Initializing new ChatHistory session: %s", self.session_id)
        try:
            sessions = _load_idx()
            sessions.insert(0, {
                "id": self.session_id,
                "started": datetime.now().isoformat(),
                "title": f"Session {datetime.now().strftime('%b %d, %H:%M')}",
                "preview": "", "message_count": 0,
            })
            _save_idx(sessions)
        except Exception as exc:
            log.error("Error creating ChatHistory session in __init__: %s", exc, exc_info=True)

    def add(self, role: str, content: str):
        log.debug("Adding message to session %s: role=%s", self.session_id, role)
        try:
            self.messages.append({"role": role, "content": content,
                                   "time": datetime.now().isoformat()})
            session_file = HIST_DIR / f"{self.session_id}.json"
            session_file.write_text(
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
        except Exception as exc:
            log.error("Error in ChatHistory.add: %s", exc, exc_info=True)

    def get_all(self) -> list:
        try:
            return _load_idx()[:20]
        except Exception as exc:
            log.error("Error in ChatHistory.get_all: %s", exc, exc_info=True)
            return []

    def load(self, session_id: str) -> list:
        log.info("Loading ChatHistory session: %s", session_id)
        try:
            f = HIST_DIR / f"{session_id}.json"
            if not f.exists():
                log.warning("ChatHistory session file not found: %s", f)
                return []
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:
            log.error("Error in ChatHistory.load for session %s: %s", session_id, exc, exc_info=True)
            return []

    def delete(self, session_id: str):
        log.info("Deleting ChatHistory session: %s", session_id)
        try:
            f = HIST_DIR / f"{session_id}.json"
            if f.exists():
                f.unlink()
            _save_idx([s for s in _load_idx() if s["id"] != session_id])
        except Exception as exc:
            log.error("Error in ChatHistory.delete for session %s: %s", session_id, exc, exc_info=True)

    def clear_all(self):
        log.info("Clearing all ChatHistory sessions")
        try:
            for f in HIST_DIR.glob("*.json"):
                try:
                    f.unlink()
                except Exception as exc:
                    log.warning("Failed to unlink chat file %s: %s", f, exc)
            _save_idx([])
        except Exception as exc:
            log.error("Error in ChatHistory.clear_all: %s", exc, exc_info=True)
