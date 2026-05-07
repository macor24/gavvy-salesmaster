"""销售预测模块 - 风险预警"""

import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskType(str, Enum):
    """风险类型"""
    CHURN = "churn"
    PRICE = "price"
    COMPETITOR = "competitor"
    TIMING = "timing"
    QUALIFICATION = "qualification"
    BUDGET = "budget"
    DECISION_MAKER = "decision_maker"
    TECHNICAL = "technical"

@dataclass
class RiskAlert:
    """风险预警"""
    id: str
    deal_id: str
    risk_type: RiskType
    level: RiskLevel
    score: float
    description: str
    recommendation: str
    detected_at: datetime = None
    resolved: bool = False
    
    def __post_init__(self):
        if self.detected_at is None:
            self.detected_at = datetime.now()

class RiskDetector:
    """风险检测器"""
    
    def __init__(self):
        self.detectors = {
            RiskType.CHURN: self._detect_churn_risk,
            RiskType.PRICE: self._detect_price_risk,
            RiskType.COMPETITOR: self._detect_competitor_risk,
            RiskType.TIMING: self._detect_timing_risk,
            RiskType.QUALIFICATION: self._detect_qualification_risk,
            RiskType.BUDGET: self._detect_budget_risk,
            RiskType.DECISION_MAKER: self._detect_decision_maker_risk,
            RiskType.TECHNICAL: self._detect_technical_risk,
        }
    
    def _detect_churn_risk(self, deal: Dict, context: Dict) -> Optional[RiskAlert]:
        """检测流失风险"""
        last_contact = context.get("last_contact_at")
        
        if last_contact:
            days_since_contact = (datetime.now() - last_contact).days
            if days_since_contact > 14:
                score = min(1.0, days_since_contact / 30)
                level = self._score_to_level(score)
                return RiskAlert(
                    id=f"risk_churn_{deal.get('id')}",
                    deal_id=deal.get("id"),
                    risk_type=RiskType.CHURN,
                    level=level,
                    score=score,
                    description=f"客户已超过{days_since_contact}天未联系",
                    recommendation="立即安排跟进，了解客户近况"
                )
        return None
    
    def _detect_price_risk(self, deal: Dict, context: Dict) -> Optional[RiskAlert]:
        """检测价格风险"""
        deal_value = deal.get("value", 0)
        budget = context.get("budget", 0)
        
        if budget > 0 and deal_value > budget * 1.5:
            score = min(1.0, (deal_value - budget * 1.5) / deal_value)
            level = self._score_to_level(score)
            return RiskAlert(
                id=f"risk_price_{deal.get('id')}",
                deal_id=deal.get("id"),
                risk_type=RiskType.PRICE,
                level=level,
                score=score,
                description=f"报价金额({deal_value})超出客户预算({budget})",
                recommendation="重新评估报价方案，考虑分期或精简功能"
            )
        return None
    
    def _detect_competitor_risk(self, deal: Dict, context: Dict) -> Optional[RiskAlert]:
        """检测竞品风险"""
        competitor_count = context.get("competitor_count", 0)
        competitor_advantage = context.get("competitor_advantage", "")
        
        score = min(1.0, competitor_count * 0.3)
        if competitor_advantage:
            score += 0.2
        
        if score >= 0.3:
            level = self._score_to_level(score)
            return RiskAlert(
                id=f"risk_competitor_{deal.get('id')}",
                deal_id=deal.get("id"),
                risk_type=RiskType.COMPETITOR,
                level=level,
                score=score,
                description=f"检测到{competitor_count}个竞争对手，竞品优势: {competitor_advantage}",
                recommendation="分析竞品，找出差异化优势，加强客户沟通"
            )
        return None
    
    def _detect_timing_risk(self, deal: Dict, context: Dict) -> Optional[RiskAlert]:
        """检测时间风险"""
        expected_close_date = deal.get("expected_close_date")
        
        if expected_close_date:
            days_to_close = (expected_close_date - datetime.now()).days
            stage = deal.get("stage", "")
            
            if stage == "lead" and days_to_close < 30:
                score = min(1.0, 1 - days_to_close / 30)
                level = self._score_to_level(score)
                return RiskAlert(
                    id=f"risk_timing_{deal.get('id')}",
                    deal_id=deal.get("id"),
                    risk_type=RiskType.TIMING,
                    level=level,
                    score=score,
                    description=f"预期成交日期过近，当前阶段为{stage}",
                    recommendation="加快推进速度，必要时调整预期日期"
                )
        return None
    
    def _detect_qualification_risk(self, deal: Dict, context: Dict) -> Optional[RiskAlert]:
        """检测资质风险"""
        qualification_score = context.get("qualification_score", 0.5)
        
        if qualification_score < 0.5:
            score = 1 - qualification_score
            level = self._score_to_level(score)
            return RiskAlert(
                id=f"risk_qualification_{deal.get('id')}",
                deal_id=deal.get("id"),
                risk_type=RiskType.QUALIFICATION,
                level=level,
                score=score,
                description=f"线索资质评分较低({qualification_score})",
                recommendation="进一步核实客户需求和购买意向"
            )
        return None
    
    def _detect_budget_risk(self, deal: Dict, context: Dict) -> Optional[RiskAlert]:
        """检测预算风险"""
        budget_verified = context.get("budget_verified", False)
        
        if not budget_verified:
            return RiskAlert(
                id=f"risk_budget_{deal.get('id')}",
                deal_id=deal.get("id"),
                risk_type=RiskType.BUDGET,
                level=RiskLevel.MEDIUM,
                score=0.5,
                description="客户预算尚未确认",
                recommendation="尽早确认客户预算情况"
            )
        return None
    
    def _detect_decision_maker_risk(self, deal: Dict, context: Dict) -> Optional[RiskAlert]:
        """检测决策者风险"""
        decision_maker_identified = context.get("decision_maker_identified", False)
        
        if not decision_maker_identified:
            return RiskAlert(
                id=f"risk_dm_{deal.get('id')}",
                deal_id=deal.get("id"),
                risk_type=RiskType.DECISION_MAKER,
                level=RiskLevel.HIGH,
                score=0.7,
                description="尚未确认最终决策者",
                recommendation="努力接触高层决策者"
            )
        return None
    
    def _detect_technical_risk(self, deal: Dict, context: Dict) -> Optional[RiskAlert]:
        """检测技术风险"""
        technical_gaps = context.get("technical_gaps", [])
        
        if technical_gaps:
            score = min(1.0, len(technical_gaps) * 0.3)
            level = self._score_to_level(score)
            return RiskAlert(
                id=f"risk_technical_{deal.get('id')}",
                deal_id=deal.get("id"),
                risk_type=RiskType.TECHNICAL,
                level=level,
                score=score,
                description=f"检测到{len(technical_gaps)}个技术障碍: {', '.join(technical_gaps)}",
                recommendation="评估技术可行性，准备解决方案"
            )
        return None
    
    def _score_to_level(self, score: float) -> RiskLevel:
        """分数转风险等级"""
        if score >= 0.7:
            return RiskLevel.CRITICAL
        elif score >= 0.5:
            return RiskLevel.HIGH
        elif score >= 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def detect_risks(self, deal: Dict, context: Dict) -> List[RiskAlert]:
        """检测所有风险"""
        alerts = []
        
        for risk_type, detector in self.detectors.items():
            alert = detector(deal, context)
            if alert:
                alerts.append(alert)
        
        return alerts

