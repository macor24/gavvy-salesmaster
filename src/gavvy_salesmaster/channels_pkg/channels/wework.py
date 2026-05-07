"""gavvy_salesmaster.channels_pkg.channels.wework — 企业微信官方 API 通信渠道

基于企业微信官方 API 实现，支持：
  1. 获取 access_token（缓存自动刷新）
  2. 应用消息推送（text / markdown / 图文）
  3. 客户联系（获取客户列表、发送消息）

API 文档: https://developer.work.weixin.qq.com/document/path/90665

不依赖任何第三方桥接库，零外部依赖（使用 urllib）。
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

from .base import ChannelBase, Message


# ── 企业微信 API 端点 ──────────────────────────────

_BASE_URL = "https://qyapi.weixin.qq.com/cgi-bin"
_TOKEN_URL = f"{_BASE_URL}/gettoken"
_SEND_URL = f"{_BASE_URL}/message/send"
_USER_LIST_URL = f"{_BASE_URL}/user/list"


class WeWorkChannel(ChannelBase):
    """企业微信官方 API 通信渠道。

    配置参数:
        corp_id: str   — 企业 ID（必填）
        agent_id: int  — 应用 AgentId（必填）
        secret: str    — 应用 Secret（必填）

    用法:
        channel = WeWorkChannel({
            "corp_id": "ww123456",
            "agent_id": 1000001,
            "secret": "your-secret",
        })
        msg = Message(to="user_id", body="Hello")
        channel.send(msg)
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config or {})
        self._token: str = ""
        self._token_expires_at: float = 0.0

    @property
    def name(self) -> str:
        return "wework"

    @property
    def is_configured(self) -> bool:
        """检查是否配置完整（三要素齐全）"""
        return bool(
            self.config.get("corp_id")
            and self.config.get("agent_id")
            and self.config.get("secret")
        )

    # ── Token 管理 ──

    def _get_token(self) -> Optional[str]:
        """获取 access_token（带缓存自动刷新）。

        企业微信 token 有效期 7200 秒，提前 300 秒刷新。
        """
        if self._token and time.time() < self._token_expires_at:
            return self._token

        if not self.is_configured:
            return None

        params = (
            f"corpid={self.config['corp_id']}"
            f"&corpsecret={self.config['secret']}"
        )

        try:
            req = Request(f"{_TOKEN_URL}?{params}", method="GET")
            resp = urlopen(req, timeout=10)
            result = json.loads(resp.read().decode("utf-8"))

            if result.get("errcode") != 0:
                return None

            self._token = result["access_token"]
            expires_in = result.get("expires_in", 7200)
            self._token_expires_at = time.time() + expires_in - 300  # 提前 5 分钟刷新
            return self._token

        except (URLError, json.JSONDecodeError, IOError):
            return None

    def _clear_token(self) -> None:
        """强制清除 token（下次调用重新获取）。"""
        self._token = ""
        self._token_expires_at = 0.0

    # ── 发送消息 ──

    def send(self, message: Message) -> bool:
        """通过企业微信应用推送消息。

        message.to — 接收人（userid，多个用 | 分隔）
        message.body — 消息内容
        message.subject — 标题（仅用于图文消息）
        """
        if not self.is_configured:
            message.status = "failed"
            self._messages.append(message)
            return False

        token = self._get_token()
        if not token:
            message.status = "failed"
            message.metadata["error"] = "无法获取 access_token"
            self._messages.append(message)
            return False

        payload = {
            "touser": message.to or "@all",
            "msgtype": "text",
            "agentid": self.config["agent_id"],
            "text": {"content": message.body},
        }

        try:
            req = Request(
                f"{_SEND_URL}?access_token={token}",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp = urlopen(req, timeout=15)
            result = json.loads(resp.read().decode("utf-8"))

            if result.get("errcode") == 0:
                message.status = "sent"
                self._messages.append(message)
                return True
            elif result.get("errcode") == 40014:  # token 过期
                self._clear_token()
                message.status = "failed"
                message.metadata["error"] = f"token 过期: {result.get('errmsg', '')}"
            else:
                message.status = "failed"
                message.metadata["error"] = (
                    f"企业微信 API 错误: {result.get('errcode')} "
                    f"- {result.get('errmsg', '')}"
                )
        except (URLError, json.JSONDecodeError, IOError) as e:
            message.status = "failed"
            message.metadata["error"] = str(e)

        self._messages.append(message)
        return False

    def send_markdown(self, to: str, content: str) -> bool:
        """发送 markdown 消息（企业微信支持 markdown 类型）。"""
        if not self.is_configured:
            return False

        token = self._get_token()
        if not token:
            return False

        payload = {
            "touser": to or "@all",
            "msgtype": "markdown",
            "agentid": self.config["agent_id"],
            "markdown": {"content": content},
        }

        try:
            req = Request(
                f"{_SEND_URL}?access_token={token}",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp = urlopen(req, timeout=15)
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("errcode") == 0
        except Exception:
            return False

    def send_news(self, to: str, articles: List[Dict]) -> bool:
        """发送图文消息。

        articles: [{"title": "...", "description": "...",
                     "url": "...", "picurl": "..."}]
        """
        if not self.is_configured or not articles:
            return False

        token = self._get_token()
        if not token:
            return False

        payload = {
            "touser": to or "@all",
            "msgtype": "news",
            "agentid": self.config["agent_id"],
            "news": {"articles": articles},
        }

        try:
            req = Request(
                f"{_SEND_URL}?access_token={token}",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp = urlopen(req, timeout=15)
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("errcode") == 0
        except Exception:
            return False

    # ── 接收消息（客户联系） ──

    def receive(self, limit: int = 10) -> List[Message]:
        """企业微信不支持常规的消息拉取，需通过回调 URL 接收。

        此方法为占位，实际使用需配置企业微信回调 URL。
        参见: https://developer.work.weixin.qq.com/document/path/92277
        """
        return []

    def get_contacts(self, department_id: int = 1) -> List[Dict]:
        """获取企业微信联系人列表（用于查找 userid）。

        返回列表，每个元素包含 userid / name / department / mobile 等。
        返回的数据已标记为 PII，建议外部调用时进行脱敏处理。
        """
        token = self._get_token()
        if not token:
            return []

        try:
            req = Request(
                f"{_USER_LIST_URL}?access_token={token}"
                f"&department_id={department_id}&fetch_child=1",
                method="GET",
            )
            resp = urlopen(req, timeout=10)
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("errcode") == 0:
                return result.get("userlist", [])
            return []
        except Exception:
            return []

    def parse_callback_message(self, body: Dict) -> Optional[Message]:
        """解析企业微信回调推送的消息体。

        当配置了企业微信回调 URL 后，收到的 POST 回调可以由此方法解析。
        返回 Message 对象或 None。
        """
        try:
            msg_type = body.get("MsgType", "")
            if msg_type == "text":
                return Message(
                    id=body.get("MsgId", ""),
                    channel="wework",
                    direction="receive",
                    from_=body.get("FromUserName", ""),
                    body=body.get("Content", ""),
                    timestamp=str(body.get("CreateTime", "")),
                    status="received",
                )
            return None
        except Exception:
            return None

    # ── 发送结果检查 ──

    def get_send_status(self) -> Dict:
        """获取最近发送的状态统计。"""
        sent = sum(1 for m in self._messages if m.status == "sent")
        failed = sum(1 for m in self._messages if m.status == "failed")
        return {
            "total": len(self._messages),
            "sent": sent,
            "failed": failed,
            "token_status": "valid" if self._token else "unauthenticated",
            "configured": self.is_configured,
        }
