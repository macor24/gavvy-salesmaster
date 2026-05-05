"""SentriKit_salesmaster.team_pkg.team.insight — 销售洞察引擎

社区版：本地模板输出
企业版：调用服务端 LLM API（需 SentriKit_API_KEY）
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from SentriKit_salesmaster.core.enterprise_client import EnterpriseAPIClient, EnterpriseConfig


class InsightEngine:
    """销售洞察引擎"""

    def __init__(self, config: Optional[EnterpriseConfig] = None):
        self._client = EnterpriseAPIClient(config)

    def analyze(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """市场洞察分析"""
        return self._client.analyze_market(lead_data)

    def analyze_performance(self, history: List[Dict]) -> Dict[str, Any]:
        """绩效洞察分析"""
        return self._client.analyze_performance(history)


class InsightSummary:
    """洞察摘要"""
    def __init__(self, data: Dict[str, Any]):
        self.total_episodes = data.get("total_episodes", 0)
        self.insights = data.get("insights", [])
        self.top_insight = data.get("top_insight", "")
        self.performance_trend = data.get("performance_trend", "stable")
        self.mode = data.get("mode", "template")
        self.hint = data.get("hint", "")


__all__ = ["InsightEngine", "InsightSummary"]
