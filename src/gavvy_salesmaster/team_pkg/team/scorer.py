"""gavvy_salesmaster.team_pkg.team.scorer — 线索评分引擎（统一评分入口）

企业版：调用服务端 LLM 智能评分（需 SentriKit_API_KEY）
社区版：委托给 crm_pkg.lead_gen.scoring.LeadScoringService 的详细因子模型

⚠️ 这是统一的评分入口。所有模块应通过此处评分，不走 crm_pkg 直接评分。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from gavvy_salesmaster.core.enterprise_client import EnterpriseAPIClient, EnterpriseConfig


@dataclass
class LeadScore:
    """线索评分（统一输出格式）"""
    score: float = 0.0          # 0-100
    level: str = "cold"         # hot/warm/cold/dead
    confidence: float = 0.0
    factors: Dict[str, float] = field(default_factory=dict)
    summary: str = ""
    hint: str = ""
    recommended_action: str = ""
    estimated_value: float = 0.0


class LeadScorer:
    """线索评分器（统一入口）

    企业版 → 服务端 LLM 智能评分
    社区版 → 委托 LeadScoringService（详细因子模型，8个维度）
    """

    def __init__(self, config: Optional[EnterpriseConfig] = None):
        self._client = EnterpriseAPIClient(config)
        self._local_service = None

    @property
    def _service(self):
        if self._local_service is None:
            from gavvy_salesmaster.crm_pkg.lead_gen.scoring import (
                LeadScoringService as _LSS,
                get_lead_scoring_service,
            )
            self._local_service = get_lead_scoring_service()
        return self._local_service

    def score(self, lead_info: Dict) -> LeadScore:
        """对线索进行评分"""
        if self._client.config.is_enterprise:
            return self._enterprise_score(lead_info)
        return self._community_score(lead_info)

    def score_batch(self, leads: List[Dict]) -> List[LeadScore]:
        """批量评分"""
        return [self.score(lead) for lead in leads]

    def _enterprise_score(self, lead_info: Dict) -> LeadScore:
        """企业版：LLM 智能评分（调服务端 API）"""
        result = self._client.score_lead_enterprise(lead_info)
        return LeadScore(
            score=result.get("score", 0),
            level=self._float_to_level(result.get("score", 0)),
            confidence=result.get("confidence", 0),
            factors=result.get("factors", {}),
            summary=result.get("summary", ""),
            hint=result.get("hint", ""),
            recommended_action=result.get("recommended_action", ""),
            estimated_value=result.get("estimated_value", 0),
        )

    def _community_score(self, lead_info: Dict) -> LeadScore:
        """社区版：委托 LeadScoringService 详细因子模型"""
        from gavvy_salesmaster.crm_pkg.lead_gen.scoring import LeadInfo as _LeadInfo

        # 适配 lead_info dict → LeadInfo
        li = _LeadInfo(
            id=lead_info.get("id", "tmp"),
            company_name=lead_info.get("company", lead_info.get("company_name", "")),
            contact_name=lead_info.get("contact_name", ""),
            contact_phone=lead_info.get("contact_phone", ""),
            contact_email=lead_info.get("contact_email", ""),
            industry=lead_info.get("industry", ""),
            company_size=lead_info.get("company_size", "medium"),
            revenue=lead_info.get("revenue", ""),
            source=lead_info.get("source", "manual"),
            tags=lead_info.get("tags", []),
        )
        result = self._service.score_lead(li)
        return LeadScore(
            score=result.total_score,
            level=result.level.value,
            confidence=result.confidence,
            factors={f.name: f.score for f in result.factors},
            summary=f"综合评分 {result.total_score:.1f}/100，等级 {result.level.value}",
            recommended_action=result.recommended_action,
            estimated_value=result.estimated_value,
        )

    @staticmethod
    def _float_to_level(score: float) -> str:
        if score >= 80:
            return "hot"
        elif score >= 60:
            return "warm"
        elif score >= 40:
            return "cold"
        return "dead"


__all__ = ["LeadScorer", "LeadScore"]
