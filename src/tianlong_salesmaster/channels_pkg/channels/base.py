"""tianlong_salesmaster.channels_pkg.channels.base — 通信基类

所有平台通信渠道的抽象基类。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Message:
    """一条消息"""
    id: str = ""
    channel: str = ""         # email / wework / whatsapp / feishu / slack
    direction: str = "send"    # send / receive
    to: str = ""
    from_: str = ""
    subject: str = ""
    body: str = ""
    timestamp: str = ""
    status: str = "pending"    # pending / sent / failed / received
    metadata: Dict = field(default_factory=dict)


class ChannelBase(ABC):
    """通信渠道基类。"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._messages: List[Message] = []

    @property
    @abstractmethod
    def name(self) -> str:
        """渠道名称"""
        ...

    @abstractmethod
    def send(self, message: Message) -> bool:
        """发送消息"""
        ...

    @abstractmethod
    def receive(self, limit: int = 10) -> List[Message]:
        """接收消息"""
        ...

    def get_history(self, limit: int = 50) -> List[Dict]:
        return [{
            "id": m.id, "channel": m.channel, "direction": m.direction,
            "to": m.to, "from": m.from_, "subject": m.subject,
            "body": m.body[:200], "timestamp": m.timestamp, "status": m.status,
        } for m in self._messages[-limit:]]

    def _make_message(self, to: str, subject: str, body: str,
                       channel: str = "") -> Message:
        import uuid
        return Message(
            id=str(uuid.uuid4())[:12],
            channel=channel or self.name,
            to=to,
            body=body,
            subject=subject,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
