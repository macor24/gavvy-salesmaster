"""tianlong.sales.value — 拆分自 master.py"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# Phase 3: 价值量化与商业洞察
# ═══════════════════════════════════════════════════════════════

@dataclass
class ValueEquation:
    """价值等式：客户对价值的认知 vs 对价格的抗拒"""
    perceived_value: float = 0.0    # 0-1 客户感知的价值
    price_resistance: float = 0.0   # 0-1 价格抗拒
    technical_metrics: List[str] = field(default_factory=list)
    business_metrics: List[str] = field(default_factory=list)

    @property
    def is_balanced(self) -> bool:
        """价值等式是否平衡（价值 > 价格抗拒）"""
        return self.perceived_value > self.price_resistance


class ValueConsultant:
    """价值量化与商业洞察（§6-7）

    能力：
    6. 实时痛点翻译与价值核算
    7. 行业先知般的威胁-机遇洞察
    """

    def __init__(self):
        self._equation = ValueEquation()

    def translate_pain_to_value(self, customer_statement: str) -> Dict:
        """将客户的技术语言翻译成商业语言（LLM驱动）。"""
        llm = _get_llm()
        if llm.available:
            try:
                result = llm.translate_value(customer_statement)
                return {
                    "business": result.get("business_value", customer_statement),
                    "metric": result.get("success_metric", "综合影响"),
                    "pain_points": result.get("pain_points", []),
                    "roi": result.get("estimated_roi", "待评估"),
                    "urgency": result.get("urgency_level", "medium"),
                }
            except Exception:
                pass
        # 降级到已有的关键词翻译
        translations = {
            "太贵": {"business": "运营成本需要优化", "metric": "年支出"},
            "不稳定": {"business": "业务连续性风险", "metric": "宕机时间"},
            "慢": {"business": "生产效率损失", "metric": "响应时间"},
            "不安全": {"business": "合规与数据泄露风险", "metric": "安全事件数"},
            "复杂": {"business": "团队学习成本高", "metric": "上手时间"},
        }
        for keyword, translation in translations.items():
            if keyword in customer_statement:
                return translation
        return {"business": customer_statement, "metric": "综合影响"}

    def build_competitive_intelligence(
        self, competitor: str, competitor_action: str,
        our_advantage: str, customer_name: str
    ) -> str:
        """构建竞品情报话术。"""
        return (
            f"{customer_name}，我刚看到{competitor}{competitor_action}。"
            f"如果他们通过{our_advantage}把成本打下来，"
            f"您这边会有竞争压力吗？"
            f"我们刚帮类似规模的企业用{our_advantage}顶住了价格战，"
            f"效果非常显著。"
        )

    def update_value_equation(self, perceived_value: float = 0.0,
                               price_resistance: float = 0.0) -> None:
        """更新价值等式。"""
        if perceived_value:
            self._equation.perceived_value = perceived_value
        if price_resistance:
            self._equation.price_resistance = price_resistance

    @property
    def value_equation(self) -> ValueEquation:
        return self._equation


# ═══════════════════════════════════════════════════════════════


# llm helper
def _get_llm():
    from .llm import SalesLLM
    return SalesLLM()
