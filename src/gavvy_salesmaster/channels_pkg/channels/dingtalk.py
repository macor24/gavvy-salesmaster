"""gavvy_salesmaster.channels_pkg.channels.dingtalk — 钉钉官方 API 通信渠道

基于钉钉开放平台官方 API：
- 群机器人 webhook 消息推送
- 企业内部应用消息推送（通过 access_token）
- 支持 text / markdown / link / action_card 消息类型

API 文档: https://open.dingtalk.com/document/orgapp/types-of-messages-sent-by-robots

零外部依赖（使用 urllib）。
"""

from __future__ import annotations

import hashlib
import base64
import hmac
import json
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Any, Dict, List, Optional

from .base import ChannelBase, Message


# ── 钉钉 API 端点 ─────────────────────────────────

_DINGTALK_TOKEN_URL = "https://oapi.dingtalk.com/gettoken"
_DINGTALK_SEND_URL = "https://oapi.dingtalk.com/topapi/message/corpconversation/asyncsend_v2"


class DingTalkChannel(ChannelBase):
    """钉钉官方 API 通信渠道。

    两种使用模式:
    1. Webhook 模式（群机器人）: 只需 webhook_url
    2. 应用消息模式: 需要 app_key + app_secret

    用法:
        # Webhook 模式
        channel = DingTalkChannel({"webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=xxx"})
        channel.send_text("大家好")

        # 应用消息模式
        channel = DingTalkChannel({
            "app_key": "dingxxx",
            "app_secret": "xxx",
        })
        msg = Message(to="userid123", body="你好")
        channel.send(msg)
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config or {})
        self._token: str = ""
        self._token_expires_at: float = 0.0

    @property
    def name(self) -> str:
        return "dingtalk"

    @property
    def is_configured(self) -> bool:
        return bool(
            self.config.get("webhook_url")
            or (self.config.get("app_key") and self.config.get("app_secret"))
        )

    @property
    def mode(self) -> str:
        """当前使用模式: webhook / app / unconfigured"""
        if self.config.get("webhook_url"):
            return "webhook"
        if self.config.get("app_key") and self.config.get("app_secret"):
            return "app"
        return "unconfigured"

    # ── Token 管理（应用消息模式） ──

    def _get_token(self) -> Optional[str]:
        if self.mode != "app":
            return None
        if self._token and time.time() < self._token_expires_at:
            return self._token
        try:
            params = f"appkey={self.config['app_key']}&appsecret={self.config['app_secret']}"
            req = urllib.request.Request(
                f"{_DINGTALK_TOKEN_URL}?{params}", method="GET"
            )
            resp = urllib.request.urlopen(req, timeout=10)
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("errcode") == 0:
                self._token = result["access_token"]
                self._token_expires_at = time.time() + 7200 - 300
                return self._token
        except Exception:
            pass
        return None

    # ── Webhook 签名 ──

    def _sign_webhook(self, webhook_url: str, secret: str) -> str:
        """生成钉钉 webhook 签名（如果配置了 secret）"""
        if not secret:
            return webhook_url
        timestamp = str(round(time.time() * 1000))
        sign_str = f"{timestamp}\n{secret}"
        signature = base64.b64encode(
            hmac.new(secret.encode("utf-8"), sign_str.encode("utf-8"),
                     digestmod=hashlib.sha256).digest()
        ).decode("utf-8")
        separator = "&" if "?" in webhook_url else "?"
        return f"{webhook_url}{separator}timestamp={timestamp}&sign={urllib.parse.quote(signature)}"

    # ── 发送消息 ──

    def send(self, message: Message) -> bool:
        """发送消息。

        Webhook 模式: message.body 为消息内容
        应用消息模式: message.to 为接收人 userid
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
            "msgtype": "text",
            "text": {"content": message.body},
        }
        webhook_url = self._sign_webhook(
            self.config["webhook_url"],
            self.config.get("secret", ""),
        )
        try:
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=15)
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("errcode") == 0:
                message.status = "sent"
                self._messages.append(message)
                return True
            message.metadata["error"] = f"钉钉 API 错误: {result}"
        except Exception as e:
            message.metadata["error"] = str(e)
        message.status = "failed"
        self._messages.append(message)
        return False

    def _send_app_message(self, message: Message) -> bool:
        """通过企业内部应用发送消息"""
        token = self._get_token()
        if not token:
            message.status = "failed"
            message.metadata["error"] = "无法获取 access_token"
            self._messages.append(message)
            return False

        payload = {
            "agent_id": self.config.get("agent_id", ""),
            "userid_list": message.to or "",
            "msg": {
                "msgtype": "text",
                "text": {"content": message.body},
            },
        }
        try:
            req = urllib.request.Request(
                f"{_DINGTALK_SEND_URL}?access_token={token}",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=15)
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("errcode") == 0:
                message.status = "sent"
                self._messages.append(message)
                return True
            message.metadata["error"] = f"钉钉 API 错误: {result}"
        except Exception as e:
            message.metadata["error"] = str(e)
        message.status = "failed"
        self._messages.append(message)
        return False

    # ── 便捷方法 ──

    def send_text(self, content: str, webhook_url: str = "") -> bool:
        """发送纯文本消息

        Args:
            content: 消息内容
            webhook_url: 可选，临时替换 webhook URL
        """
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

    def send_markdown(self, title: str, content: str) -> bool:
        """发送 markdown 消息（仅 webhook 模式）"""
        if self.mode != "webhook":
            return False
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": content,
            },
        }
        webhook_url = self._sign_webhook(
            self.config["webhook_url"],
            self.config.get("secret", ""),
        )
        try:
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=15)
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("errcode") == 0:
                msg = self._make_message(to="", title=title, body=content)
                msg.status = "sent"
                self._messages.append(msg)
                return True
        except Exception:
            pass
        return False

    def send_link(self, title: str, text: str, message_url: str,
                  pic_url: str = "") -> bool:
        """发送链接消息（仅 webhook 模式）"""
        if self.mode != "webhook":
            return False
        link = {"title": title, "text": text, "messageUrl": message_url}
        if pic_url:
            link["picUrl"] = pic_url
        payload = {"msgtype": "link", "link": link}
        webhook_url = self._sign_webhook(
            self.config["webhook_url"],
            self.config.get("secret", ""),
        )
        try:
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=15)
            result = json.loads(resp.read().decode("utf-8"))
            ok = result.get("errcode") == 0
            if ok:
                msg = self._make_message(to="", subject=title, body=text)
                msg.status = "sent"
                self._messages.append(msg)
            return ok
        except Exception:
            return False

    # ── 接收消息 ──

    def receive(self, limit: int = 10) -> List[Message]:
        """钉钉消息接收需配置回调 URL，此处为占位"""
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
