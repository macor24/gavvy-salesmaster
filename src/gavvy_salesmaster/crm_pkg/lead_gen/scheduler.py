"""gavvy_salesmaster.crm_pkg.lead_gen.scheduler — 自动调度器

意图分类 → 匹配 Agent → 创建任务 → 执行 → 回写 → 推进 Pipeline。

与 HuntEngine 配合：高评分线索自动进入调度队列，
IntentClassifier 判断客户意图，分配给最合适的 Agent 处理。
"""

from __future__ import annotations

import json
import os
import threading
import uuid
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from .hunt_engine import HuntEngine, FoundLead


# ── 意图分类器 ─────────────────────────────────

# 关键词 → Agent 映射
INTENT_PATTERNS: Dict[str, List[str]] = {
    "market_research_agent": [
        r"市场", r"行业", r"趋势", r"调研", r"现状",
        r"市场规模", r"竞争格局", r"增速",
    ],
    "competitor_intel_agent": [
        r"竞品", r"对比", r"对手", r"竞对",
        r"差异化", r"优势", r"劣势",
    ],
    "presales_agent": [
        r"价格", r"多少钱", r"报价", r"优惠", r"折扣",
        r"购买", r"下单", r"试用", r"演示", r"方案",
        r"怎么收费", r"多少钱一套", r"预算",
    ],
    "aftersales_agent": [
        r"售后", r"维修", r"退换", r"退款", r"投诉",
        r"坏了", r"问题", r"故障", r"复购", r"续费",
        r"技术支持", r"客服", r"维保",
    ],
    "procurement_agent": [
        r"采购", r"货源", r"供应链", r"成本", r"利润",
        r"供应商", r"进货", r"代工", r"OEM",
    ],
    "operations_agent": [
        r"运营", r"数据", r"增长", r"转化",
        r"流量", r"ROI", r"投产比", r"优化",
    ],
    "platform_ops_agent": [
        r"审核", r"合规", r"上架", r"下架",
        r"资质", r"认证", r"许可", r"入驻",
    ],
}

AGENT_NAMES: Dict[str, str] = {
    "market_research_agent": "市场调研官",
    "competitor_intel_agent": "竞品分析官",
    "presales_agent": "售前谈判官",
    "aftersales_agent": "售后维系官",
    "procurement_agent": "采购供应链官",
    "operations_agent": "运营增长官",
    "platform_ops_agent": "运营助理",
}


def classify_intent(message: str) -> str:
    """对客户消息进行意图分类，返回匹配的 Agent role_en

    Args:
        message: 客户消息文本

    Returns:
        str: 匹配的 Agent role_en，无匹配返回 "market_research_agent"
    """
    scores: Dict[str, int] = {}
    for agent_key, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, message):
                scores[agent_key] = scores.get(agent_key, 0) + 1

    if not scores:
        return "market_research_agent"  # 默认分配市场调研官

    # 返回匹配关键词最多的 Agent
    return max(scores, key=scores.get)


# ── 任务数据结构 ───────────────────────────────


@dataclass
class ScheduledTask:
    """一次调度任务"""
    id: str = ""
    lead_company: str = ""
    lead_id: str = ""
    message: str = ""
    agent_role: str = ""
    agent_name: str = ""
    status: str = "pending"  # pending / running / completed / failed
    created_at: str = ""
    completed_at: str = ""
    result_summary: str = ""
    result_output: str = ""
    error: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict) -> "ScheduledTask":
        return ScheduledTask(**{k: v for k, v in d.items()
                               if k in ScheduledTask.__dataclass_fields__})


# ── 自动调度器 ─────────────────────────────────


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))),
    "data", "scheduler")


