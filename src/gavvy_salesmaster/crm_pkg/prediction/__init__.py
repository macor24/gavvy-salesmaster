"""销售预测模块 - 入口"""

from .ai_model import (
    SalesPredictionService,
    get_sales_prediction_service,
    Deal,
    DealStage,
    PredictionResult,
    AIPredictionModel,
    PipelineForecast,
)

from .risk_management import (
    RiskManagementService,
    get_risk_management_service,
    RiskAlert,
    RiskLevel,
    RiskType,
    RiskDetector,
)

from .smart_recommendation import (
    SmartRecommendationService,
    get_smart_recommendation_service,
    Recommendation,
    RecommendationType,
    TimingAnalyzer,
    ScriptRecommender,
    CrossSellRecommender,
)

__all__ = [
    # AI预测模型
    "SalesPredictionService",
    "get_sales_prediction_service",
    "Deal",
    "DealStage",
    "PredictionResult",
    "AIPredictionModel",
    "PipelineForecast",
    
    # 风险预警
    "RiskManagementService",
    "get_risk_management_service",
    "RiskAlert",
    "RiskLevel",
    "RiskType",
    "RiskDetector",
    
    # 智能推荐
    "SmartRecommendationService",
    "get_smart_recommendation_service",
    "Recommendation",
    "RecommendationType",
    "TimingAnalyzer",
    "ScriptRecommender",
    "CrossSellRecommender",
]

# 服务实例
prediction = get_sales_prediction_service()
risk_management = get_risk_management_service()
recommendation = get_smart_recommendation_service()