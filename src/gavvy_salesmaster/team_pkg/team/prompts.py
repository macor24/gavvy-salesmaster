"""gavvy_salesmaster.team_pkg.team.prompts — Agent 提示词摘要（社区版模板降级用）

社区版：仅保留模板降级摘要和辅助函数
企业版：完整 prompt 在服务端，通过 EnterpriseAPIClient.chat_agent() 调用

完整 prompt 定义：
    MARKET_RESEARCH_SYSTEM, MARKET_RESEARCH_USER     — 市场调研官（~200行）
    COMPETITOR_SYSTEM, COMPETITOR_USER                — 竞品分析官（~140行）
    PRESALES_SYSTEM, PRESALES_USER                    — 售前谈判官（~150行）
    AFTERSALES_SYSTEM, AFTERSALES_USER                 — 售后维系官（~80行）
    PROCUREMENT_SYSTEM, PROCUREMENT_USER               — 采购供应链官（~60行）
    OPERATIONS_SYSTEM, OPERATIONS_USER                — 运营增长官（~50行）
    PLATFORM_OPS_SYSTEM, PLATFORM_OPS_USER             — 平台运营助理（~40行）
只有企业版 API 有访问权限。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ── 模板降级用摘要（社区版 Agent 模板输出时引用） ────
# 企业版完整 prompt 在服务端 api.sentrikit.com/v1/agent/chat

AGENT_SUMMARIES = {
    "market_research_agent": "市场调研官：分析客户行业趋势、技术栈成熟度、安全需求、商机评估",
    "competitor_intel_agent": "竞品分析官：竞品对标、差异化策略、市场定位、威胁评估",
    "presales_agent": "售前谈判官：客户需求挖掘、价值传递、异议处理、成交策略",
    "aftersales_agent": "售后维系官：客户回访、满意度调查、续约推荐、增购机会",
    "procurement_agent": "采购供应链官：供应商评估、成本控制、采购优化、合规检查",
    "operations_agent": "运营增长官：数据分析、市场策略、渠道优化、增长实验",
    "platform_ops_agent": "平台运营助理：日常运维、数据同步、合规审查、监控告警",
}


# ── 辅助函数 ────────────────────────────────────


def build_agent_history_section(history: List[Dict]) -> str:
    """构建跨 Agent 历史数据上下文（社区版企业版共用）"""
    if not history:
        return ""
    lines = ["\n前期调研数据参考："]
    for h in history:
        lines.append(f"- [{h.get('agent', '?')}] {h.get('summary', '')}")
    return "\n".join(lines)


__all__ = [
    "AGENT_SUMMARIES",
    "build_agent_history_section",
]
