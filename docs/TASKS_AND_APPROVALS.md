# 📋 任务与审批流程系统使用文档

## 简介

任务与审批流程系统是销售宗师（SalesMaster）的核心协作模块，提供完整的任务管理、审批流程和消息通知功能。

## 功能架构

```
任务与审批流程系统
├── 任务管理（TaskManager）
│   ├── 创建/分配/跟踪任务
│   ├── 任务状态流转
│   ├── 优先级管理
│   ├── 子任务分解
│   └── 任务统计
│
├── 审批流程（ApprovalManager）
│   ├── 报价审批
│   ├── 合同审批
│   ├── 折扣审批
│   ├── 付款审批
│   ├── 自定义审批
│   └── 审批规则引擎
│
└── 通知系统（NotificationManager）
    ├── 任务通知
    ├── 审批通知
    └── 未读计数
```

## 快速开始

### 安装

确保已安装销售宗师：

```bash
pip install SentriKit-salesmaster
```

### 基础使用

```python
from SentriKit_salesmaster.tasks import (
    TaskManager, ApprovalManager, NotificationManager
)

# 创建管理器
tm = TaskManager()
am = ApprovalManager()
nm = NotificationManager()
```

## 任务管理

### 创建任务

```python
from datetime import datetime, timedelta

task = tm.create_task(
    title="跟进客户A",
    description="与客户A沟通需求",
    category="follow_up",     # follow_up/quote/contract/meeting/demo/other
    priority=2,               # 1=紧急, 2=高, 3=中, 4=低
    assignee="销售员A",
    creator="经理",
    due_date=(datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
    related_lead_id="lead_001"
)
```

### 任务状态管理

```python
# 获取任务
task = tm.get_task("task_id")

# 更新任务
task.status = "in_progress"
tm.update_task(task)

# 完成任务
tm.complete_task("task_id")

# 取消任务
tm.cancel_task("task_id")

# 删除任务
tm.delete_task("task_id")
```

### 查询任务

```python
# 获取所有任务
tasks = tm.get_tasks()

# 按状态筛选
pending = tm.get_tasks(status="pending")
in_progress = tm.get_tasks(status="in_progress")
completed = tm.get_tasks(status="completed")
overdue = tm.get_tasks(status="overdue")  # 过期任务

# 按负责人筛选
my_tasks = tm.get_tasks(assignee="销售员A")

# 按分类筛选
quotes = tm.get_tasks(category="quote")

# 按客户筛选
lead_tasks = tm.get_tasks(related_lead_id="lead_001")
```

### 子任务

```python
# 添加子任务
subtask = tm.add_subtask("task_id", "准备报价PPT")

# 获取子任务列表
subtasks = tm.get_subtasks("task_id")

# 完成子任务
tm.complete_subtask("task_id", "subtask_id")
```

### 任务统计

```python
stats = tm.get_stats()
# stats = {
#     "total": 10,
#     "pending": 5,
#     "in_progress": 3,
#     "completed": 2,
#     "overdue": 1,
#     "by_priority": {"urgent": 1, "high": 2, "medium": 3, "low": 4},
#     "by_category": {"follow_up": 4, "quote": 3, "contract": 2, ...}
# }

# 按负责人统计
my_stats = tm.get_stats(assignee="销售员A")

# 获取即将到期的任务（24小时内）
due_soon = tm.get_due_soon_tasks(hours=24)

# 获取过期任务
overdue = tm.get_overdue_tasks()
```

## 审批流程

### 发起审批

```python
# 报价审批
approval = am.request_approval(
    title="客户A报价单",
    description="产品报价50000元",
    approval_type="quote",
    requester="销售员A",
    approver="经理",
    amount=50000,
    related_lead_id="lead_001",
    due_date="2024-12-31"
)

# 合同审批
approval = am.request_approval(
    title="客户B合同",
    description="合同金额100000元",
    approval_type="contract",
    requester="销售员B",
    amount=100000
)

# 折扣审批
approval = am.request_approval(
    title="客户C折扣申请",
    description="申请25%折扣",
    approval_type="discount",
    requester="销售员A",
    amount=10000
)
```

### 审批操作

```python
# 获取审批
approval = am.get_approval("approval_id")

# 审批通过
am.approve("approval_id", approver="经理", decision="同意")

# 审批拒绝
am.reject("approval_id", approver="经理", reason="金额超出预算")

# 取消审批
am.cancel_approval("approval_id")
```

### 查询审批

```python
# 获取所有审批
approvals = am.get_approvals()

# 按状态筛选
pending = am.get_approvals(status="pending")
approved = am.get_approvals(status="approved")
rejected = am.get_approvals(status="rejected")

# 按类型筛选
quotes = am.get_approvals(approval_type="quote")

# 按申请人筛选
my_requests = am.get_approvals(requester="销售员A")

# 按审批人筛选
my_approvals = am.get_approvals(approver="经理")
```

### 审批规则

系统内置了默认审批规则：

```python
# 小额报价（≤10000）自动审批
# 大额报价（>50000）需主管审批
# 高折扣（>20%）需总监审批
# 大额付款（>100000）需财务审批
```

