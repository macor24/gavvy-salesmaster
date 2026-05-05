"""线索评分模块 - AI智能评分模型"""

import json
import random
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum


class LeadScoreLevel(str, Enum):
    """线索评分等级"""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    DEAD = "dead"


class LeadStatus(str, Enum):
    """线索状态"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class LeadPriority(str, Enum):
    """线索优先级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Lead:
    """线索数据结构（兼容旧版）"""
    id: str
    company_name: str
    contact_name: str = ""
    contact_phone: str = ""
    contact_email: str = ""
    status: LeadStatus = LeadStatus.NEW
    priority: LeadPriority = LeadPriority.MEDIUM
    score: float = 0.0
    source: str = ""
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self):
        d = asdict(self)
        d["status"] = self.status.value
        d["priority"] = self.priority.value
        d["created_at"] = self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return d


@dataclass
class LeadInfo:
    """线索信息数据结构"""
    id: str
    company_name: str
    unified_code: str = ""
    contact_name: str = ""
    contact_phone: str = ""
    contact_email: str = ""
    industry: str = ""
    company_size: str = ""  # small/medium/large/enterprise
    revenue: str = ""
    source: str = ""  # tianyancha/qichacha/tender/recruitment/manual
    created_at: datetime = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.tags is None:
            self.tags = []
    
    def to_dict(self):
        d = asdict(self)
        d["created_at"] = self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return d


@dataclass
class ScoreFactor:
    """评分因子"""
    name: str
    weight: float
    value: float
    max_value: float = 1.0
    description: str = ""
    
    @property
    def score(self) -> float:
        """计算该因子的贡献分数"""
        return (self.value / self.max_value) * self.weight


@dataclass
class LeadScoreResult:
    """线索评分结果"""
    lead_id: str
    company_name: str
    total_score: float
    level: LeadScoreLevel
    factors: List[ScoreFactor]
    confidence: float = 0.0
    recommended_action: str = ""
    estimated_value: float = 0.0
    
    def to_dict(self):
        return {
            "lead_id": self.lead_id,
            "company_name": self.company_name,
            "total_score": round(self.total_score, 2),
            "level": self.level.value,
            "factors": [asdict(f) for f in self.factors],
            "confidence": round(self.confidence, 2),
            "recommended_action": self.recommended_action,
            "estimated_value": round(self.estimated_value, 2)
        }


