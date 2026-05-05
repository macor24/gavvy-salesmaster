"""tianlong_salesmaster.team_pkg.team.scorer — 线索评分引擎

社区版：基于规则的基础评分
企业版：调用服务端 LLM 智能评分（需 TIANLONG_API_KEY）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from tianlong_salesmaster.core.enterprise_client import EnterpriseAPIClient, EnterpriseConfig


@dataclass
class LeadScore:
    """线索评分"""
    score: float = 0.0
    confidence: float = 0.0
    factors: Dict[str, float] = field(default_factory=dict)
    summary: str = ""
    hint: str = ""


class LeadScorer:
    """线索评分器

    社区版：基于行业和描述的规则评分
    企业版：调用服务端 LLM 智能评分
    """

    def __init__(self, config: Optional[EnterpriseConfig] = None):
        self._client = EnterpriseAPIClient(config)

    def score(self, lead_info: Dict) -> LeadScore:
        """对线索进行评分"""
        if self._client.config.is_enterprise:
            result = self._client.score_lead(lead_info)
            return LeadScore(
                score=result.get("score", 0),
                confidence=result.get("confidence", 0),
                factors=result.get("factors", {}),
                summary=result.get("summary", ""),
                hint=result.get("hint", ""),
            )

        return self._local_score(lead_info)

    @staticmethod
    def _local_score(lead_info: Dict) -> LeadScore:
        """本地规则评分"""
        score = 0.0
        factors = {}
        industry = lead_info.get("industry", "")
        description = lead_info.get("description", "")
        source = lead_info.get("source", "manual")

        high_value = ["AI Agent", "LLM", "大模型", "金融科技", "医疗AI",
                       "FinTech", "智能驾驶", "机器人", "人工智能"]
        medium_value = ["电商", "SaaS", "企业服务", "教育", "制造"]
        for hv in high_value:
            if hv in industry:
                factors["industry_match"] = 0.3
                score += 0.3
                break
        for mv in medium_value:
            if mv in industry:
                score += 0.15
                factors.setdefault("industry_match", 0.15)
                break

        if len(description) > 100:
            factors["description_detail"] = 0.2
            score += 0.2
        elif len(description) > 50:
            factors["description_detail"] = 0.1
            score += 0.1

        source_scores = {"web_search": 0.15, "manual": 0.1, "preset": 0.05}
        factors["source"] = source_scores.get(source, 0.05)
        score += factors["source"]
        score = min(score, 1.0)

        return LeadScore(
            score=score,
            confidence=0.6 + score * 0.3,
            factors=factors,
            summary=f"行业匹配度{'高' if score > 0.5 else '中' if score > 0.2 else '低'}，综合评分 {score:.1%}（模板）",
        )


__all__ = ["LeadScorer", "LeadScore"]
