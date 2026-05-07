"""gavvy_salesmaster.core.workflow.listeners — 工作流事件监听器

监听各种事件并触发相应的工作流：
- 报价单事件 → 合同签署
- 合同签署事件 → 支付收款
- 支付成功事件 → CRM更新
- 线索事件 → 培育流程
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional

from . import EventType, WorkflowEvent, get_event_bus, EventBus

logger = logging.getLogger(__name__)


class WorkflowListener:
    """工作流事件监听器"""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self._event_bus = event_bus or get_event_bus()
        self._handlers: Dict[str, Callable] = {}
        self._setup_default_listeners()

    def _setup_default_listeners(self) -> None:
        """设置默认监听器"""
        self._event_bus.subscribe(EventType.QUOTE_APPROVED.value, self._on_quote_approved)
        self._event_bus.subscribe(EventType.CONTRACT_COMPLETED.value, self._on_contract_completed)
        self._event_bus.subscribe(EventType.PAYMENT_SUCCEEDED.value, self._on_payment_succeeded)
        self._event_bus.subscribe(EventType.LEAD_CREATED.value, self._on_lead_created)
        self._event_bus.subscribe(EventType.SIGN_FLOW_COMPLETED.value, self._on_sign_completed)

    def register(self, event_type: str, handler: Callable) -> None:
        """注册事件处理器"""
        self._handlers[event_type] = handler

    def _on_quote_approved(self, event: WorkflowEvent) -> None:
        """报价单审批通过"""
        logger.info(f"Quote approved: {event.data}")

        workflow_engine = self._get_workflow_engine()
        if workflow_engine:
            context = {
                "quote_id": event.data.get("quote_id", ""),
                "quote_title": event.data.get("title", "合同"),
                "amount": event.data.get("amount", 0),
                "customer_id": event.data.get("customer_id", ""),
                "signers": event.data.get("signers", []),
            }
            workflow_engine.start_workflow("quote_to_contract", context=context)

    def _on_contract_completed(self, event: WorkflowEvent) -> None:
        """合同签署完成"""
        logger.info(f"Contract completed: {event.data}")

        workflow_engine = self._get_workflow_engine()
        if workflow_engine:
            context = {
                "contract_id": event.data.get("contract_id", ""),
                "title": event.data.get("title", ""),
                "amount": event.data.get("amount", 0),
                "customer_id": event.data.get("customer_id", ""),
            }
            workflow_engine.start_workflow("contract_to_payment", context=context)

    def _on_payment_succeeded(self, event: WorkflowEvent) -> None:
        """支付成功"""
        logger.info(f"Payment succeeded: {event.data}")

        self._notify_customer(event.data)
        self._update_crm_deal(event.data)

    def _on_lead_created(self, event: WorkflowEvent) -> None:
        """新线索创建"""
        logger.info(f"Lead created: {event.data}")

        workflow_engine = self._get_workflow_engine()
        if workflow_engine:
            context = {
                "lead_id": event.data.get("lead_id", ""),
                "name": event.data.get("name", ""),
                "company": event.data.get("company", ""),
                "phone": event.data.get("phone", ""),
                "email": event.data.get("email", ""),
            }
            workflow_engine.start_workflow("lead_qualification", context=context)

    def _on_sign_completed(self, event: WorkflowEvent) -> None:
        """签署完成（来自webhook）"""
        logger.info(f"Sign completed: {event.data}")

        workflow_engine = self._get_workflow_engine()
        if workflow_engine:
            context = {
                "flow_id": event.data.get("flow_id", ""),
                "contract_id": event.data.get("contract_id", ""),
            }

    def _notify_customer(self, data: Dict[str, Any]) -> None:
        """通知客户"""
        message_gateway = self._get_message_gateway()
        if message_gateway:
            try:
                message_gateway.send(
                    channel="email",
                    to=data.get("customer_email", ""),
                    template="payment_success",
                    data={
                        "order_no": data.get("order_no", ""),
                        "amount": data.get("amount", 0),
                    },
                )
            except Exception as e:
                logger.error(f"Failed to notify customer: {e}")

    def _update_crm_deal(self, data: Dict[str, Any]) -> None:
        """更新CRM交易"""
        crm = self._get_crm_manager()
        if crm:
            try:
                crm.update_deal_status(
                    deal_id=data.get("deal_id", ""),
                    status="paid",
                    payment_info=data,
                )
            except Exception as e:
                logger.error(f"Failed to update CRM deal: {e}")

    def _get_workflow_engine(self):
        """获取工作流引擎"""
        try:
            from .engine import get_workflow_engine
            return get_workflow_engine()
        except Exception:
            return None

    def _get_message_gateway(self):
        """获取消息网关"""
        try:
            from ..channels import get_message_gateway
            return get_message_gateway()
        except Exception:
            return None

    def _get_crm_manager(self):
        """获取CRM管理器"""
        try:
            from ..crm import get_crm_manager
            return get_crm_manager()
        except Exception:
            return None


_listener: Optional[WorkflowListener] = None


def get_workflow_listener() -> WorkflowListener:
    global _listener
    if _listener is None:
        _listener = WorkflowListener()
    return _listener
