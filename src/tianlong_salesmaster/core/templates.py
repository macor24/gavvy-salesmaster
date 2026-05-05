"""SentriKit_salesmaster.core.templates — 销售提案和调研模板

所有模板中的 {product_name} 由 SalesPipeline 传入。
"""

# 客户调研模板
SALES_RESEARCH_TEMPLATE = """## 客户调研报告: {company_name}

### 1. 基础信息
{basic_info}

### 2. AI Agent 成熟度评估
{ai_maturity}

### 3. 安全与合规需求
{security_needs}

### 4. 商业机会评估
{opportunity_assessment}

### 5. 建议切入点
{entry_point}

---

*由 {product_name} Sales Agent 自动生成*
"""

# 销售提案模板
SALES_PROPOSAL_TEMPLATE = """## 销售提案: {company_name}

### 1. 客户概况
{company_profile}

### 2. 需求分析
{needs_analysis}

### 3. 产品价值主张
{value_proposition}

### 4. 推荐方案
{recommended_solution}

### 5. 联系策略
{contact_strategy}

### 6. 跟进计划
{follow_up_plan}

---

*由 {product_name} Sales Agent 自动生成 | {generated_at}*
"""

# 销售周期汇报模板
SALES_CYCLE_REPORT_TEMPLATE = """## {product_name} 销售周期报告

### 周期: {cycle_time}

### 摘要
{summary}

### 本次发现的潜在客户 ({leads_count}个)
| 公司 | 行业 | 优先级 | 状态 | 联系方式 |
|------|------|--------|------|----------|
{leads_table}

### 已生成提案 ({proposals_count}个)
{proposals_list}

### 下一步
{next_steps}
"""
