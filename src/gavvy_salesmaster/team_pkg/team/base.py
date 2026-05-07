"""gavvy_salesmaster.team_pkg.team.base — AI Agent 基类体系（社区版实现）

提供 Agent 基类、上下文、结果、私有输入、四维内核等核心类型。
企业版能力通过服务端 API（SentriKit_API_KEY）提供。

社区版限制（MIT）：
- Agent 执行限 1 个 Lead（演示模式）
- Agent 输出仅使用模板降级，不调用真实 LLM
- 升级提示嵌入输出中
"""

from __future__ import annotations

import json
import os
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# ── 社区版门控 ──────────────────────────────────

_SALES_EDITION: Optional[str] = None


def _get_edition() -> str:
    """获取当前版本：community / enterprise"""
    global _SALES_EDITION
    if _SALES_EDITION is not None:
        return _SALES_EDITION
    try:
        from .. import SALES_EDITION as _SE
        _SALES_EDITION = _SE
    except ImportError:
        _SALES_EDITION = "community"
    return _SALES_EDITION


def is_enterprise() -> bool:
    return _get_edition() == "enterprise"


COMMUNITY_LEAD_LIMIT = 1
COMMUNITY_UPGRADE_HINT = (
    "\n\n---\n💡 **需要企业版解锁完整AI Agent能力？**\n"
    "当前为 MIT 社区版演示模式。企业版提供：\n"
    "- ✅ AI 驱动的智能对话（DeepSeek/Ollama 集成）\n"
    "- ✅ 无限 Lead 管理与多 Agent 编排\n"
    "- ✅ 跨 Agent 数据总线与自动销售闭环\n"
    "- ✅ 记忆库-销售学习进化\n"
    "申请：https://SentriKit.ai/pricing"
)


# ── 基础类型 ─────────────────────────────────────


class AgentRole(Enum):
    """Agent 角色枚举"""
    MARKET_RESEARCH = "market_research_agent"
    COMPETITOR_INTEL = "competitor_intel_agent"
    PRESALES = "presales_agent"
    AFTERSALES = "aftersales_agent"
    PROCUREMENT = "procurement_agent"
    OPERATIONS = "operations_agent"
    PLATFORM_OPS = "platform_ops_agent"

    @classmethod
    def from_string(cls, name: str) -> Optional["AgentRole"]:
        for r in cls:
            if r.value == name:
                return r
        return None


AGENT_LABELS: Dict[AgentRole, str] = {
    AgentRole.MARKET_RESEARCH: "market-research",
    AgentRole.COMPETITOR_INTEL: "competitor-intel",
    AgentRole.PRESALES: "presales",
    AgentRole.AFTERSALES: "aftersales",
    AgentRole.PROCUREMENT: "procurement",
    AgentRole.OPERATIONS: "operations",
    AgentRole.PLATFORM_OPS: "platform-ops",
}

AGENT_DESCRIPTIONS: Dict[AgentRole, str] = {
    AgentRole.MARKET_RESEARCH: "🎯 市场调研官 — 搜索潜在客户、行业分析、线索评分",
    AgentRole.COMPETITOR_INTEL: "🔍 竞品分析官 — 竞品对标、差异化策略、市场定位",
    AgentRole.PRESALES: "💬 售前谈判官 — 客户接触、价值传递、异议处理、促成成交",
    AgentRole.AFTERSALES: "🤝 售后维系官 — 售后支持、客户续约、推荐裂变",
    AgentRole.PROCUREMENT: "💰 采购供应链官 — 成本分析、供应商匹配、利润核算",
    AgentRole.OPERATIONS: "📊 运营增长官 — 客户分层、话术迭代、渠道优化",
    AgentRole.PLATFORM_OPS: "📋 运营助理 — 商品上架审核、平台规则检查、违禁词检测",
}


# ── 数据类 ───────────────────────────────────────


@dataclass
class PrivateInput:
    """私有输入 — 携带敏感数据（定价、成本、违禁词等）"""
    pricing: str = ""              # 定价信息
    cost: str = ""                 # 成本信息
    forbidden_phrases: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "PrivateInput":
        return PrivateInput(**{k: v for k, v in data.items() if k in
                               ["pricing", "cost", "forbidden_phrases", "extra"]})


@dataclass
class AgentContext:
    """Agent 执行上下文"""
    product_info: str = ""              # 产品信息描述
    customer_name: str = ""             # 客户名称
    customer_id: str = ""               # 客户 ID
    message: str = ""                   # 用户输入消息
    stage: str = "discovery"            # 当前销售阶段
    private: PrivateInput = field(default_factory=PrivateInput)
    extra: Dict[str, Any] = field(default_factory=dict)  # 跨 Agent 数据总线
    lead_id: str = ""                   # 关联的 Lead ID

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["private"] = self.private.to_dict()
        return d

    @staticmethod
    def from_dict(data: Dict) -> "AgentContext":
        priv = PrivateInput.from_dict(data.get("private", {}))
        return AgentContext(
            product_info=data.get("product_info", ""),
            customer_name=data.get("customer_name", ""),
            customer_id=data.get("customer_id", ""),
            message=data.get("message", ""),
            stage=data.get("stage", "discovery"),
            private=priv,
            extra=data.get("extra", {}),
            lead_id=data.get("lead_id", ""),
        )


