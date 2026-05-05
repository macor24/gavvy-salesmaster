# tests/quality/test_llm_judge.py
"""AI质检员 — 用DeepSeek给AI Agent输出打分"""
import pytest
import json
import os
from typing import Dict

JUDGE_PROMPT = """你是一个销售质量评审专家。请对以下销售AI的输出进行评分（1-10分）。

评分维度：
1. 专业性：是否展现行业知识
2. 实用性：销售能否直接使用
3. 准确性：事实判断是否合理
4. 结构化：是否清晰易读
5. 行动导向：是否包含明确的下一步建议

被评估AI角色：{agent_role}
输出内容：
---
{output}
---

请严格按JSON回复：{{"总分": <1-50>, "主要问题": "<一句话>", "改进建议": "<一句话>"}}"""


class LLMJudge:
    """AI质检员 — 调用 DeepSeek API 评估输出质量

    成本约1分钱/次。需要设置 DEEPSEEK_API_KEY 环境变量。
    如果没有API Key，使用模拟评分模式（仅用于测试框架功能）。
    """

    def __init__(self):
        self.api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        self._using_mock = not bool(self.api_key)

    def evaluate(self, output: str, agent_role: str) -> Dict:
        if self._using_mock:
            # 模拟评分 — 基于规则估算
            score = self._mock_score(output)
            return {
                "总分": score,
                "主要问题": "模拟模式（未配置DEEPSEEK_API_KEY）",
                "改进建议": "设置环境变量 DEEPSEEK_API_KEY 启用真实AI评测",
            }

        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": JUDGE_PROMPT.format(
                agent_role=agent_role, output=output
            )}],
            response_format={"type": "json_object"},
            temperature=0,
        )
        return json.loads(response.choices[0].message.content)

    def _mock_score(self, output: str) -> int:
        """基于规则的快速质量估算（无API时的兜底）"""
        score = 0
        # 长度分数
        if len(output) > 300:
            score += 10
        elif len(output) > 100:
            score += 5
        # 结构分数
        if "##" in output:
            score += 8
        if "- " in output:
            score += 5
        # 内容分数
        for kw in ["建议", "方案", "分析", "价值", "价格", "下一步", "推荐"]:
            if kw in output:
                score += 2
        # 行动导向
        if "建议" in output or "推荐" in output:
            score += 5
        return min(score, 50)


# 加载真实输出
from pathlib import Path
_HERE = Path(__file__).parent
_real_path = _HERE / "_real_outputs.json"
if _real_path.exists():
    with open(_real_path) as f:
        _REAL_OUTPUTS = json.load(f)
else:
    _REAL_OUTPUTS = {}


class TestWithAI:
    @pytest.fixture
    def judge(self):
        return LLMJudge()

    def test_market_researcher_quality(self, judge):
        output = _REAL_OUTPUTS.get("market_researcher", "")
        if not output:
            pytest.skip("没有真实输出数据")
        result = judge.evaluate(output, "market_researcher")
        print(f"\n📊 市场调研官质量评分: {result['总分']}/50")
        print(f"   主要问题: {result['主要问题']}")
        print(f"   改进建议: {result['改进建议']}")
        assert result["总分"] >= 15, f"市场调研质量过低: {result['总分']}/50"

    def test_presales_negotiator_quality(self, judge):
        output = _REAL_OUTPUTS.get("presales_negotiator", "")
        if not output:
            pytest.skip("没有真实输出数据")
        result = judge.evaluate(output, "sales_negotiator")
        print(f"\n📊 售前谈判官质量评分: {result['总分']}/50")
        print(f"   主要问题: {result['主要问题']}")
        print(f"   改进建议: {result['改进建议']}")
        assert result["总分"] >= 15, f"售前谈判质量过低: {result['总分']}/50"
