"""销售预测模块 - 智能推荐"""

import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class RecommendationType(str, Enum):
    """推荐类型"""
    TIMING = "timing"
    SCRIPT = "script"
    CROSS_SELL = "cross_sell"
    UP_SELL = "up_sell"

@dataclass
class Recommendation:
    """推荐结果"""
    id: str
    type: RecommendationType
    deal_id: str
    content: str
    confidence: float = 0.0
    priority: int = 100
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class TimingAnalyzer:
    """最佳跟进时机分析器"""
    
    def __init__(self):
        # 最佳联系时段（工作日）
        self.best_hours = [9, 10, 11, 14, 15, 16]
        # 最佳联系日期
        self.best_days = [0, 1, 2, 3]  # 周一到周四
    
    def analyze_best_time(self, context: Dict) -> Dict[str, Any]:
        """分析最佳跟进时机"""
        now = datetime.now()
        
        # 获取上次联系时间
        last_contact = context.get("last_contact_at")
        
        # 计算下次最佳时间
        next_time = self._calculate_next_best_time(now, last_contact)
        
        # 计算推荐置信度
        confidence = self._calculate_confidence(context)
        
        return {
            "recommended_time": next_time,
            "confidence": confidence,
            "reason": self._generate_reason(context, next_time)
        }
    
    def _calculate_next_best_time(self, now: datetime, last_contact: Optional[datetime]) -> datetime:
        """计算下次最佳时间"""
        next_time = now
        
        # 如果刚联系过，等待一段时间
        if last_contact:
            hours_since_contact = (now - last_contact).total_seconds() / 3600
            if hours_since_contact < 4:
                next_time = last_contact + timedelta(hours=4)
        
        # 调整到最佳时段
        if next_time.hour not in self.best_hours:
            # 找到下一个最佳时段
            for hour in self.best_hours:
                if hour > next_time.hour:
                    next_time = next_time.replace(hour=hour, minute=0, second=0)
                    break
            else:
                # 今天没有合适时段，明天第一个时段
                next_time = (next_time + timedelta(days=1)).replace(hour=self.best_hours[0], minute=0, second=0)
        
        # 调整到最佳日期
        while next_time.weekday() not in self.best_days:
            next_time = next_time + timedelta(days=1)
        
        return next_time
    
    def _calculate_confidence(self, context: Dict) -> float:
        """计算置信度"""
        factors = []
        
        # 客户活跃度
        engagement_score = context.get("engagement_score", 0.5)
        factors.append(engagement_score)
        
        # 上次联系时间
        last_contact = context.get("last_contact_at")
        if last_contact:
            hours_since = (datetime.now() - last_contact).total_seconds() / 3600
            if hours_since < 24:
                factors.append(0.8)
            elif hours_since < 48:
                factors.append(0.6)
            else:
                factors.append(0.4)
        else:
            factors.append(0.5)
        
        # 阶段因素
        stage = context.get("stage", "")
        stage_confidence = {
            "lead": 0.6,
            "qualified": 0.7,
            "proposal": 0.8,
            "negotiation": 0.9,
        }
        factors.append(stage_confidence.get(stage, 0.5))
        
        return sum(factors) / len(factors)
    
    def _generate_reason(self, context: Dict, next_time: datetime) -> str:
        """生成推荐理由"""
        reasons = []
        
        if context.get("engagement_score", 0.5) > 0.7:
            reasons.append("客户近期活跃度较高")
        
        last_contact = context.get("last_contact_at")
        if last_contact:
            hours_since = (datetime.now() - last_contact).total_seconds() / 3600
            if hours_since > 24:
                reasons.append("距离上次联系已超过24小时")
        
        stage = context.get("stage", "")
        if stage in ["proposal", "negotiation"]:
            reasons.append(f"当前处于{stage}阶段，需要密切跟进")
        
        if not reasons:
            reasons.append("根据历史数据分析")
        
        reasons.append(f"推荐在{next_time.strftime('%m-%d %H:%M')}联系")
        
        return "; ".join(reasons)

