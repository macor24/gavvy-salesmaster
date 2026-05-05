"""tianlong_salesmaster.core.workflow — 事件驱动流程引擎

核心能力：
- 事件定义与发布订阅
- 流程状态机
- 工作流引擎
- 异步任务队列
- 流程可视化

典型流程：
报价单生成 → LLM生成内容 → 发送邮件/短信通知 → 客户签署合同 → 发起支付 → 支付成功 → CRM更新
"""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型"""

    QUOTE_CREATED = "quote.created"
    QUOTE_SENT = "quote.sent"
    QUOTE_APPROVED = "quote.approved"
    QUOTE_REJECTED = "quote.rejected"

    CONTRACT_CREATED = "contract.created"
    CONTRACT_SENT = "contract.sent"
    CONTRACT_SIGNED = "contract.signed"
    CONTRACT_COMPLETED = "contract.completed"

    PAYMENT_CREATED = "payment.created"
    PAYMENT_PENDING = "payment.pending"
    PAYMENT_SUCCEEDED = "payment.succeeded"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"

    LEAD_CREATED = "lead.created"
    LEAD_UPDATED = "lead.updated"
    LEAD_ASSIGNED = "lead.assigned"
    LEAD_CONVERTED = "lead.converted"

    MESSAGE_SENT = "message.sent"
    MESSAGE_DELIVERED = "message.delivered"
    MESSAGE_FAILED = "message.failed"

    TASK_CREATED = "task.created"
    TASK_COMPLETED = "task.completed"
    TASK_APPROVED = "task.approved"

    LLM_RESPONSE = "llm.response"
    WORKFLOW_STEP = "workflow.step"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"

    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"


class FlowStatus(Enum):
    """流程状态"""
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING = "waiting"


@dataclass
class WorkflowEvent:
    """工作流事件"""
    id: str = ""
    type: str = ""
    source: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    correlation_id: str = ""
    causation_id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class WorkflowStep:
    """工作流步骤"""
    id: str = ""
    name: str = ""
    description: str = ""
    action: str = ""
    handler: Optional[Callable] = None
    timeout: int = 300
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: int = 5
    status: str = StepStatus.PENDING.value
    result: Optional[Dict] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

    @property
    def is_completed(self) -> bool:
        return self.status == StepStatus.COMPLETED.value

    @property
    def is_failed(self) -> bool:
        return self.status == StepStatus.FAILED.value


@dataclass
class Workflow:
    """工作流定义"""
    id: str = ""
    name: str = ""
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    status: str = FlowStatus.PENDING.value
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    current_step_index: int = 0
    error: Optional[str] = None

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    @property
    def current_step(self) -> Optional[WorkflowStep]:
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    @property
    def is_completed(self) -> bool:
        return self.status == FlowStatus.COMPLETED.value

    @property
    def is_failed(self) -> bool:
        return self.status == FlowStatus.FAILED.value


@dataclass
class WorkflowTemplate:
    """工作流模板"""
    id: str = ""
    name: str = ""
    description: str = ""
    trigger_event: str = ""
    steps: List[Dict[str, Any]] = field(default_factory=list)
    is_active: bool = True

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


class EventBus:
    """事件总线（发布订阅）"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._subscribers: Dict[str, List[Callable]] = {}
        self._wildcard_subscribers: List[Callable] = []
        self._event_history: List[WorkflowEvent] = []
        self._max_history: int = 1000
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """订阅事件"""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(handler)

    def subscribe_wildcard(self, handler: Callable) -> None:
        """订阅所有事件"""
        with self._lock:
            self._wildcard_subscribers.append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """取消订阅"""
        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(handler)
                except ValueError:
                    pass

    def publish(self, event: WorkflowEvent) -> None:
        """发布事件"""
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history:]

        handlers = self._subscribers.get(event.type, [])

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error for {event.type}: {e}")

        for handler in self._wildcard_subscribers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Wildcard event handler error: {e}")

    def get_history(
        self,
        event_type: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[WorkflowEvent]:
        """获取事件历史"""
        with self._lock:
            events = self._event_history.copy()

        if event_type:
            events = [e for e in events if e.type == event_type]
        if since:
            events = [e for e in events if datetime.fromisoformat(e.timestamp) >= since]

        return events[-limit:]

    def clear_history(self) -> None:
        """清空历史"""
        with self._lock:
            self._event_history.clear()


_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
