"""SentriKit_salesmaster.core.webhook.routes — Webhook API 路由

提供 Webhook 回调接收端点，用于接收支付和电子签服务的通知。
"""

from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException, Header, Response
from typing import Optional

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def stripe_webhook(request: Request, stripe_signature: Optional[str] = Header(None)):
    """接收 Stripe Webhook 回调"""
    from . import get_webhook_handler

    body = await request.body()
    headers = {
        "Stripe-Signature": stripe_signature or "",
    }

    handler = get_webhook_handler()
    event = handler.handle_stripe_webhook(body, headers)

    if event.processed:
        return {"status": "ok", "event_id": event.id}

    return {"status": "error", "event_id": event.id, "error": event.error}


@router.post("/alipay")
async def alipay_webhook(request: Request):
    """接收支付宝回调"""
    from . import get_webhook_handler

    body = await request.body()
    body_str = body.decode("utf-8") if body else ""

    handler = get_webhook_handler()
    event = handler.handle_alipay_notification(body_str, dict(request.headers))

    if event.processed:
        return "success"

    return "fail"


@router.post("/wechatpay")
async def wechatpay_webhook(request: Request):
    """接收微信支付回调"""
    from . import get_webhook_handler

    body = await request.body()
    body_str = body.decode("utf-8") if body else ""

    handler = get_webhook_handler()
    event = handler.handle_wechatpay_notification(dict(request.headers), body_str)

    if event.processed:
        return {"code": "SUCCESS", "message": "成功"}

    return {"code": "FAIL", "message": event.error or "处理失败"}


@router.post("/bytedance-esign")
async def bytedance_esign_webhook(
    request: Request,
    x_signature: Optional[str] = Header(None),
):
    """接收字节跳动电子签署署回调"""
    from . import get_webhook_handler

    body = await request.body()
    body_str = body.decode("utf-8") if body else ""

    headers = dict(request.headers)
    if x_signature:
        headers["X-Signature"] = x_signature

    handler = get_webhook_handler()
    event = handler.handle_bytedance_esign_notification(headers, body_str)

    if event.processed:
        return {"code": 0, "message": "success"}

    return {"code": -1, "message": event.error or "处理失败"}


@router.post("/tencent-esign")
async def tencent_esign_webhook(
    request: Request,
    x_tc_signature: Optional[str] = Header(None),
):
    """接收腾讯电子签回调"""
    from . import get_webhook_handler

    body = await request.body()
    body_str = body.decode("utf-8") if body else ""

    headers = dict(request.headers)
    if x_tc_signature:
        headers["X-TC-Signature"] = x_tc_signature

    handler = get_webhook_handler()
    event = handler.handle_tencent_esign_notification(headers, body_str)

    if event.processed:
        return {"code": 0, "message": "success"}

    return {"code": -1, "message": event.error or "处理失败"}


@router.get("/events")
async def list_events(
    provider: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
):
    """获取 Webhook 事件历史"""
    from . import get_webhook_handler

    handler = get_webhook_handler()
    events = handler.get_events(
        provider=provider,
        event_type=event_type,
        limit=limit,
    )

    return {
        "events": [
            {
                "id": e.id,
                "type": e.type,
                "provider": e.provider,
                "received_at": e.received_at,
                "processed": e.processed,
                "error": e.error,
            }
            for e in events
        ],
        "count": len(events),
    }


@router.get("/events/{event_id}")
async def get_event(event_id: str):
    """获取指定事件详情"""
    from . import get_webhook_handler

    handler = get_webhook_handler()
    events = handler.get_events(limit=1000)

    for event in events:
        if event.id == event_id:
            return {
                "id": event.id,
                "type": event.type,
                "provider": event.provider,
                "payload": event.payload,
                "headers": event.headers,
                "received_at": event.received_at,
                "processed": event.processed,
                "retry_count": event.retry_count,
                "error": event.error,
            }

    raise HTTPException(status_code=404, detail="Event not found")