class ScriptRecommender:
    """话术推荐器"""
    
    def __init__(self):
        self.scripts = {
            "lead": [
                {
                    "id": "script_lead_1",
                    "content": "您好，我是{company}的{name}。通过{source}了解到您可能对我们的产品感兴趣，方便简单沟通一下吗？",
                    "variables": ["company", "name", "source"],
                    "confidence": 0.9
                },
                {
                    "id": "script_lead_2",
                    "content": "您好，我是{name}。想了解一下贵公司在{area}方面有什么需求吗？我们可以提供专业的解决方案。",
                    "variables": ["name", "area"],
                    "confidence": 0.85
                },
            ],
            "qualified": [
                {
                    "id": "script_qualified_1",
                    "content": "感谢您的信任！根据我们的沟通，我整理了一份针对您需求的方案概述，您看什么时候方便给您详细介绍一下？",
                    "variables": [],
                    "confidence": 0.95
                },
                {
                    "id": "script_qualified_2",
                    "content": "了解到您的核心需求是{need}，我们有成熟的解决方案，预计能为您带来{benefit}的提升。",
                    "variables": ["need", "benefit"],
                    "confidence": 0.9
                },
            ],
            "proposal": [
                {
                    "id": "script_proposal_1",
                    "content": "您好，报价单已经发送到您的邮箱。价格是基于{factors}计算的，如果有任何需要调整的地方，请随时和我沟通。",
                    "variables": ["factors"],
                    "confidence": 0.92
                },
                {
                    "id": "script_proposal_2",
                    "content": "想了解一下报价单您这边看的怎么样了？是否有什么问题需要我们协助解决的？",
                    "variables": [],
                    "confidence": 0.88
                },
            ],
            "negotiation": [
                {
                    "id": "script_negotiation_1",
                    "content": "感谢您的反馈！关于您提到的{concern}，我们可以{solution}。您觉得这个方案怎么样？",
                    "variables": ["concern", "solution"],
                    "confidence": 0.95
                },
                {
                    "id": "script_negotiation_2",
                    "content": "为了达成合作，我们愿意在{aspect}方面做出调整，希望能尽快推进合作。",
                    "variables": ["aspect"],
                    "confidence": 0.9
                },
            ],
        }
    
    def recommend_script(self, context: Dict) -> List[Dict]:
        """推荐话术"""
        stage = context.get("stage", "lead")
        
        if stage in self.scripts:
            return self.scripts[stage]
        
        return self.scripts["lead"]
    
    def render_script(self, script_id: str, variables: Dict) -> str:
        """渲染话术"""
        for stage_scripts in self.scripts.values():
            for script in stage_scripts:
                if script["id"] == script_id:
                    content = script["content"]
                    for key, value in variables.items():
                        content = content.replace(f"{{{key}}}", str(value))
                    return content
        return ""

class CrossSellRecommender:
    """交叉销售推荐器"""
    
    def __init__(self):
        self.product_matrix = {
            "CRM": ["数据分析", "营销自动化", "客户服务"],
            "数据分析": ["BI报表", "数据可视化", "预测分析"],
            "营销自动化": ["邮件营销", "短信营销", "社交媒体管理"],
            "客户服务": ["知识库", "在线客服", "工单系统"],
        }
    
    def recommend_cross_sell(self, current_product: str, context: Dict) -> List[Dict]:
        """推荐交叉销售产品"""
        recommendations = []
        
        if current_product in self.product_matrix:
            related_products = self.product_matrix[current_product]
            
            for product in related_products:
                score = self._calculate_score(product, context)
                if score > 0.3:
                    recommendations.append({
                        "product": product,
                        "score": score,
                        "reason": self._generate_reason(product, context),
                        "estimated_value": self._estimate_value(product, context)
                    })
        
        return sorted(recommendations, key=lambda x: x["score"], reverse=True)
    
    def _calculate_score(self, product: str, context: Dict) -> float:
        """计算推荐分数"""
        score = 0.5
        
        # 根据行业匹配
        industry = context.get("industry", "")
        if industry:
            industry_weights = {
                "科技": 0.2,
                "金融": 0.15,
                "制造": 0.1,
            }
            score += industry_weights.get(industry, 0.05)
        
        # 根据公司规模
        company_size = context.get("company_size", "medium")
        size_weights = {
            "small": 0.1,
            "medium": 0.15,
            "large": 0.2,
            "enterprise": 0.25,
        }
        score += size_weights.get(company_size, 0.15)
        
        # 根据现有产品数量
        existing_products = context.get("existing_products_count", 1)
        if existing_products < 3:
            score += 0.1
        
        return min(1.0, score)
    
    def _generate_reason(self, product: str, context: Dict) -> str:
        """生成推荐理由"""
        reasons = []
        
        industry = context.get("industry", "")
        if industry:
            reasons.append(f"{industry}行业客户常用")
        
        company_size = context.get("company_size", "")
        if company_size:
            reasons.append(f"适合{company_size}规模企业")
        
        if not reasons:
            reasons.append("根据您的使用情况")
        
        reasons.append(f"推荐搭配{product}模块")
        
        return "; ".join(reasons)
    
    def _estimate_value(self, product: str, context: Dict) -> float:
        """估算价值"""
        base_values = {
            "数据分析": 50000,
            "营销自动化": 30000,
            "客户服务": 40000,
            "BI报表": 20000,
            "数据可视化": 15000,
            "预测分析": 35000,
            "邮件营销": 10000,
            "短信营销": 8000,
            "社交媒体管理": 12000,
            "知识库": 15000,
            "在线客服": 25000,
            "工单系统": 20000,
        }
        
        base_value = base_values.get(product, 15000)
        
        # 根据公司规模调整
        size_multiplier = {
            "small": 0.5,
            "medium": 1.0,
            "large": 1.5,
            "enterprise": 2.0,
        }
        
        return base_value * size_multiplier.get(context.get("company_size", "medium"), 1.0)

