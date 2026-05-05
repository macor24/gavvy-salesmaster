"""tianlong.sales.language — 拆分自 master.py"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class LanguageMaster:
    """语言与非语言信号精密操作（§10-11）

    能力：
    10. 副语言解码与应对
    11. 极致精准的赞美与认可
    """

    @staticmethod
    def decode_paralanguage(text: str, pause_sec: float = 0.0) -> Dict:
        """解码副语言信号。"""
        signals = {}

        # 停顿分析
        if pause_sec > 1.5:
            signals["hesitation"] = True
            signals["interpretation"] = "有隐忧但不愿直说"

        # 关键词分析
        hedging_words = ["可能吧", "再想想", "考虑考虑", "maybe", "i'll think about it",
                         "let me think", "probably", "not sure"]
        if any(k in text.lower() for k in hedging_words):
            signals["hedging"] = True
            signals["interpretation"] = "需要更具体的价值论证"

        # 触发应对
        if signals.get("hesitation"):
            return {
                "signal": "hesitation",
                "response": (
                    "我感觉您是不是对后期运维这块还有顾虑？"
                    "没关系的，很多客户最开始都会有这个疑问，"
                    "我来为您详细说明我们的做法。"
                ),
            }
        if signals.get("hedging"):
            return {
                "signal": "hedging",
                "response": (
                    "我理解您需要一些时间来评估。其实很多客户在深入了解后，"
                    "都发现这个方案比预期中更能解决实际问题。"
                    "我再为您梳理一下核心价值点？"
                ),
            }
        return {"signal": "normal", "response": ""}

    @staticmethod
    def precise_praise(behavior: str, context: str = "") -> str:
        """极致精准的赞美。

        不是拍马屁，而是针对具体行为进行专业认可。
        """
        templates = [
            f"您刚才提到的{behavior}这个想法非常专业，很多客户都会忽略这一点。",
            f"感谢您的坦诚，这样的沟通效率很高。",
            f"您对{behavior}的深入理解，说明您在这个领域有很深的积累。",
        ]
        if context:
            return f"在{context}方面，{templates[0]}"
        return templates[0]


# ═══════════════════════════════════════════════════════════════
