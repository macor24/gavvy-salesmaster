"""tianlong_salesmaster.crm_pkg.tasks.db — 任务与审批存储接口

封装对数据库的访问，提供统一的存储接口。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class TasksStorage:
    """任务存储接口"""

    def __init__(self, kernel):
        self._kernel = kernel

    def get_tasks(self) -> List[Dict]:
        """获取所有任务"""
        return self._kernel.get("tasks_items") or []

    def save_tasks(self, tasks: List[Dict]) -> None:
        """保存任务列表"""
        self._kernel.write("tasks_items", tasks)

    def get_subtasks(self) -> List[Dict]:
        """获取所有子任务"""
        return self._kernel.get("tasks_subtasks") or []

    def save_subtasks(self, subtasks: List[Dict]) -> None:
        """保存子任务列表"""
        self._kernel.write("tasks_subtasks", subtasks)


class ApprovalStorage:
    """审批存储接口"""

    def __init__(self, kernel):
        self._kernel = kernel

    def get_approvals(self) -> List[Dict]:
        """获取所有审批"""
        return self._kernel.get("approvals_items") or []

    def save_approvals(self, approvals: List[Dict]) -> None:
        """保存审批列表"""
        self._kernel.write("approvals_items", approvals)

    def get_rules(self) -> List[Dict]:
        """获取所有审批规则"""
        return self._kernel.get("approval_rules") or []

    def save_rules(self, rules: List[Dict]) -> None:
        """保存审批规则"""
        self._kernel.write("approval_rules", rules)


class NotificationStorage:
    """通知存储接口"""

    def __init__(self, kernel):
        self._kernel = kernel

    def get_notifications(self) -> List[Dict]:
        """获取所有通知"""
        return self._kernel.get("notifications_items") or []

    def save_notifications(self, notifications: List[Dict]) -> None:
        """保存通知列表"""
        self._kernel.write("notifications_items", notifications)


# ── 获取存储实例 ──────────────────────────────────────

_global_tasks_storage: Optional[TasksStorage] = None
_global_approval_storage: Optional[ApprovalStorage] = None
_global_notification_storage: Optional[NotificationStorage] = None


def get_tasks_kernel(storage_dir: Optional[str] = None) -> TasksStorage:
    """获取任务存储内核"""
    global _global_tasks_storage
    if _global_tasks_storage is None:
        from tianlong_salesmaster.core.storage.db import get_kernel
        kernel = get_kernel(storage_dir)
        _global_tasks_storage = TasksStorage(kernel)
    return _global_tasks_storage


def get_approval_kernel(storage_dir: Optional[str] = None) -> ApprovalStorage:
    """获取审批存储内核"""
    global _global_approval_storage
    if _global_approval_storage is None:
        from tianlong_salesmaster.core.storage.db import get_kernel
        kernel = get_kernel(storage_dir)
        _global_approval_storage = ApprovalStorage(kernel)
    return _global_approval_storage


def get_notification_kernel(storage_dir: Optional[str] = None) -> NotificationStorage:
    """获取通知存储内核"""
    global _global_notification_storage
    if _global_notification_storage is None:
        from tianlong_salesmaster.core.storage.db import get_kernel
        kernel = get_kernel(storage_dir)
        _global_notification_storage = NotificationStorage(kernel)
    return _global_notification_storage
