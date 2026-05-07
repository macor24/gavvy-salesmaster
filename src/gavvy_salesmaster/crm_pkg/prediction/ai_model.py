"""销售预测模块 - AI预测模型"""

import json
import random
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum


class DealStage(str, Enum):
    """交易阶段"""
    LEAD = "lead"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Deal:
    """交易数据结构"""
    id: str
    lead_id: str
    company_name: str
    value: float = 0.0
    stage: DealStage = DealStage.LEAD
    probability: float = 0.0
    expected_close_date: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None
    owner: str = ""
    competitor: str = ""
    discount: float = 0.0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self):
        d = asdict(self)
        d["stage"] = self.stage.value
        d["created_at"] = self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        d["updated_at"] = self.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        if self.expected_close_date:
            d["expected_close_date"] = self.expected_close_date.strftime("%Y-%m-%d")
        return d


@dataclass
class PredictionResult:
    """预测结果"""
    deal_id: str
    probability: float
    expected_value: float
    expected_close_date: Optional[datetime] = None
    confidence: float = 0.0
    factors: Dict[str, float] = None
    
    def __post_init__(self):
        if self.factors is None:
            self.factors = {}
    
    def to_dict(self):
        d = asdict(self)
        if self.expected_close_date:
            d["expected_close_date"] = self.expected_close_date.strftime("%Y-%m-%d")
        return d


@dataclass
class RiskWarning:
    """风险预警"""
    deal_id: str
    risk_type: str
    level: RiskLevel
    score: float
    description: str
    recommendation: str
    detected_at: datetime = None
    
    def __post_init__(self):
        if self.detected_at is None:
            self.detected_at = datetime.now()
    
    def to_dict(self):
        d = asdict(self)
        d["level"] = self.level.value
        d["detected_at"] = self.detected_at.strftime("%Y-%m-%d %H:%M:%S")
        return d


@dataclass
class Recommendation:
    """智能推荐"""
    deal_id: str
    type: str
    content: str
    confidence: float = 0.0
    timing_score: float = 0.0
    
    def to_dict(self):
        return asdict(self)


