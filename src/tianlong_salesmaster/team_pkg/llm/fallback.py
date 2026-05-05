"""SentriKit_salesmaster.team_pkg.llm.fallback — 规则引擎降级

当 DeepSeek API 不可用时，使用规则引擎提供基础能力。
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional


class RuleFallback:
    """规则引擎降级——API 不可用时的兜底方案。"""

    @staticmethod
    def generate_sales_message(product_name: str, customer_name: str) -> str:
        templates = [
            f"您好，我是{product_name}的销售顾问。了解到贵公司在行业内的卓越表现，想与您探讨如何通过我们的解决方案进一步提升效率。",
            f"您好，我们{product_name}正在为同行业客户提供AI驱动的高效解决方案，想了解一下您目前是否有这方面的需求？",
        ]
        return random.choice(templates)

    @staticmethod
    def analyze_intent(keywords: List[str]) -> Dict:
        """基于关键词的简单意图分析。"""
        high_signals = ["价格", "购买", "多少钱", "下单", "合作", "签约"]
        low_signals = ["看看", "了解", "随便", "没兴趣", "不需要"]

        text = " ".join(keywords).lower()
        high = sum(1 for s in high_signals if s in text)
        low = sum(1 for s in low_signals if s in text)

        if high > low:
            return {"intent": "high", "score": 0.7 + random.random() * 0.2}
        elif low > high:
            return {"intent": "low", "score": 0.2 + random.random() * 0.2}
        return {"intent": "medium", "score": 0.4 + random.random() * 0.3}

    @staticmethod
    def negotiate_price(base_price: float, customer_offer: float) -> Dict:
        """简单价格谈判策略。"""
        ratio = customer_offer / base_price if base_price > 0 else 1

        if ratio >= 0.9:
            return {"action": "accept", "reason": "客户出价合理"}
        elif ratio >= 0.7:
            mid = (base_price + customer_offer) / 2
            return {"action": "counter", "counter_price": round(mid, -2), "reason": "折中方案"}
        else:
            return {"action": "reject", "reason": "出价过低，无法接受"}
