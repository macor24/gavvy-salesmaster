# 📋 报价与合同管理系统使用文档

## 简介

报价与合同管理系统是销售宗师（SalesMaster）的核心业务模块，提供完整的产品管理、报价单生成、合同管理、模板配置等功能。

## 功能架构

```
报价与合同管理系统
├── 产品管理（ProductManager）
│   ├── 产品创建/编辑/删除
│   ├── 产品分类和标签
│   └── 产品价格和成本
├── 报价管理（QuoteManager）
│   ├── 报价单创建和编辑
│   ├── 报价明细（产品+数量+折扣+税费）
│   ├── 状态流转（草稿/待审批/已发送/已接受/已过期）
│   ├── 报价统计
│   └── 有效期管理
├── 合同管理（ContractManager）
│   ├── 合同创建（可从报价单生成）
│   ├── 合同明细
│   ├── 付款计划管理
│   ├── 状态流转（草稿/待审批/已签署/履行中/已完成）
│   └── 合同统计
└── 模板管理（TemplateManager）
    ├── 报价模板
    ├── 合同模板
    └── 默认模板设置
```

## 快速开始

### 基础使用

```python
from SentriKit_salesmaster.quotes import (
    ProductManager,
    QuoteManager,
    ContractManager,
    TemplateManager,
)

# 创建管理器
pm = ProductManager()
qm = QuoteManager()
cm = ContractManager()
tmpl_mgr = TemplateManager()
```

## 产品管理

### 创建产品

```python
product = pm.create_product(
    name="企业版套餐",
    description="为企业客户提供的完整解决方案",
    sku="ENT-2024-001",
    unit_price=50000.0,
    cost_price=25000.0,
    category="软件产品",
    tags=["企业", "套餐"]
)
```

### 产品查询

```python
# 获取所有活跃产品
products = pm.get_products()

# 获取指定分类的产品
software_products = pm.get_products(category="软件产品")

# 获取单个产品
product = pm.get_product("product-id")
```

### 产品更新和删除

```python
# 更新产品
product.description = "新的描述"
pm.update_product(product)

# 删除产品（标记为不活跃）
pm.delete_product("product-id")
```

## 报价管理

### 创建报价单

```python
quote = qm.create_quote(
    title="客户A企业方案",
    customer_id="CUST-001",
    customer_name="客户A科技有限公司",
    salesperson="销售员A",
    related_lead_id="lead-001",
    valid_days=30
)
```

### 添加报价明细

```python
qm.add_quote_item(
    quote_id=quote.id,
    product_id=product.id,
    product_name=product.name,
    quantity=2,
    unit_price=product.unit_price,
    discount_percent=10.0,
    tax_percent=13.0
)
```

### 报价状态管理

```python
# 更新报价状态
qm.update_quote_status(quote.id, "pending_approval")  # 待审批
qm.update_quote_status(quote.id, "approved")            # 已审批
qm.update_quote_status(quote.id, "sent")                # 已发送
qm.update_quote_status(quote.id, "accepted")            # 已接受

# 查询报价列表
quotes = qm.get_quotes()
pending_quotes = qm.get_quotes(status="pending")
my_quotes = qm.get_quotes(salesperson="销售员A")

# 获取报价总额
quote = qm.get_quote(quote.id)
print(f"总额: {quote.total_amount}")
print(f"小计: {quote.subtotal}")
print(f"折扣: {quote.total_discount}")
print(f"税费: {quote.total_tax}")
```

### 报价统计

```python
stats = qm.get_stats()
print(f"总报价数: {stats['total']}")
print(f"按状态: {stats['by_status']}")
print(f"已接受总额: {stats['total_amount']}")
```

## 合同管理

### 创建合同

```python
# 方式1: 从报价单创建（推荐）
contract = cm.create_contract_from_quote(
    quote_id=quote.id,
    title="客户A技术服务合同",
    salesperson="销售员A"
)

# 方式2: 直接创建
contract = cm.create_contract(
    title="客户B服务合同",
    customer_id="CUST-002",
    customer_name="客户B有限公司",
    salesperson="销售员B"
)
```

### 合同状态管理

```python
cm.update_contract_status(contract.id, "pending_approval")   # 待审批
cm.update_contract_status(contract.id, "signed")             # 已签署
cm.update_contract_status(contract.id, "fulfilling")         # 履行中
cm.update_contract_status(contract.id, "completed")          # 已完成

# 查询合同列表
contracts = cm.get_contracts()
active_contracts = cm.get_contracts(status="fulfilling")
```

### 付款计划

```python
# 添加付款计划
cm.add_payment_plan(
    contract_id=contract.id,
    description="首期付款",
    amount=30000.0,
    due_date="2024-12-31"
)

# 标记付款完成
first_plan = contract.payment_plans[0]
cm.mark_payment_paid(contract.id, first_plan.id)
```

