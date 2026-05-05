"""SentriKit_salesmaster.channels_pkg.channels.dispatcher — 多渠道消息调度引擎

统一注册、路由、发送所有渠道的消息。
支持单发、群发、按规则路由。

用法:
    dispatcher = MessageDispatcher()
    dispatcher.register("email", EmailChannel(...))
    dispatcher.register("wework", WeWorkChannel(...))
    dispatcher.send("email", to="user@example.com", body="你好")
    dispatcher.dispatch({"channels": ["email", "wework"], ...})
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from .base import ChannelBase, Message


# ── 发送结果 ──────────────────────────────────────

@dataclass
class DispatchResult:
    """单条消息发送结果"""
    channel: str
    to: str
    subject: str = ""
    status: str = "pending"   # pending / sent / failed / skipped
    error: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict:
        return {
            "channel": self.channel,
            "to": self.to,
            "subject": self.subject,
            "status": self.status,
            "error": self.error,
            "timestamp": self.timestamp or datetime.now().isoformat(),
        }


# ── 渠道配置 ──────────────────────────────────────

CHANNEL_KEYS = {
    "email": {"smtp_host", "smtp_port", "smtp_user", "smtp_pass", "from_addr"},
    "wework": {"corp_id", "agent_id", "secret"},
    "dingtalk": {"webhook_url", "secret", "app_key", "app_secret"},
    "feishu": {"webhook_url", "app_id", "app_secret"},
}


# ── 调度引擎 ──────────────────────────────────────

class MessageDispatcher:
    """多渠道消息调度引擎 — 单例"""

    _instance: Optional[MessageDispatcher] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._channels: Dict[str, ChannelBase] = {}
        self._history: List[DispatchResult] = []
        self._history_lock = threading.Lock()
        self._load_config()

    # ── 渠道管理 ──

    def register(self, name: str, channel: ChannelBase) -> None:
        """注册一个渠道实例"""
        self._channels[name] = channel

    def unregister(self, name: str) -> bool:
        """注销渠道"""
        return self._channels.pop(name, None) is not None

    def get_channel(self, name: str) -> Optional[ChannelBase]:
        return self._channels.get(name)

    @property
    def channels(self) -> Dict[str, ChannelBase]:
        return dict(self._channels)

    @property
    def channel_names(self) -> List[str]:
        return list(self._channels.keys())

    # ── 单发 ──

    def send(self, channel_name: str, to: str = "", body: str = "",
             subject: str = "", metadata: Optional[Dict] = None) -> DispatchResult:
        """通过指定渠道发送一条消息"""
        channel = self._channels.get(channel_name)
        if not channel:
            result = DispatchResult(
                channel=channel_name, to=to, subject=subject,
                status="skipped", error=f"渠道 '{channel_name}' 未注册",
                timestamp=datetime.now().isoformat(),
            )
            self._add_history(result)
            return result

        msg = channel._make_message(to=to, subject=subject, body=body,
                                     channel=channel_name)
        if metadata:
            msg.metadata.update(metadata)

        ok = channel.send(msg)
        result = DispatchResult(
            channel=channel_name, to=to, subject=subject,
            status="sent" if ok else "failed",
            error="" if ok else msg.metadata.get("error", "发送失败"),
            timestamp=msg.timestamp,
        )
        self._add_history(result)
        return result

    # ── 群发 ──

    def send_all(self, to: str = "", body: str = "",
                 subject: str = "") -> List[DispatchResult]:
        """向所有已注册渠道发送同一条消息"""
        results = []
        for name in self._channels:
            results.append(self.send(name, to=to, body=body, subject=subject))
        return results

    # ── 按规则分发 ──

    def dispatch(self, message: Dict[str, Any]) -> List[DispatchResult]:
        """按配置分发消息

        message 格式:
        {
            "channels": ["email", "wework"],  # 目标渠道列表，空=全部已注册
            "to": "...",
            "body": "...",
            "subject": "...",
            "metadata": {...},
        }
        """
        targets = message.get("channels", []) or list(self._channels.keys())
        results = []
        for name in targets:
            results.append(self.send(
                channel_name=name,
                to=message.get("to", ""),
                body=message.get("body", ""),
                subject=message.get("subject", ""),
                metadata=message.get("metadata"),
            ))
        return results

    # ── 历史 ──

    def get_history(self, limit: int = 50) -> List[Dict]:
        with self._history_lock:
            return [r.to_dict() for r in self._history[-limit:]]

    def get_stats(self) -> Dict:
        """获取发送统计"""
        with self._history_lock:
            total = len(self._history)
            sent = sum(1 for r in self._history if r.status == "sent")
            failed = sum(1 for r in self._history if r.status == "failed")
            skipped = sum(1 for r in self._history if r.status == "skipped")
            by_channel = {}
            for r in self._history:
                by_channel.setdefault(r.channel, {"total": 0, "sent": 0, "failed": 0})
                by_channel[r.channel]["total"] += 1
                if r.status == "sent":
                    by_channel[r.channel]["sent"] += 1
                elif r.status == "failed":
                    by_channel[r.channel]["failed"] += 1
        return {
            "total": total,
            "sent": sent,
            "failed": failed,
            "skipped": skipped,
            "registered_channels": list(self._channels.keys()),
            "by_channel": by_channel,
        }

    def _add_history(self, result: DispatchResult) -> None:
        with self._history_lock:
            self._history.append(result)
            if len(self._history) > 2000:
                self._history = self._history[-1000:]

    # ── 外部消息入口（渠道 → Orchestrator） ──

    def on_incoming_message(self, channel: str, sender: str,
                            body: str, metadata: Optional[Dict] = None) -> None:
        """处理来自外部渠道的消息，路由到 SalesOrchestrator

        当 WeChat/DingTalk/Email 等渠道收到外部消息时调用此方法。
        自动匹配已有 Lead 或创建新 Lead，然后调度对应 Agent 处理。
        """
        try:
            from SentriKit_salesmaster.team_pkg.team.coordinator import (
                SalesOrchestrator,
            )
            orch = SalesOrchestrator()

            # 在已有 Lead 中查找匹配的（按名称/渠道标识）
            matched_lead_id = None
            lead_name = sender
            for lid, lead in orch.get_leads().items():
                if lead.name == sender or lead.context_extra.get("channel_id") == sender:
                    matched_lead_id = lid
                    break

            if matched_lead_id:
                # 更新已有 Lead 的消息历史
                orch.update_lead(matched_lead_id, {
                    "context_extra": {
                        "last_message": body[:200],
                        "last_channel": channel,
                        "last_contact": datetime.now().isoformat(),
                    }
                })
                # 触发 Agent 处理
                orch.assign_task(matched_lead_id)
            else:
                # 创建新 Lead
                lid = orch.add_lead(f"lead_{uuid.uuid4().hex[:8]}", {
                    "name": sender,
                    "stage": "contact",
                    "extra": {
                        "channel_id": sender,
                        "source_channel": channel,
                        "first_message": body[:200],
                    },
                })
                orch.assign_task(lid)
        except Exception:
            pass

    # ── 配置持久化 ──

    def _load_config(self) -> None:
        """从存储层加载渠道配置并自动注册"""
        try:
            from SentriKit_salesmaster.core.storage.db import get_kernel
            configs = get_kernel().get("channel_configs")
            if configs and isinstance(configs, dict):
                for name, cfg in configs.items():
                    channel = self._build_channel(name, cfg)
                    if channel:
                        self._channels[name] = channel
        except Exception:
            pass

    def save_config(self, name: str, config: Dict) -> bool:
        """保存渠道配置到存储层"""
        try:
            from SentriKit_salesmaster.core.storage.db import get_kernel
            configs = get_kernel().get("channel_configs") or {}
            configs[name] = config
            get_kernel().write("channel_configs", configs)
            return True
        except Exception:
            return False

    def delete_config(self, name: str) -> bool:
        """删除渠道配置"""
        try:
            from SentriKit_salesmaster.core.storage.db import get_kernel
            configs = get_kernel().get("channel_configs") or {}
            configs.pop(name, None)
            get_kernel().write("channel_configs", configs)
            return True
        except Exception:
            return False

    def _build_channel(self, name: str, config: Dict) -> Optional[ChannelBase]:
        """根据名称和配置构建渠道实例"""
        try:
            if name == "email":
                from .email import EmailChannel
                return EmailChannel(config)
            elif name == "wework":
                from .wework import WeWorkChannel
                return WeWorkChannel(config)
            elif name == "dingtalk":
                from .dingtalk import DingTalkChannel
                return DingTalkChannel(config)
            elif name == "feishu":
                from .feishu import FeishuChannel
                return FeishuChannel(config)
        except Exception:
            return None
        return None