@dataclass
class AgentResult:
    """Agent 执行结果"""
    status: str = "success"              # success / blocked / failed
    action: str = ""                     # 执行的动作名称
    summary: str = ""                    # 动作摘要（用于下游Agent数据总线）
    thinking: str = ""                   # 推理过程
    output_text: str = ""                # 对外输出文本
    internal_note: str = ""              # 内部备注（日志、诊断用）
    output: List[Dict] = field(default_factory=list)  # 结构化输出
    agent_cn: str = ""                   # Agent 中文名（前端展示用）
    agent_en: str = ""                   # Agent 英文名

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "AgentResult":
        return AgentResult(**{k: v for k, v in data.items()
                              if k in AgentResult.__dataclass_fields__})


@dataclass
class Kernels:
    """四维内核 — 每个 Agent 携带的心理/战略/分析/谈判维度"""
    psychologist: str = ""   # 心理博弈能力描述
    strategist: str = ""     # 战略规划能力描述
    analyst: str = ""        # 数据分析能力描述
    negotiator: str = ""     # 谈判博弈能力描述


# ── Agent 基类 ────────────────────────────────────


class BaseAgent(ABC):
    """所有 Agent 的抽象基类"""

    @property
    @abstractmethod
    def role_en(self) -> str:
        """Agent 英文标识（如 'market_research_agent'）"""
        ...

    @property
    @abstractmethod
    def role_cn(self) -> str:
        """Agent 中文名称（如 '市场调研官'）"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Agent 职责描述"""
        ...

    @property
    def kernels(self) -> Kernels:
        """四维内核（默认空实现，子类可覆盖）"""
        return Kernels()

    @abstractmethod
    def execute(self, context: AgentContext) -> AgentResult:
        """执行 Agent 任务

        Args:
            context: Agent 执行上下文（含产品信息、客户、跨 Agent 数据等）

        Returns:
            AgentResult: 执行结果
        """
        ...

    def _make_result(self, status: str = "success", action: str = "",
                     summary: str = "", thinking: str = "",
                     output_text: str = "", internal_note: str = "",
                     output: Optional[List[Dict]] = None) -> AgentResult:
        """构建 AgentResult 的辅助方法"""
        return AgentResult(
            status=status, action=action, summary=summary,
            thinking=thinking, output_text=output_text,
            internal_note=internal_note,
            output=output or [],
            agent_cn=self.role_cn,
            agent_en=self.role_en,
        )


# ── 线索评分器 ───────────────────────────────────


# ── 会话记忆 ─────────────────────────────────────


_SESSION_MEMORY: Dict[str, List[Dict]] = {}


def get_session_memory() -> Dict[str, Any]:
    """获取会话记忆（简单内存存储）"""
    return _SESSION_MEMORY


def set_session_memory(session_id: str, data: Dict) -> None:
    """设置会话记忆"""
    _SESSION_MEMORY[session_id] = data


def clear_session_memory(session_id: str = "") -> None:
    """清除会话记忆"""
    if session_id:
        _SESSION_MEMORY.pop(session_id, None)
    else:
        _SESSION_MEMORY.clear()


# ── Insight 引擎（社区简化版） ─────────────────


@dataclass
class InsightSummary:
    """洞察总结"""
    total_episodes: int = 0
    insights: List[str] = field(default_factory=list)
    top_insight: str = ""
    performance_trend: str = "stable"


class InsightEngine:
    """洞察引擎 — 从执行记录中提取可学习的洞察"""

    def analyze(self, history: List[Dict]) -> InsightSummary:
        if not history:
            return InsightSummary()
        # 简化的洞察提取：统计成功的动作
        successful = [h for h in history if h.get("status") == "success"]
        return InsightSummary(
            total_episodes=len(history),
            insights=[f"成功执行 {len(successful)}/{len(history)} 次"
                     ] if successful else ["暂无成功案例"],
            top_insight=f"成功率 {len(successful)/len(history):.0%}" if history else "无数据",
            performance_trend="improving" if len(successful) > len(history) * 0.7 else "stable",
        )


# ── Safety 模块（社区简化版） ────────────────────


class SafetyMode(Enum):
    CONSERVATIVE = "conservative"
    OPEN = "open"
    CUSTOM = "custom"


