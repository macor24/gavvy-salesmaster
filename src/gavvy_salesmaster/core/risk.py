"""SentriKit.sales.risk — 拆分自 master.py"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# Phase 4: 风险管控与极限场景决策
# ═══════════════════════════════════════════════════════════════

class RiskManager:
    """风险管控与极限场景决策（§8-9）

    能力：
    8. 高风险议题的"柔道术"
    9. "完美失败"机制
    """

    @staticmethod
    def handle_difficult_request(request: str) -> str:
        """应对超出权限的要求。

        策略：
        - 反问澄清式：把要求转化为可探讨的方案
        - 向上绑定式：升级到更高层决策
        """
        if "折扣" in request or "降价" in request or "免费" in request or "打折" in request or "八折" in request:
            return (
                "这个要求我理解。如果我们用阶梯式付款或年度承诺的方式"
                "来对等实现，您觉得可以探讨吗？"
            )
        if "保证" in request or "承诺" in request or "一定" in request:
            return (
                "这个要求需要我协同总监与您开个三方会议，"
                "确保我们承诺的资源都是可落地的。您看明天下午方便吗？"
            )
        if "退款" in request or "赔偿" in request or "投诉" in request:
            return (
                "我完全理解您的要求。我先把情况完整记录下来，"
                "上报给相关负责人，24小时内给您正式答复。"
                "您看这样可以吗？"
            )
        return (
            "您提的这个角度很好。我先确认一下内部流程，"
            "尽快给您一个明确的答复。"
        )

    @staticmethod
    def graceful_fail(reason: str, restart_condition: str) -> str:
        """优雅失败，为未来播下种子。"""
        return (
            f"非常感谢您今天的坦诚沟通。我理解目前无法推进的原因是：{reason}。\n\n"
            f"如果您方便的话，我想记录一下：当{restart_condition}时，"
            f"我是否可以再次联系您？届时我相信我们的方案会更契合您的需求。"
        )


# ═══════════════════════════════════════════════════════════════
