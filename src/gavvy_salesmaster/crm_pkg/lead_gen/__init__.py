"""智能寻客模块 - 入口"""

from .data_mining import (
    DataMiningService,
    get_data_mining_service,
    CompanyInfo,
    TenderInfo,
    RecruitmentInfo,
    TianYanChaMock,
    QiChaChaMock,
    TenderCrawler,
    RecruitmentAnalyzer,
)

from .scoring import (
    LeadScoringService,
    get_lead_scoring_service,
    ScoredLead,
    LeadStatus,
    LeadPriority,
    LeadScoringModel,
    IntentPredictor,
    PrioritySorter,
)

from .assignment import (
    LeadAssignmentService,
    get_lead_assignment_service,
    Salesperson,
    AssignmentRule,
    AssignmentStrategy,
)

__all__ = [
    # 数据挖掘
    "DataMiningService",
    "get_data_mining_service",
    "CompanyInfo",
    "TenderInfo",
    "RecruitmentInfo",
    "TianYanChaMock",
    "QiChaChaMock",
    "TenderCrawler",
    "RecruitmentAnalyzer",
    
    # 线索评分
    "LeadScoringService",
    "get_lead_scoring_service",
    "Lead",
    "LeadStatus",
    "LeadPriority",
    "LeadScoringModel",
    "IntentPredictor",
    "PrioritySorter",
    
    # 线索分配
    "LeadAssignmentService",
    "get_lead_assignment_service",
    "Salesperson",
    "AssignmentRule",
    "AssignmentStrategy",
]

# 服务实例
data_mining = get_data_mining_service()
scoring = get_lead_scoring_service()
assignment = get_lead_assignment_service()