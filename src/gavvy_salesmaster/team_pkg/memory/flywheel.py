"""gavvy_salesmaster.team_pkg.memory.flywheel — 数据飞轮

从 Agent 执行数据中自动分析模式，反馈到评分和策略优化。

数据流:
    Agent 执行 → Learner记录episodes → 数据分析 → 评分权重优化 → Agent策略优化
                                      ↕
                             洞察/模式/技能沉淀
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from . import MemoryKernel


class DataFlywheel:
    """数据飞轮 — 从 Agent 执行数据中自动学习和优化

    用法:
        flywheel = DataFlywheel()
        report = flywheel.cycle()  # 执行一轮飞轮
    """

    def __init__(self, kernel: Optional[MemoryKernel] = None):
        self._kernel = kernel or MemoryKernel()

    # ── 核心循环 ──

    def cycle(self) -> Dict:
        """执行一轮数据飞轮：分析数据 → 生成优化
        
        Returns:
            Dict 包含分析结果和优化动作
        """
        episodes = self._kernel.get("episodes") or []
        agent_stats = self._kernel.get("agent_stats") or {}
        existing_insights = self._kernel.get("insights") or []
        existing_skills = self._kernel.get("skills") or []

        if not episodes:
            return {"status": "skipped", "reason": "无执行数据"}

        result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_episodes": len(episodes),
            "new_insights": 0,
            "new_skills": 0,
            "weight_adjustments": [],
            "patterns_found": [],
        }

        # 1. 分析 Agent 效能趋势
        trend = self._analyze_trend(episodes)
        result["trend"] = trend

        # 2. 发现模式（哪些策略组合更有效）
        patterns = self._discover_patterns(episodes, agent_stats)
        result["patterns_found"] = patterns

        # 3. 生成新洞察
        for pattern in patterns:
            title = pattern.get("title", "")
            # 去重：避免重复洞察
            if not any(i.get("title") == title for i in existing_insights):
                insight = {
                    "title": title,
                    "detail": pattern.get("detail", ""),
                    "confidence": pattern.get("confidence", 0.5),
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "data_flywheel",
                }
                existing_insights.append(insight)
                result["new_insights"] += 1

        # 4. 生成技能优化
        skill = self._evolve_skill(trend, agent_stats)
        if skill and not any(s.get("name") == skill["name"] for s in existing_skills):
            existing_skills.append(skill)
            result["new_skills"] += 1

        # 5. 反馈到评分权重
        adjustments = self._feedback_to_scoring(episodes, agent_stats)
        result["weight_adjustments"] = adjustments

        # 保存
        if result["new_insights"] > 0:
            self._kernel.write("insights", existing_insights[-100:])
        if result["new_skills"] > 0:
            self._kernel.write("skills", existing_skills[-50:])

        return result

    # ── 趋势分析 ──

    @staticmethod
    def _analyze_trend(episodes: List[Dict]) -> Dict:
        """分析 Agent 执行趋势"""
        if not episodes:
            return {}

        recent = episodes[-50:]  # 最近50条
        total = len(recent)
        success = sum(1 for e in recent if e.get("status") in ("success", "completed"))
        failed = sum(1 for e in recent if e.get("status") in ("failed", "blocked"))

        # 按 Agent 统计
        by_agent = defaultdict(lambda: {"total": 0, "success": 0, "failed": 0})
        for e in episodes:
            agent = e.get("agent", "unknown")
            by_agent[agent]["total"] += 1
            if e.get("status") in ("success", "completed"):
                by_agent[agent]["success"] += 1
            elif e.get("status") in ("failed", "blocked"):
                by_agent[agent]["failed"] += 1

        agent_rates = {}
        for agent, stats in by_agent.items():
            t = stats["total"]
            agent_rates[agent] = {
                "total": t,
                "rate": round(stats["success"] / max(t, 1) * 100, 1),
            }

        return {
            "recent_total": total,
            "recent_success_rate": round(success / max(total, 1) * 100, 1),
            "total_episodes": len(episodes),
            "total_success_rate": round(
                sum(1 for e in episodes if e.get("status") in ("success", "completed"))
                / max(len(episodes), 1) * 100, 1
            ),
            "by_agent": agent_rates,
        }

    # ── 模式发现 ──

    @staticmethod
    def _discover_patterns(episodes: List[Dict],
                           agent_stats: Dict) -> List[Dict]:
        """从执行记录中发现有效模式"""
        patterns = []

        if not episodes:
            return patterns

        # 按 action 统计成功率
        action_stats = defaultdict(lambda: {"total": 0, "success": 0})
        for e in episodes:
            action = e.get("action", "unknown")
            action_stats[action]["total"] += 1
            if e.get("status") in ("success", "completed"):
                action_stats[action]["success"] += 1

        # 高成功率 action 作为模式
        for action, stats in action_stats.items():
            if stats["total"] >= 3:
                rate = stats["success"] / stats["total"]
                if rate >= 0.8:
                    patterns.append({
                        "title": f"「{action}」策略成功率 {rate*100:.0f}%",
                        "detail": f"执行 {stats['total']} 次，成功 {stats['success']} 次，建议优先使用",
                        "confidence": round(rate * min(1.0, stats["total"] / 10), 2),
                        "type": "action_pattern",
                        "action": action,
                    })

        # 低成功率 action 报警
        for action, stats in action_stats.items():
            if stats["total"] >= 3:
                rate = stats["success"] / stats["total"]
                if rate < 0.3:
                    patterns.append({
                        "title": f"「{action}」策略成功率偏低 ({rate*100:.0f}%)",
                        "detail": f"执行 {stats['total']} 次，成功 {stats['success']} 次，建议优化或替换",
                        "confidence": round((1 - rate) * min(1.0, stats["total"] / 10), 2),
                        "type": "action_warning",
                        "action": action,
                    })

        # Agent 效能排名
        if agent_stats:
            sorted_agents = sorted(
                agent_stats.items(),
                key=lambda x: x[1].get("success", 0) / max(x[1].get("total", 0), 1),
                reverse=True,
            )
            if sorted_agents:
                best = sorted_agents[0]
                worst = sorted_agents[-1]
                if best != worst:
                    b_rate = best[1].get("success", 0) / max(best[1].get("total", 0), 1) * 100
                    w_rate = worst[1].get("success", 0) / max(worst[1].get("total", 0), 1) * 100
                    if b_rate > w_rate + 20:
                        patterns.append({
                            "title": f"效能差异：{best[0]} ({b_rate:.0f}%) vs {worst[0]} ({w_rate:.0f}%)",
                            "detail": f"最佳 Agent 效能是末位的显著优势，可分析 {best[0]} 的策略用于提升整体表现",
                            "confidence": 0.6,
                            "type": "agent_comparison",
                        })

        return patterns[:10]

    # ── 技能进化 ──

    @staticmethod
    def _evolve_skill(trend: Dict, agent_stats: Dict) -> Optional[Dict]:
        """基于数据分析生成新技能"""
        by_agent = trend.get("by_agent", {})
        if not by_agent:
            return None

        # 找出表现最好的 Agent 的策略作为新技能
        best_agent = max(by_agent.items(),
                         key=lambda x: x[1].get("rate", 0))
        if best_agent[1].get("rate", 0) < 60:
            return None

        return {
            "name": f"{best_agent[0]}_optimized",
            "label": f"{best_agent[0]} 优化策略",
            "description": f"基于 {best_agent[1].get('total', 0)} 次执行数据分析，"
                           f"成功率 {best_agent[1].get('rate', 0):.0f}%",
            "source": "data_flywheel",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    # ── 评分权重反馈 ──

    @staticmethod
    def _feedback_to_scoring(episodes: List[Dict],
                             agent_stats: Dict) -> List[Dict]:
        """根据执行数据反馈到线索评分权重"""
        adjustments = []

        try:
            from gavvy_salesmaster.crm_pkg.lead_gen.scoring import (
                get_lead_scoring_service,
            )
            service = get_lead_scoring_service()

            # 分析各 Agent 的成功率
            for agent_name, stats in agent_stats.items():
                total = stats.get("total", 0)
                if total < 5:
                    continue

                success_rate = stats.get("success", 0) / max(total, 1)
                if success_rate > 0.7:
                    # 某个 Agent 成功率高，增加行业匹配权重
                    service.model.adjust_weight("industry_match", 0.005)
                    adjustments.append({
                        "factor": "industry_match",
                        "delta": 0.005,
                        "reason": f"{agent_name} 成功率 {success_rate*100:.0f}%",
                    })
                elif success_rate < 0.3:
                    service.model.adjust_weight("engagement", -0.005)
                    adjustments.append({
                        "factor": "engagement",
                        "delta": -0.005,
                        "reason": f"{agent_name} 成功率偏低 ({success_rate*100:.0f}%)",
                    })
        except Exception:
            pass

        return adjustments