class LeadScoringModel:
    """线索评分模型"""
    
    def __init__(self):
        # 评分因子权重配置
        self.factor_weights = {
            "industry_match": 0.20,      # 行业匹配度
            "company_size": 0.15,         # 公司规模
            "revenue": 0.15,              # 营收规模
            "engagement": 0.15,          # 参与度
            "activity_score": 0.12,       # 公司活跃度
            "tender_activity": 0.10,      # 招标活跃度
            "recruitment_activity": 0.08, # 招聘活跃度
            "data_quality": 0.05,         # 数据完整性
        }
        
        # 公司规模评分映射
        self.size_score_map = {
            "small": 0.3,
            "medium": 0.6,
            "large": 0.85,
            "enterprise": 1.0,
        }
        
        # 营收规模评分映射
        self.revenue_score_map = {
            "500万以下": 0.2,
            "500-1000万": 0.35,
            "1000-5000万": 0.5,
            "5000万-1亿": 0.7,
            "1亿-5亿": 0.85,
            "5亿-10亿": 0.95,
            "10亿以上": 1.0,
        }
    
    def _calculate_industry_match(self, lead: LeadInfo, target_industries: List[str] = None) -> float:
        """计算行业匹配度"""
        if not target_industries:
            target_industries = ["科技", "软件", "互联网", "人工智能", "智能制造", "云计算"]
        
        industry = lead.industry.lower()
        for target in target_industries:
            if target.lower() in industry:
                return 1.0
        return 0.3
    
    def _calculate_company_size_score(self, lead: LeadInfo) -> float:
        """计算公司规模分数"""
        return self.size_score_map.get(lead.company_size.lower(), 0.3)
    
    def _calculate_revenue_score(self, lead: LeadInfo) -> float:
        """计算营收分数"""
        revenue = lead.revenue.replace("人民币", "").strip()
        
        if "万" in revenue:
            try:
                value = float(revenue.replace("万", ""))
                if value < 500:
                    return 0.2
                elif value < 1000:
                    return 0.35
                elif value < 5000:
                    return 0.5
                elif value < 10000:
                    return 0.7
                elif value < 50000:
                    return 0.85
                elif value < 100000:
                    return 0.95
                else:
                    return 1.0
            except:
                pass
        
        return self.revenue_score_map.get(lead.revenue, 0.3)
    
    def _calculate_engagement_score(self, lead: LeadInfo) -> float:
        """计算参与度分数"""
        score = 0.5
        
        # 有联系人电话 +0.3
        if lead.contact_phone:
            score += 0.3
        
        # 有联系人邮箱 +0.15
        if lead.contact_email:
            score += 0.15
        
        # 有联系人姓名 +0.05
        if lead.contact_name:
            score += 0.05
        
        return min(1.0, score)
    
    def _calculate_activity_score(self, activity_data: Dict = None) -> float:
        """计算公司活跃度分数"""
        if not activity_data:
            return 0.5
        
        recruitment_count = activity_data.get("recruitment_count", 0)
        tender_count = activity_data.get("tender_count", 0)
        
        score = 0.5
        
        if recruitment_count >= 3:
            score += 0.3
        elif recruitment_count >= 1:
            score += 0.15
        
        if tender_count >= 2:
            score += 0.2
        elif tender_count >= 1:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_data_quality(self, lead: LeadInfo) -> float:
        """计算数据完整性分数"""
        fields = [
            lead.unified_code,
            lead.contact_name,
            lead.contact_phone,
            lead.contact_email,
            lead.industry,
            lead.company_size,
            lead.revenue,
        ]
        
        filled_count = sum(1 for f in fields if f)
        return filled_count / len(fields)
    
    def score(self, lead: LeadInfo, activity_data: Dict = None, **context) -> LeadScoreResult:
        """计算线索评分"""
        factors = []
        
        # 计算各因子分数
        industry_match = self._calculate_industry_match(lead, context.get("target_industries"))
        factors.append(ScoreFactor(
            name="industry_match",
            weight=self.factor_weights["industry_match"],
            value=industry_match,
            description="行业匹配度"
        ))
        
        company_size = self._calculate_company_size_score(lead)
        factors.append(ScoreFactor(
            name="company_size",
            weight=self.factor_weights["company_size"],
            value=company_size,
            description="公司规模"
        ))
        
        revenue = self._calculate_revenue_score(lead)
        factors.append(ScoreFactor(
            name="revenue",
            weight=self.factor_weights["revenue"],
            value=revenue,
            description="营收规模"
        ))
        
        engagement = self._calculate_engagement_score(lead)
        factors.append(ScoreFactor(
            name="engagement",
            weight=self.factor_weights["engagement"],
            value=engagement,
            description="参与度"
        ))
        
        activity = self._calculate_activity_score(activity_data)
        factors.append(ScoreFactor(
            name="activity_score",
            weight=self.factor_weights["activity_score"],
            value=activity,
            description="公司活跃度"
        ))
        
        tender_activity = activity_data.get("tender_count", 0) > 0 if activity_data else False
        factors.append(ScoreFactor(
            name="tender_activity",
            weight=self.factor_weights["tender_activity"],
            value=1.0 if tender_activity else 0.3,
            description="招标活跃度"
        ))
        
        recruitment_activity = activity_data.get("recruitment_count", 0) > 0 if activity_data else False
        factors.append(ScoreFactor(
            name="recruitment_activity",
            weight=self.factor_weights["recruitment_activity"],
            value=1.0 if recruitment_activity else 0.3,
            description="招聘活跃度"
        ))
        
        data_quality = self._calculate_data_quality(lead)
        factors.append(ScoreFactor(
            name="data_quality",
            weight=self.factor_weights["data_quality"],
            value=data_quality,
            description="数据完整性"
        ))
        
        # 计算总分
        total_score = sum(f.score for f in factors) * 100
        
        # 确定等级
        if total_score >= 80:
            level = LeadScoreLevel.HOT
        elif total_score >= 60:
            level = LeadScoreLevel.WARM
        elif total_score >= 40:
            level = LeadScoreLevel.COLD
        else:
            level = LeadScoreLevel.DEAD
        
        # 计算置信度
        confidence = min(1.0, 0.5 + data_quality * 0.5)
        
        # 推荐行动
        action_map = {
            LeadScoreLevel.HOT: "立即联系，重点跟进",
            LeadScoreLevel.WARM: "尽快联系，持续培育",
            LeadScoreLevel.COLD: "定期跟进，保持触达",
            LeadScoreLevel.DEAD: "暂时搁置，定期清理"
        }
        recommended_action = action_map.get(level, "继续观察")
        
        # 预估价值
        estimated_value = self._estimate_value(lead, total_score)
        
        return LeadScoreResult(
            lead_id=lead.id,
            company_name=lead.company_name,
            total_score=total_score,
            level=level,
            factors=factors,
            confidence=confidence,
            recommended_action=recommended_action,
            estimated_value=estimated_value
        )
    
    def _estimate_value(self, lead: LeadInfo, score: float) -> float:
        """预估线索价值"""
        base_value = 100000  # 基础价值
        
        # 根据公司规模调整
        size_multiplier = self.size_score_map.get(lead.company_size.lower(), 0.5)
        
        # 根据评分调整
        score_multiplier = score / 50
        
        return base_value * size_multiplier * score_multiplier


