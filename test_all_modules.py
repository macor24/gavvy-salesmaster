#!/usr/bin/env python3
"""测试销售宗师所有核心模块"""

import sys
sys.path.insert(0, 'src')

# 测试智能寻客模块
print("=== 智能寻客测试 ===")
from SentriKit_salesmaster.lead_gen.data_mining import get_data_mining_service

dm_service = get_data_mining_service()
companies = dm_service.search_companies('科技')
print(f"搜索到 {len(companies)} 家公司")
for c in companies[:3]:
    print(f"  - {c.name} ({c.industry})")

# 测试线索评分模块
print("\n=== 线索评分测试 ===")
from SentriKit_salesmaster.lead_gen.scoring import get_lead_scoring_service, LeadInfo

score_service = get_lead_scoring_service()
lead = LeadInfo(
    id='test001', 
    company_name='测试科技公司', 
    industry='科技推广', 
    company_size='large', 
    contact_phone='13800138000'
)
result = score_service.score_lead(lead)
print(f"评分: {result.total_score:.2f}")
print(f"等级: {result.level.value}")
print(f"建议: {result.recommended_action}")

# 测试企微通信模块
print("\n=== 企微通信测试 ===")
from SentriKit_salesmaster.followup.communication import get_communication_service, ChannelType

comm_service = get_communication_service()
result = comm_service.send_message(ChannelType.WEWORK, 'test_user', '您好！这是测试消息')
print(f"消息发送: {'成功' if result else '失败'}")

# 测试销售预测模块
print("\n=== 销售预测测试 ===")
from SentriKit_salesmaster.prediction.ai_model import get_sales_prediction_service, Deal, DealStage

pred_service = get_sales_prediction_service()
deal = Deal(
    id='deal001', 
    lead_id='lead001', 
    company_name='测试客户', 
    value=100000, 
    stage=DealStage.PROPOSAL
)
prediction = pred_service.predict_deal(deal, engagement_score=0.8)
print(f"成交概率: {prediction.probability:.2%}")
print(f"预期金额: {prediction.expected_value:.2f}")

# 测试风险预警
print("\n=== 风险预警测试 ===")
risks = pred_service.detect_risks(deal)
print(f"检测到 {len(risks)} 个风险")
for risk in risks:
    print(f"  - {risk.risk_type}: {risk.level.value} - {risk.description}")

# 测试智能推荐
print("\n=== 智能推荐测试 ===")
recommendations = pred_service.generate_recommendations(deal)
print(f"生成 {len(recommendations)} 条推荐")
for rec in recommendations:
    print(f"  - {rec.type}: {rec.content}")

print("\n✅ 所有模块测试通过！")