@dataclass
class SafetyLog:
    action: str = ""
    reason: str = ""
    passed: bool = False
    timestamp: str = ""


class SafetyGuard:
    """安全守卫 — 检查 Agent 动作是否安全"""

    # 涉及成交/报价的敏感动作关键词
    SENSITIVE_ACTIONS = {"deal", "quote", "contract", "payment", "price"}

    def __init__(self, mode: SafetyMode = SafetyMode.CONSERVATIVE):
        self.mode = mode
        self.logs: List[SafetyLog] = []

    def check_action(self, action: str, output_text: str = "",
                     price_ceiling: float = 50000,
                     discount_floor: float = 0.7) -> bool:
        """检查动作是否安全"""
        action_lower = action.lower()

        # 检测敏感动作
        is_sensitive = any(kw in action_lower for kw in self.SENSITIVE_ACTIONS)

        if self.mode == SafetyMode.CONSERVATIVE:
            passed = not is_sensitive  # 保守模式：阻止所有敏感动作
        elif self.mode == SafetyMode.OPEN:
            passed = True  # 开放模式：全部放行
        else:
            # 自定义模式：根据阈值判断
            passed = True
            if is_sensitive:
                amount = self._extract_amount(output_text)
                if amount > price_ceiling:
                    passed = False

        self.logs.append(SafetyLog(
            action=action,
            reason=f"mode={self.mode.value}, sensitive={is_sensitive}, passed={passed}",
            passed=passed,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ))
        return passed

    @staticmethod
    def _extract_amount(text: str) -> float:
        """从文本中提取金额"""
        import re
        amounts = re.findall(r'[¥￥](\d+(?:\.\d+)?)', text)
        if not amounts:
            amounts = re.findall(r'(\d+(?:\.\d+)?)\s*万?元', text)
        if amounts:
            return max(float(a) for a in amounts)
        return 0.0


# ── Quickstart 引导 ──────────────────────────────


QUICKSTART_INDUSTRIES = {
    "电商": {
        "pricing": {"base": 299, "enterprise": 999},
        "scripts": ["您好，我们是做电商解决方案的..."],
        "faq": [{"q": "价格多少", "a": "基础版299/月"}],
        "competitors": ["有赞", "微盟"],
    },
    "SaaS企业服务": {
        "pricing": {"base": 499, "enterprise": 1999},
        "scripts": ["您好，了解到贵公司在使用XX系统，我们..."],
        "faq": [{"q": "支持私有部署吗", "a": "支持"}],
        "competitors": ["钉钉", "飞书"],
    },
    "AI/科技": {
        "pricing": {"base": 999, "enterprise": 4999},
        "scripts": ["我们在AI Agent领域有成熟方案..."],
        "faq": [{"q": "API接入复杂吗", "a": "3行代码接入"}],
        "competitors": ["OpenAI", "LangChain"],
    },
}


class QuickstartGuide:
    """快速启动引导"""

    @staticmethod
    def get_industries() -> Dict:
        return QUICKSTART_INDUSTRIES

    @staticmethod
    def apply_template(industry: str, product_name: str) -> Dict:
        tmpl = QUICKSTART_INDUSTRIES.get(industry, {})
        return {
            "product_name": product_name,
            "industry": industry,
            "pricing": tmpl.get("pricing", {}),
            "competitors": tmpl.get("competitors", []),
        }

    @staticmethod
    def generate_demo_data() -> List[Dict]:
        return [
            {"id": "demo_1", "name": "演示客户A", "intent": "了解产品", "stage": "contact",
             "last_msg": "请介绍下方案", "last_time": "2026-05-03 10:00"},
            {"id": "demo_2", "name": "演示客户B", "intent": "咨询价格", "stage": "negotiation",
             "last_msg": "价格能再优惠吗", "last_time": "2026-05-03 10:30"},
        ]


# ── API 配置管理器 ──────────────────────────────


class APIConfigManager:
    """API 配置管理器 — 管理 LLM/渠道 等 API 密钥"""

    def __init__(self, config_path: str = ""):
        self._config: Dict[str, Dict] = {}

    def get(self, key: str) -> Optional[Dict]:
        return self._config.get(key)

    def set(self, key: str, value: Dict) -> None:
        self._config[key] = value

    def all(self) -> Dict[str, Dict]:
        return dict(self._config)


def update_llm_config(provider: str, api_key: str, **kwargs) -> bool:
    """更新 LLM 配置"""
    return True


def is_llm_ready() -> bool:
    """检查 LLM 是否已配置"""
    return False


def get_api_config() -> Dict:
    """获取 API 配置"""
    return {}


def build_sales_llm(provider: str = "deepseek", **kwargs) -> Any:
    """构建销售 LLM 实例"""
    from ..llm import get_llm
    return get_llm(provider=provider, **kwargs)
