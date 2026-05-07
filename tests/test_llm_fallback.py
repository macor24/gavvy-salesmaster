"""test_llm_fallback.py — 三级降级链测试

覆盖：
  1. LocalLLM — available 检测、chat/chat_json 降级路径
  2. FallbackChain — 三级降级编排、熔断、状态
  3. RuleFallback — 各类型响应生成
  4. 集成 — SalesLLM 向后兼容
"""

import sys
import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from gavvy_salesmaster.core.llm_engine import (
    SalesLLM, SalesLLMConfig, FallbackChain, LocalLLM, RuleFallback,
)
from gavvy_salesmaster.team_pkg.llm import (
    SalesLLM as SalesLLM_via_package,
    FallbackChain as FallbackChain_via_package,
)


# ═══════════════════════════════════════════════════════
# LocalLLM 测试
# ═══════════════════════════════════════════════════════

class TestLocalLLM(unittest.TestCase):
    """本地 3B 量化模型调用器测试"""

    def setUp(self):
        # 用不存在的路径保证 available=False
        self.llm = LocalLLM(model_path="/nonexistent/model.gguf", cli_cmd="nonexistent-cli")

    def test_available_false_when_no_model(self):
        """没有模型文件时返回 False"""
        self.assertFalse(self.llm.available)

    def test_chat_returns_none_when_not_available(self):
        """不可用时 chat 返回 None"""
        result = self.llm.chat("system", "user")
        self.assertIsNone(result)

    def test_chat_json_returns_none_when_not_available(self):
        """不可用时 chat_json 返回 None"""
        result = self.llm.chat_json("system", "user")
        self.assertIsNone(result)

    @patch("gavvy_salesmaster.core.llm_engine.subprocess.run")
    @patch("gavvy_salesmaster.core.llm_engine.os.path.exists", return_value=True)
    @patch("gavvy_salesmaster.core.llm_engine.shutil.which", return_value="/usr/bin/llama-cli")
    def test_chat_returns_output(self, mock_which, mock_exists, mock_run):
        """chat 返回子进程 stdout"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Hello, I am an AI assistant.\n",
            stderr="",
        )
        llm = LocalLLM(model_path="/tmp/fake.gguf")  # now available due to mocks
        result = llm.chat("test system", "test user")
        self.assertIsNotNone(result)
        self.assertIn("Hello", result)

    @patch("gavvy_salesmaster.core.llm_engine.subprocess.run")
    @patch("gavvy_salesmaster.core.llm_engine.os.path.exists", return_value=True)
    @patch("gavvy_salesmaster.core.llm_engine.shutil.which", return_value="/usr/bin/llama-cli")
    def test_chat_timeout_returns_none(self, mock_which, mock_exists, mock_run):
        """子进程超时时返回 None"""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired("cmd", 30)
        llm = LocalLLM(model_path="/tmp/fake.gguf")
        result = llm.chat("system", "user")
        self.assertIsNone(result)

    @patch("gavvy_salesmaster.core.llm_engine.subprocess.run")
    @patch("gavvy_salesmaster.core.llm_engine.os.path.exists", return_value=True)
    @patch("gavvy_salesmaster.core.llm_engine.shutil.which", return_value="/usr/bin/llama-cli")
    def test_chat_nonzero_returncode(self, mock_which, mock_exists, mock_run):
        """子进程返回非零时返回 None"""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        llm = LocalLLM(model_path="/tmp/fake.gguf")
        result = llm.chat("system", "user")
        self.assertIsNone(result)

    @patch("gavvy_salesmaster.core.llm_engine.subprocess.run")
    @patch("gavvy_salesmaster.core.llm_engine.os.path.exists", return_value=True)
    @patch("gavvy_salesmaster.core.llm_engine.shutil.which", return_value="/usr/bin/llama-cli")
    def test_chat_json_parses_json(self, mock_which, mock_exists, mock_run):
        """chat_json 解析返回的 JSON"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"emotion": "interested", "intensity": 0.8}\n',
            stderr="",
        )
        llm = LocalLLM(model_path="/tmp/fake.gguf")
        result = llm.chat_json("system", "user")
        self.assertEqual(result["emotion"], "interested")
        self.assertEqual(result["intensity"], 0.8)

    def test_extract_json_valid(self):
        """_extract_json 正确解析"""
        result = LocalLLM._extract_json('{"key": "value"}')
        self.assertEqual(result["key"], "value")

    def test_extract_json_with_markdown(self):
        """_extract_json 处理 markdown 包裹的 JSON"""
        result = LocalLLM._extract_json('```json\n{"key": "val"}\n```')
        self.assertEqual(result["key"], "val")

    def test_extract_json_invalid(self):
        """_extract_json 无效 JSON 返回 None"""
        result = LocalLLM._extract_json("not json at all")
        self.assertIsNone(result)