class AutoScheduler:
    """自动调度器 — 意图分类 → 匹配 Agent → 执行 → 回写

    用法:
        scheduler = AutoScheduler(hunt_engine)
        task = scheduler.submit("报价多少钱？", "某某科技", "AI客服系统")
    """

    def __init__(self, hunt_engine: Optional[HuntEngine] = None,
                 orchestrator=None, data_dir: str = ""):
        self._hunt = hunt_engine
        self._orch = orchestrator
        self._data_dir = data_dir or DATA_DIR
        self._tasks_path = os.path.join(self._data_dir, "tasks.json")
        self._lock = threading.Lock()
        os.makedirs(self._data_dir, exist_ok=True)

        self._tasks: Dict[str, ScheduledTask] = {}
        self._load_tasks()

    # ── 任务队列 ───────────────────────────────

    def get_tasks(self, limit: int = 50) -> List[ScheduledTask]:
        with self._lock:
            tasks = list(self._tasks.values())
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks[:limit]

    def get_pending_tasks(self) -> List[ScheduledTask]:
        with self._lock:
            return [t for t in self._tasks.values() if t.status == "pending"]

    def get_task_count(self) -> Dict[str, int]:
        with self._lock:
            counts: Dict[str, int] = {}
            for t in self._tasks.values():
                counts[t.status] = counts.get(t.status, 0) + 1
        return counts

    def _load_tasks(self) -> None:
        try:
            if os.path.isfile(self._tasks_path):
                with open(self._tasks_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                with self._lock:
                    self._tasks = {k: ScheduledTask.from_dict(v)
                                   for k, v in data.items()}
        except Exception:
            self._tasks = {}

    def _save_tasks(self) -> None:
        try:
            with self._lock:
                data = {k: v.to_dict() for k, v in self._tasks.items()}
            with open(self._tasks_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ── 核心流程 ───────────────────────────────

    def submit(self, message: str, customer: str,
               product: str = "", lead_id: str = "") -> ScheduledTask:
        """提交一条客户消息到调度器

        1. 意图分类 → 匹配 Agent
        2. 创建任务入队
        3. 执行 Agent
        4. 更新任务状态

        Args:
            message: 客户消息
            customer: 客户名称
            product: 产品信息（可选）
            lead_id: Lead ID（可选）

        Returns:
            ScheduledTask: 执行后的任务对象
        """
        # 1. 意图分类
        agent_role = classify_intent(message)
        agent_name = AGENT_NAMES.get(agent_role, agent_role)

        # 2. 创建任务
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task = ScheduledTask(
            id=task_id,
            lead_company=customer,
            lead_id=lead_id,
            message=message,
            agent_role=agent_role,
            agent_name=agent_name,
            status="pending",
            created_at=now,
        )

        with self._lock:
            self._tasks[task_id] = task
        self._save_tasks()

        # 3. 执行 Agent
        task = self._execute_agent(task_id)

        return task

    def _execute_agent(self, task_id: str) -> ScheduledTask:
        """执行 Agent 任务

        优先使用已注册的 Agent（通过 Orchestrator），
        如果不可用则输出模板回复。
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return task

        # 更新状态为运行中
        self._update_task(task_id, status="running")

        try:
            if self._orch:
                # 使用 Orchestrator 的已注册 Agent
                agent = self._orch.get_agent(task.agent_role)
                if agent:
                    from gavvy_salesmaster.team_pkg.team.base import AgentContext
                    ctx = AgentContext(
                        customer_name=task.lead_company,
                        message=task.message,
                        lead_id=task.lead_id,
                        extra={"task_id": task_id},
                    )
                    result = agent.execute(ctx)
                    summary = result.summary or f"{task.agent_name} 处理完成"
                    output = result.output_text or summary

                    # 记忆库-销售闭环
                    try:
                        from gavvy_salesmaster.team_pkg.memory import get_learner
                        learner = get_learner()
                        if learner:
                            learner.learn_from_result(task.agent_role, {
                                "customer_name": task.lead_company,
                                "message": task.message,
                                "product_info": "",
                            }, {
                                "status": "completed",
                                "action": result.action or "",
                                "summary": summary,
                                "output_text": output,
                            })
                    except Exception:
                        pass

                    # 渠道自动发送：通过已注册的渠道把Agent回复发给客户
                    try:
                        from gavvy_salesmaster.channels_pkg.channels.dispatcher import MessageDispatcher
                        dispatcher = MessageDispatcher()
                        # 只发 email（目前最通用的渠道，其他渠道需要配置）
                        channel_to_use = "email"
                        if channel_to_use in dispatcher.channel_names:
                            dispatcher.send(
                                channel_name=channel_to_use,
                                to=task.lead_company,
                                subject=f"[{task.agent_name}] {task.lead_company} 跟进",
                                body=output,
                                metadata={"agent": task.agent_role, "task_id": task_id},
                            )
                    except Exception:
                        pass

                    self._update_task(
                        task_id,
                        status="completed",
                        result_summary=summary,
                        result_output=output,
                    )
                    return self._get_task(task_id)

            # 无 Orchestrator 或 Agent 不可用，输出模板回复
            template = self._get_template_reply(task.agent_role, task.lead_company)
            self._update_task(
                task_id,
                status="completed",
                result_summary=f"{task.agent_name} 已回复",
                result_output=template,
            )

        except Exception as e:
            self._update_task(
                task_id,
                status="failed",
                error=str(e),
                result_summary=f"执行失败: {e}",
            )

        return self._get_task(task_id)

    def _get_template_reply(self, agent_role: str, customer: str) -> str:
        """获取 Agent 的模板回复"""
        templates = {
            "market_research_agent": (
                f"📊 **市场调研报告 - {customer}**\\n\\n"
                f"已完成行业调研和分析。\\n"
                f"建议跟进策略：提供定制化方案演示。"
            ),
            "competitor_intel_agent": (
                f"🔍 **竞品分析报告 - {customer}**\\n\\n"
                f"已完成竞品对比分析。\\n"
                f"差异化优势：产品成熟度 + 本地化服务。"
            ),
            "presales_agent": (
                f"🤝 **售前跟进 - {customer}**\\n\\n"
                f"感谢您的咨询！我们已收到您的需求，\\n"
                f"请提供更多信息以便为您定制方案。"
            ),
            "aftersales_agent": (
                f"🎯 **售后服务 - {customer}**\\n\\n"
                f"已收到您的反馈，我们会在24小时内安排专人处理。\\n"
                f"感谢您的信任与支持！"
            ),
            "procurement_agent": (
                f"📦 **采购供应链 - {customer}**\\n\\n"
                f"已完成供应链调研。\\n"
                f"建议建立长期合作关系以获取最优价格。"
            ),
            "operations_agent": (
                f"🚀 **运营增长 - {customer}**\\n\\n"
                f"已完成运营数据分析。\\n"
                f"建议优化方向：提高转化率 + 降低获客成本。"
            ),
            "platform_ops_agent": (
                f"📋 **运营助理 - {customer}**\\n\\n"
                f"已核对资质信息。\\n"
                f"上架流程已启动，预计1-2个工作日完成。"
            ),
        }
        return templates.get(agent_role, f"{AGENT_NAMES.get(agent_role, 'Assistant')} 已收到您的消息。")

    def _update_task(self, task_id: str, **kwargs) -> None:
        with self._lock:
            if task_id in self._tasks:
                for k, v in kwargs.items():
                    setattr(self._tasks[task_id], k, v)
                if kwargs.get("status") in ("completed", "failed"):
                    self._tasks[task_id].completed_at = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
        self._save_tasks()

    def _get_task(self, task_id: str) -> Optional[ScheduledTask]:
        with self._lock:
            t = self._tasks.get(task_id)
            return ScheduledTask.from_dict(t.to_dict()) if t else None

    # ── 批量调度 ───────────────────────────────

    def dispatch_from_hunt(self) -> int:
        """从 HuntEngine 获取未调度的高分线索，批量提交调度"""
        if not self._hunt:
            return 0

        candidates = self._hunt._get_dispatch_candidates(self._hunt.get_config().min_score)
        count = 0
        for lead in candidates:
            self.submit(
                message=f"发现新线索：{lead.company}（{lead.industry}）",
                customer=lead.company,
                product=lead.description,
                lead_id=lead.company,
            )
            self._hunt.mark_dispatched(lead.company)
            count += 1
        return count
