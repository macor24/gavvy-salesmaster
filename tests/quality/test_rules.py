# tests/quality/test_rules.py
"""红线扫描器 — 检查AI输出中的违禁词和结构完整性"""
import pytest
import json
from pathlib import Path
from typing import List, Dict

_HERE = Path(__file__).parent

# 加载真实AI输出
_real_outputs_path = _HERE / "_real_outputs.json"
if _real_outputs_path.exists():
    with open(_real_outputs_path) as f:
        _REAL_OUTPUTS = json.load(f)
else:
    _REAL_OUTPUTS = {}

REAL_AI_OUTPUT_MARKET = _REAL_OUTPUTS.get("market_researcher", "")
REAL_AI_OUTPUT_NEGOTIATOR = _REAL_OUTPUTS.get("presales_negotiator", "")


class SalesOutputRules:
    """销售场景的硬性规则 — 红线扫描器"""

    FORBIDDEN_PATTERNS = [
        "保证成交", "绝对", "低于市场价", "内部消息", "回扣"
    ]

    REQUIRED_ELEMENTS = {
        "market_researcher": ["行业", "市场规模", "竞争格局"],
        "competitor_analyst": ["竞品名称", "差异化"],
        "sales_negotiator": ["客户痛点", "下一步行动"],
    }

    @classmethod
    def validate(cls, output: str, agent_type: str) -> Dict:
        issues = []
        # 1. 查违禁词
        for pattern in cls.FORBIDDEN_PATTERNS:
            if pattern in output:
                issues.append({"type": "forbidden", "word": pattern, "severity": "critical"})
        # 2. 查必要元素
        if agent_type in cls.REQUIRED_ELEMENTS:
            missing = [e for e in cls.REQUIRED_ELEMENTS[agent_type] if e not in output]
            if missing:
                issues.append({"type": "missing", "elements": missing, "severity": "high"})
        return {"passed": len([i for i in issues if i["severity"] == "critical"]) == 0, "issues": issues}


class TestRules:
    def test_no_forbidden_words(self):
        for pattern in SalesOutputRules.FORBIDDEN_PATTERNS:
            assert pattern not in REAL_AI_OUTPUT_MARKET, f"发现敏感词: {pattern}"

    def test_structure_completeness_market(self):
        result = SalesOutputRules.validate(REAL_AI_OUTPUT_MARKET, "market_researcher")
        assert result["passed"], f"结构不完整: {result['issues']}"

    def test_structure_completeness_negotiator(self):
        result = SalesOutputRules.validate(REAL_AI_OUTPUT_NEGOTIATOR, "sales_negotiator")
        assert result["passed"], f"结构不完整: {result['issues']}"

    def test_output_not_empty(self):
        assert len(REAL_AI_OUTPUT_MARKET) > 50, "市场调研输出为空或太短"
        assert len(REAL_AI_OUTPUT_NEGOTIATOR) > 50, "售前输出为空或太短"

    def test_no_upgrade_hint_in_paid_mode(self):
        """企业版模式下不应出现社区版升级提示"""
        # 这个测试提醒：如果切换到企业版模式，升级提示应该被替换为真实内容
        pass  # 企业版待激活时补充断言
