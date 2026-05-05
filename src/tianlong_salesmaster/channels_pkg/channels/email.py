"""tianlong_salesmaster.channels_pkg.channels.email — 邮件通信渠道

基于 smtplib 的邮件发送和 IMAP 接收。
"""

from __future__ import annotations

import os
import smtplib
import imaplib
import email as email_lib
from email.mime.text import MIMEText
from email.header import decode_header
from typing import Dict, List, Optional

from .base import ChannelBase, Message


class EmailChannel(ChannelBase):
    """邮件通信渠道"""

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config or {
            "smtp_host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
            "smtp_port": int(os.environ.get("SMTP_PORT", "587")),
            "smtp_user": os.environ.get("SMTP_USER", ""),
            "smtp_pass": os.environ.get("SMTP_PASS", ""),
            "imap_host": os.environ.get("IMAP_HOST", "imap.gmail.com"),
            "imap_port": int(os.environ.get("IMAP_PORT", "993")),
            "from_addr": os.environ.get("SMTP_FROM", ""),
        })

    @property
    def name(self) -> str:
        return "email"

    @property
    def is_configured(self) -> bool:
        return bool(self.config.get("smtp_user") and self.config.get("smtp_pass"))

    def send(self, message: Message) -> bool:
        if not self.is_configured:
            message.status = "failed"
            self._messages.append(message)
            return False

        try:
            msg = MIMEText(message.body, "plain", "utf-8")
            msg["Subject"] = message.subject
            msg["From"] = self.config.get("from_addr", "")
            msg["To"] = message.to

            with smtplib.SMTP(self.config["smtp_host"], self.config["smtp_port"]) as server:
                server.starttls()
                server.login(self.config["smtp_user"], self.config["smtp_pass"])
                server.send_message(msg)

            message.status = "sent"
            self._messages.append(message)
            return True
        except Exception as e:
            message.status = "failed"
            message.metadata["error"] = str(e)
            self._messages.append(message)
            return False

    def receive(self, limit: int = 10) -> List[Message]:
        if not self.is_configured:
            return []

        messages = []
        try:
            with imaplib.IMAP4_SSL(self.config["imap_host"], self.config["imap_port"]) as server:
                server.login(self.config["smtp_user"], self.config["smtp_pass"])
                server.select("INBOX")
                status, data = server.search(None, "UNSEEN")
                if status == "OK":
                    for num in data[0].split()[:limit]:
                        status, msg_data = server.fetch(num, "(RFC822)")
                        if status == "OK":
                            raw = email_lib.message_from_bytes(msg_data[0][1])
                            subject = self._decode_header(raw["Subject"])
                            from_addr = raw["From"] or ""
                            body = self._get_body(raw)
                            msg = Message(
                                id=str(num, "utf-8"),
                                channel="email",
                                direction="receive",
                                from_=from_addr,
                                subject=subject,
                                body=body[:1000],
                                timestamp=raw["Date"] or "",
                                status="received",
                            )
                            self._messages.append(msg)
                            messages.append(msg)
        except Exception:
            pass
        return messages

    @staticmethod
    def _decode_header(header: str) -> str:
        if not header:
            return ""
        parts = decode_header(header)
        return " ".join(
            p.decode(charset or "utf-8") if isinstance(p, bytes) else str(p)
            for p, charset in parts
        )

    @staticmethod
    def _get_body(msg) -> str:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        return payload.decode("utf-8", errors="replace")
        payload = msg.get_payload(decode=True)
        return payload.decode("utf-8", errors="replace") if payload else ""
