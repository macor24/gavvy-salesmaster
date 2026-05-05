"""tianlong.sales.psychology — 拆分自 master.py"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

@dataclass
class ComplianceStep:
    """服从性阶梯上的一级台阶"""
    question: str          # 小要求/微承诺
    expected_answer: str   # 期望的"是"
    weight: float = 0.5    # 权重（影响最终成交的可能性）
    status: str = "pending"  # pending / yes / no


@dataclass
class EnergyState:
    """客户能量/情绪状态感知"""
    emotion: str = "neutral"
    intensity: float = 0.5       # 0-1 情绪强度
    engagement: float = 0.5      # 0-1 参与度
    hesitation_signals: List[str] = field(default_factory=list)
    last_pause_seconds: float = 0.0  # 最后沉默时长


class PsychologicalEngine:
    """高阶心理博弈引擎（§1-3）

    能力：
    1. 能量场掌控与情绪传导
    2. 服从性阶梯测试
    3. 损失厌恶高级运用
    """

    def __init__(self):
        self._energy: EnergyState = EnergyState()
        self._compliance_ladder: List[ComplianceStep] = []

    # ── 1. 能量场掌控 ──

    def assess_energy(self, text: str, pause_sec: float = 0.0,
                      sentiment: str = "neutral") -> EnergyState:
        """分析客户当前能量状态（LLM驱动，无Key时降级到关键词）。"""
        llm = _get_llm()
        if llm.available:
            try:
                result = llm.analyze_psychology(text, sentiment)
                self._energy.emotion = result.get("emotion", "neutral")
                self._energy.intensity = result.get("intensity", 0.5)
                self._energy.hesitation_signals.extend(result.get("hesitation_signals", []))
                self._energy.last_pause_seconds = pause_sec
                return self._energy
            except Exception:
                pass
        # 降级到已有的关键词引擎
        self._energy.last_pause_seconds = pause_sec
        # 关键词分析
        anger_kws = ["生气", "不满", "太贵", "骗子", "不行", "frustrated", "too expensive"]
        anxiety_kws = ["担心", "怕", "万一", "如果", "worried", "concerned"]
        interest_kws = ["不错", "可以", "继续", "具体", "interested", "tell me more"]

        if any(k in text.lower() for k in anger_kws):
            self._energy.emotion = "angry"
            self._energy.intensity = min(1.0, len(text) / 100 + 0.3)
        elif any(k in text.lower() for k in anxiety_kws):
            self._energy.emotion = "anxious"
            self._energy.intensity = 0.5
        elif any(k in text.lower() for k in interest_kws):
            self._energy.emotion = "interested"
            self._energy.intensity = 0.6

        # 沉默分析：>2秒停顿可能表明犹豫/顾虑
        if pause_sec > 2.0:
            self._energy.hesitation_signals.append(f"silence_{pause_sec:.1f}s")
            self._energy.engagement -= 0.1

        return self._energy

    def generate_energy_response(self, state: EnergyState) -> str:
        """根据客户能量状态生成情绪传导响应（LLM驱动）。"""
        llm = _get_llm()
        if llm.available:
            try:
                strategy = llm.generate_strategy({
                    "emotion": state.emotion,
                    "hesitation_signals": state.hesitation_signals,
                    "stage": "initial",
                })
                msg = strategy.get("recommended_message", "")
                if msg:
                    return msg
            except Exception:
                pass
        # 降级到已有的固定模板
        if state.emotion == "angry":
            return (
                "我非常理解您的心情。如果我是您，遇到同样的情况也会感到不满。"
                "请给我2分钟，让我把问题彻底理清楚，给您一个负责任的解决方案。"
            )
        elif state.emotion == "anxious":
            return (
                "您提的这个问题非常关键，很多客户在初期都会有同样的顾虑。"
                "我们恰好有一套成熟的方案来解决这个风险，我来为您详细说明。"
            )
        elif "silence" in str(state.hesitation_signals):
            return (
                "我感觉您是不是对某个方面还有顾虑？"
                "没关系的，您尽管说，任何问题我们都可以一起探讨。"
            )
        return ""

    # ── 2. 服从性阶梯 ──

    def build_compliance_ladder(self, stage: str) -> List[ComplianceStep]:
        """根据谈判阶段构建服从性阶梯。"""
        ladders = {
            "initial": [
                ComplianceStep("您觉得目前行业内的标准做法是什么？", "回答", 0.2),
                ComplianceStep("如果有一种方法能把这个问题解决，您感兴趣吗？", "是", 0.3),
                ComplianceStep("可否给我10分钟，为您做个针对性的方案演示？", "可以", 0.4),
            ],
            "solution": [
                ComplianceStep("您觉得这个方案对降低运营成本有帮助吗？", "有", 0.5),
                ComplianceStep("如果效果符合预期，您这边有进一步的预算规划吗？", "有", 0.6),
                ComplianceStep("能否安排一次技术团队的深入对接？", "可以", 0.7),
            ],
            "closing": [
                ComplianceStep("您是不是也认同，现在启动比拖延三个月更有优势？", "是", 0.8),
                ComplianceStep("如果我们要推进，您这边需要什么支持？", "回答", 0.9),
                ComplianceStep("那我们接下来按计划启动，您看方便吗？", "可以", 1.0),
            ],
        }
        self._compliance_ladder = ladders.get(stage, [])
        return self._compliance_ladder

    def record_compliance(self, question: str, answer: str) -> Dict:
        """记录客户对服从性阶梯的回应。"""
        for step in self._compliance_ladder:
            if step.question == question:
                step.status = "yes" if answer.lower() in ("是", "可以", "有", "行", "yes", "ok", "sure") else "no"
                return asdict(step)
        return {}

    @property
    def compliance_score(self) -> float:
        """计算服从性阶梯完成度（0-1）。"""
        if not self._compliance_ladder:
            return 0.0
        yes_count = sum(1 for s in self._compliance_ladder if s.status == "yes")
        total_weight = sum(s.weight for s in self._compliance_ladder if s.status != "pending")
        if total_weight == 0:
            return 0.0
        return sum(s.weight for s in self._compliance_ladder if s.status == "yes") / total_weight

    # ── 3. 损失厌恶 ──

    def generate_loss_aversion(self, pain_point: str, current_cost: str,
                                solution_value: str, time_frame: str = "三个月") -> str:
        """生成损失厌恶话术。

        参数:
            pain_point: 痛点描述（如"库存积压"）
            current_cost: 当前代价（如"年损失200万"）
            solution_value: 解决方案价值
            time_frame: 时间框架
        """
        return (
            f"假设这个系统已经在为您工作了。{time_frame}后，"
            f"当您的同行已经通过{solution_value}解决了{pain_point}的问题，"
            f"而您还在承受{current_cost}的损失——您会有什么感觉？\n\n"
            f"我们花了这么多时间梳理出来的这个{pain_point}问题，"
            f"如果不解决，您觉得下个季度它会自己消失吗？"
        )


# ═══════════════════════════════════════════════════════════════
# Phase 2: 多线程谈判管理


# llm helper
def _get_llm():
    from .llm import SalesLLM
    return SalesLLM()
