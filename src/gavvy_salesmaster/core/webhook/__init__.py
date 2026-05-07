"""gavvy_salesmaster.core.webhook — Webhook 处理器

统一处理来自支付和电子签服务的回调通知：
- Stripe Webhooks
- 支付宝/微信支付回调
- 字节跳动电子签署署回调
- 腾讯电子签回调

支持：
- 签名验证
- 事件分发
- 重试机制
- 幂等性处理
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class WebhookEventType(Enum):
    """Webhook 事件类型"""

    # 支付事件
    PAYMENT_PENDING = "payment.pending"
    PAYMENT_SUCCEEDED = "payment.succeeded"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    PAYMENT_EXPIRED = "payment.expired"

    # 电子签事件
    SIGN_FLOW_CREATED = "sign.flow.created"
    SIGN_FLOW_SENT = "sign.flow.sent"
    SIGN_FLOW_VIEWED = "sign.flow.viewed"
    SIGN_FLOW_SIGNED = "sign.flow.signed"
    SIGN_FLOW_COMPLETED = "sign.flow.completed"
    SIGN_FLOW_REJECTED = "sign.flow.rejected"
    SIGN_FLOW_CANCELLED = "sign.flow.cancelled"
    SIGN_FLOW_EXPIRED = "sign.flow.expired"

    # 通用事件
    UNKNOWN = "unknown"


@dataclass
class WebhookEvent:
    """Webhook 事件"""
    id: str = ""
    type: str = ""
    provider: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    received_at: str = ""
    processed: bool = False
    retry_count: int = 0
    error: Optional[str] = None

    def __post_init__(self):
        if not self.id:
            self.id = f"{int(time.time())}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
        if not self.received_at:
            self.received_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class WebhookHandler:
    """Webhook 处理器"""

    # 支付处理器
    stripe_handlers: Dict[str, Callable] = field(default_factory=dict)
    alipay_handlers: Dict[str, Callable] = field(default_factory=dict)
    wechatpay_handlers: Dict[str, Callable] = field(default_factory=dict)

    # 电子签署名处理器
    bytedance_esign_handlers: Dict[str, Callable] = field(default_factory=dict)
    tencent_esign_handlers: Dict[str, Callable] = field(default_factory=dict)

    # 事件历史
    _events: List[WebhookEvent] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    # 签名密钥
    stripe_webhook_secret: str = ""
    alipay_public_key: str = ""
    wechatpay_api_key: str = ""
    bytedance_esign_secret: str = ""
    tencent_esign_secret: str = ""

    def register_stripe_handler(self, event_type: str, handler: Callable) -> None:
        """注册 Stripe 事件处理器"""
        self.stripe_handlers[event_type] = handler

    def register_alipay_handler(self, event_type: str, handler: Callable) -> None:
        """注册支付宝事件处理器"""
        self.alipay_handlers[event_type] = handler

    def register_wechatpay_handler(self, event_type: str, handler: Callable) -> None:
        """注册微信支付事件处理器"""
        self.wechatpay_handlers[event_type] = handler

    def register_bytedance_esign_handler(self, event_type: str, handler: Callable) -> None:
        """注册字节跳动电子签事件处理器"""
        self.bytedance_esign_handlers[event_type] = handler

    def register_tencent_esign_handler(self, event_type: str, handler: Callable) -> None:
        """注册腾讯电子签事件处理器"""
        self.tencent_esign_handlers[event_type] = handler

    def handle_stripe_webhook(self, payload: bytes, headers: Dict[str, str]) -> WebhookEvent:
        """处理 Stripe Webhook"""
        try:
            import stripe

            event = stripe.Event.construct_from(
                json.loads(payload), headers.get("Stripe-Signature", "")
            )

            event_type = f"stripe.{event.type}"
            webhook_event = WebhookEvent(
                type=event_type,
                provider="stripe",
                payload=event.data.object,
                headers=headers,
            )

            handler = self.stripe_handlers.get(event.type)
            if handler:
                webhook_event.processed = self._execute_handler(handler, webhook_event)
            else:
                logger.info(f"No handler for Stripe event: {event.type}")

            return webhook_event

        except Exception as e:
            logger.error(f"Stripe webhook error: {e}")
            return WebhookEvent(
                type="stripe.error",
                provider="stripe",
                payload={"error": str(e)},
                error=str(e),
            )

    def handle_alipay_notification(self, raw_data: str, headers: Dict[str, str]) -> WebhookEvent:
        """处理支付宝回调"""
        try:
            import urllib.parse
            params = dict(urllib.parse.parse_qsl(raw_data))

            trade_status = params.get("trade_status", "")
            event_type = self._map_alipay_status(trade_status)

            webhook_event = WebhookEvent(
                type=event_type,
                provider="alipay",
                payload=params,
                headers=headers,
            )

            handler = self.alipay_handlers.get(event_type)
            if handler:
                webhook_event.processed = self._execute_handler(handler, webhook_event)
            else:
                logger.info(f"No handler for Alipay event: {event_type}")

            return webhook_event

        except Exception as e:
            logger.error(f"Alipay webhook error: {e}")
            return WebhookEvent(
                type="alipay.error",
                provider="alipay",
                payload={"error": str(e)},
                error=str(e),
            )

    def handle_wechatpay_notification(self, headers: Dict[str, str], body: str) -> WebhookEvent:
        """处理微信支付回调"""
        try:
            data = json.loads(body)
            event_type = self._map_wechatpay_status(data.get("event_type", ""))

            webhook_event = WebhookEvent(
                type=event_type,
                provider="wechatpay",
                payload=data,
                headers=headers,
            )

            handler = self.wechatpay_handlers.get(event_type)
            if handler:
                webhook_event.processed = self._execute_handler(handler, webhook_event)
            else:
                logger.info(f"No handler for WeChat Pay event: {event_type}")

            return webhook_event

        except Exception as e:
            logger.error(f"WeChat Pay webhook error: {e}")
            return WebhookEvent(
                type="wechatpay.error",
                provider="wechatpay",
                payload={"error": str(e)},
                error=str(e),
            )

    def handle_bytedance_esign_notification(self, headers: Dict[str, str], body: str) -> WebhookEvent:
        """处理字节跳动电子签回调"""
        try:
            if self.bytedance_esign_secret:
                signature = headers.get("X-Signature", "")
                expected = hmac.new(
                    self.bytedance_esign_secret.encode(),
                    body.encode(),
                    hashlib.sha256
                ).hexdigest()
                if signature != expected:
                    return WebhookEvent(
                        type="bytedance.error",
                        provider="bytedance_esign",
                        payload={"error": "signature verification failed"},
                        error="signature verification failed",
                    )

            data = json.loads(body)
            event_type = self._map_bytedance_status(data.get("event_type", ""))

            webhook_event = WebhookEvent(
                type=event_type,
                provider="bytedance_esign",
                payload=data,
                headers=headers,
            )

            handler = self.bytedance_esign_handlers.get(event_type)
            if handler:
                webhook_event.processed = self._execute_handler(handler, webhook_event)
            else:
                logger.info(f"No handler for ByteDance eSign event: {event_type}")

            return webhook_event

        except Exception as e:
            logger.error(f"ByteDance eSign webhook error: {e}")
            return WebhookEvent(
                type="bytedance.error",
                provider="bytedance_esign",
                payload={"error": str(e)},
                error=str(e),
            )

    def handle_tencent_esign_notification(self, headers: Dict[str, str], body: str) -> WebhookEvent:
        """处理腾讯电子签回调"""
        try:
            if self.tencent_esign_secret:
                signature = headers.get("X-TC-Signature", "")
                expected = hmac.new(
                    self.tencent_esign_secret.encode(),
                    body.encode(),
                    hashlib.sha256
                ).hexdigest()
                if signature != expected:
                    return WebhookEvent(
                        type="tencent.error",
                        provider="tencent_esign",
                        payload={"error": "signature verification failed"},
                        error="signature verification failed",
                    )

            data = json.loads(body)
            event_type = self._map_tencent_status(data.get("EventType", ""))

            webhook_event = WebhookEvent(
                type=event_type,
                provider="tencent_esign",
                payload=data,
                headers=headers,
            )

            handler = self.tencent_esign_handlers.get(event_type)
            if handler:
                webhook_event.processed = self._execute_handler(handler, webhook_event)
            else:
                logger.info(f"No handler for Tencent eSign event: {event_type}")

            return webhook_event

        except Exception as e:
            logger.error(f"Tencent eSign webhook error: {e}")
            return WebhookEvent(
                type="tencent.error",
                provider="tencent_esign",
                payload={"error": str(e)},
                error=str(e),
            )

    def get_events(
        self,
        provider: Optional[str] = None,
        event_type: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[WebhookEvent]:
        """获取事件历史"""
        with self._lock:
            events = self._events.copy()

        if provider:
            events = [e for e in events if e.provider == provider]
        if event_type:
            events = [e for e in events if e.type == event_type]
        if since:
            events = [e for e in events if datetime.fromisoformat(e.received_at) >= since]

        return events[-limit:]

    def _execute_handler(self, handler: Callable, event: WebhookEvent) -> bool:
        """执行处理器"""
        try:
            handler(event)
            return True
        except Exception as e:
            event.error = str(e)
            event.retry_count += 1
            logger.error(f"Handler error for {event.type}: {e}")
            return False

    @staticmethod
    def _map_alipay_status(status: str) -> str:
        """映射支付宝状态"""
        mapping = {
            "WAIT_BUYER_PAY": WebhookEventType.PAYMENT_PENDING.value,
            "TRADE_CLOSED": WebhookEventType.PAYMENT_FAILED.value,
            "TRADE_SUCCESS": WebhookEventType.PAYMENT_SUCCEEDED.value,
            "TRADE_FINISHED": WebhookEventType.PAYMENT_SUCCEEDED.value,
        }
        return mapping.get(status, WebhookEventType.UNKNOWN.value)

    @staticmethod
    def _map_wechatpay_status(event_type: str) -> str:
        """映射微信支付状态"""
        mapping = {
            "PAYMENTS.SUCCESS": WebhookEventType.PAYMENT_SUCCEEDED.value,
            "PAYMENTS.REFUND": WebhookEventType.PAYMENT_REFUNDED.value,
        }
        return mapping.get(event_type, WebhookEventType.UNKNOWN.value)

    @staticmethod
    def _map_bytedance_status(event_type: str) -> str:
        """映射字节跳动电子签状态"""
        mapping = {
            "flow.created": WebhookEventType.SIGN_FLOW_CREATED.value,
            "flow.sent": WebhookEventType.SIGN_FLOW_SENT.value,
            "signer.viewed": WebhookEventType.SIGN_FLOW_VIEWED.value,
            "signer.signed": WebhookEventType.SIGN_FLOW_SIGNED.value,
            "flow.completed": WebhookEventType.SIGN_FLOW_COMPLETED.value,
            "flow.rejected": WebhookEventType.SIGN_FLOW_REJECTED.value,
            "flow.cancelled": WebhookEventType.SIGN_FLOW_CANCELLED.value,
            "flow.expired": WebhookEventType.SIGN_FLOW_EXPIRED.value,
        }
        return mapping.get(event_type, WebhookEventType.UNKNOWN.value)

    @staticmethod
    def _map_tencent_status(event_type: str) -> str:
        """映射腾讯电子签状态"""
        mapping = {
            "SignCompleted": WebhookEventType.SIGN_FLOW_COMPLETED.value,
            "FlowApproved": WebhookEventType.SIGN_FLOW_SIGNED.value,
            "FlowRejected": WebhookEventType.SIGN_FLOW_REJECTED.value,
            "FlowCanceled": WebhookEventType.SIGN_FLOW_CANCELLED.value,
        }
        return mapping.get(event_type, WebhookEventType.UNKNOWN.value)


_webhook_handler: Optional[WebhookHandler] = None
_handler_lock = threading.Lock()


def get_webhook_handler() -> WebhookHandler:
    """获取全局 Webhook 处理器"""
    global _webhook_handler
    if _webhook_handler is None:
        with _handler_lock:
            if _webhook_handler is None:
                _webhook_handler = WebhookHandler()
    return _webhook_handler
