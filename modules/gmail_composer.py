"""HELIOS - Gmail Composer: open compose window pre-filled"""
import urllib.parse
import webbrowser
import logging

log = logging.getLogger("helios.gmail_composer")

class GmailComposer:
    def compose(self, to: str = "", subject: str = "", body: str = "") -> str:
        log.info("compose called: to=%s, subject=%s", to, subject)
        try:
            url = "https://mail.google.com/mail/?view=cm&fs=1"
            if to:      url += f"&to={urllib.parse.quote(to)}"
            if subject: url += f"&su={urllib.parse.quote(subject)}"
            if body:    url += f"&body={urllib.parse.quote(body)}"
            webbrowser.open(url)
            result = "Gmail compose opened!\n"
            if to:      result += f"  To:      {to}\n"
            if subject: result += f"  Subject: {subject}\n"
            if body:    result += f"  Body:    {body[:80]}{'...' if len(body)>80 else ''}\n"
            result += "Review and click Send in your browser."
            log.info("Successfully opened Gmail compose in browser.")
            return result
        except Exception as exc:
            log.error("Failed to open Gmail compose in browser: %s", exc, exc_info=True)
            return f"Failed to compose email: {exc}"

    def open_gmail(self) -> str:
        log.info("open_gmail called")
        try:
            webbrowser.open("https://mail.google.com")
            log.info("Successfully opened Gmail inbox in browser.")
            return "Opened Gmail."
        except Exception as exc:
            log.error("Failed to open Gmail in browser: %s", exc, exc_info=True)
            return f"Failed to open Gmail: {exc}"
