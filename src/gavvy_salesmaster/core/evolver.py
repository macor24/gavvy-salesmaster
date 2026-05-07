"""SentriKit.sales.evolver — 拆分自 master.py"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# ═══════════════════════════════════════════════════════════════

@dataclass
class DealAnalysis:
    """一次成交/失败的分析记录"""
    customer: str = ""
    smoothness: float = 0.5      # 沟通过程顺畅度
    result: str = "lost"         # won / lost
    failure_patterns: List[str] = field(default_factory=list)
    successful_tactics: List[str] = field(default_factory=list)
    hidden_pattern: str = ""


class StrategyEvolver:
    """策略网络自我迭代与反学习（§12-13）

    能力：
    12. 发现"未知的未知"
    13. 跨行业策略迁移
    """

    def __init__(self):
        self._deals: List[DealAnalysis] = []
        self._cross_industry_patterns: Dict[str, List[str]] = {}

    def analyze_deal(self, deal: DealAnalysis) -> DealAnalysis:
        """分析成交/失败案例，发现隐藏模式。"""
        # 发现"未知的未知"：对话顺畅但最终失败
        if deal.smoothness > 0.7 and deal.result == "lost":
            deal.hidden_pattern = (
                "【未知的未知检测】沟通过程极度顺畅但最终未成交。"
                "可能隐藏原因：价值传递未触及决策者真正痛点，"
                "或内部存在未暴露的反对者。建议：在后期引入第三方权威背书。"
            )
        self._deals.append(deal)
        return deal

    def suggest_ab_test(self) -> str:
        """生成A/B测试建议。"""
        if not self._deals:
            return "尚无足够数据，建议积累至少5次成交/失败案例后启用"

        lost_count = sum(1 for d in self._deals if d.result == "lost")
        won_count = sum(1 for d in self._deals if d.result == "won")
        total = len(self._deals)

        return (
            f"数据积累：{won_count}胜 / {lost_count}败 (总计{total}次)\n"
            f"A/B测试建议：\n"
            f"  方案A：标准化话术（当前方案）\n"
            f"  方案B：针对{self._find_common_failure()}痛点的新型话术\n"
            f"  建议周期：2周 / 各20次对话"
        )

    def _find_common_failure(self) -> str:
        """找出最常见的失败原因。"""
        from collections import Counter
        all_patterns = []
        for d in self._deals:
            all_patterns.extend(d.failure_patterns)
        if not all_patterns:
            return "价格"
        return Counter(all_patterns).most_common(1)[0][0]

    def transfer_strategy(self, from_industry: str, to_industry: str,
                          strategy: str) -> str:
        """跨行业策略迁移。"""
        key = f"{from_industry}->{to_industry}"
        if key not in self._cross_industry_patterns:
            self._cross_industry_patterns[key] = []
        self._cross_industry_patterns[key].append(strategy)

        return (
            f"策略迁移：从{from_industry}行业 -> {to_industry}行业\n"
            f"原始策略：{strategy}\n"
            f"迁移适配：注意到两个行业在"
            f"{self._find_common_psychology(from_industry, to_industry)}"
            f"方面具有相似的客户心理结构，策略可复用。"
        )

    @staticmethod
    def _find_common_psychology(a: str, b: str) -> str:
        """查找跨行业共通的客户心理特征。"""
        common_map = {
            ("SaaS", "金融"): "对长期合同的风险规避心理",
            ("电商", "零售"): "库存周转效率焦虑",
            ("制造", "物流"): "运营成本敏感度",
        }
        for (ia, ib), psychology in common_map.items():
            if (a == ia and b == ib) or (a == ib and b == ia):
                return psychology
        return "决策谨慎度"

    def get_stats(self) -> Dict:
        """获取进化统计"""
        return {
            "total_deals": len(self._deals),
            "won": sum(1 for d in self._deals if d.result == "won"),
            "lost": sum(1 for d in self._deals if d.result == "lost"),
            "hidden_patterns_found": sum(1 for d in self._deals if d.hidden_pattern),
            "cross_industry_transfers": len(self._cross_industry_patterns),
        }


# ═══════════════════════════════════════════════════════════════
# 全局单例 + 桥接 Learner -> Evolver
# ═══════════════════════════════════════════════════════════════

_global_evolver: Optional[StrategyEvolver] = None


def get_evolver() -> StrategyEvolver:
    global _global_evolver
    if _global_evolver is None:
        _global_evolver = StrategyEvolver()
    return _global_evolver


def learn_to_evolver(episode: Dict) -> Optional[str]:
    """将 Learner 的 episode 记录自动桥接到 StrategyEvolver

    当 Learner 记录了一条执行结果后调用此函数，
    将执行数据转换为 DealAnalysis 并推给 evolver 分析。
    返回隐藏模式检测结果（如有），否则 None。
    """
    evolver = get_evolver()
    status = episode.get("status", "")
    agent_name = episode.get("agent", "")
    action = episode.get("action", "")

    # 只处理销售相关 Agent 的 completed/success 或 failed 记录
    if status not in ("success", "completed", "failed", "blocked"):
        return None

    deal = DealAnalysis(
        customer=episode.get("input_summary", "未知客户")[:20],
        smoothness=0.8 if status in ("success", "completed") else 0.3,
        result="won" if status in ("success", "completed") else "lost",
        failure_patterns=[] if status in ("success", "completed") else [f"agent:{agent_name}"],
        successful_tactics=[action] if action and status in ("success", "completed") else [],
    )
    result = evolver.analyze_deal(deal)
    return result.hidden_pattern if result.hidden_pattern else None


# ═══════════════════════════════════════════════════════════════
# 导出
# ═══════════════════════════════════════════════════════════════

__all__ = [
    "DealAnalysis",
    "StrategyEvolver",
    "get_evolver",
    "learn_to_evolver",
]
