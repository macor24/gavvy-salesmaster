"""tianlong_salesmaster.core.routers.channels — 消息渠道路由

从 app.py 拆分。保持 100% 兼容。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["消息渠道"])


def _get_dispatcher():
    from ..channels.dispatcher import MessageDispatcher
    return MessageDispatcher()


@router.get("/api/channels")
async def api_channels_list():
    """列出所有已注册的渠道"""
    d = _get_dispatcher()
    channels = {}
    for name, ch in d.channels.items():
        channels[name] = {
            "name": name,
            "configured": ch.is_configured,
            "mode": getattr(ch, "mode", "unknown"),
        }
    return {"channels": channels, "count": len(channels)}


@router.get("/api/channels/stats")
async def api_channels_stats():
    """获取渠道发送统计"""
    return _get_dispatcher().get_stats()


@router.get("/api/channels/history")
async def api_channels_history(limit: int = 50):
    """获取消息发送历史"""
    return {"history": _get_dispatcher().get_history(limit=limit)}


@router.post("/api/channels/send")
async def api_channels_send(body: dict):
    """发送消息到指定渠道"""
    channel = body.get("channel", "")
    to = body.get("to", "")
    subject = body.get("subject", "")
    body_text = body.get("body", "")
    if not channel:
        raise HTTPException(status_code=400, detail="缺少 channel 字段")
    if not body_text:
        raise HTTPException(status_code=400, detail="缺少 body 字段")
    d = _get_dispatcher()
    result = d.send(channel, to=to, body=body_text, subject=subject)
    return result.to_dict()


@router.post("/api/channels/dispatch")
async def api_channels_dispatch(body: dict):
    """分发消息到多个渠道"""
    if not body.get("body"):
        raise HTTPException(status_code=400, detail="缺少 body 字段")
    d = _get_dispatcher()
    results = d.dispatch(body)
    return {
        "results": [r.to_dict() for r in results],
        "total": len(results),
        "sent": sum(1 for r in results if r.status == "sent"),
        "failed": sum(1 for r in results if r.status == "failed"),
    }


@router.post("/api/channels/config")
async def api_channels_config(body: dict):
    """配置并注册渠道"""
    name = body.get("name", "")
    config = body.get("config", {})
    if not name or not config:
        raise HTTPException(status_code=400, detail="需要 name 和 config")
    d = _get_dispatcher()
    d.save_config(name, config)
    channel = d._build_channel(name, config)
    if not channel:
        raise HTTPException(status_code=400, detail=f"不支持的渠道: {name}")
    d.register(name, channel)
    return {"status": "ok", "name": name, "configured": channel.is_configured}


@router.delete("/api/channels/config")
async def api_channels_config_delete(body: dict):
    """删除渠道配置"""
    name = body.get("name", "")
    if not name:
        raise HTTPException(status_code=400, detail="缺少 name 字段")
    d = _get_dispatcher()
    d.unregister(name)
    d.delete_config(name)
    return {"status": "ok", "name": name}
