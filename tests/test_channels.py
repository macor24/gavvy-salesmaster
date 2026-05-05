"""test_channels.py — 消息渠道模块测试"""

import unittest
import tempfile
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tianlong_salesmaster.channels_pkg.channels import (
    ChannelType, MessageType, Message, MessageResult,
    EmailConfig, SMSConfig, WeChatWorkConfig, DingTalkConfig,
)


class TestChannelTypes(unittest.TestCase):
    """渠道类型枚举测试"""

    def test_channel_type_values(self):
        self.assertEqual(ChannelType.EMAIL.value, "email")
        self.assertEqual(ChannelType.SMS.value, "sms")
        self.assertEqual(ChannelType.WECHAT_WORK.value, "wechat_work")
        self.assertEqual(ChannelType.DINGTALK.value, "dingtalk")

    def test_message_type_values(self):
        self.assertEqual(MessageType.TEXT.value, "text")
        self.assertEqual(MessageType.IMAGE.value, "image")
        self.assertEqual(MessageType.MARKDOWN.value, "markdown")
        self.assertEqual(MessageType.TEMPLATE.value, "template")
        self.assertEqual(MessageType.CARD.value, "card")


class TestMessage(unittest.TestCase):
    """消息模型测试"""

    def test_message_creation(self):
        msg = Message(
            to="test@example.com",
            subject="测试",
            content="Hello World",
            channel=ChannelType.EMAIL,
            msg_type=MessageType.TEXT,
        )
        self.assertEqual(msg.to, "test@example.com")
        self.assertEqual(msg.channel, ChannelType.EMAIL)

    def test_message_defaults(self):
        msg = Message(to="user", content="test")
        self.assertEqual(msg.channel, "email")
        self.assertEqual(msg.msg_type, "text")
        self.assertNotEqual(msg.created_at, "")


class TestMessageResult(unittest.TestCase):
    """消息结果测试"""

    def test_result_success(self):
        result = MessageResult(success=True, message_id="msg_001")
        self.assertTrue(result.success)
        self.assertEqual(result.message_id, "msg_001")
        self.assertIsNone(result.error)

    def test_result_failure(self):
        result = MessageResult(success=False, error="发送失败")
        self.assertFalse(result.success)
        self.assertEqual(result.error, "发送失败")


class TestChannelConfigs(unittest.TestCase):
    """渠道配置测试"""

    def test_email_config(self):
        cfg = EmailConfig(smtp_host="smtp.example.com", smtp_port=587, smtp_user="user", smtp_password="pass")
        self.assertEqual(cfg.smtp_host, "smtp.example.com")
        self.assertEqual(cfg.smtp_port, 587)

    def test_sms_config(self):
        cfg = SMSConfig(access_key="key_xxx", access_secret="secret", sign_name="测试")
        self.assertEqual(cfg.access_key, "key_xxx")
        self.assertEqual(cfg.sign_name, "测试")

    def test_wechat_config(self):
        cfg = WeChatWorkConfig(corp_id="corp", agent_id="1001", corp_secret="sec")
        self.assertEqual(cfg.corp_id, "corp")
        self.assertEqual(cfg.agent_id, "1001")

    def test_dingtalk_config(self):
        cfg = DingTalkConfig(app_key="key", app_secret="secret")
        self.assertEqual(cfg.app_key, "key")


if __name__ == "__main__":
    unittest.main()
