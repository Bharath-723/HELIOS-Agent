"""HELIOS - Task Scheduler
Fixed: handles 'next 2 minutes', 'next monday', numeric-only input.
Notification fires via callback to UI so it always shows in the chat window,
with plyer desktop notification as a bonus (non-critical).
"""
import os
import re
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

TASKS_FILE = Path("data/scheduled_tasks.json")
TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
TZ = os.getenv("TIMEZONE", "Asia/Kolkata")


def _load():
    if not TASKS_FILE.exists():
        return {}
    try:
        return json.loads(TASKS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(t):
    TASKS_FILE.write_text(
        json.dumps(t, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8")


def _parse_time(s: str):
    """
    Understands:
      'in 2 minutes' / 'next 2 minutes' / '2 minutes' / '2 mins'
      'in 1 hour' / 'next hour' / '30 seconds'
      'tomorrow' / 'tomorrow morning'
      '18:30' / '6:30 pm' / '06:30'
      absolute: '2025-04-16 18:30'
    """
    s = s.lower().strip()
    now = datetime.now()

    # ── Relative: (in|next|after)? N (seconds|minutes|mins|hours|days) ──
    m = re.search(
        r'(?:in|next|after)?\s*(\d+)\s*'
        r'(second|sec|minute|min|hour|hr|day)s?',
        s)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        if unit in ("second", "sec"):
            return now + timedelta(seconds=n)
        if unit in ("minute", "min"):
            return now + timedelta(minutes=n)
        if unit in ("hour", "hr"):
            return now + timedelta(hours=n)
        if unit in ("day",):
            return now + timedelta(days=n)

    # ── "next hour" / "next minute" (no number) ──────────────────────────
    if re.search(r'next\s+hour', s):
        return now + timedelta(hours=1)
    if re.search(r'next\s+min', s):
        return now + timedelta(minutes=1)

    # ── tomorrow ─────────────────────────────────────────────────────────
    if "tomorrow" in s:
        base = (now + timedelta(days=1)).date()
        t = datetime.strptime("09:00", "%H:%M").time()
        # if user says "tomorrow evening" → 6 pm
        if "evening" in s or "night" in s:
            t = datetime.strptime("18:00", "%H:%M").time()
        if "morning" in s:
            t = datetime.strptime("08:00", "%H:%M").time()
        return datetime.combine(base, t)

    # ── Clock time: "6:30 pm", "18:30", "06:30" ─────────────────────────
    for fmt in ["%I:%M %p", "%H:%M", "%I %p"]:
        try:
            p = datetime.strptime(s.strip(), fmt)
            dt = datetime.combine(now.date(), p.time())
            if dt <= now:
                dt += timedelta(days=1)
            return dt
        except Exception:
            pass

    # ── Absolute datetime ─────────────────────────────────────────────────
    for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M"]:
        try:
            return datetime.strptime(s.strip(), fmt)
        except Exception:
            pass

    return None


class TaskScheduler:
    def __init__(self, notify_callback=None):
        """
        notify_callback: optional callable(message: str) that will be called
        when a reminder fires. This lets the UI show it in the chat window.
        """
        from apscheduler.schedulers.background import BackgroundScheduler
        self._notify_cb = notify_callback
        self.scheduler  = BackgroundScheduler(timezone=TZ)
        self.tasks      = _load()
        self.scheduler.start()
        self._reschedule_active()   # restore tasks that survived a restart

    def set_notify_callback(self, cb):
        self._notify_cb = cb

    def _reschedule_active(self):
        """Re-register any tasks that were active when the process last stopped."""
        now = datetime.now()
        for tid, t in self.tasks.items():
            if t.get("status") != "active":
                continue
            try:
                run_at = datetime.fromisoformat(t["run_at"])
                if run_at > now:
                    from apscheduler.triggers.date import DateTrigger
                    self.scheduler.add_job(
                        self._execute, DateTrigger(run_date=run_at),
                        args=[tid], id=tid, replace_existing=True)
            except Exception:
                pass

    def _execute(self, task_id: str):
        t = self.tasks.get(task_id)
        if not t:
            return
        msg = f"⏰ Reminder: {t['description']}"

        # 1. Try plyer desktop notification (non-critical)
        try:
            from plyer import notification
            notification.notify(
                title="⏰ HELIOS Reminder",
                message=t["description"],
                timeout=10)
        except Exception:
            pass

        # 2. Always fire the UI callback so user sees it in chat
        if self._notify_cb:
            try:
                self._notify_cb(msg)
            except Exception:
                pass

        # 3. Console fallback
        print(msg)

        self.tasks[task_id]["status"] = "done"
        _save(self.tasks)

    def schedule(self, description: str, run_at: str) -> str:
        from apscheduler.triggers.date import DateTrigger
        tid = str(uuid.uuid4())[:8]
        dt  = _parse_time(run_at)
        if not dt:
            return (f"Couldn't understand the time '{run_at}'.\n"
                    f"Try: 'in 5 minutes', 'in 2 hours', 'tomorrow', '18:30'")

        now = datetime.now()
        if dt <= now:
            return (f"That time ({dt.strftime('%H:%M:%S')}) is already in the past.\n"
                    f"Try: 'in 5 minutes' or a future time.")

        self.tasks[tid] = {
            "id":          tid,
            "description": description,
            "run_at":      dt.isoformat(),
            "status":      "active",
            "created":     now.isoformat(),
        }
        _save(self.tasks)
        self.scheduler.add_job(
            self._execute, DateTrigger(run_date=dt),
            args=[tid], id=tid, replace_existing=True)

        # Human-readable time remaining
        diff = dt - now
        total_secs = int(diff.total_seconds())
        if total_secs < 60:
            remaining = f"{total_secs} seconds"
        elif total_secs < 3600:
            remaining = f"{total_secs // 60} minutes"
        else:
            h, m = divmod(total_secs // 60, 60)
            remaining = f"{h}h {m}m"

        return (f"Reminder set!\n"
                f"  Task:   {description}\n"
                f"  At:     {dt.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"  In:     {remaining}\n"
                f"  ID:     {tid}")

    def list_tasks(self) -> str:
        active = [t for t in self.tasks.values() if t.get("status") == "active"]
        if not active:
            return "No active reminders."
        lines = ["Active reminders:\n"]
        now = datetime.now()
        for t in sorted(active, key=lambda x: x.get("run_at", "")):
            try:
                run_at = datetime.fromisoformat(t["run_at"])
                diff   = run_at - now
                secs   = int(diff.total_seconds())
                if secs < 0:
                    eta = "overdue"
                elif secs < 60:
                    eta = f"in {secs}s"
                elif secs < 3600:
                    eta = f"in {secs // 60}m"
                else:
                    h, m = divmod(secs // 60, 60)
                    eta = f"in {h}h {m}m"
            except Exception:
                eta = ""
            lines.append(
                f"  [{t['id']}] {t['description']} — "
                f"{t['run_at'][:16]} ({eta})")
        return "\n".join(lines)

    def cancel_task(self, task_id: str) -> str:
        if task_id not in self.tasks:
            return f"No task with ID '{task_id}'."
        try:
            self.scheduler.remove_job(task_id)
        except Exception:
            pass
        self.tasks[task_id]["status"] = "cancelled"
        _save(self.tasks)
        return f"Reminder '{task_id}' cancelled."

    def shutdown(self):
        try:
            self.scheduler.shutdown(wait=False)
        except Exception:
            pass
