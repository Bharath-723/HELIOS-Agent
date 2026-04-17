"""HELIOS - Gmail Composer: open compose window pre-filled"""
import urllib.parse
import webbrowser

class GmailComposer:
    def compose(self, to: str = "", subject: str = "", body: str = "") -> str:
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
        return result

    def open_gmail(self) -> str:
        webbrowser.open("https://mail.google.com")
        return "Opened Gmail."