class AIPredictionModel:
    """AI预测模型"""
    
    def __init__(self):
        self.stage_probabilities = {
            DealStage.LEAD: 0.15,
            DealStage.QUALIFIED: 0.35,
            DealStage.PROPOSAL: 0.60,
            DealStage.NEGOTIATION: 0.80,
            DealStage.CLOSED_WON: 1.0,
            DealStage.CLOSED_LOST: 0.0,
        }
        
        self.factor_weights = {
            "engagement_score": 0.25,
            "company_size": 0.20,
            "industry_match": 0.15,
            "deal_age": 0.20,
            "competitor_pressure": 0.10,
            "decision_maker_involved": 0.10,
        }
    
    def predict_probability(self, deal: Deal, **context) -> float:
        """预测成交概率"""
        base_prob = self.stage_probabilities.get(deal.stage, 0.15)
        factors = self._calculate_factors(deal, context)
        
        final_prob = base_prob
        for factor, weight in self.factor_weights.items():
            factor_value = factors.get(factor, 0.5)
            adjustment = (factor_value - 0.5) * 2 * weight
            final_prob += adjustment
        
        return max(0.0, min(1.0, final_prob))
    
    def _calculate_factors(self, deal: Deal, context: Dict) -> Dict[str, float]:
        """计算各影响因子"""
        factors = {}
        
        factors["engagement_score"] = context.get("engagement_score", 0.5)
        
        company_size = context.get("company_size", "medium")
        size_map = {"small": 0.3, "medium": 0.5, "large": 0.8, "enterprise": 0.9}
        factors["company_size"] = size_map.get(company_size, 0.5)
        
        factors["industry_match"] = context.get("industry_match", 0.5)
        
        if deal.created_at:
            days_old = (datetime.now() - deal.created_at).days
            factors["deal_age"] = max(0.1, min(1.0, 1 - days_old / 90))
        else:
            factors["deal_age"] = 0.5
        
        factors["competitor_pressure"] = context.get("competitor_pressure", 0.3)
        
        factors["decision_maker_involved"] = 1.0 if context.get("decision_maker_involved", False) else 0.5
        
        return factors
    
    def predict_value(self, deal: Deal, **context) -> float:
        """预测成交金额"""
        base_value = deal.value
        probability = self.predict_probability(deal, **context)
        discount_factor = 1.0 - min(deal.discount, 0.3)
        
        return base_value * probability * discount_factor
    
    def predict_close_date(self, deal: Deal, **context) -> Optional[datetime]:
        """预测成交时间"""
        if deal.expected_close_date:
            return deal.expected_close_date
        
        stage_days = {
            DealStage.LEAD: 60,
            DealStage.QUALIFIED: 45,
            DealStage.PROPOSAL: 30,
            DealStage.NEGOTIATION: 15,
        }
        
        base_days = stage_days.get(deal.stage, 45)
        engagement = context.get("engagement_score", 0.5)
        adjustment_factor = 1 - (engagement - 0.5) * 0.3
        
        estimated_days = int(base_days * adjustment_factor)
        return datetime.now() + timedelta(days=estimated_days)
    
    def predict(self, deal: Deal, **context) -> PredictionResult:
        """完整预测"""
        probability = self.predict_probability(deal, **context)
        expected_value = self.predict_value(deal, **context)
        expected_close_date = self.predict_close_date(deal, **context)
        factors = self._calculate_factors(deal, context)
        
        data_points = sum(1 for v in context.values() if v is not None)
        confidence = min(1.0, 0.5 + data_points * 0.1)
        
        return PredictionResult(
            deal_id=deal.id,
            probability=probability,
            expected_value=expected_value,
            expected_close_date=expected_close_date,
            confidence=confidence,
            factors=factors
        )
    
    def detect_risks(self, deal: Deal, **context) -> List[RiskWarning]:
        """检测风险"""
        warnings = []
        
        # 流失风险检测
        if deal.stage not in [DealStage.CLOSED_WON, DealStage.CLOSED_LOST]:
            days_since_update = (datetime.now() - deal.updated_at).days
            if days_since_update > 7:
                score = min(1.0, days_since_update / 30)
                level = RiskLevel.HIGH if score > 0.5 else RiskLevel.MEDIUM
                warnings.append(RiskWarning(
                    deal_id=deal.id,
                    risk_type="churn",
                    level=level,
                    score=score,
                    description=f"交易已{days_since_update}天未更新，存在流失风险",
                    recommendation="建议立即跟进联系客户"
                ))
        
        # 价格风险检测
        if deal.discount > 0.25:
            score = min(1.0, (deal.discount - 0.25) / 0.25)
            level = RiskLevel.CRITICAL if score > 0.5 else RiskLevel.HIGH
            warnings.append(RiskWarning(
                deal_id=deal.id,
                risk_type="price",
                level=level,
                score=score,
                description=f"折扣率{deal.discount*100:.0f}%超过阈值，存在利润风险",
                recommendation="建议重新评估报价策略或申请特殊审批"
            ))
        
        # 竞品风险检测
        if deal.competitor:
            score = context.get("competitor_pressure", 0.5)
            level = RiskLevel.HIGH if score > 0.7 else RiskLevel.MEDIUM if score > 0.4 else RiskLevel.LOW
            warnings.append(RiskWarning(
                deal_id=deal.id,
                risk_type="competitor",
                level=level,
                score=score,
                description=f"存在竞品竞争({deal.competitor})",
                recommendation="建议分析竞品优劣势，制定差异化策略"
            ))
        
        # 预期时间风险
        if deal.expected_close_date and deal.expected_close_date < datetime.now():
            days_overdue = (datetime.now() - deal.expected_close_date).days
            score = min(1.0, days_overdue / 14)
            level = RiskLevel.CRITICAL if score > 0.5 else RiskLevel.HIGH
            warnings.append(RiskWarning(
                deal_id=deal.id,
                risk_type="timing",
                level=level,
                score=score,
                description=f"交易已逾期{days_overdue}天",
                recommendation="建议立即联系客户确认状态"
            ))
        
        return warnings
    
    def generate_recommendations(self, deal: Deal, **context) -> List[Recommendation]:
        """生成智能推荐"""
        recommendations = []
        
        # 最佳跟进时机推荐
        timing_score = context.get("engagement_score", 0.5)
        if timing_score > 0.7:
            recommendations.append(Recommendation(
                deal_id=deal.id,
                type="timing",
                content="当前是跟进的最佳时机，客户参与度高",
                confidence=timing_score,
                timing_score=timing_score
            ))
        elif timing_score < 0.3:
            recommendations.append(Recommendation(
                deal_id=deal.id,
                type="timing",
                content="建议等待更佳时机跟进，当前客户参与度较低",
                confidence=0.7,
                timing_score=timing_score
            ))
        
        # 话术推荐
        probability = self.predict_probability(deal, **context)
        if probability > 0.7:
            recommendations.append(Recommendation(
                deal_id=deal.id,
                type="script",
                content="建议使用促成话术，如：'根据您的需求，我们可以尽快安排合同签署'",
                confidence=probability
            ))
        elif probability > 0.4:
            recommendations.append(Recommendation(
                deal_id=deal.id,
                type="script",
                content="建议使用探询话术，了解客户顾虑",
                confidence=probability
            ))
        else:
            recommendations.append(Recommendation(
                deal_id=deal.id,
                type="script",
                content="建议使用培育话术，提供更多价值内容",
                confidence=0.6
            ))
        
        # 交叉销售推荐
        if deal.value > 100000:
            recommendations.append(Recommendation(
                deal_id=deal.id,
                type="cross_sell",
                content="客户预算较高，可推荐增值服务或套餐升级",
                confidence=0.8
            ))
        
        return recommendations


