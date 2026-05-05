"""tianlong_salesmaster.crm_pkg.tasks — 任务与审批流程系统

完整的任务管理和审批流程系统，包含：
- 任务管理（创建/分配/跟踪/完成）
- 审批流程（报价/合同/折扣/付款审批）
- 多人协作
- 消息通知

使用方法：
    from tianlong_salesmaster.crm_pkg.tasks import TaskManager, ApprovalManager

    # 任务管理
    tm = TaskManager()
    task = tm.create_task(
        title="跟进客户XX",
        assignee="销售员A",
        due_date="2024-12-31"
    )

    # 审批流程
    am = ApprovalManager()
    approval = am.request_approval(
        type="quote",
        title="客户XX报价单",
        amount=50000
    )
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set


# ── 枚举定义 ────────────────────────────────────────

class TaskStatus(Enum):
    PENDING = "pending"           # 待处理
    IN_PROGRESS = "in_progress"   # 进行中
    COMPLETED = "completed"       # 已完成
    CANCELLED = "cancelled"       # 已取消
    OVERDUE = "overdue"           # 已过期


class TaskPriority(Enum):
    URGENT = 1   # 紧急
    HIGH = 2     # 高
    MEDIUM = 3   # 中
    LOW = 4      # 低


class TaskCategory(Enum):
    FOLLOW_UP = "follow_up"       # 客户跟进
    QUOTE = "quote"              # 报价
    CONTRACT = "contract"        # 合同
    APPROVAL = "approval"        # 审批
    MEETING = "meeting"          # 会议
    DEMO = "demo"               # 产品演示
    OTHER = "other"             # 其他


class ApprovalType(Enum):
    QUOTE = "quote"             # 报价审批
    CONTRACT = "contract"       # 合同审批
    DISCOUNT = "discount"       # 折扣审批
    PAYMENT = "payment"         # 付款审批
    CUSTOM = "custom"           # 自定义审批


class ApprovalStatus(Enum):
    PENDING = "pending"         # 待审批
    APPROVED = "approved"       # 已通过
    REJECTED = "rejected"       # 已拒绝
    CANCELLED = "cancelled"     # 已取消
    EXPIRED = "expired"         # 已过期


# ── 数据类型定义 ────────────────────────────────────────

@dataclass
class Task:
    """任务"""
    id: str = ""
    title: str = ""
    description: str = ""
    category: str = "other"           # 任务分类
    status: str = "pending"           # 任务状态
    priority: int = 3                 # 优先级 1-4
    assignee: str = ""                # 负责人
    creator: str = ""                 # 创建人
    due_date: str = ""               # 截止日期
    completed_at: str = ""            # 完成时间
    related_lead_id: str = ""         # 关联客户ID
    related_approval_id: str = ""     # 关联审批ID
    tags: List[str] = field(default_factory=list)  # 标签
    subtasks: List[str] = field(default_factory=list)  # 子任务ID列表
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:12]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> Task:
        return Task(**data)

    @property
    def is_overdue(self) -> bool:
        """检查是否过期"""
        if not self.due_date or self.status == "completed":
            return False
        try:
            due = datetime.fromisoformat(self.due_date)
            return datetime.now() > due
        except:
            return False


@dataclass
class SubTask:
    """子任务"""
    id: str = ""
    title: str = ""
    status: str = "pending"
    created_at: str = ""
    completed_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.created_at:
            self.created_at = now

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Approval:
    """审批"""
    id: str = ""
    title: str = ""
    description: str = ""
    type: str = "custom"              # 审批类型
    status: str = "pending"           # 审批状态
    requester: str = ""               # 申请人
    approver: str = ""                # 审批人
    amount: float = 0.0              # 关联金额
    related_lead_id: str = ""         # 关联客户ID
    decision: str = ""                # 审批意见
    decided_at: str = ""              # 审批时间
    due_date: str = ""                # 审批截止日期
    attachments: List[str] = field(default_factory=list)  # 附件
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:12]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> Approval:
        return Approval(**data)

    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        if not self.due_date or self.status != "pending":
            return False
        try:
            due = datetime.fromisoformat(self.due_date)
            return datetime.now() > due
        except:
            return False


@dataclass
class ApprovalRule:
    """审批规则"""
    id: str = ""
    name: str = ""
    type: str = "custom"              # 审批类型
    threshold: float = 0.0           # 触发阈值
    approver_role: str = ""           # 审批人角色
    auto_approve: bool = False        # 是否自动通过
    conditions: Dict = field(default_factory=dict)  # 条件
    enabled: bool = True
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.created_at:
            self.created_at = now

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Notification:
    """通知"""
    id: str = ""
    type: str = ""                    # 通知类型
    title: str = ""
    message: str = ""
    recipient: str = ""               # 接收人
    related_type: str = ""           # 关联类型（task/approval）
    related_id: str = ""             # 关联ID
    is_read: bool = False
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:12]
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> Notification:
        return Notification(**data)


# ── 任务管理器 ────────────────────────────────────────

class TaskManager:
    """任务管理器"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_tasks_kernel
        self.db = get_tasks_kernel(storage_dir)

    # ── 任务 CRUD ──────────────────────────────────────

    def create_task(self, title: str, description: str = "",
                   category: str = "other", priority: int = 3,
                   assignee: str = "", creator: str = "",
                   due_date: str = "", related_lead_id: str = "",
                   tags: Optional[List[str]] = None) -> Task:
        """创建任务"""
        task = Task(
            title=title,
            description=description,
            category=category,
            priority=priority,
            assignee=assignee,
            creator=creator or assignee,
            due_date=due_date,
            related_lead_id=related_lead_id,
            tags=tags or []
        )
        tasks = self.db.get_tasks()
        tasks.append(task.to_dict())
        self.db.save_tasks(tasks)
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        tasks = self.db.get_tasks()
        for data in tasks:
            if data["id"] == task_id:
                return Task.from_dict(data)
        return None

    def get_tasks(self, status: Optional[str] = None,
                  assignee: Optional[str] = None,
                  category: Optional[str] = None,
                  related_lead_id: Optional[str] = None) -> List[Task]:
        """获取任务列表"""
        tasks = [Task.from_dict(d) for d in self.db.get_tasks()]

        if status:
            if status == "overdue":
                tasks = [t for t in tasks if t.is_overdue]
            else:
                tasks = [t for t in tasks if t.status == status]

        if assignee:
            tasks = [t for t in tasks if t.assignee == assignee]

        if category:
            tasks = [t for t in tasks if t.category == category]

        if related_lead_id:
            tasks = [t for t in tasks if t.related_lead_id == related_lead_id]

        # 排序：优先级升序 + 创建时间降序
        tasks.sort(key=lambda x: (x.priority, -datetime.fromisoformat(x.created_at).timestamp()
                                  if x.created_at else 0))
        return tasks

    def update_task(self, task: Task) -> bool:
        """更新任务"""
        task.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tasks = self.db.get_tasks()
        for i, data in enumerate(tasks):
            if data["id"] == task.id:
                tasks[i] = task.to_dict()
                self.db.save_tasks(tasks)
                return True
        return False

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        tasks = self.db.get_tasks()
        for i, data in enumerate(tasks):
            if data["id"] == task_id:
                del tasks[i]
                self.db.save_tasks(tasks)
                return True
        return False

    def complete_task(self, task_id: str) -> bool:
        """完成任务"""
        task = self.get_task(task_id)
        if not task:
            return False
        task.status = "completed"
        task.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.update_task(task)

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.get_task(task_id)
        if not task:
            return False
        task.status = "cancelled"
        return self.update_task(task)

    # ── 任务统计 ──────────────────────────────────────

    def get_stats(self, assignee: Optional[str] = None) -> Dict:
        """获取任务统计"""
        tasks = self.get_tasks(assignee=assignee)

        total = len(tasks)
        pending = len([t for t in tasks if t.status == "pending"])
        in_progress = len([t for t in tasks if t.status == "in_progress"])
        completed = len([t for t in tasks if t.status == "completed"])
        overdue = len([t for t in tasks if t.is_overdue])

        by_priority = {
            "urgent": len([t for t in tasks if t.priority == 1]),
            "high": len([t for t in tasks if t.priority == 2]),
            "medium": len([t for t in tasks if t.priority == 3]),
            "low": len([t for t in tasks if t.priority == 4]),
        }

        by_category = {}
        for task in tasks:
            by_category[task.category] = by_category.get(task.category, 0) + 1

        return {
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "overdue": overdue,
            "by_priority": by_priority,
            "by_category": by_category,
        }

    # ── 子任务 ──────────────────────────────────────

    def add_subtask(self, task_id: str, title: str) -> Optional[SubTask]:
        """添加子任务"""
        task = self.get_task(task_id)
        if not task:
            return None
        subtask = SubTask(title=title)
        task.subtasks.append(subtask.id)
        self.update_task(task)
        # 保存子任务
        subtasks = self.db.get_subtasks()
        subtasks.append(subtask.to_dict())
        self.db.save_subtasks(subtasks)
        return subtask

    def get_subtasks(self, task_id: str) -> List[SubTask]:
        """获取子任务列表"""
        task = self.get_task(task_id)
        if not task:
            return []
        all_subtasks = self.db.get_subtasks()
        return [SubTask.from_dict(s) for s in all_subtasks if s["id"] in task.subtasks]

    def complete_subtask(self, task_id: str, subtask_id: str) -> bool:
        """完成子任务"""
        subtasks = self.db.get_subtasks()
        for i, data in enumerate(subtasks):
            if data["id"] == subtask_id:
                subtasks[i]["status"] = "completed"
                subtasks[i]["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.db.save_subtasks(subtasks)

                # 检查是否所有子任务都完成
                task = self.get_task(task_id)
                if task:
                    all_done = all(
                        s.status == "completed"
                        for s in self.get_subtasks(task_id)
                    )
                    if all_done and task.subtasks:
                        self.complete_task(task_id)
                return True
        return False

    # ── 任务提醒 ──────────────────────────────────────

    def get_due_soon_tasks(self, hours: int = 24,
                          assignee: Optional[str] = None) -> List[Task]:
        """获取即将到期的任务"""
        tasks = self.get_tasks(status="pending", assignee=assignee)
        soon = []

        for task in tasks:
            if not task.due_date:
                continue
            try:
                due = datetime.fromisoformat(task.due_date)
                now = datetime.now()
                delta = due - now
                if 0 <= delta.total_seconds() <= hours * 3600:
                    soon.append(task)
            except:
                continue

        return soon

    def get_overdue_tasks(self, assignee: Optional[str] = None) -> List[Task]:
        """获取过期任务"""
        return self.get_tasks(assignee=assignee)


# ── 审批管理器 ────────────────────────────────────────

class ApprovalManager:
    """审批管理器"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_approval_kernel
        self.db = get_approval_kernel(storage_dir)
        self._init_default_rules()

    def _init_default_rules(self) -> None:
        """初始化默认审批规则"""
        rules = self.get_rules()
        if not rules:
            default_rules = [
                ApprovalRule(
                    name="小额报价自动审批",
                    type="quote",
                    threshold=10000,
                    approver_role="manager",
                    auto_approve=True
                ),
                ApprovalRule(
                    name="大额报价主管审批",
                    type="quote",
                    threshold=50000,
                    approver_role="director",
                    auto_approve=False
                ),
                ApprovalRule(
                    name="高折扣需总监审批",
                    type="discount",
                    threshold=0.2,
                    approver_role="director",
                    auto_approve=False
                ),
                ApprovalRule(
                    name="大额付款需审批",
                    type="payment",
                    threshold=100000,
                    approver_role="finance",
                    auto_approve=False
                ),
            ]
            for rule in default_rules:
                self.add_rule(rule)

    # ── 审批 CRUD ──────────────────────────────────────

    def request_approval(self, title: str, description: str = "",
                        approval_type: str = "custom",
                        requester: str = "", approver: str = "",
                        amount: float = 0.0, related_lead_id: str = "",
                        due_date: str = "", attachments: Optional[List[str]] = None) -> Approval:
        """发起审批请求"""
        # 检查是否需要自动审批
        rule = self.find_rule(approval_type, amount)
        if rule and rule.auto_approve:
            # 自动审批通过
            approval = Approval(
                title=title,
                description=description,
                type=approval_type,
                requester=requester,
                approver=approver or rule.approver_role,
                amount=amount,
                related_lead_id=related_lead_id,
                due_date=due_date or (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                attachments=attachments or [],
                status="approved",
                decision="自动通过（金额未超阈值）",
                decided_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        else:
            approval = Approval(
                title=title,
                description=description,
                type=approval_type,
                requester=requester,
                approver=approver or (rule.approver_role if rule else ""),
                amount=amount,
                related_lead_id=related_lead_id,
                due_date=due_date or (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                attachments=attachments or []
            )

        approvals = self.db.get_approvals()
        approvals.append(approval.to_dict())
        self.db.save_approvals(approvals)
        return approval

    def get_approval(self, approval_id: str) -> Optional[Approval]:
        """获取审批"""
        approvals = self.db.get_approvals()
        for data in approvals:
            if data["id"] == approval_id:
                return Approval.from_dict(data)
        return None

    def get_approvals(self, status: Optional[str] = None,
                     approval_type: Optional[str] = None,
                     requester: Optional[str] = None,
                     approver: Optional[str] = None) -> List[Approval]:
        """获取审批列表"""
        approvals = [Approval.from_dict(d) for d in self.db.get_approvals()]

        if status:
            if status == "expired":
                approvals = [a for a in approvals if a.is_expired]
            else:
                approvals = [a for a in approvals if a.status == status]

        if approval_type:
            approvals = [a for a in approvals if a.type == approval_type]

        if requester:
            approvals = [a for a in approvals if a.requester == requester]

        if approver:
            approvals = [a for a in approvals if a.approver == approver]

        # 排序：待审批优先 + 创建时间降序
        approvals.sort(
            key=lambda x: (x.status != "pending", -datetime.fromisoformat(x.created_at).timestamp()
                          if x.created_at else 0)
        )
        return approvals

    def approve(self, approval_id: str, approver: str,
                decision: str = "同意") -> bool:
        """审批通过"""
        approval = self.get_approval(approval_id)
        if not approval or approval.status != "pending":
            return False
        approval.status = "approved"
        approval.decision = decision
        approval.approver = approver
        approval.decided_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self._save_approval(approval)

    def reject(self, approval_id: str, approver: str,
              reason: str = "不同意") -> bool:
        """审批拒绝"""
        approval = self.get_approval(approval_id)
        if not approval or approval.status != "pending":
            return False
        approval.status = "rejected"
        approval.decision = reason
        approval.approver = approver
        approval.decided_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self._save_approval(approval)

    def cancel_approval(self, approval_id: str) -> bool:
        """取消审批"""
        approval = self.get_approval(approval_id)
        if not approval:
            return False
        approval.status = "cancelled"
        return self._save_approval(approval)

    def _save_approval(self, approval: Approval) -> bool:
        """保存审批"""
        approval.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        approvals = self.db.get_approvals()
        for i, data in enumerate(approvals):
            if data["id"] == approval.id:
                approvals[i] = approval.to_dict()
                self.db.save_approvals(approvals)
                return True
        return False

    # ── 审批规则 ──────────────────────────────────────

    def find_rule(self, approval_type: str, amount: float) -> Optional[ApprovalRule]:
        """查找匹配的审批规则"""
        rules = self.get_rules()
        for rule in rules:
            if rule.type == approval_type and rule.threshold <= amount and rule.enabled:
                return rule
        return None

    def add_rule(self, rule: ApprovalRule) -> None:
        """添加审批规则"""
        rules = self.db.get_rules()
        rules.append(rule.to_dict())
        self.db.save_rules(rules)

    def get_rules(self) -> List[ApprovalRule]:
        """获取所有审批规则"""
        return [ApprovalRule(**d) for d in self.db.get_rules()]

    def update_rule(self, rule: ApprovalRule) -> bool:
        """更新审批规则"""
        rules = self.db.get_rules()
        for i, data in enumerate(rules):
            if data["id"] == rule.id:
                rules[i] = rule.to_dict()
                self.db.save_rules(rules)
                return True
        return False

    def delete_rule(self, rule_id: str) -> bool:
        """删除审批规则"""
        rules = self.db.get_rules()
        for i, data in enumerate(rules):
            if data["id"] == rule_id:
                del rules[i]
                self.db.save_rules(rules)
                return True
        return False

    # ── 审批统计 ──────────────────────────────────────

    def get_stats(self, requester: Optional[str] = None,
                 approver: Optional[str] = None) -> Dict:
        """获取审批统计"""
        approvals = self.get_approvals(requester=requester, approver=approver)

        total = len(approvals)
        pending = len([a for a in approvals if a.status == "pending"])
        approved = len([a for a in approvals if a.status == "approved"])
        rejected = len([a for a in approvals if a.status == "rejected"])
        expired = len([a for a in approvals if a.is_expired])

        total_amount = sum(a.amount for a in approvals if a.status == "approved")
        avg_amount = total_amount / approved if approved > 0 else 0

        by_type = {}
        for a in approvals:
            by_type[a.type] = by_type.get(a.type, 0) + 1

        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "expired": expired,
            "total_amount": total_amount,
            "avg_amount": avg_amount,
            "by_type": by_type,
        }


# ── 通知管理器 ────────────────────────────────────────

class NotificationManager:
    """通知管理器"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_notification_kernel
        self.db = get_notification_kernel(storage_dir)

    def create_notification(self, notification_type: str,
                          title: str, message: str,
                          recipient: str,
                          related_type: str = "",
                          related_id: str = "") -> Notification:
        """创建通知"""
        notif = Notification(
            type=notification_type,
            title=title,
            message=message,
            recipient=recipient,
            related_type=related_type,
            related_id=related_id
        )
        notifs = self.db.get_notifications()
        notifs.append(notif.to_dict())
        self.db.save_notifications(notifs)
        return notif

    def get_notifications(self, recipient: str,
                         is_read: Optional[bool] = None) -> List[Notification]:
        """获取通知列表"""
        notifs = [Notification.from_dict(d) for d in self.db.get_notifications()
                 if d["recipient"] == recipient]

        if is_read is not None:
            notifs = [n for n in notifs if n.is_read == is_read]

        # 排序：未读优先 + 创建时间降序
        notifs.sort(key=lambda x: (x.is_read, -datetime.fromisoformat(x.created_at).timestamp()
                                   if x.created_at else 0))
        return notifs

    def mark_as_read(self, notification_id: str) -> bool:
        """标记为已读"""
        notifs = self.db.get_notifications()
        for i, data in enumerate(notifs):
            if data["id"] == notification_id:
                notifs[i]["is_read"] = True
                self.db.save_notifications(notifs)
                return True
        return False

    def mark_all_as_read(self, recipient: str) -> int:
        """标记全部为已读"""
        notifs = self.db.get_notifications()
        count = 0
        for i, data in enumerate(notifs):
            if data["recipient"] == recipient and not data["is_read"]:
                notifs[i]["is_read"] = True
                count += 1
        if count > 0:
            self.db.save_notifications(notifs)
        return count

    def delete_notification(self, notification_id: str) -> bool:
        """删除通知"""
        notifs = self.db.get_notifications()
        for i, data in enumerate(notifs):
            if data["id"] == notification_id:
                del notifs[i]
                self.db.save_notifications(notifs)
                return True
        return False

    def get_unread_count(self, recipient: str) -> int:
        """获取未读数量"""
        return len([n for n in self.get_notifications(recipient) if not n.is_read])


# ── 工厂函数 ────────────────────────────────────────

def get_task_manager(storage_dir: Optional[str] = None) -> TaskManager:
    """获取任务管理器实例"""
    return TaskManager(storage_dir)


def get_approval_manager(storage_dir: Optional[str] = None) -> ApprovalManager:
    """获取审批管理器实例"""
    return ApprovalManager(storage_dir)


def get_notification_manager(storage_dir: Optional[str] = None) -> NotificationManager:
    """获取通知管理器实例"""
    return NotificationManager(storage_dir)
