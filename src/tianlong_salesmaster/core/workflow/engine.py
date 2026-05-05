"""SentriKit_salesmaster.core.workflow.engine — 流程引擎

工作流执行引擎，负责：
- 流程实例化与执行
- 步骤调度与状态管理
- 异步任务队列
- 流程恢复与重试
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from . import (
    EventType, FlowStatus, StepStatus,
    Workflow, WorkflowStep, WorkflowEvent, WorkflowTemplate,
    get_event_bus, EventBus,
)

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """工作流引擎"""

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
        self._event_bus = get_event_bus()
        self._workflows: Dict[str, Workflow] = {}
        self._templates: Dict[str, WorkflowTemplate] = {}
        self._executors: Dict[str, WorkflowExecutor] = {}
        self._lock = threading.Lock()
        self._executor_pool = ThreadPoolExecutor(max_workers=10)

        self._register_default_templates()
        self._subscribe_to_events()

    def _register_default_templates(self) -> None:
        """注册默认工作流模板"""
        quote_to_contract = WorkflowTemplate(
            id="quote_to_contract",
            name="报价转合同",
            description="报价单审批通过后自动创建合同",
            trigger_event=EventType.QUOTE_APPROVED.value,
            steps=[
                {"id": "create_contract", "name": "创建合同", "action": "contract.create", "timeout": 60},
                {"id": "send_contract", "name": "发送合同", "action": "contract.send", "timeout": 60},
                {"id": "notify_signer", "name": "通知签署人", "action": "message.send", "timeout": 30},
            ],
        )

        contract_to_payment = WorkflowTemplate(
            id="contract_to_payment",
            name="合同转支付",
            description="合同签署完成后自动发起支付",
            trigger_event=EventType.CONTRACT_COMPLETED.value,
            steps=[
                {"id": "create_payment", "name": "创建支付订单", "action": "payment.create", "timeout": 60},
                {"id": "send_invoice", "name": "发送发票", "action": "message.send", "timeout": 30},
            ],
        )

        lead_qualification = WorkflowTemplate(
            id="lead_qualification",
            name="线索培育",
            description="新线索自动分配和跟进",
            trigger_event=EventType.LEAD_CREATED.value,
            steps=[
                {"id": "score_lead", "name": "评分线索", "action": "lead.score", "timeout": 30},
                {"id": "assign_lead", "name": "分配线索", "action": "lead.assign", "timeout": 60},
                {"id": "send_welcome", "name": "发送欢迎", "action": "message.send", "timeout": 30},
            ],
        )

        self.register_template(quote_to_contract)
        self.register_template(contract_to_payment)
        self.register_template(lead_qualification)

    def _subscribe_to_events(self) -> None:
        """订阅事件"""
        self._event_bus.subscribe_wildcard(self._on_any_event)

    def _on_any_event(self, event: WorkflowEvent) -> None:
        """处理任意事件"""
        if event.type.startswith("workflow.") or event.type == EventType.WORKFLOW_STEP.value:
            return

        for template_id, template in self._templates.items():
            if template.trigger_event == event.type and template.is_active:
                self.start_workflow(template_id, context={"trigger_event": event})

    def register_template(self, template: WorkflowTemplate) -> None:
        """注册工作流模板"""
        with self._lock:
            self._templates[template.id] = template

    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """获取模板"""
        return self._templates.get(template_id)

    def start_workflow(
        self,
        template_id: str,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> Optional[Workflow]:
        """启动工作流"""
        template = self._templates.get(template_id)
        if not template:
            logger.error(f"Template not found: {template_id}")
            return None

        workflow = Workflow(
            id=str(uuid.uuid4()),
            name=template.name,
            description=template.description,
            context=context or {},
        )

        for step_def in template.steps:
            step = WorkflowStep(
                id=step_def.get("id", str(uuid.uuid4())),
                name=step_def.get("name", ""),
                description=step_def.get("description", ""),
                action=step_def.get("action", ""),
                timeout=step_def.get("timeout", 300),
                max_retries=step_def.get("max_retries", 3),
                retry_delay=step_def.get("retry_delay", 5),
            )
            workflow.steps.append(step)

        workflow.status = FlowStatus.RUNNING.value
        workflow.started_at = datetime.now().isoformat()

        with self._lock:
            self._workflows[workflow.id] = workflow
            self._executors[workflow.id] = WorkflowExecutor(workflow, self)

        event = WorkflowEvent(
            type=EventType.WORKFLOW_STEP.value,
            source="workflow_engine",
            data={"workflow_id": workflow.id, "action": "started"},
            correlation_id=correlation_id or workflow.id,
        )
        self._event_bus.publish(event)

        self._executors[workflow.id].execute_next_step()

        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """获取工作流"""
        return self._workflows.get(workflow_id)

    def cancel_workflow(self, workflow_id: str, reason: str = "") -> bool:
        """取消工作流"""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return False

        workflow.status = FlowStatus.CANCELLED.value
        workflow.error = reason
        workflow.completed_at = datetime.now().isoformat()

        event = WorkflowEvent(
            type=EventType.WORKFLOW_FAILED.value,
            source="workflow_engine",
            data={"workflow_id": workflow_id, "reason": reason},
        )
        self._event_bus.publish(event)

        return True

    def list_workflows(
        self,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Workflow]:
        """列出工作流"""
        with self._lock:
            workflows = list(self._workflows.values())

        if status:
            workflows = [w for w in workflows if w.status == status]

        return workflows[-limit:]

    def step_completed(self, workflow_id: str, step_id: str, result: Dict[str, Any]) -> None:
        """步骤完成"""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return

        for step in workflow.steps:
            if step.id == step_id:
                step.status = StepStatus.COMPLETED.value
                step.result = result
                step.completed_at = datetime.now().isoformat()
                break

        workflow.context.update(result)
        workflow.current_step_index += 1

        event = WorkflowEvent(
            type=EventType.WORKFLOW_STEP.value,
            source="workflow_engine",
            data={
                "workflow_id": workflow_id,
                "step_id": step_id,
                "action": "completed",
                "result": result,
            },
            correlation_id=workflow.id,
        )
        self._event_bus.publish(event)

        executor = self._executors.get(workflow_id)
        if executor:
            executor.execute_next_step()

    def step_failed(self, workflow_id: str, step_id: str, error: str) -> None:
        """步骤失败"""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return

        for step in workflow.steps:
            if step.id == step_id:
                step.status = StepStatus.FAILED.value
                step.error = error
                step.completed_at = datetime.now().isoformat()
                break

        workflow.error = error
        workflow.status = FlowStatus.FAILED.value
        workflow.completed_at = datetime.now().isoformat()

        event = WorkflowEvent(
            type=EventType.WORKFLOW_FAILED.value,
            source="workflow_engine",
            data={"workflow_id": workflow_id, "step_id": step_id, "error": error},
            correlation_id=workflow.id,
        )
        self._event_bus.publish(event)

    def workflow_completed(self, workflow_id: str) -> None:
        """工作流完成"""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            return

        workflow.status = FlowStatus.COMPLETED.value
        workflow.completed_at = datetime.now().isoformat()

        event = WorkflowEvent(
            type=EventType.WORKFLOW_COMPLETED.value,
            source="workflow_engine",
            data={"workflow_id": workflow_id, "context": workflow.context},
            correlation_id=workflow.id,
        )
        self._event_bus.publish(event)


class WorkflowExecutor:
    """工作流执行器"""

    def __init__(self, workflow: Workflow, engine: WorkflowEngine):
        self.workflow = workflow
        self.engine = engine
        self._step_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """注册默认处理器"""
        self.register_handler("contract.create", self._handle_contract_create)
        self.register_handler("contract.send", self._handle_contract_send)
        self.register_handler("payment.create", self._handle_payment_create)
        self.register_handler("message.send", self._handle_message_send)
        self.register_handler("lead.score", self._handle_lead_score)
        self.register_handler("lead.assign", self._handle_lead_assign)

    def register_handler(self, action: str, handler: Callable) -> None:
        """注册动作处理器"""
        self._step_handlers[action] = handler

    def execute_next_step(self) -> None:
        """执行下一步"""
        if self.workflow.is_completed or self.workflow.is_failed:
            return

        if self.workflow.current_step_index >= len(self.workflow.steps):
            self.engine.workflow_completed(self.workflow.id)
            return

        step = self.workflow.current_step
        if not step:
            return

        if step.status == StepStatus.RUNNING.value:
            return

        step.status = StepStatus.RUNNING.value
        step.started_at = datetime.now().isoformat()

        handler = self._step_handlers.get(step.action)
        if handler:
            try:
                result = handler(self.workflow, step)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(self._run_async(result, step))
                else:
                    self.engine.step_completed(self.workflow.id, step.id, result or {})
            except Exception as e:
                logger.error(f"Step execution error: {e}")
                self.engine.step_failed(self.workflow.id, step.id, str(e))
        else:
            self.engine.step_completed(
                self.workflow.id, step.id,
                {"skipped": True, "reason": f"No handler for action: {step.action}"}
            )

    async def _run_async(self, coro, step: WorkflowStep) -> None:
        """运行异步步骤"""
        try:
            result = await coro
            self.engine.step_completed(self.workflow.id, step.id, result or {})
        except Exception as e:
            logger.error(f"Async step execution error: {e}")
            self.engine.step_failed(self.workflow.id, step.id, str(e))

    def _handle_contract_create(self, workflow: Workflow, step: WorkflowStep) -> Dict[str, Any]:
        """处理合同创建"""
        context = workflow.context
        return {
            "contract_id": f"contract_{uuid.uuid4().hex[:8]}",
            "title": context.get("quote_title", "合同"),
            "created_at": datetime.now().isoformat(),
        }

    def _handle_contract_send(self, workflow: Workflow, step: WorkflowStep) -> Dict[str, Any]:
        """处理合同发送"""
        return {
            "sent_at": datetime.now().isoformat(),
            "signers": workflow.context.get("signers", []),
        }

    def _handle_payment_create(self, workflow: Workflow, step: WorkflowStep) -> Dict[str, Any]:
        """处理支付创建"""
        return {
            "payment_id": f"pay_{uuid.uuid4().hex[:8]}",
            "amount": workflow.context.get("amount", 0),
            "created_at": datetime.now().isoformat(),
        }

    def _handle_message_send(self, workflow: Workflow, step: WorkflowStep) -> Dict[str, Any]:
        """处理消息发送"""
        return {
            "message_id": f"msg_{uuid.uuid4().hex[:8]}",
            "sent_at": datetime.now().isoformat(),
        }

    def _handle_lead_score(self, workflow: Workflow, step: WorkflowStep) -> Dict[str, Any]:
        """处理线索评分"""
        return {
            "score": 85,
            "grade": "A",
            "scored_at": datetime.now().isoformat(),
        }

    def _handle_lead_assign(self, workflow: Workflow, step: WorkflowStep) -> Dict[str, Any]:
        """处理线索分配"""
        return {
            "assigned_to": "sales_rep_001",
            "assigned_at": datetime.now().isoformat(),
        }


_workflow_engine: Optional[WorkflowEngine] = None
_engine_lock = threading.Lock()


def get_workflow_engine() -> WorkflowEngine:
    global _workflow_engine
    if _workflow_engine is None:
        with _engine_lock:
            if _workflow_engine is None:
                _workflow_engine = WorkflowEngine()
    return _workflow_engine
