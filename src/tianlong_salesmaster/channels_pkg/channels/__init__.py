"""SentriKit_salesmaster.channels_pkg.channels — 消息触达模块

支持多种消息渠道：邮件、短信、企业微信、钉钉等。
"""

from __future__ import annotations

import os
import json
import uuid
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from enum import Enum
from typing import Any, Dict, List, Optional, Callable


# ── 消息渠道枚举 ────────────────────────────────────────

class ChannelType(Enum):
    """消息渠道类型"""
    EMAIL = "email"
    SMS = "sms"
    WECHAT_WORK = "wechat_work"  # 企业微信
    DINGTALK = "dingtalk"
    WEBHOOK = "webhook"  # 通用 Webhook
    MOCK = "mock"  # 模拟模式


class MessageType(Enum):
    """消息类型"""
    TEXT = "text"
    IMAGE = "image"
    MARKDOWN = "markdown"
    TEMPLATE = "template"
    CARD = "card"


# ── 数据类型定义 ────────────────────────────────────────

@dataclass
class Message:
    """消息"""
    id: str = ""
    channel: str = "email"
    msg_type: str = "text"
    to: List[str] = field(default_factory=list)  # 收件人
    cc: List[str] = field(default_factory=list)   # 抄送
    subject: str = ""  # 标题（邮件）
    content: str = ""  # 内容
    template_id: str = ""  # 模板 ID
    template_data: Dict = field(default_factory=dict)  # 模板变量
    attachments: List[str] = field(default_factory=list)  # 附件路径
    metadata: Dict = field(default_factory=dict)  # 元数据
    status: str = "pending"  # pending/sent/failed
    sent_at: str = ""
    error: Optional[str] = None
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:12]
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class MessageResult:
    """消息发送结果"""
    success: bool = False
    message_id: str = ""
    channel: str = ""
    error: Optional[str] = None
    response: Optional[Dict] = None


@dataclass
class EmailConfig:
    """邮件配置"""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = ""
    from_name: str = ""
    use_tls: bool = True


@dataclass
class SMSConfig:
    """短信配置"""
    provider: str = "aliyun"  # aliyun / tencent / mock
    access_key: str = ""
    access_secret: str = ""
    sign_name: str = ""
    template_code: str = ""


@dataclass
class WeChatWorkConfig:
    """企业微信配置"""
    corp_id: str = ""
    corp_secret: str = ""
    agent_id: str = ""


@dataclass
class DingTalkConfig:
    """钉钉配置"""
    app_key: str = ""
    app_secret: str = ""


# ── 消息发送器基类 ────────────────────────────────────────

