"""HELIOS - Chat History: save/load conversations by session"""
import json
import logging
from datetime import datetime
from pathlib import Path

from core.system import paths_manager

log = logging.getLogger("helios.chat_history")

# Writable chat history directory from PathsManager (%APPDATA%/HELIOS/ChatHistory or ./Data/ChatHistory)
HIST_DIR = paths_manager.chat_history_dir
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

    def purge_expired(self):
        """Purge soft-deleted sessions older than 7 days."""
        try:
            sessions = _load_idx()
            now = datetime.now()
            updated = []
            for s in sessions:
                if s.get("is_deleted") and s.get("deleted_at"):
                    try:
                        del_time = datetime.fromisoformat(s["deleted_at"])
                        if (now - del_time).days >= 7:
                            f = HIST_DIR / f"{s['id']}.json"
                            if f.exists():
                                f.unlink()
                            log.info("7-day retention expired. Permanently purged session %s", s["id"])
                            continue
                    except Exception:
                        pass
                updated.append(s)
            _save_idx(updated)
        except Exception as exc:
            log.error("Error in purge_expired: %s", exc, exc_info=True)

    def get_all(self) -> list:
        try:
            self.purge_expired()
            sessions = _load_idx()
            return [s for s in sessions if not s.get("is_deleted")]
        except Exception as exc:
            log.error("Error in ChatHistory.get_all: %s", exc, exc_info=True)
            return []

    def get_recently_deleted(self) -> list:
        try:
            self.purge_expired()
            sessions = _load_idx()
            return [s for s in sessions if s.get("is_deleted")]
        except Exception as exc:
            log.error("Error in get_recently_deleted: %s", exc, exc_info=True)
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

    def soft_delete(self, session_id: str):
        """Soft delete session, preserving it for 7-day recovery window."""
        log.info("Soft deleting ChatHistory session: %s", session_id)
        try:
            sessions = _load_idx()
            for s in sessions:
                if s["id"] == session_id:
                    s["is_deleted"] = True
                    s["deleted_at"] = datetime.now().isoformat()
                    break
            _save_idx(sessions)
        except Exception as exc:
            log.error("Error in ChatHistory.soft_delete for session %s: %s", session_id, exc, exc_info=True)

    def restore_session(self, session_id: str):
        """Restore a soft-deleted session back to active Chat History."""
        log.info("Restoring ChatHistory session: %s", session_id)
        try:
            sessions = _load_idx()
            for s in sessions:
                if s["id"] == session_id:
                    s["is_deleted"] = False
                    s["deleted_at"] = None
                    break
            _save_idx(sessions)
        except Exception as exc:
            log.error("Error in ChatHistory.restore_session for session %s: %s", session_id, exc, exc_info=True)

    def permanent_delete(self, session_id: str):
        """Permanently delete a session file and index entry."""
        log.info("Permanently deleting ChatHistory session: %s", session_id)
        try:
            f = HIST_DIR / f"{session_id}.json"
            if f.exists():
                f.unlink()
            _save_idx([s for s in _load_idx() if s["id"] != session_id])
        except Exception as exc:
            log.error("Error in ChatHistory.permanent_delete for session %s: %s", session_id, exc, exc_info=True)

    def permanent_delete_all(self):
        """Permanently delete all soft-deleted sessions."""
        log.info("Permanently deleting all soft-deleted ChatHistory sessions")
        try:
            sessions = _load_idx()
            remaining = []
            for s in sessions:
                if s.get("is_deleted"):
                    f = HIST_DIR / f"{s['id']}.json"
                    if f.exists():
                        try:
                            f.unlink()
                        except Exception:
                            pass
                else:
                    remaining.append(s)
            _save_idx(remaining)
        except Exception as exc:
            log.error("Error in permanent_delete_all: %s", exc, exc_info=True)

    def delete(self, session_id: str):
        self.soft_delete(session_id)

    def clear_all(self):
        log.info("Clearing all ChatHistory sessions to soft-deleted state")
        try:
            sessions = _load_idx()
            now_iso = datetime.now().isoformat()
            for s in sessions:
                s["is_deleted"] = True
                s["deleted_at"] = now_iso
            _save_idx(sessions)
        except Exception as exc:
            log.error("Error in ChatHistory.clear_all: %s", exc, exc_info=True)
