"""SentriKit_salesmaster.channels_pkg.channels.feishu — 飞书开放平台 API 通信渠道

基于飞书开放平台官方 API：
- 群机器人 webhook 消息推送
- 企业自建应用消息推送（通过 tenant_access_token）
- 支持 text / markdown / interactive 消息类型（Card 消息）

API 文档: https://open.feishu.cn/document/server-docs/im-v1/message/create

零外部依赖（使用 urllib）。
"""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

from .base import ChannelBase, Message


# ── 飞书 API 端点 ─────────────────────────────────

_FEISHU_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
_FEISHU_SEND_URL = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
_FEISHU_WEBHOOK_SEND = "https://open.feishu.cn/open-apis/bot/v2/hook/"


class FeishuChannel(ChannelBase):
    """飞书开放平台 API 通信渠道。

    两种使用模式:
    1. Webhook 模式（群机器人）: 只需 webhook_url
    2. 应用消息模式: 需要 app_id + app_secret

    用法:
        # Webhook 模式
        channel = FeishuChannel({"webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"})
        channel.send_text("大家好")

        # 应用消息模式
        channel = FeishuChannel({
            "app_id": "cli_xxx",
            "app_secret": "xxx",
        })
        msg = Message(to="ou_xxx", body="你好")
        channel.send(msg)
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config or {})
        self._token: str = ""
        self._token_expires_at: float = 0.0

    @property
    def name(self) -> str:
        return "feishu"

    @property
    def is_configured(self) -> bool:
        return bool(
            self.config.get("webhook_url")
            or (self.config.get("app_id") and self.config.get("app_secret"))
        )

    @property
    def mode(self) -> str:
        """当前使用模式: webhook / app / unconfigured"""
        if self.config.get("webhook_url"):
            return "webhook"
        if self.config.get("app_id") and self.config.get("app_secret"):
            return "app"
        return "unconfigured"

    # ── Token 管理（应用消息模式） ──

    def _get_token(self) -> Optional[str]:
        if self.mode != "app":
            return None
        if self._token and time.time() < self._token_expires_at:
            return self._token
        try:
            payload = {
                "app_id": self.config["app_id"],
                "app_secret": self.config["app_secret"],
            }
            req = urllib.request.Request(
                _FEISHU_TOKEN_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=10)
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("code") == 0:
                self._token = result["tenant_access_token"]
                self._token_expires_at = time.time() + result.get("expire", 7200) - 300
                return self._token
        except Exception:
            pass
        return None

    # ── 发送消息 ──

    def send(self, message: Message) -> bool:
        """发送消息。

        Webhook 模式: message.body 为消息内容
        应用消息模式: message.to 为接收人 open_id / user_id
        """
        if not self.is_configured:
            message.status = "failed"
            self._messages.append(message)
            return False

        if self.mode == "webhook":
            return self._send_webhook(message)
        return self._send_app_message(message)

    def _send_webhook(self, message: Message) -> bool:
        """通过群机器人 webhook 发送"""
        payload = {
            "msg_type": "text",
            "content": json.dumps({"text": message.body}),
        }
        webhook_url = self.config["webhook_url"]
        if not webhook_url.startswith("http"):
            webhook_url = f"{_FEISHU_WEBHOOK_SEND}{webhook_url}"
        try:
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=15)
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("code") == 0:
                message.status = "sent"
                self._messages.append(message)
                return True
            message.metadata["error"] = f"飞书 API 错误: {result}"
        except Exception as e:
            message.metadata["error"] = str(e)
        message.status = "failed"
        self._messages.append(message)
        return False

    def _send_app_message(self, message: Message) -> bool:
        """通过自建应用发送消息"""
        token = self._get_token()
        if not token:
            message.status = "failed"
            message.metadata["error"] = "无法获取 tenant_access_token"
            self._messages.append(message)
            return False

        payload = {
            "receive_id": message.to or "",
            "msg_type": "text",
            "content": json.dumps({"text": message.body}),
        }
        try:
            req = urllib.request.Request(
                _FEISHU_SEND_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=15)
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("code") == 0:
                message.status = "sent"
                self._messages.append(message)
                return True
            message.metadata["error"] = f"飞书 API 错误: {result}"
        except Exception as e:
            message.metadata["error"] = str(e)
        message.status = "failed"
        self._messages.append(message)
        return False

    # ── 便捷方法 ──

    def send_text(self, content: str, webhook_url: str = "") -> bool:
        """发送纯文本消息"""
        if webhook_url:
            old_url = self.config.get("webhook_url", "")
            self.config["webhook_url"] = webhook_url
            try:
                msg = self._make_message(to="", subject="", body=content)
                return self._send_webhook(msg)
            finally:
                self.config["webhook_url"] = old_url
        msg = self._make_message(to="", subject="", body=content)
        return self.send(msg)

    def send_markdown(self, content: str) -> bool:
        """发送 markdown 消息（仅 webhook 模式）"""
        if self.mode != "webhook":
            return False
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {"title": {"tag": "plain_text", "content": "消息通知"}},
                "elements": [{"tag": "markdown", "content": content}],
            },
        }
        webhook_url = self.config["webhook_url"]
        if not webhook_url.startswith("http"):
            webhook_url = f"{_FEISHU_WEBHOOK_SEND}{webhook_url}"
        try:
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=15)
            result = json.loads(resp.read().decode("utf-8"))
            ok = result.get("code") == 0
            if ok:
                msg = self._make_message(to="", body=content)
                msg.status = "sent"
                self._messages.append(msg)
            return ok
        except Exception:
            return False

    def send_card(self, card: Dict) -> bool:
        """发送飞书 Card 消息（仅 webhook 模式）

        card 格式参考飞书 Card Builder 生成的 JSON。
        """
        if self.mode != "webhook":
            return False
        payload = {"msg_type": "interactive", "card": card}
        webhook_url = self.config["webhook_url"]
        if not webhook_url.startswith("http"):
            webhook_url = f"{_FEISHU_WEBHOOK_SEND}{webhook_url}"
        try:
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=15)
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("code") == 0
        except Exception:
            return False

    # ── 接收消息 ──

    def receive(self, limit: int = 10) -> List[Message]:
        """飞书消息接收需配置事件回调，此处为占位"""
        return []

    def get_send_status(self) -> Dict:
        """获取发送状态统计"""
        sent = sum(1 for m in self._messages if m.status == "sent")
        failed = sum(1 for m in self._messages if m.status == "failed")
        return {
            "total": len(self._messages),
            "sent": sent,
            "failed": failed,
            "mode": self.mode,
            "configured": self.is_configured,
        }