class BaseSender(ABC):
    """消息发送器基类"""

    def __init__(self, config: Any = None):
        self.config = config

    @abstractmethod
    def send(self, message: Message) -> MessageResult:
        """发送消息"""
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置"""
        pass


# ── 邮件发送器 ────────────────────────────────────────

class EmailSender(BaseSender):
    """邮件发送器"""

    def __init__(self, config: EmailConfig):
        super().__init__(config)

    def validate_config(self) -> bool:
        """验证配置"""
        return bool(
            self.config.smtp_host and
            self.config.smtp_user and
            self.config.smtp_password
        )

    def send(self, message: Message) -> MessageResult:
        """发送邮件"""
        if not self.validate_config():
            return MessageResult(
                success=False,
                error="邮件配置不完整"
            )

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.subject or "无主题"
            msg["From"] = f"{self.config.from_name} <{self.config.from_email}>"
            msg["To"] = ", ".join(message.to)
            if message.cc:
                msg["Cc"] = ", ".join(message.cc)

            # 添加纯文本内容
            text_part = MIMEText(message.content, "plain", "utf-8")
            msg.attach(text_part)

            # 添加 HTML 内容（如果有）
            if "<html>" in message.content.lower():
                html_part = MIMEText(message.content, "html", "utf-8")
                msg.attach(html_part)

            # 添加附件
            for attachment_path in message.attachments:
                try:
                    with open(attachment_path, "rb") as f:
                        attachment = MIMEImage(f.read())
                        attachment.add_header(
                            "Content-Disposition",
                            "attachment",
                            filename=os.path.basename(attachment_path)
                        )
                        msg.attach(attachment)
                except Exception:
                    pass

            # 发送邮件
            if self.config.use_tls:
                server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)

            server.login(self.config.smtp_user, self.config.smtp_password)
            server.sendmail(
                self.config.from_email,
                message.to + message.cc,
                msg.as_string()
            )
            server.quit()

            return MessageResult(
                success=True,
                message_id=message.id,
                channel="email"
            )

        except Exception as e:
            return MessageResult(
                success=False,
                message_id=message.id,
                channel="email",
                error=str(e)
            )


# ── 短信发送器 ────────────────────────────────────────

class SMSSender(BaseSender):
    """短信发送器"""

    def __init__(self, config: SMSConfig):
        super().__init__(config)

    def validate_config(self) -> bool:
        """验证配置"""
        return bool(
            self.config.access_key and
            self.config.access_secret and
            self.config.sign_name
        )

    def send(self, message: Message) -> MessageResult:
        """发送短信"""
        if not self.validate_config():
            return MessageResult(
                success=False,
                error="短信配置不完整"
            )

        try:
            if self.config.provider == "aliyun":
                return self._send_aliyun(message)
            elif self.config.provider == "tencent":
                return self._send_tencent(message)
            else:
                return self._send_mock(message)

        except Exception as e:
            return MessageResult(
                success=False,
                message_id=message.id,
                channel="sms",
                error=str(e)
            )

    def _send_aliyun(self, message: Message) -> MessageResult:
        """阿里云短信"""
        # 实际实现需要安装 aliyun-python-sdk-core
        # 这里使用模拟实现
        return self._send_mock(message)

    def _send_tencent(self, message: Message) -> MessageResult:
        """腾讯云短信"""
        # 实际实现需要安装 qcloudsms-py
        return self._send_mock(message)

    def _send_mock(self, message: Message) -> MessageResult:
        """模拟发送"""
        return MessageResult(
            success=True,
            message_id=message.id,
            channel="sms",
            response={"mock": True, "status": "success"}
        )


# ── 企业微信发送器 ────────────────────────────────────────

class WeChatWorkSender(BaseSender):
    """企业微信发送器"""

    def __init__(self, config: WeChatWorkConfig):
        super().__init__(config)

    def validate_config(self) -> bool:
        """验证配置"""
        return bool(
            self.config.corp_id and
            self.config.corp_secret and
            self.config.agent_id
        )

    def send(self, message: Message) -> MessageResult:
        """发送企业微信消息"""
        if not self.validate_config():
            return MessageResult(
                success=False,
                error="企业微信配置不完整"
            )

        try:
            # 获取 Access Token
            token = self._get_access_token()
            if not token:
                return MessageResult(
                    success=False,
                    error="获取 Access Token 失败"
                )

            # 发送消息
            url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"

            payload = {
                "touser": "|".join(message.to),
                "msgtype": message.msg_type,
                "agentid": self.config.agent_id,
                message.msg_type: {
                    "content": message.content
                }
            }

            # 使用 requests 发送
            import requests
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()

            if result.get("errcode") == 0:
                return MessageResult(
                    success=True,
                    message_id=message.id,
                    channel="wechat_work",
                    response=result
                )
            else:
                return MessageResult(
                    success=False,
                    message_id=message.id,
                    channel="wechat_work",
                    error=result.get("errmsg", "发送失败")
                )

        except Exception as e:
            return MessageResult(
                success=False,
                message_id=message.id,
                channel="wechat_work",
                error=str(e)
            )

    def _get_access_token(self) -> Optional[str]:
        """获取 Access Token"""
        try:
            import requests
            url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
            params = {
                "corpid": self.config.corp_id,
                "corpsecret": self.config.corp_secret
            }
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            if result.get("errcode") == 0:
                return result.get("access_token")
        except Exception:
            pass
        return None


# ── 钉钉发送器 ────────────────────────────────────────

class DingTalkSender(BaseSender):
    """钉钉发送器"""

    def __init__(self, config: DingTalkConfig):
        super().__init__(config)

    def validate_config(self) -> bool:
        """验证配置"""
        return bool(self.config.app_key and self.config.app_secret)

    def send(self, message: Message) -> MessageResult:
        """发送钉钉消息"""
        if not self.validate_config():
            return MessageResult(
                success=False,
                error="钉钉配置不完整"
            )

        try:
            # 获取 Access Token
            token = self._get_access_token()
            if not token:
                return MessageResult(
                    success=False,
                    error="获取 Access Token 失败"
                )

            # 发送消息
            url = "https://oapi.dingtalk.com/robot/send"

            payload = {
                "msgtype": message.msg_type,
                message.msg_type: {
                    "content": message.content
                }
            }

            # 如果是群机器人，使用 webhook
            # 这里简化实现
            import requests
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()

            if result.get("errcode") == 0:
                return MessageResult(
                    success=True,
                    message_id=message.id,
                    channel="dingtalk",
                    response=result
                )
            else:
                return MessageResult(
                    success=False,
                    message_id=message.id,
                    channel="dingtalk",
                    error=result.get("errmsg", "发送失败")
                )

        except Exception as e:
            return MessageResult(
                success=False,
                message_id=message.id,
                channel="dingtalk",
                error=str(e)
            )

    def _get_access_token(self) -> Optional[str]:
        """获取 Access Token"""
        try:
            import requests
            url = "https://oapi.dingtalk.com/gettoken"
            params = {
                "appkey": self.config.app_key,
                "appsecret": self.config.app_secret
            }
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            if result.get("errcode") == 0:
                return result.get("access_token")
        except Exception:
            pass
        return None


# ── Webhook 发送器 ────────────────────────────────────────

class WebhookSender(BaseSender):
    """通用 Webhook 发送器"""

    def __init__(self, webhook_url: str = "", headers: Optional[Dict] = None):
        super().__init__(None)
        self.webhook_url = webhook_url
        self.headers = headers or {}

    def validate_config(self) -> bool:
        """验证配置"""
        return bool(self.webhook_url)

    def send(self, message: Message) -> MessageResult:
        """发送 Webhook"""
        if not self.validate_config():
            return MessageResult(
                success=False,
                error="Webhook URL 未配置"
            )

        try:
            import requests

            payload = {
                "message_id": message.id,
                "channel": message.channel,
                "msg_type": message.msg_type,
                "to": message.to,
                "subject": message.subject,
                "content": message.content,
                "metadata": message.metadata,
                "created_at": message.created_at
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                return MessageResult(
                    success=True,
                    message_id=message.id,
                    channel="webhook",
                    response=response.json() if response.content else {}
                )
            else:
                return MessageResult(
                    success=False,
                    message_id=message.id,
                    channel="webhook",
                    error=f"HTTP {response.status_code}"
                )

        except Exception as e:
            return MessageResult(
                success=False,
                message_id=message.id,
                channel="webhook",
                error=str(e)
            )


# ── Mock 发送器 ────────────────────────────────────────

class MockSender(BaseSender):
    """模拟发送器（用于测试）"""

    def __init__(self):
        super().__init__(None)
        self.sent_messages: List[Message] = []

    def validate_config(self) -> bool:
        """验证配置"""
        return True

    def send(self, message: Message) -> MessageResult:
        """模拟发送"""
        self.sent_messages.append(message)
        return MessageResult(
            success=True,
            message_id=message.id,
            channel=message.channel,
            response={"mock": True}
        )

    def get_sent_messages(self) -> List[Message]:
        """获取已发送的消息"""
        return self.sent_messages


# ── 消息网关管理器 ────────────────────────────────────────

class MessageGateway:
    """消息网关管理器"""

    def __init__(self):
        self._senders: Dict[str, BaseSender] = {}
        self._default_channel: Optional[str] = None

    def register_sender(self, channel: str, sender: BaseSender) -> None:
        """注册发送器"""
        self._senders[channel] = sender
        if self._default_channel is None:
            self._default_channel = channel

    def set_default_channel(self, channel: str) -> None:
        """设置默认渠道"""
        if channel in self._senders:
            self._default_channel = channel

    def get_sender(self, channel: str) -> Optional[BaseSender]:
        """获取发送器"""
        return self._senders.get(channel)

    def send(self, message: Message, channel: Optional[str] = None) -> MessageResult:
        """发送消息"""
        target_channel = channel or message.channel or self._default_channel
        sender = self._senders.get(target_channel)

        if not sender:
            return MessageResult(
                success=False,
                error=f"未注册的渠道: {target_channel}"
            )

        message.channel = target_channel
        result = sender.send(message)

        if result.success:
            message.status = "sent"
            message.sent_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            message.status = "failed"
            message.error = result.error

        return result

    def send_email(self, to: List[str], subject: str, content: str,
                   cc: Optional[List[str]] = None,
                   attachments: Optional[List[str]] = None) -> MessageResult:
        """快捷发送邮件"""
        message = Message(
            channel="email",
            to=to,
            cc=cc or [],
            subject=subject,
            content=content,
            attachments=attachments or []
        )
        return self.send(message)

    def send_sms(self, to: List[str], content: str,
                 template_id: str = "", template_data: Optional[Dict] = None) -> MessageResult:
        """快捷发送短信"""
        message = Message(
            channel="sms",
            to=to,
            content=content,
            template_id=template_id,
            template_data=template_data or {}
        )
        return self.send(message)

    def send_wechat_work(self, to: List[str], content: str,
                         msg_type: str = "text") -> MessageResult:
        """快捷发送企业微信"""
        message = Message(
            channel="wechat_work",
            to=to,
            content=content,
            msg_type=msg_type
        )
        return self.send(message)

    def send_dingtalk(self, to: List[str], content: str,
                      msg_type: str = "text") -> MessageResult:
        """快捷发送钉钉"""
        message = Message(
            channel="dingtalk",
            to=to,
            content=content,
            msg_type=msg_type
        )
        return self.send(message)


# ── 消息模板 ────────────────────────────────────────

class MessageTemplates:
    """消息模板"""

    TEMPLATES = {
        "quote_sent": {
            "email": {
                "subject": "【报价单】{customer_name} - {product_name}",
                "content": """