```python
# 获取审批规则
rules = am.get_rules()
for rule in rules:
    print(f"{rule.name}: 阈值{rule.threshold}, 自动审批{rule.auto_approve}")

# 添加自定义规则
from SentriKit_salesmaster.tasks import ApprovalRule

rule = ApprovalRule(
    name="超大额订单需CEO审批",
    type="contract",
    threshold=500000,
    approver_role="CEO",
    auto_approve=False
)
am.add_rule(rule)

# 更新规则
rule.enabled = False
am.update_rule(rule)

# 删除规则
am.delete_rule("rule_id")
```

### 审批统计

```python
stats = am.get_stats()
# stats = {
#     "total": 20,
#     "pending": 5,
#     "approved": 12,
#     "rejected": 3,
#     "total_amount": 500000,
#     "avg_amount": 41666.67,
#     "by_type": {"quote": 10, "contract": 5, "discount": 3, ...}
# }
```

## 通知系统

### 创建通知

```python
notif = nm.create_notification(
    notification_type="task",
    title="新任务分配",
    message="您有一个新任务：跟进客户D",
    recipient="销售员C",
    related_type="task",
    related_id="task_001"
)
```

### 查询通知

```python
# 获取所有通知
notifs = nm.get_notifications("销售员C")

# 只看未读
unread = nm.get_notifications("销售员C", is_read=False)

# 获取未读数量
count = nm.get_unread_count("销售员C")
```

### 管理通知

```python
# 标记为已读
nm.mark_as_read("notification_id")

# 全部标记为已读
nm.mark_all_as_read("销售员C")

# 删除通知
nm.delete_notification("notification_id")
```

## 数据类型

### TaskStatus（任务状态）
| 状态 | 说明 |
|------|------|
| pending | 待处理 |
| in_progress | 进行中 |
| completed | 已完成 |
| cancelled | 已取消 |
| overdue | 已过期 |

### TaskPriority（优先级）
| 优先级 | 值 | 说明 |
|--------|------|------|
| URGENT | 1 | 紧急 |
| HIGH | 2 | 高 |
| MEDIUM | 3 | 中 |
| LOW | 4 | 低 |

### TaskCategory（任务分类）
| 分类 | 值 |
|------|------|
| follow_up | 客户跟进 |
| quote | 报价 |
| contract | 合同 |
| approval | 审批 |
| meeting | 会议 |
| demo | 产品演示 |
| other | 其他 |

### ApprovalType（审批类型）
| 类型 | 说明 |
|------|------|
| quote | 报价审批 |
| contract | 合同审批 |
| discount | 折扣审批 |
| payment | 付款审批 |
| custom | 自定义审批 |

### ApprovalStatus（审批状态）
| 状态 | 说明 |
|------|------|
| pending | 待审批 |
| approved | 已通过 |
| rejected | 已拒绝 |
| cancelled | 已取消 |
| expired | 已过期 |

## 使用示例

### 示例 1: 完整的销售流程

```python
from SentriKit_salesmaster.tasks import (
    TaskManager, ApprovalManager
)
from datetime import datetime, timedelta

tm = TaskManager()
am = ApprovalManager()

# 1. 创建跟进任务
task = tm.create_task(
    title=f"跟进客户A",
    description="与客户A沟通产品需求",
    category="follow_up",
    priority=2,
    assignee="销售员A"
)

# 2. 报价
quote_task = tm.create_task(
    title=f"为客户A准备报价",
    description="根据需求准备报价单",
    category="quote",
    priority=1,
    assignee="销售员A",
    related_lead_id="lead_001"
)

# 3. 发起报价审批
approval = am.request_approval(
    title=f"客户A报价单",
    description="报价金额50000元",
    approval_type="quote",
    requester="销售员A",
    amount=50000
)

# 4. 审批通过后，创建合同任务
if approval.status == "approved":
    contract_task = tm.create_task(
        title=f"为客户A准备合同",
        description="根据报价准备合同",
        category="contract",
        priority=1,
        assignee="销售员A"
    )

# 5. 完成任务
tm.complete_task(task.id)
tm.complete_task(quote_task.id)
```

### 示例 2: 审批规则配置

```python
from SentriKit_salesmaster.tasks import ApprovalManager, ApprovalRule

am = ApprovalManager()

# 查看现有规则
rules = am.get_rules()

# 添加新规则：超过20万的合同需要CEO审批
new_rule = ApprovalRule(
    name="大额合同CEO审批",
    type="contract",
    threshold=200000,
    approver_role="CEO",
    auto_approve=False,
    enabled=True
)
am.add_rule(new_rule)

# 禁用不需要的规则
for rule in rules:
    if rule.name == "小额报价自动审批":
        rule.auto_approve = False
        am.update_rule(rule)
```

## 最佳实践

### 1. 任务组织
- 每个任务只做一件事
- 设置明确的截止日期
- 合理分配优先级
- 及时更新任务状态

### 2. 审批流程
- 金额阈值要合理设置
- 自动审批只用于小额高频场景
- 大额审批要有多级复核

### 3. 通知管理
- 及时处理待审批项
- 定期清理过期通知
- 重要通知要标记

## 下一步

- 阅读 `tests/test_tasks.py` 查看完整测试
- 集成到您的销售系统中

---

**祝您使用愉快！** 🎉