class RiskManagementService:
    """风险管理服务"""
    
    def __init__(self):
        self.detector = RiskDetector()
        self.alerts: List[RiskAlert] = []
    
    def analyze_deal(self, deal: Dict, context: Dict) -> List[RiskAlert]:
        """分析交易风险"""
        alerts = self.detector.detect_risks(deal, context)
        self.alerts.extend(alerts)
        return alerts
    
    def get_alerts(self, deal_id: Optional[str] = None, risk_type: Optional[RiskType] = None, 
                   level: Optional[RiskLevel] = None) -> List[RiskAlert]:
        """获取风险预警"""
        alerts = [a for a in self.alerts if not a.resolved]
        
        if deal_id:
            alerts = [a for a in alerts if a.deal_id == deal_id]
        
        if risk_type:
            alerts = [a for a in alerts if a.risk_type == risk_type]
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        # 按风险等级排序
        level_order = {RiskLevel.CRITICAL: 0, RiskLevel.HIGH: 1, RiskLevel.MEDIUM: 2, RiskLevel.LOW: 3}
        alerts.sort(key=lambda a: level_order.get(a.level, 3))
        
        return alerts
    
    def resolve_alert(self, alert_id: str):
        """解决风险预警"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolved = True
                break
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """获取风险摘要"""
        unresolved = [a for a in self.alerts if not a.resolved]
        
        summary = {
            "total_alerts": len(self.alerts),
            "unresolved_alerts": len(unresolved),
            "by_level": {level.value: 0 for level in RiskLevel},
            "by_type": {risk_type.value: 0 for risk_type in RiskType},
        }
        
        for alert in unresolved:
            summary["by_level"][alert.level.value] += 1
            summary["by_type"][alert.risk_type.value] += 1
        
        return summary

# 全局实例
risk_management_service = RiskManagementService()

def get_risk_management_service() -> RiskManagementService:
    """获取风险管理服务实例"""
    return risk_management_service