亲爱的 {customer_name}：

感谢您对我们产品的关注！附件是我们的报价单，请您查收。

报价明细：
- 产品：{product_name}
- 数量：{quantity}
- 金额：{amount}
- 有效期：{valid_until}

如有任何问题，欢迎随时联系我。

Best regards,
{salesperson}
                """
            },
            "sms": "【{company}】尊敬的{customer_name}，您的报价单已发送，请查收。如有疑问请回复。"
        },

        "contract_sent": {
            "email": {
                "subject": "【合同】{contract_title}",
                "content": """
亲爱的 {customer_name}：

感谢您选择我们的产品！附件是正式的合同文件，请您审阅并签署。

合同要点：
- 合同编号：{contract_number}
- 金额：{amount}
- 签署截止：{deadline}

签署方式：请登录我们的平台完成电子签署。

Best regards,
{salesperson}
                """
            }
        },

        "payment_reminder": {
            "email": {
                "subject": "【付款提醒】{contract_title}",
                "content": """
亲爱的 {customer_name}：

您的合同（{contract_number}）有一笔款项即将到期：

应付金额：{amount}
应付日期：{due_date}

请及时安排付款，如有任何疑问请联系我们。

Best regards,
{salesperson}
                """
            }
        },

        "follow_up": {
            "sms": "【{company}】尊敬的{customer_name}，我是{salesperson}，想和您沟通一下产品使用情况，请问您方便吗？"
        }
    }

    @classmethod
    def get_template(cls, template_name: str, channel: str = "email") -> Optional[Dict]:
        """获取模板"""
        template = cls.TEMPLATES.get(template_name, {})
        return template.get(channel)

    @classmethod
    def render_template(cls, template_name: str, channel: str,
                       variables: Dict) -> Optional[Message]:
        """渲染模板"""
        template = cls.get_template(template_name, channel)
        if not template:
            return None

        subject = template.get("subject", "")
        content = template.get("content", "")

        # 替换变量
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            subject = subject.replace(placeholder, str(value))
            content = content.replace(placeholder, str(value))

        return Message(
            channel=channel,
            to=[variables.get("customer_email", "")],
            subject=subject,
            content=content
        )


# ── 工厂函数 ────────────────────────────────────────

def create_email_sender(config: EmailConfig) -> EmailSender:
    """创建邮件发送器"""
    return EmailSender(config)


def create_sms_sender(config: SMSConfig) -> SMSSender:
    """创建短信发送器"""
    return SMSSender(config)


def create_wechat_work_sender(config: WeChatWorkConfig) -> WeChatWorkSender:
    """创建企业微信发送器"""
    return WeChatWorkSender(config)


def create_dingtalk_sender(config: DingTalkConfig) -> DingTalkSender:
    """创建钉钉发送器"""
    return DingTalkSender(config)


def create_webhook_sender(webhook_url: str, headers: Optional[Dict] = None) -> WebhookSender:
    """创建 Webhook 发送器"""
    return WebhookSender(webhook_url, headers)


def get_message_gateway() -> MessageGateway:
    """获取消息网关"""
    gateway = MessageGateway()
    gateway.register_sender("mock", MockSender())
    return gateway
