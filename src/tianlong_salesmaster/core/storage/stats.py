"""tianlong_salesmaster.core.storage.stats — 统计聚合引擎

从数据仓库中聚合统计信息，支持多维度分析：

1. 销售漏斗统计 — 按阶段/时间分布
2. Agent 效能统计 — 各 Agent 执行次数/成功/拦截
3. 时间序列统计 — 日/周/月趋势
4. 评分分布统计 — 评分区间分布
5. 安全日志统计 — 拦截/通过比
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from .repository import DataRepository, get_repository


# 销售阶段顺序
_STAGE_ORDER = [
    "discovery", "research", "contact",
    "negotiation", "closing", "after_sales", "listing",
]

# 阶段中文名
_STAGE_LABELS = {
    "discovery": "发现",
    "research": "调研",
    "contact": "接触",
    "negotiation": "谈判",
    "closing": "成交",
    "after_sales": "售后",
    "listing": "上架",
    "initial": "初始",
}

# 各阶段权重（用于计算漏斗转化率）
_STAGE_WEIGHTS = {
    "initial": 0.0,
    "discovery": 0.1,
    "research": 0.2,
    "contact": 0.4,
    "negotiation": 0.6,
    "closing": 0.8,
    "after_sales": 0.9,
    "listing": 1.0,
}


class StatsEngine:
    """统计聚合引擎"""

    def __init__(self, repository: Optional[DataRepository] = None):
        self._repo = repository or get_repository()

    # ── 漏斗统计 ──

    def funnel_summary(self) -> Dict:
        """销售漏斗阶段分布统计"""
        leads = self._repo._kernel.get("leads")
        stage_counts: Dict[str, int] = {}
        for lead_id, lead in leads.items():
            stage = lead.get("stage", "initial")
            stage_counts[stage] = stage_counts.get(stage, 0) + 1

        # 按阶段顺序输出
        result = {}
        total = sum(stage_counts.values()) or 1
        for stage in _STAGE_ORDER:
            count = stage_counts.get(stage, 0)
            result[stage] = {
                "label": _STAGE_LABELS.get(stage, stage),
                "count": count,
                "pct": round(count / total * 100, 1),
            }

        # 计算整体转化进度
        weighted_sum = sum(
            _STAGE_WEIGHTS.get(stage, 0) * count
            for stage, count in stage_counts.items()
        )
        result["_meta"] = {
            "total_leads": sum(stage_counts.values()),
            "funnel_progress": round(weighted_sum / total, 2),
        }
        return result

    # ── Agent 效能统计 ──

    def agent_performance(self) -> Dict:
        """各 Agent 执行效能统计"""
        safety_logs = self._repo._kernel.get("safety_logs")
        agent_stats: Dict[str, Dict] = {}

        for log in safety_logs:
            agent = log.get("agent", "unknown")
            if agent not in agent_stats:
                agent_stats[agent] = {
                    "total": 0,
                    "approved": 0,
                    "rejected": 0,
                    "actions": {},
                }
            agent_stats[agent]["total"] += 1
            if log.get("approved", False):
                agent_stats[agent]["approved"] += 1
            else:
                agent_stats[agent]["rejected"] += 1

            action = log.get("action", "")
            agent_stats[agent]["actions"][action] = \
                agent_stats[agent]["actions"].get(action, 0) + 1

        # 补充计算通过率
        for agent, stats in agent_stats.items():
            total = stats["total"] or 1
            stats["approval_rate"] = round(stats["approved"] / total * 100, 1)

        return agent_stats

    # ── 评分统计 ──

    def score_distribution(self) -> Dict:
        """评分区间分布统计"""
        scores = self._repo._kernel.get("scores")
        if not scores:
            return {"buckets": {}, "average": 0.0, "count": 0}

        buckets = {
            "SS (90-100)": 0,
            "A  (75-89)": 0,
            "B  (60-74)": 0,
            "C  (40-59)": 0,
            "D  (0-39)": 0,
        }
        scores_list = []

        for score_record in scores:
            total_score = score_record.get("total_score") or \
                score_record.get("score", 0)
            scores_list.append(total_score)

            if total_score >= 90:
                buckets["SS (90-100)"] += 1
            elif total_score >= 75:
                buckets["A  (75-89)"] += 1
            elif total_score >= 60:
                buckets["B  (60-74)"] += 1
            elif total_score >= 40:
                buckets["C  (40-59)"] += 1
            else:
                buckets["D  (0-39)"] += 1

        average = round(sum(scores_list) / len(scores_list), 1) \
            if scores_list else 0.0

        return {
            "buckets": buckets,
            "average": average,
            "count": len(scores_list),
            "max": round(max(scores_list), 1) if scores_list else 0.0,
            "min": round(min(scores_list), 1) if scores_list else 0.0,
        }

    # ── 安全日志统计 ──

    def safety_summary(self, days: int = 7) -> Dict:
        """安全日志汇总统计"""
        logs = self._repo._kernel.get("safety_logs")
        cutoff = (datetime.now() - timedelta(days=days))

        recent = [
            log for log in logs
            if log.get("timestamp", "").startswith(
                cutoff.strftime("%Y-%m-%d")
            ) or log.get("saved_at", "").startswith(
                cutoff.strftime("%Y-%m-%d")
            )
        ]

        approved = sum(1 for log in recent if log.get("approved", False))
        rejected = sum(1 for log in recent if not log.get("approved", True))
        total = len(recent) or 1

        # 按天统计
        daily: Dict[str, Dict] = {}
        for log in recent:
            day = (log.get("timestamp") or log.get("saved_at", ""))[:10]
            if day not in daily:
                daily[day] = {"total": 0, "approved": 0, "rejected": 0}
            daily[day]["total"] += 1
            if log.get("approved", False):
                daily[day]["approved"] += 1
            else:
                daily[day]["rejected"] += 1

        return {
            "period_days": days,
            "total": total,
            "approved": approved,
            "rejected": rejected,
            "approval_rate": round(approved / total * 100, 1),
            "reject_rate": round(rejected / total * 100, 1),
            "daily": daily,
        }

    # ── 时间序列统计 ──

    def timeline(self, days: int = 30) -> Dict:
        """时间序列统计：每天的新增 lead、session、score、log"""
        result: Dict[str, Dict] = {}
        today = date.today()

        # 初始化空的天
        for i in range(days - 1, -1, -1):
            d = (today - timedelta(days=i)).isoformat()
            result[d] = {
                "leads": 0,
                "sessions": 0,
                "scores": 0,
                "insights": 0,
                "safety_logs": 0,
            }

        # 统计 leads
        leads = self._repo._kernel.get("leads")
        for lead in leads.values():
            dt = (lead.get("created_at") or lead.get("updated_at", ""))[:10]
            if dt in result:
                result[dt]["leads"] += 1

        # 统计 sessions
        sessions = self._repo._kernel.get("sessions")
        for sess in sessions.values():
            dt = (sess.get("created_at") or sess.get("updated_at", ""))[:10]
            if dt in result:
                result[dt]["sessions"] += 1

        # 统计 scores
        scores = self._repo._kernel.get("scores")
        for s in scores:
            dt = (s.get("timestamp") or s.get("saved_at", ""))[:10]
            if dt in result:
                result[dt]["scores"] += 1

        # 统计 insights
        insights = self._repo._kernel.get("insights")
        for ins in insights:
            dt = (ins.get("timestamp") or ins.get("saved_at", ""))[:10]
            if dt in result:
                result[dt]["insights"] += 1

        # 统计 safety_logs
        logs = self._repo._kernel.get("safety_logs")
        for log in logs:
            dt = (log.get("timestamp") or log.get("saved_at", ""))[:10]
            if dt in result:
                result[dt]["safety_logs"] += 1

        return result

    # ── 总览仪表盘 ──

    def dashboard(self) -> Dict:
        """全量汇总仪表盘"""
        return {
            "funnel": self.funnel_summary(),
            "agents": self.agent_performance(),
            "scores": self.score_distribution(),
            "safety": self.safety_summary(),
            "timeline": self.timeline(days=14),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