class LeadPrioritizer:
    """线索优先级排序器"""
    
    def __init__(self):
        self.model = LeadScoringModel()
    
    def score_leads(self, leads: List[LeadInfo], **context) -> List[LeadScoreResult]:
        """批量评分线索"""
        results = []
        for lead in leads:
            activity_data = context.get("activity_data", {}).get(lead.company_name)
            result = self.model.score(lead, activity_data, **context)
            results.append(result)
        return results
    
    def prioritize(self, leads: List[LeadInfo], **context) -> List[LeadScoreResult]:
        """优先级排序"""
        results = self.score_leads(leads, **context)
        return sorted(results, key=lambda x: x.total_score, reverse=True)
    
    def get_hot_leads(self, leads: List[LeadInfo], threshold: float = 80, **context) -> List[LeadScoreResult]:
        """获取高价值线索"""
        results = self.score_leads(leads, **context)
        return [r for r in results if r.total_score >= threshold]
    
    def get_cold_leads(self, leads: List[LeadInfo], threshold: float = 40, **context) -> List[LeadScoreResult]:
        """获取低价值线索"""
        results = self.score_leads(leads, **context)
        return [r for r in results if r.total_score < threshold]


class LeadScoringService:
    """线索评分服务"""
    
    def __init__(self):
        self.model = LeadScoringModel()
        self.prioritizer = LeadPrioritizer()
    
    def score_lead(self, lead: LeadInfo, activity_data: Dict = None, **context) -> LeadScoreResult:
        """评分单个线索"""
        return self.model.score(lead, activity_data, **context)
    
    def score_leads(self, leads: List[LeadInfo], **context) -> List[LeadScoreResult]:
        """批量评分线索"""
        return self.prioritizer.score_leads(leads, **context)
    
    def prioritize_leads(self, leads: List[LeadInfo], **context) -> List[LeadScoreResult]:
        """优先级排序"""
        return self.prioritizer.prioritize(leads, **context)
    
    def get_hot_leads(self, leads: List[LeadInfo], threshold: float = 80, **context) -> List[LeadScoreResult]:
        """获取高价值线索"""
        return self.prioritizer.get_hot_leads(leads, threshold, **context)
    
    def batch_score_with_activity(self, leads: List[LeadInfo], activity_data_list: List[Dict]) -> List[LeadScoreResult]:
        """批量评分（带活跃度数据）"""
        results = []
        for lead in leads:
            activity_data = next((a for a in activity_data_list 
                                if a.get("company_name") == lead.company_name or
                                   a.get("company", {}).get("name") == lead.company_name), None)
            result = self.model.score(lead, activity_data)
            results.append(result)
        return sorted(results, key=lambda x: x.total_score, reverse=True)


# 全局实例
lead_scoring_service = LeadScoringService()


def get_lead_scoring_service() -> LeadScoringService:
    """获取线索评分服务实例"""
    return lead_scoring_service


class IntentPredictor:
    """意向预测器"""
    
    def __init__(self):
        self.intent_patterns = {
            "interested": ["需要", "想要", "有意向", "想了解", "感兴趣", "咨询", "报价"],
            "urgent": ["紧急", "尽快", "马上", "立刻", "急需"],
            "comparing": ["对比", "比较", "哪个好", "性价比", "价格"],
            "objection": ["太贵", "不需要", "暂时不需要", "再考虑"],
        }
    
    def predict_intent(self, text: str) -> str:
        """预测用户意向"""
        text_lower = text.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    return intent
        
        return "neutral"
    
    def get_intent_score(self, text: str) -> float:
        """获取意向分数"""
        intent = self.predict_intent(text)
        scores = {
            "interested": 0.8,
            "urgent": 0.9,
            "comparing": 0.6,
            "objection": 0.2,
            "neutral": 0.5,
        }
        return scores.get(intent, 0.5)


class PrioritySorter:
    """优先级排序器"""
    
    def __init__(self):
        pass
    
    def sort_by_score(self, leads: List[LeadInfo], **context) -> List[LeadInfo]:
        """按评分排序"""
        service = get_lead_scoring_service()
        scored = [(lead, service.score_lead(lead, **context)) for lead in leads]
        scored.sort(key=lambda x: x[1].total_score, reverse=True)
        return [lead for lead, _ in scored]
    
    def sort_by_priority(self, leads: List[Lead]) -> List[Lead]:
        """按优先级排序"""
        priority_order = {LeadPriority.HIGH: 0, LeadPriority.MEDIUM: 1, LeadPriority.LOW: 2}
        return sorted(leads, key=lambda x: priority_order.get(x.priority, 3))
    
    def sort_by_activity(self, leads: List[LeadInfo], activity_data: Dict) -> List[LeadInfo]:
        """按活跃度排序"""
        def get_activity_score(lead):
            activity = activity_data.get(lead.company_name, {})
            return activity.get("activity_score", 0.5)
        
        return sorted(leads, key=get_activity_score, reverse=True)