# ═══════════════════════════════════════════════════════
# FallbackChain 测试
# ═══════════════════════════════════════════════════════

class TestFallbackChain(unittest.TestCase):
    """三级降级链编排器测试"""

    def setUp(self):
        # 无 API Key + 无本地模型 → 直接到规则引擎
        self.chain = FallbackChain(
            api=SalesLLMConfig(api_key=""),
            local=LocalLLM(model_path="/nonexistent", cli_cmd="nonexistent"),
        )

    def test_level_rule_when_nothing_available(self):
        """全部不可用时应为 rule 等级"""
        self.assertEqual(self.chain.level, "rule")

    def test_chat_returns_fallback_message(self):
        """都不可用时返回规则生成的响应"""
        result = self.chain.chat(
            "你是一位销售顾问。",
            "客户说想看看产品",
        )
        self.assertIsNotNone(result)

    def test_chat_json_returns_dict(self):
        """chat_json 返回 JSON"""
        result = self.chain.chat_json(
            "你是一位销售心理分析师。",
            "客户说价格太贵",
        )
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

    def test_get_status(self):
        """get_status 返回状态信息"""
        status = self.chain.get_status()
        self.assertIn("level", status)
        self.assertIn("api_available", status)
        self.assertIn("local_available", status)
        self.assertEqual(status["level"], "rule")

    def test_reset_circuit(self):
        """reset_circuit 重置熔断器"""
        self.chain._circuit_open = True
        self.chain._api_fail_count = 5
        self.chain.reset_circuit()
        self.assertFalse(self.chain._circuit_open)
        self.assertEqual(self.chain._api_fail_count, 0)

    @patch("gavvy_salesmaster.core.llm_engine.urlopen")
    @patch("gavvy_salesmaster.core.llm_engine.time.sleep", return_value=None)  # 跳过重试等待
    def test_circuit_opens_after_threshold(self, mock_sleep, mock_urlopen):
        """连续失败达到阈值后熔断"""
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("connection refused")
        from gavvy_salesmaster.core.llm_engine import _CIRCUIT_BREAK_THRESHOLD
        chain = FallbackChain(
            api=SalesLLMConfig(api_key="sk-test-valid", timeout=1),
            local=LocalLLM(model_path="/nonexistent", cli_cmd="nonexistent"),
        )
        for _ in range(_CIRCUIT_BREAK_THRESHOLD):
            chain._call_api("system", "user")
        self.assertTrue(chain._circuit_open)
        self.assertEqual(chain._api_fail_count, _CIRCUIT_BREAK_THRESHOLD)

    def test_api_level_with_key(self):
        """有 API Key 时 level 应为 api"""
        chain = FallbackChain(
            api=SalesLLMConfig(api_key="sk-test-key"),
            local=LocalLLM(model_path="/nonexistent", cli_cmd="nonexistent"),
        )
        # 即使有 Key，实际调用会因为 Key 无效失败，但 api_available 应为 True
        self.assertTrue(chain.api_available)
        # 熔断前 level 为 api
        self.assertEqual(chain.level, "api")

    # ── 各类型规则响应的 JSON 格式验证 ──

    def test_rule_psychology_returns_valid_json(self):
        """心理分析的规则响应是可解析的 JSON"""
        result = self.chain.chat_json(
            "你是一位销售心理分析师。分析客户的以下发言",
            "客户说考虑一下",
        )
        self.assertIsNotNone(result)
        self.assertIn("emotion", result)
        self.assertIn("intensity", result)

    def test_rule_competitor_returns_valid_json(self):
        """竞品分析的规则响应是可解析的 JSON"""
        result = self.chain.chat_json(
            "你是一位竞品情报分析师。",
            "客户比较了我们的产品和友商的产品",
        )
        self.assertIsNotNone(result)
        self.assertIn("mentioned_competitors", result)
        self.assertIn("our_advantages", result)

    def test_rule_strategy_returns_valid_json(self):
        """策略生成的规则响应是可解析的 JSON"""
        result = self.chain.chat_json(
            "你是一位销售策略师。基于以下对话分析制定下一步策略",
            "客户已经了解了产品",
        )
        self.assertIsNotNone(result)
        self.assertIn("next_action", result)
        self.assertIn("deal_readiness", result)

    def test_rule_value_returns_valid_json(self):
        """价值翻译的规则响应是可解析的 JSON"""
        result = self.chain.chat_json(
            "将客户的技术需求翻译为商业价值。",
            "我们需要一个能自动审计AI Agent安全的工具",
        )
        self.assertIsNotNone(result)
        self.assertIn("business_value", result)

    def test_rule_sales_returns_text(self):
        """销售话术返回文本"""
        result = self.chain.chat(
            "你是一位销售顾问",
            "您好，我想了解产品",
        )
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)

    # ── 重试机制 ──

    @patch("gavvy_salesmaster.core.llm_engine.urlopen")
    def test_api_retry_on_failure(self, mock_urlopen):
        """API 调用失败时重试"""
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("connection error")
        chain = FallbackChain(
            api=SalesLLMConfig(api_key="sk-test", timeout=1),
            local=LocalLLM(model_path="/nonexistent", cli_cmd="nonexistent"),
        )
        result = chain._call_api("system", "user")
        self.assertIsNone(result)
        # 应该调用了 3 次
        self.assertEqual(mock_urlopen.call_count, 3)