class SmartRecommendationService:
    """智能推荐服务"""
    
    def __init__(self):
        self.timing_analyzer = TimingAnalyzer()
        self.script_recommender = ScriptRecommender()
        self.cross_sell_recommender = CrossSellRecommender()
    
    def recommend_best_time(self, context: Dict) -> Recommendation:
        """推荐最佳跟进时机"""
        result = self.timing_analyzer.analyze_best_time(context)
        
        return Recommendation(
            id=f"rec_timing_{context.get('deal_id', '')}",
            type=RecommendationType.TIMING,
            deal_id=context.get("deal_id", ""),
            content=f"建议在{result['recommended_time'].strftime('%Y-%m-%d %H:%M')}联系客户",
            confidence=result["confidence"],
            priority=10,
            metadata={
                "recommended_time": result["recommended_time"],
                "reason": result["reason"]
            }
        )
    
    def recommend_script(self, context: Dict) -> List[Recommendation]:
        """推荐话术"""
        scripts = self.script_recommender.recommend_script(context)
        
        return [Recommendation(
            id=f"rec_script_{script['id']}",
            type=RecommendationType.SCRIPT,
            deal_id=context.get("deal_id", ""),
            content=self.script_recommender.render_script(script["id"], context),
            confidence=script["confidence"],
            priority=20,
            metadata={
                "script_id": script["id"],
                "variables": script["variables"]
            }
        ) for script in scripts]
    
    def recommend_cross_sell(self, context: Dict) -> List[Recommendation]:
        """推荐交叉销售"""
        current_product = context.get("current_product", "CRM")
        recommendations = self.cross_sell_recommender.recommend_cross_sell(current_product, context)
        
        return [Recommendation(
            id=f"rec_crosssell_{rec['product']}",
            type=RecommendationType.CROSS_SELL,
            deal_id=context.get("deal_id", ""),
            content=f"推荐购买「{rec['product']}」模块",
            confidence=rec["score"],
            priority=30,
            metadata={
                "product": rec["product"],
                "reason": rec["reason"],
                "estimated_value": rec["estimated_value"]
            }
        ) for rec in recommendations]
    
    def get_all_recommendations(self, context: Dict) -> List[Recommendation]:
        """获取所有推荐"""
        recommendations = []

        # 最佳时机推荐
        timing_rec = self.recommend_best_time(context)
        recommendations.append(timing_rec)

        # 话术推荐
        script_recs = self.recommend_script(context)
        recommendations.extend(script_recs)

        # 交叉销售推荐
        cross_sell_recs = self.recommend_cross_sell(context)
        recommendations.extend(cross_sell_recs)

        # 按优先级排序
        recommendations.sort(key=lambda r: r.priority)

        # 桥接到 SalesOrchestrator（注入推荐到 Lead 上下文）
        self._bridge_to_orchestrator(context, recommendations)

        return recommendations

    def _bridge_to_orchestrator(self, context: Dict, recommendations: List[Recommendation]) -> None:
        """将推荐注入到 SalesOrchestrator 的 Lead 上下文"""
        deal_id = context.get("deal_id", "")
        if not deal_id:
            return
        try:
            from SentriKit_salesmaster.team_pkg.team.coordinator import SalesOrchestrator
            orch = SalesOrchestrator()
            recs_dict = [
                {"type": r.type.value, "content": r.content,
                 "confidence": r.confidence, "priority": r.priority}
                for r in recommendations
            ]
            orch.update_lead(deal_id, {"recommendations": recs_dict})
        except Exception:
            pass  # Orchestrator 不可用时静默降级

# 全局实例
smart_recommendation_service = SmartRecommendationService()

def get_smart_recommendation_service() -> SmartRecommendationService:
    """获取智能推荐服务实例"""
    return smart_recommendation_service