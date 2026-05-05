"""SentriKit_salesmaster.team_pkg.team — AI 销售智能体团队

包含：
- Agent 基类和核心类型（base.py）
- SalesOrchestrator 编排器和 PipelineTrigger（coordinator.py）
- 3个核心 Agent 实现（agents.py）
- 企业版 API 客户端代理（insight/safety/scorer/session 等）

企业版能力通过服务端 API 提供，需设置 SentriKit_API_KEY 环境变量。
社区版使用本地模板输出，离线可用。
"""

from __future__ import annotations

from .base import (
    BaseAgent, AgentContext, AgentResult, PrivateInput, Kernels,
    AgentRole, AGENT_LABELS, AGENT_DESCRIPTIONS,
    is_enterprise, COMMUNITY_LEAD_LIMIT, COMMUNITY_UPGRADE_HINT,
)
from .coordinator import (
    SalesOrchestrator, PipelineTrigger,
    STAGES, STAGE_LABELS, STAGE_AGENTS, STAGE_TIMEOUTS,
)
from .insight import InsightEngine, InsightSummary
from .safety import SafetyGuard, SafetyMode, SafetyLog
from .scorer import LeadScorer, LeadScore
from .session import get_session_memory
from .quickstart import QuickstartGuide
from .api_config import APIConfigManager, update_llm_config, is_llm_ready, get_api_config, build_sales_llm

__all__ = [
    # Agent 基类
    "BaseAgent", "AgentContext", "AgentResult", "PrivateInput", "Kernels",
    "AgentRole", "AGENT_LABELS", "AGENT_DESCRIPTIONS",
    # 编排器
    "SalesOrchestrator", "PipelineTrigger",
    "STAGES", "STAGE_LABELS", "STAGE_AGENTS", "STAGE_TIMEOUTS",
    # 企业版 API 代理
    "InsightEngine", "InsightSummary",
    "SafetyGuard", "SafetyMode", "SafetyLog",
    "LeadScorer", "LeadScore",
    "get_session_memory",
    "QuickstartGuide",
    "APIConfigManager", "update_llm_config", "is_llm_ready", "get_api_config", "build_sales_llm",
    # 社区版门控
    "is_enterprise", "COMMUNITY_LEAD_LIMIT", "COMMUNITY_UPGRADE_HINT",
]