class PipelineForecast:
    """销售管道预测"""
    
    def __init__(self):
        self.model = AIPredictionModel()
    
    def forecast_pipeline(self, deals: List[Deal], **context) -> Dict[str, Any]:
        """预测整个销售管道"""
        predictions = []
        total_expected_value = 0.0
        total_deal_count = len(deals)
        won_count = 0
        risks = []
        recommendations = []
        
        for deal in deals:
            if deal.stage == DealStage.CLOSED_WON:
                total_expected_value += deal.value
                won_count += 1
            elif deal.stage != DealStage.CLOSED_LOST:
                prediction = self.model.predict(deal, **context)
                predictions.append(prediction)
                total_expected_value += prediction.expected_value
                
                risks.extend(self.model.detect_risks(deal, **context))
                recommendations.extend(self.model.generate_recommendations(deal, **context))
        
        return {
            "total_deals": total_deal_count,
            "active_deals": len(predictions),
            "won_deals": won_count,
            "expected_revenue": total_expected_value,
            "predictions": predictions,
            "risks": risks,
            "recommendations": recommendations,
            "confidence": self._calculate_overall_confidence(predictions)
        }
    
    def forecast_by_month(self, deals: List[Deal], months: int = 3) -> Dict[str, float]:
        """按月份预测"""
        forecast = {}
        now = datetime.now()
        
        for i in range(months):
            month_start = (now + timedelta(days=i*30)).replace(day=1)
            month_end = (month_start + timedelta(days=31)).replace(day=1) - timedelta(days=1)
            month_key = month_start.strftime("%Y-%m")
            
            month_deals = [d for d in deals 
                          if d.stage != DealStage.CLOSED_LOST 
                          and (not d.expected_close_date or (month_start <= d.expected_close_date <= month_end))]
            
            month_value = sum(self.model.predict_value(d) for d in month_deals)
            forecast[month_key] = month_value
        
        return forecast
    
    def _calculate_overall_confidence(self, predictions: List[PredictionResult]) -> float:
        """计算整体置信度"""
        if not predictions:
            return 0.0
        return sum(p.confidence for p in predictions) / len(predictions)


class SalesPredictionService:
    """销售预测服务"""
    
    def __init__(self):
        self.model = AIPredictionModel()
        self.pipeline_forecast = PipelineForecast()
    
    def predict_deal(self, deal: Deal, **context) -> PredictionResult:
        """预测单个交易"""
        return self.model.predict(deal, **context)
    
    def predict_probability(self, deal: Deal, **context) -> float:
        """预测成交概率"""
        return self.model.predict_probability(deal, **context)
    
    def predict_value(self, deal: Deal, **context) -> float:
        """预测成交金额"""
        return self.model.predict_value(deal, **context)
    
    def predict_close_date(self, deal: Deal, **context) -> Optional[datetime]:
        """预测成交时间"""
        return self.model.predict_close_date(deal, **context)
    
    def forecast_pipeline(self, deals: List[Deal], **context) -> Dict[str, Any]:
        """预测销售管道"""
        return self.pipeline_forecast.forecast_pipeline(deals, **context)
    
    def forecast_by_month(self, deals: List[Deal], months: int = 3) -> Dict[str, float]:
        """按月份预测"""
        return self.pipeline_forecast.forecast_by_month(deals, months)
    
    def detect_risks(self, deal: Deal, **context) -> List[RiskWarning]:
        """检测风险"""
        return self.model.detect_risks(deal, **context)
    
    def generate_recommendations(self, deal: Deal, **context) -> List[Recommendation]:
        """生成智能推荐"""
        return self.model.generate_recommendations(deal, **context)
    
    def get_high_risk_deals(self, deals: List[Deal], **context) -> List[Dict]:
        """获取高风险交易"""
        high_risk = []
        for deal in deals:
            risks = self.model.detect_risks(deal, **context)
            critical_risks = [r for r in risks if r.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
            if critical_risks:
                high_risk.append({
                    "deal": deal.to_dict(),
                    "risks": [r.to_dict() for r in critical_risks]
                })
        return high_risk


# 全局实例
sales_prediction_service = SalesPredictionService()


def get_sales_prediction_service() -> SalesPredictionService:
    """获取销售预测服务实例"""
    return sales_prediction_service