### 合同统计

```python
stats = cm.get_stats()
print(f"总合同数: {stats['total']}")
print(f"已签署总额: {stats['total_amount']}")
```

## 模板管理

### 内置默认模板

系统初始化时自动创建标准模板：

```python
# 获取默认报价模板
default_quote_template = tmpl_mgr.get_default_quote_template()
print(default_quote_template.name)

# 获取所有模板
quote_templates = tmpl_mgr.get_quote_templates()
contract_templates = tmpl_mgr.get_contract_templates()
```

## 完整销售流程示例

以下是完整的销售业务流程示例：

```python
# 1. 创建产品
product = pm.create_product(
    name="企业解决方案",
    unit_price=50000.0,
    category="软件产品"
)

# 2. 创建报价单
quote = qm.create_quote(
    title="客户A方案",
    customer_id="CUST-001",
    customer_name="客户A有限公司",
    salesperson="销售员A"
)

# 3. 添加报价明细
qm.add_quote_item(
    quote_id=quote.id,
    product_id=product.id,
    product_name=product.name,
    quantity=1,
    unit_price=product.unit_price,
    discount_percent=5.0,
    tax_percent=13.0
)

# 4. 审批和发送报价
qm.update_quote_status(quote.id, "pending_approval")
qm.update_quote_status(quote.id, "approved")
qm.update_quote_status(quote.id, "sent")

# 5. 客户接受后，从报价单创建合同
qm.update_quote_status(quote.id, "accepted")
contract = cm.create_contract_from_quote(quote.id, title="正式合同")

# 6. 签署并开始履行合同
cm.update_contract_status(contract.id, "signed")
cm.update_contract_status(contract.id, "fulfilling")

# 7. 管理付款计划
cm.add_payment_plan(contract.id, "首期付款", 30000.0)
cm.mark_payment_paid(contract.id, contract.payment_plans[0].id)
```

## 数据类型

### 报价状态（Quote Status）

| 状态 | 值 | 说明 |
|------|----|------|
| 草稿 | draft | 初始状态，未发送给客户 |
| 待审批 | pending_approval | 等待内部审批 |
| 已审批 | approved | 已审批通过 |
| 已发送 | sent | 已发送给客户 |
| 已接受 | accepted | 客户已接受报价 |
| 已拒绝 | rejected | 客户已拒绝报价 |
| 已过期 | expired | 超过有效期 |

### 合同状态（Contract Status）

| 状态 | 值 | 说明 |
|------|----|------|
| 草稿 | draft | 初始状态 |
| 待审批 | pending_approval | 等待内部审批 |
| 已签署 | signed | 已由双方签署 |
| 履行中 | fulfilling | 合同执行中 |
| 已完成 | completed | 合同执行完成 |
| 已终止 | terminated | 合同终止 |

## 集成与扩展

### 与任务审批系统集成

```python
from SentriKit_salesmaster.tasks import ApprovalManager, TaskManager

approval_mgr = ApprovalManager()
task_mgr = TaskManager()

# 报价审批时同时创建内部审批记录
approval = approval_mgr.request_approval(
    title=f"报价审批: {quote.title}",
    approval_type="quote",
    amount=quote.total_amount
)

# 创建跟进任务
task = task_mgr.create_task(
    title=f"跟进报价: {quote.title}",
    description="等待客户反馈",
    assignee="销售员A",
    related_lead_id="lead-001"
)
```

### 与知识库系统集成

```python
from SentriKit_salesmaster.knowledge import KnowledgeBase

kb = KnowledgeBase()

# 保存产品信息到知识库
kb.add_item(
    title=f"产品: {product.name}",
    content=product.description,
    category="产品信息",
    tags=["产品", product.category]
)

# 添加常见问题
kb.add_faq(
    question=f"{product.name} 的价格是多少？",
    answer=f"{product.name} 的单价是 {product.unit_price} 元",
    category="常见问题"
)
```

## 最佳实践

1. **产品管理**：
   - 合理设置 SKU 编号，便于管理
   - 定期更新产品信息和价格
   - 使用标签分类管理产品

2. **报价管理**：
   - 报价单发送前设置合理有效期
   - 使用折扣和税费功能生成完整报价
   - 及时更新报价状态，便于跟踪

3. **合同管理**：
   - 尽量从报价单生成合同，保持数据一致
   - 设置明确的付款计划
   - 及时标记付款状态

4. **审批流程**：
   - 建立清晰的审批权限规则
   - 大额报价/合同多级审批
   - 及时处理待审批事项

## 下一步

- 查看完整测试案例：`tests/test_quotes.py`
- 学习任务与审批系统：`docs/TASKS_AND_APPROVALS.md`
- 了解知识库系统：`docs/KNOWLEDGE_BASE.md`

---

**祝您使用愉快！🎉**
