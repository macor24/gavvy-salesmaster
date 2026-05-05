"""test_wework.py — 企业微信 API 通信渠道测试

覆盖：
  1. WeWorkChannel 基础功能（配置检测、Token 管理）
  2. 消息发送（所有消息类型）
  3. API 错误处理
  4. 消息状态管理
"""

import sys
import os
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tianlong_salesmaster.channels_pkg.channels.wework import WeWorkChannel
from tianlong_salesmaster.channels_pkg.channels.base import Message


VALID_CONFIG = {
    "corp_id": "ww12345678",
    "agent_id": 1000001,
    "secret": "test-secret",
}


class TestWeWorkChannel(unittest.TestCase):
    """企业微信通信渠道测试"""

    def setUp(self):
        self.channel = WeWorkChannel(config=dict(VALID_CONFIG))

    def test_name(self):
        """渠道名称正确"""
        self.assertEqual(self.channel.name, "wework")

    def test_is_configured_complete(self):
        """完整配置时返回 True"""
        self.assertTrue(self.channel.is_configured)

    def test_is_configured_missing_corp_id(self):
        """缺少 corp_id 时返回 False"""
        c = WeWorkChannel(config={"agent_id": 1, "secret": "s"})
        self.assertFalse(c.is_configured)

    def test_is_configured_missing_agent_id(self):
        """缺少 agent_id 时返回 False"""
        c = WeWorkChannel(config={"corp_id": "c", "secret": "s"})
        self.assertFalse(c.is_configured)

    def test_is_configured_missing_secret(self):
        """缺少 secret 时返回 False"""
        c = WeWorkChannel(config={"corp_id": "c", "agent_id": 1})
        self.assertFalse(c.is_configured)

    def test_is_configured_empty_config(self):
        """空配置时返回 False"""
        c = WeWorkChannel()
        self.assertFalse(c.is_configured)

    # ── Token 管理 ──

    @patch("tianlong_salesmaster.channels_pkg.channels.wework.urlopen")
    def test_get_token_success(self, mock_urlopen):
        """获取 Token 成功"""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "errcode": 0,
            "access_token": "mock-token-123",
            "expires_in": 7200,
        }).encode("utf-8")
        mock_urlopen.return_value = mock_resp

        token = self.channel._get_token()
        self.assertEqual(token, "mock-token-123")
        self.assertEqual(self.channel._token, "mock-token-123")

    @patch("tianlong_salesmaster.channels_pkg.channels.wework.urlopen")
    def test_get_token_failure(self, mock_urlopen):
        """Token 获取失败返回 None"""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "errcode": 40013,
            "errmsg": "invalid corpid",
        }).encode("utf-8")
        mock_urlopen.return_value = mock_resp

        token = self.channel._get_token()
        self.assertIsNone(token)

    @patch("tianlong_salesmaster.channels_pkg.channels.wework.urlopen")
    def test_get_token_network_error(self, mock_urlopen):
        """网络错误返回 None"""
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("connection failed")
        token = self.channel._get_token()
        self.assertIsNone(token)

    def test_get_token_not_configured(self):
        """未配置时返回 None"""
        c = WeWorkChannel()
        token = c._get_token()
        self.assertIsNone(token)

    @patch("tianlong_salesmaster.channels_pkg.channels.wework.urlopen")
    def test_token_caching(self, mock_urlopen):
        """Token 缓存避免重复请求"""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "errcode": 0,
            "access_token": "cached-token",
            "expires_in": 7200,
        }).encode("utf-8")
        mock_urlopen.return_value = mock_resp

        # 第一次调用
        token1 = self.channel._get_token()
        # 第二次应该走缓存
        self.channel._token_expires_at = 9999999999  # 模拟未过期
        token2 = self.channel._get_token()
        self.assertEqual(token2, "cached-token")
        self.assertEqual(mock_urlopen.call_count, 1)

    def test_clear_token(self):
        """清除 Token"""
        self.channel._token = "some-token"
        self.channel._token_expires_at = 9999999999
        self.channel._clear_token()
        self.assertEqual(self.channel._token, "")
        self.assertEqual(self.channel._token_expires_at, 0.0)

    # ── 消息发送 ──

    @patch("tianlong_salesmaster.channels_pkg.channels.wework.WeWorkChannel._get_token")
    @patch("tianlong_salesmaster.channels_pkg.channels.wework.urlopen")
    def test_send_text_success(self, mock_urlopen, mock_token):
        """发送文本消息成功"""
        mock_token.return_value = "valid-token"
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "errcode": 0,
            "errmsg": "ok",
        }).encode("utf-8")
        mock_urlopen.return_value = mock_resp

        msg = Message(to="user123", body="您好，我是销售助理")
        result = self.channel.send(msg)
        self.assertTrue(result)
        self.assertEqual(msg.status, "sent")

    @patch("tianlong_salesmaster.channels_pkg.channels.wework.WeWorkChannel._get_token")
    @patch("tianlong_salesmaster.channels_pkg.channels.wework.urlopen")
    def test_send_text_api_error(self, mock_urlopen, mock_token):
        """API 返回错误码时标记失败"""
        mock_token.return_value = "valid-token"
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "errcode": 40003,
            "errmsg": "invalid userid",
        }).encode("utf-8")
        mock_urlopen.return_value = mock_resp

        msg = Message(to="invalid_user", body="test")
        result = self.channel.send(msg)
        self.assertFalse(result)
        self.assertEqual(msg.status, "failed")

    def test_send_not_configured(self):
        """未配置时发送失败"""
        c = WeWorkChannel()
        msg = Message(to="user", body="test")
        result = c.send(msg)
        self.assertFalse(result)
        self.assertEqual(msg.status, "failed")

    @patch("tianlong_salesmaster.channels_pkg.channels.wework.WeWorkChannel._get_token")
    def test_send_token_expired(self, mock_token):
        """Token 过期时自动清除并标记失败"""
        mock_token.return_value = None

        msg = Message(to="user", body="test")
        result = self.channel.send(msg)
        self.assertFalse(result)
        self.assertIn("access_token", msg.metadata.get("error", ""))

    # ── send_markdown ──

    @patch("tianlong_salesmaster.channels_pkg.channels.wework.WeWorkChannel._get_token")
    @patch("tianlong_salesmaster.channels_pkg.channels.wework.urlopen")
    def test_send_markdown(self, mock_urlopen, mock_token):
        """发送 markdown 消息"""
        mock_token.return_value = "token"
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "errcode": 0, "errmsg": "ok",
        }).encode("utf-8")
        mock_urlopen.return_value = mock_resp

        result = self.channel.send_markdown("user1", "# 标题\n内容")
        self.assertTrue(result)

    # ── send_news ──

    @patch("tianlong_salesmaster.channels_pkg.channels.wework.WeWorkChannel._get_token")
    @patch("tianlong_salesmaster.channels_pkg.channels.wework.urlopen")
    def test_send_news(self, mock_urlopen, mock_token):
        """发送图文消息"""
        mock_token.return_value = "token"
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "errcode": 0, "errmsg": "ok",
        }).encode("utf-8")
        mock_urlopen.return_value = mock_resp

        articles = [{"title": "产品介绍", "url": "https://example.com"}]
        result = self.channel.send_news("user1", articles)
        self.assertTrue(result)

    # ── receive / get_contacts ──

    def test_receive_returns_empty(self):
        """receive 返回空列表（企业微信通过回调接收）"""
        msgs = self.channel.receive()
        self.assertEqual(msgs, [])

    @patch("tianlong_salesmaster.channels_pkg.channels.wework.WeWorkChannel._get_token")
    @patch("tianlong_salesmaster.channels_pkg.channels.wework.urlopen")
    def test_get_contacts(self, mock_urlopen, mock_token):
        """获取联系人列表"""
        mock_token.return_value = "token"
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "errcode": 0,
            "userlist": [
                {"userid": "zhangsan", "name": "张三"},
                {"userid": "lisi", "name": "李四"},
            ],
        }).encode("utf-8")
        mock_urlopen.return_value = mock_resp

        contacts = self.channel.get_contacts()
        self.assertEqual(len(contacts), 2)

    # ── parse_callback_message ──

    def test_parse_callback_text(self):
        """解析文本回调消息"""
        body = {
            "MsgId": "abc123",
            "MsgType": "text",
            "FromUserName": "user1",
            "Content": "你好",
            "CreateTime": "1714567890",
        }
        msg = self.channel.parse_callback_message(body)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.body, "你好")
        self.assertEqual(msg.from_, "user1")

    def test_parse_callback_unsupported_type(self):
        """不支持的 type 返回 None"""
        body = {"MsgType": "image"}
        msg = self.channel.parse_callback_message(body)
        self.assertIsNone(msg)

    # ── get_send_status ──

    def test_get_send_status_empty(self):
        """未发送时状态为空"""
        status = self.channel.get_send_status()
        self.assertEqual(status["total"], 0)
        self.assertEqual(status["sent"], 0)
        self.assertEqual(status["failed"], 0)

    @patch("tianlong_salesmaster.channels_pkg.channels.wework.WeWorkChannel._get_token")
    @patch("tianlong_salesmaster.channels_pkg.channels.wework.urlopen")
    def test_get_send_status_after_send(self, mock_urlopen, mock_token):
        """发送后状态更新正确"""
        mock_token.return_value = "token"
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "errcode": 0, "errmsg": "ok",
        }).encode("utf-8")
        mock_urlopen.return_value = mock_resp

        self.channel.send(Message(to="u1", body="hi"))
        status = self.channel.get_send_status()
        self.assertEqual(status["sent"], 1)

    # ── 企业微信特有：AgentId 为 0 时不可用 ──

    def test_agent_id_zero_not_configured(self):
        """agent_id 为 0 视为未配置"""
        c = WeWorkChannel(config={"corp_id": "c", "agent_id": 0, "secret": "s"})
        self.assertFalse(c.is_configured)


if __name__ == "__main__":
    unittest.main()
