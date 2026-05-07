"""gavvy_salesmaster.team_pkg.team.coordinator — SalesOrchestrator 编排器（社区版实现）

多 Agent 任务调度、状态管理、安全门控、跨 Agent 数据总线。
企业版能力通过服务端 API（SentriKit_API_KEY）提供。
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple

from .base import (
    AgentContext, AgentResult, PrivateInput, SafetyGuard, SafetyMode,
    is_enterprise, COMMUNITY_LEAD_LIMIT, COMMUNITY_UPGRADE_HINT,
)


# ── 销售阶段定义 ─────────────────────────────────


STAGES = [
    "discovery",     # 初步发现
    "research",      # 调研分析
    "contact",       # 接触沟通
    "negotiation",   # 谈判议价
    "closing",       # 成交
    "after_sales",   # 售后
    "listing",       # 上架运营
]

STAGE_LABELS = {
    "discovery": "初步发现",
    "research": "调研分析",
    "contact": "接触沟通",
    "negotiation": "谈判议价",
    "closing": "成交",
    "after_sales": "售后",
    "listing": "上架运营",
}

# 阶段 → Agent 映射
STAGE_AGENTS = {
    "discovery": "market_research_agent",
    "research": "competitor_intel_agent",
    "contact": "presales_agent",
    "negotiation": "presales_agent",
    "closing": "presales_agent",
    "after_sales": "aftersales_agent",
    "listing": "platform_ops_agent",
}

# 超时定义（秒）
STAGE_TIMEOUTS = {
    "discovery": 86400 * 3,     # 3 天
    "research": 86400 * 2,       # 2 天
    "contact": 86400 * 1,        # 1 天
    "negotiation": 43200,        # 12 小时
    "closing": 21600,            # 6 小时
    "after_sales": 86400 * 7,    # 7 天
    "listing": 86400 * 1,        # 1 天
}


# ── Lead 数据结构 ────────────────────────────────


@dataclass
class LeadInfo:
    """Orchestrator 内部的 Lead 数据结构"""
    id: str = ""
    name: str = ""
    stage: str = "discovery"
    created_at: str = ""
    updated_at: str = ""
    history: List[Dict] = field(default_factory=list)
    product_info: str = ""
    context_extra: Dict[str, Any] = field(default_factory=dict)
    private_pricing: str = ""
    private_cost: str = ""
    active: bool = True

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict) -> "LeadInfo":
        return LeadInfo(**{k: v for k, v in d.items()
                           if k in LeadInfo.__dataclass_fields__})


# ── 流程开关（Flow Toggles） ────────────────────


DEFAULT_FLOW_TOGGLES = {
    "auto_pipeline": True,
    "auto_evolve": True,
    "auto_follow_up": True,
    "safety_gate": True,
    "chat_sales": True,
}


class FlowToggleManager:
    """流程开关管理器"""

    def __init__(self):
        self._toggles: Dict[str, bool] = dict(DEFAULT_FLOW_TOGGLES)
        self._lock = threading.Lock()

    def get_all(self) -> Dict[str, bool]:
        with self._lock:
            return dict(self._toggles)

    def is_enabled(self, name: str) -> bool:
        with self._lock:
            return self._toggles.get(name, False)

    def set(self, name: str, enabled: bool) -> bool:
        with self._lock:
            if name not in self._toggles:
                return False
            self._toggles[name] = enabled
            return True


# ══════════════════════════════════════════════════
# SalesOrchestrator
# ══════════════════════════════════════════════════


class SalesOrchestrator:
    """销售编排器 — 多 Agent 任务调度与状态管理"""

    STAGES = STAGES
    STAGE_LABELS = STAGE_LABELS
    STAGE_AGENTS = STAGE_AGENTS

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, storage_path: str = ""):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._leads: Dict[str, LeadInfo] = {}
        self._leads_lock = threading.Lock()
        self._safety = SafetyGuard()
        self._flow_toggles = FlowToggleManager()
        self._agent_registry: Dict[str, Any] = {}  # role_en -> BaseAgent instance
        self._storage_path = storage_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "orchestrator"
        )
        os.makedirs(self._storage_path, exist_ok=True)

    # ── 注册 Agent ─────────────────────────────

    def register_agent(self, agent: Any) -> None:
        """注册 Agent 到编排器"""
        self._agent_registry[agent.role_en] = agent

    def get_agent(self, role_en: str) -> Optional[Any]:
        return self._agent_registry.get(role_en)

    def get_registered_agents(self) -> Dict[str, Any]:
        return dict(self._agent_registry)

    # ── Lead 管理 ───────────────────────────────

    def add_lead(self, lead_id: str, info: Dict) -> str:
        """添加新的 Lead

        社区版限 {COMMUNITY_LEAD_LIMIT} 个 Lead（演示模式）。
        """
        if not is_enterprise():
            with self._leads_lock:
                if len(self._leads) >= COMMUNITY_LEAD_LIMIT:
                    raise RuntimeError(
                        f"社区版最多支持 {COMMUNITY_LEAD_LIMIT} 个 Lead（演示模式）。"
                        f"企业版无限制。{COMMUNITY_UPGRADE_HINT}"
                    )
        lid = lead_id or f"lead_{uuid.uuid4().hex[:8]}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._leads_lock:
            self._leads[lid] = LeadInfo(
                id=lid,
                name=info.get("name", ""),
                stage=info.get("stage", "discovery"),
                created_at=now,
                updated_at=now,
                product_info=info.get("product_info", ""),
                private_pricing=info.get("private", {}).get("pricing", ""),
                private_cost=info.get("private", {}).get("cost", ""),
                context_extra=info.get("extra", {}),
            )
        return lid

    def update_lead(self, lead_id: str, updates: Dict) -> bool:
        """更新 Lead 信息"""
        with self._leads_lock:
            if lead_id not in self._leads:
                return False
            lead = self._leads[lead_id]
            for k, v in updates.items():
                if hasattr(lead, k):
                    setattr(lead, k, v)
            lead.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return True

    def update_lead_stage(self, lead_id: str, stage: str) -> bool:
        """更新 Lead 阶段"""
        if stage not in STAGES:
            return False
        return self.update_lead(lead_id, {"stage": stage})

    def get_lead(self, lead_id: str) -> Optional[LeadInfo]:
        with self._leads_lock:
            lead = self._leads.get(lead_id)
            if lead:
                return LeadInfo.from_dict(lead.to_dict())  # 返回深拷贝
            return None

    def get_leads(self) -> Dict[str, LeadInfo]:
        with self._leads_lock:
            return {k: LeadInfo.from_dict(v.to_dict())
                    for k, v in self._leads.items()}

    def get_lead_count(self) -> int:
        with self._leads_lock:
            return len(self._leads)

    def remove_lead(self, lead_id: str) -> bool:
        with self._leads_lock:
            if lead_id not in self._leads:
                return False
            del self._leads[lead_id]
        return True

    # ── 汇总统计 ───────────────────────────────

    def get_summary(self) -> Dict:
        """获取编排器汇总"""
        leads = self.get_leads()
        stage_counts = {s: 0 for s in STAGES}
        total = len(leads)
        for lead in leads.values():
            stage_counts[lead.stage] = stage_counts.get(lead.stage, 0) + 1
        return {
            "total_leads": total,
            "stage_counts": stage_counts,
            "agent_count": len(self._agent_registry),
            "safety_mode": self._safety.mode.value,
            "active_agents": [k for k in self._agent_registry],
        }

    def get_agents_summary(self) -> Dict:
        """获取所有已注册 Agent 的摘要信息"""
        agents = {}
        for en, agent in self._agent_registry.items():
            agents[en] = {
                "role_en": agent.role_en,
                "role_cn": agent.role_cn,
                "description": agent.description,
            }
        return agents

    # ── 任务调度 ───────────────────────────────

    def assign_task(self, lead_id: str, stage: Optional[str] = None) -> AgentResult:
        """为 Lead 分配当前阶段对应的 Agent 任务

        Args:
            lead_id: Lead 唯一标识
            stage: 指定阶段（默认为 Lead 当前阶段）

        Returns:
            AgentResult: Agent 执行结果
        """
        lead = self.get_lead(lead_id)
        if not lead:
            return AgentResult(status="failed", action="assign_task",
                               summary=f"Lead {lead_id} 不存在")

        target_stage = stage or lead.stage
        agent_key = STAGE_AGENTS.get(target_stage)
        if not agent_key:
            return AgentResult(status="failed", action="assign_task",
                               summary=f"阶段 {target_stage} 无对应 Agent")

        agent = self._agent_registry.get(agent_key)
        if not agent:
            return AgentResult(status="failed", action="assign_task",
                               summary=f"Agent {agent_key} 未注册",
                               agent_cn=agent_key, agent_en=agent_key)

        # 构建上下文
        context = AgentContext(
            product_info=lead.product_info,
            customer_name=lead.name,
            customer_id=lead.id,
            stage=target_stage,
            private=PrivateInput(
                pricing=lead.private_pricing,
                cost=lead.private_cost,
            ),
            extra=dict(lead.context_extra),
            lead_id=lead_id,
        )

        # 注入跨 Agent 数据总线
        if lead.history:
            prev_outputs = []
            seen_agents = set()
            for h in lead.history:
                ak = h.get("agent", "")
                if ak and ak not in seen_agents:
                    seen_agents.add(ak)
                    prev_outputs.append({
                        "agent": ak,
                        "action": h.get("action", ""),
                        "summary": h.get("summary", ""),
                        "status": h.get("status", ""),
                    })
            if prev_outputs:
                context.extra["agent_history"] = prev_outputs

        # 安全门控
        if self._flow_toggles.is_enabled("safety_gate"):
            if not self._safety.check_action("assign_task", target_stage):
                return AgentResult(status="blocked", action="assign_task",
                                   summary="安全门控阻止了任务分配")

        # 执行
        result = agent.execute(context)

        # 记录执行历史
        history_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "agent": agent_key,
            "action": result.action,
            "summary": result.summary,
            "status": result.status,
            "stage": target_stage,
        }
        with self._leads_lock:
            if lead_id in self._leads:
                self._leads[lead_id].history.append(history_entry)
                self._leads[lead_id].updated_at = history_entry["timestamp"]

        # 记忆库-销售闭环（可选，如果 memory 模块可用）
        try:
            self._auto_learn(agent_key, context, result)
        except Exception:
            pass

        return result

    def _auto_learn(self, agent_name: str, context: AgentContext,
                    result: AgentResult) -> None:
        """自动从销售结果中学习"""
        try:
            from ..memory import get_learner
            learner = get_learner()
            if learner is None:
                return
            learner.learn_from_result(agent_name, {
                "product_info": context.product_info,
                "customer_name": context.customer_name,
                "message": context.message,
            }, {
                "status": result.status,
                "action": result.action,
                "summary": result.summary,
                "output_text": result.output_text,
            })
        except Exception:
            pass

    # ── 安全模式 ───────────────────────────────

    def get_safety_mode(self) -> Dict:
        return {
            "mode": self._safety.mode.value,
            "logs": [asdict(l) for l in self._safety.logs[-20:]],
        }

    def set_safety_mode(self, mode: str) -> bool:
        try:
            self._safety.mode = SafetyMode(mode)
            return True
        except ValueError:
            return False

    def get_safety_logs(self) -> List[Dict]:
        return [asdict(l) for l in self._safety.logs]

    # ── 流程开关 ───────────────────────────────

    def get_flow_toggles(self) -> Dict[str, bool]:
        return self._flow_toggles.get_all()

    def set_flow_toggle(self, name: str, enabled: bool) -> bool:
        return self._flow_toggles.set(name, enabled)

    def is_flow_enabled(self, name: str) -> bool:
        return self._flow_toggles.is_enabled(name)

    # ── 持久化 ─────────────────────────────────

    def persist(self) -> bool:
        """保存编排器状态到磁盘"""
        try:
            path = os.path.join(self._storage_path, "leads.json")
            with self._leads_lock:
                data = {k: v.to_dict() for k, v in self._leads.items()}
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            return False

    def restore(self) -> bool:
        """从磁盘恢复编排器状态"""
        try:
            path = os.path.join(self._storage_path, "leads.json")
            if not os.path.exists(path):
                return False
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            with self._leads_lock:
                self._leads = {k: LeadInfo.from_dict(v) for k, v in data.items()}
            return True
        except Exception as e:
            return False


# ══════════════════════════════════════════════════
# PipelineTrigger
# ══════════════════════════════════════════════════


class PipelineTrigger:
    """Pipeline 自动触发引擎 — 超时检测、阶段推进"""

    STAGE_AGENTS = STAGE_AGENTS
    TIMEOUTS = STAGE_TIMEOUTS

    @staticmethod
    def advance_stage(orch: SalesOrchestrator, lead_id: str) -> Dict:
        """手动推进客户到下一阶段

        Returns:
            Dict 包含推进结果和分配的任务信息
        """
        lead = orch.get_lead(lead_id)
        if not lead:
            return {"success": False, "error": f"Lead {lead_id} 不存在"}

        current_idx = STAGES.index(lead.stage) if lead.stage in STAGES else -1
        if current_idx >= len(STAGES) - 1:
            return {
                "success": False,
                "error": f"Lead {lead.name} 已在最终阶段 ({STAGE_LABELS.get(lead.stage, lead.stage)})",
                "lead_id": lead_id,
                "current_stage": lead.stage,
            }

        next_stage = STAGES[current_idx + 1]
        orch.update_lead_stage(lead_id, next_stage)
        result = orch.assign_task(lead_id, stage=next_stage)

        # 推进通知：通过渠道发送阶段变更通知
        try:
            from gavvy_salesmaster.channels_pkg.channels.dispatcher import MessageDispatcher
            dispatcher = MessageDispatcher()
            stage_label = STAGE_LABELS.get(next_stage, next_stage)
            if "email" in dispatcher.channel_names:
                dispatcher.send(
                    channel_name="email",
                    to=lead.name,
                    subject=f"[销售Pipeline] {lead.name} 已进入 {stage_label} 阶段",
                    body=(
                        f"尊敬的 {lead.name}，\n\n"
                        f"您的商机已进入「{stage_label}」阶段。\n"
                        f"我们将安排 {STAGE_LABELS.get(next_stage, '')} 阶段专属顾问跟进。\n\n"
                        f"如有任何问题，请随时回复此邮件。\n"
                        f"-- Gavvy 销售引擎"
                    ),
                    metadata={"action": "stage_advance", "lead_id": lead_id, "stage": next_stage},
                )
        except Exception:
            pass

        return {
            "success": result.status == "success",
            "lead_id": lead_id,
            "lead_name": lead.name,
            "from_stage": lead.stage,
            "to_stage": next_stage,
            "agent_result": result.to_dict() if result else None,
        }

    @staticmethod
    def check_timeouts(orch: SalesOrchestrator) -> List[Dict]:
        """扫描所有超时的 Lead

        Returns:
            List[Dict] 超时 Lead 列表，每项含 lead_id, name, stage, elapsed_hours
        """
        now = datetime.now()
        alerts = []
        leads = orch.get_leads()

        for lead in leads.values():
            timeout = STAGE_TIMEOUTS.get(lead.stage)
            if not timeout:
                continue
            try:
                updated = datetime.strptime(lead.updated_at, "%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                continue
            elapsed = (now - updated).total_seconds()
            if elapsed > timeout:
                alerts.append({
                    "lead_id": lead.id,
                    "name": lead.name,
                    "stage": lead.stage,
                    "stage_label": STAGE_LABELS.get(lead.stage, lead.stage),
                    "elapsed_hours": round(elapsed / 3600, 1),
                    "timeout_hours": round(timeout / 3600, 1),
                })

        return sorted(alerts, key=lambda x: x["elapsed_hours"], reverse=True)

    @staticmethod
    def auto_follow_up(orch: SalesOrchestrator,
                       external_save_func: Optional[Callable] = None) -> Dict:
        """全量管道自动跟进：超时检测 + 自动推进

        Returns:
            Dict 包含超时检查和推进结果
        """
        timeouts = PipelineTrigger.check_timeouts(orch)
        advanced = []
        errors = []

        for t in timeouts:
            # discovery 阶段有历史的，自动推进
            lead = orch.get_lead(t["lead_id"])
            if lead and t["stage"] == "discovery" and lead.history:
                r = PipelineTrigger.advance_stage(orch, t["lead_id"])
                if r.get("success"):
                    advanced.append(r)
                else:
                    errors.append({"lead_id": t["lead_id"], "error": r.get("error")})

        # 持久化
        if external_save_func:
            try:
                external_save_func()
            except Exception:
                pass

        return {
            "checked": len(list(orch.get_leads().keys())),
            "timeouts_count": len(timeouts),
            "timeout_details": timeouts,
            "auto_advanced": len(advanced),
            "advanced_details": advanced,
            "errors": errors,
        }

    @staticmethod
    def run_scheduled_checks(orch: SalesOrchestrator,
                             interval_seconds: int = 300,
                             external_save_func: Optional[Callable] = None,
                             run_once: bool = False) -> None:
        """定时自动跟进循环

        后台扫描超时 Lead 并自动推进。300s=5min 间隔。
        在独立线程中运行，不阻塞主流程。

        Args:
            orch: SalesOrchestrator 实例
            interval_seconds: 检查间隔（秒）
            external_save_func: 外部持久化回调
            run_once: 仅执行一次（用于测试）
        """
        import time

        def _loop():
            while True:
                try:
                    PipelineTrigger.auto_follow_up(orch, external_save_func)
                except Exception:
                    pass
                if run_once:
                    break
                time.sleep(interval_seconds)

        thread = threading.Thread(target=_loop, daemon=True)
        thread.start()