# ═══════════════════════════════════════════════════════
# RuleFallback 测试
# ═══════════════════════════════════════════════════════

class TestRuleFallback(unittest.TestCase):
    """规则引擎降级测试"""

    def setUp(self):
        self.rules = RuleFallback()

    def test_generate_response_sales(self):
        resp = self.rules.generate_response("你是一位销售顾问", "客户咨询产品")
        self.assertIsNotNone(resp)
        self.assertTrue(len(resp) > 10)

    def test_generate_response_unknown(self):
        resp = self.rules.generate_response("unknown type", "hello")
        self.assertIsNone(resp)

    def test_negotiate_price_accept(self):
        result = self.rules.negotiate_price(10000, 9500)
        self.assertEqual(result["action"], "accept")

    def test_negotiate_price_counter(self):
        result = self.rules.negotiate_price(10000, 7500)
        self.assertEqual(result["action"], "counter")

    def test_negotiate_price_reject(self):
        result = self.rules.negotiate_price(10000, 3000)
        self.assertEqual(result["action"], "reject")


# ═══════════════════════════════════════════════════════
# 集成测试：SalesLLM 向后兼容
# ═══════════════════════════════════════════════════════

class TestSalesLLMIntegration(unittest.TestCase):
    """SalesLLM 向后兼容测试"""

    def test_sales_llm_importable(self):
        """SalesLLM 可以从两个路径导入"""
        from gavvy_salesmaster.team_pkg.llm import SalesLLM as ViaLlm
        from gavvy_salesmaster.core.llm_engine import SalesLLM as ViaEngine
        self.assertEqual(ViaLlm.__name__, "SalesLLM")
        self.assertEqual(ViaEngine.__name__, "SalesLLM")

    def test_available_false_without_key(self):
        """无 Key 时 available 为 False"""
        # 保存并清除环境变量，避免被SENTRIKIT_API_KEY污染
        old_sk = os.environ.pop("SENTRIKIT_API_KEY", None)
        old_ds = os.environ.pop("DEEPSEEK_API_KEY", None)
        try:
            llm = SalesLLM()
            self.assertEqual(llm.available, False)
        finally:
            if old_sk: os.environ["SENTRIKIT_API_KEY"] = old_sk
            if old_ds: os.environ["DEEPSEEK_API_KEY"] = old_ds

    def test_call_returns_none_without_key(self):
        """无 Key 时 _call 返回 None（因为降级链全不可用）"""
        old_sk = os.environ.pop("SENTRIKIT_API_KEY", None)
        old_ds = os.environ.pop("DEEPSEEK_API_KEY", None)
        try:
            llm = SalesLLM()
            result = llm._call("system prompt", "user prompt")
            self.assertIsNone(result)
        finally:
            if old_sk: os.environ["SENTRIKIT_API_KEY"] = old_sk
            if old_ds: os.environ["DEEPSEEK_API_KEY"] = old_ds

    def test_call_with_rules_returns_something(self):
        """直接使用 FallbackChain 时规则引擎返回响应"""
        chain = FallbackChain(
            api=SalesLLMConfig(api_key=""),
            local=LocalLLM(model_path="/nonexistent", cli_cmd="nonexistent"),
        )
        result = chain.chat(
            "你是一位销售顾问。生成销售话术。",
            "客户说想了解产品",
        )
        self.assertIsNotNone(result)

    def test_cache_works(self):
        """_call 的缓存功能正常"""
        llm = SalesLLM()
        # 首次调用返回 None（无 API Key）
        r1 = llm._call("sys", "user")
        r2 = llm._call("sys", "user")
        self.assertEqual(r1, r2)


# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main()
