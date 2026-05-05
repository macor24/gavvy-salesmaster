"""自动化跟进模块 - 任务自动化"""

import json
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"

class TaskPriority(str, Enum):
    """任务优先级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TaskType(str, Enum):
    """任务类型"""
    CALL = "call"
    MEETING = "meeting"
    EMAIL = "email"
    FOLLOWUP = "followup"
    DEMO = "demo"
    PROPOSAL = "proposal"
    CONTRACT = "contract"
    OTHER = "other"

@dataclass
class Task:
    """任务数据结构"""
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    task_type: TaskType = TaskType.OTHER
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    reminder_time: Optional[datetime] = None
    lead_id: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def is_overdue(self) -> bool:
        """检查是否逾期"""
        if self.status == TaskStatus.COMPLETED or self.status == TaskStatus.CANCELLED:
            return False
        if self.due_date and datetime.now() > self.due_date:
            return True
        return False

class ReminderService:
    """提醒服务"""
    
    def __init__(self):
        self.reminders: Dict[str, Dict] = {}
    
    def schedule_reminder(self, task_id: str, reminder_time: datetime, callback: Callable):
        """调度提醒"""
        self.reminders[task_id] = {
            "time": reminder_time,
            "callback": callback,
            "sent": False
        }
    
    def cancel_reminder(self, task_id: str):
        """取消提醒"""
        if task_id in self.reminders:
            del self.reminders[task_id]
    
    def process_reminders(self):
        """处理待发送提醒"""
        now = datetime.now()
        tasks_to_remove = []
        
        for task_id, reminder in self.reminders.items():
            if not reminder["sent"] and reminder["time"] <= now:
                reminder["callback"]()
                reminder["sent"] = True
                tasks_to_remove.append(task_id)
        
        # 清理已发送的提醒
        for task_id in tasks_to_remove:
            del self.reminders[task_id]

class EscalationRule:
    """升级规则"""
    
    def __init__(self, name: str, condition: Callable, action: Callable, priority: int = 100):
        self.name = name
        self.condition = condition
        self.action = action
        self.priority = priority

class TaskAutomationService:
    """任务自动化服务"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.reminder_service = ReminderService()
        self.escalation_rules: List[EscalationRule] = []
        
        # 初始化默认升级规则
        self._init_default_escalation_rules()
    
    def _init_default_escalation_rules(self):
        """初始化默认升级规则"""
        # 逾期24小时升级给主管
        rule1 = EscalationRule(
            name="逾期24小时升级",
            condition=lambda task: task.is_overdue() and (datetime.now() - task.due_date).days >= 1,
            action=self._escalate_to_manager
        )
        self.escalation_rules.append(rule1)
        
        # 逾期48小时升级给经理
        rule2 = EscalationRule(
            name="逾期48小时升级",
            condition=lambda task: task.is_overdue() and (datetime.now() - task.due_date).days >= 2,
            action=self._escalate_to_director
        )
        self.escalation_rules.append(rule2)
    
    def create_task(self, **kwargs) -> Task:
        """创建任务"""
        task_id = f"task_{datetime.now().timestamp()}"
        task = Task(id=task_id, **kwargs)
        self.tasks[task_id] = task
        
        # 如果设置了提醒时间，调度提醒
        if task.reminder_time:
            self.reminder_service.schedule_reminder(
                task_id,
                task.reminder_time,
                lambda: self._send_reminder(task_id)
            )
        
        print(f"📋 创建任务: {task.title}")
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, **kwargs):
        """更新任务"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            for key, value in kwargs.items():
                setattr(task, key, value)
            task.updated_at = datetime.now()
            
            # 如果任务完成，取消提醒
            if task.status == TaskStatus.COMPLETED:
                self.reminder_service.cancel_reminder(task_id)
            
            print(f"🔄 更新任务: {task.title} -> {task.status.value}")
    
    def delete_task(self, task_id: str):
        """删除任务"""
        if task_id in self.tasks:
            self.reminder_service.cancel_reminder(task_id)
            del self.tasks[task_id]
            print(f"🗑️ 删除任务: {task_id}")
    
    def get_tasks_by_assignee(self, assignee: str) -> List[Task]:
        """按负责人获取任务"""
        return [task for task in self.tasks.values() if task.assignee == assignee]
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """按状态获取任务"""
        return [task for task in self.tasks.values() if task.status == status]
    
    def get_overdue_tasks(self) -> List[Task]:
        """获取逾期任务"""
        return [task for task in self.tasks.values() if task.is_overdue()]
    
    def get_today_tasks(self) -> List[Task]:
        """获取今天的任务"""
        today = datetime.now().date()
        return [task for task in self.tasks.values() 
                if task.due_date and task.due_date.date() == today 
                and task.status != TaskStatus.COMPLETED]
    
    def complete_task(self, task_id: str):
        """完成任务"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.updated_at = datetime.now()
            self.reminder_service.cancel_reminder(task_id)
            print(f"✅ 完成任务: {task.title}")
    
    def _send_reminder(self, task_id: str):
        """发送提醒"""
        task = self.get_task(task_id)
        if task:
            print(f"🔔 任务提醒: [{task.priority.value}] {task.title}")
            if task.assignee:
                print(f"   负责人: {task.assignee}")
            if task.due_date:
                print(f"   截止日期: {task.due_date.strftime('%Y-%m-%d %H:%M')}")
    
    def _escalate_to_manager(self, task: Task):
        """升级给主管"""
        print(f"🚨 任务升级: {task.title} -> 主管")
        # 实际实现中可以发送通知给主管
    
    def _escalate_to_director(self, task: Task):
        """升级给经理"""
        print(f"🚨 任务紧急升级: {task.title} -> 经理")
        # 实际实现中可以发送通知给经理
    
    def process_escalations(self):
        """处理升级规则"""
        for task in self.tasks.values():
            if task.status == TaskStatus.COMPLETED or task.status == TaskStatus.CANCELLED:
                continue
            
            for rule in self.escalation_rules:
                if rule.condition(task):
                    rule.action(task)
    
    def schedule_daily_tasks(self, lead_id: str, assignee: str):
        """自动安排每日任务"""
        # 创建今日跟进任务
        task1 = self.create_task(
            title=f"跟进线索 {lead_id}",
            description="今日跟进线索，了解最新进展",
            task_type=TaskType.FOLLOWUP,
            assignee=assignee,
            due_date=datetime.now() + timedelta(hours=4),
            reminder_time=datetime.now() + timedelta(hours=1),
            lead_id=lead_id,
            priority=TaskPriority.MEDIUM
        )
        
        return task1
    
    def schedule_weekly_report(self, assignee: str):
        """安排周报任务"""
        task = self.create_task(
            title="提交本周工作报告",
            description="总结本周工作内容和下周计划",
            task_type=TaskType.OTHER,
            assignee=assignee,
            due_date=datetime.now() + timedelta(days=(4 - datetime.now().weekday()) % 7),
            priority=TaskPriority.LOW
        )
        return task

# 全局实例
task_automation_service = TaskAutomationService()

def get_task_automation_service() -> TaskAutomationService:
    """获取任务自动化服务实例"""
    return task_automation_service