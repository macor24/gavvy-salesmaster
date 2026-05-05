"""tianlong_salesmaster.core.routers.scripts — 话术训练路由

从 app.py 拆分。保持 100% 兼容。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["话术训练"])


def _get_scripts():
    from ..scripts import ScriptsEngine
    return ScriptsEngine()


@router.get("/api/scripts/scenarios")
async def api_scripts_scenarios():
    """获取所有话术场景"""
    return {"scenarios": _get_scripts().list_scenarios()}


@router.get("/api/scripts/scenarios/{scenario_id}")
async def api_scripts_scenario_get(scenario_id: str):
    """获取场景详情"""
    sc = _get_scripts().get_scenario(scenario_id)
    if not sc:
        raise HTTPException(status_code=404, detail="场景不存在")
    return sc


@router.get("/api/scripts/recommend")
async def api_scripts_recommend(scenario: str = "", tags: str = ""):
    """推荐话术"""
    tag_list = tags.split(",") if tags else None
    return {"scripts": _get_scripts().recommend_scripts(scenario=scenario, tags=tag_list)}


@router.get("/api/scripts/stats")
async def api_scripts_stats():
    """话术训练系统统计"""
    return _get_scripts().get_stats()


@router.get("/api/scripts")
async def api_scripts_list(scenario: str = "", tag: str = "",
                           search: str = "", sort: str = "rating"):
    """话术列表"""
    engine = _get_scripts()
    if search:
        return {"scripts": engine.search_scripts(search)}
    return {"scripts": engine.list_scripts(scenario=scenario, tag=tag, sort=sort)}


@router.get("/api/scripts/{script_id}")
async def api_scripts_get(script_id: str):
    """话术详情"""
    script = _get_scripts().get_script(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="话术不存在")
    return script


@router.post("/api/scripts")
async def api_scripts_create(body: dict):
    """创建话术"""
    from ..scripts import Script
    script = Script(
        scenario=body.get("scenario", ""),
        title=body.get("title", ""),
        content=body.get("content", ""),
        tags=body.get("tags", []),
        tips=body.get("tips", ""),
    )
    return _get_scripts().add_script(script)


@router.put("/api/scripts/{script_id}")
async def api_scripts_update(script_id: str, body: dict):
    """更新话术"""
    result = _get_scripts().update_script(script_id, body)
    if not result:
        raise HTTPException(status_code=404, detail="话术不存在")
    return result


@router.delete("/api/scripts/{script_id}")
async def api_scripts_delete(script_id: str):
    """删除话术"""
    if not _get_scripts().delete_script(script_id):
        raise HTTPException(status_code=404, detail="话术不存在")
    return {"status": "ok"}


@router.post("/api/scripts/{script_id}/rate")
async def api_scripts_rate(script_id: str, body: dict):
    """评分话术"""
    score = body.get("score", 3)
    comment = body.get("comment", "")
    result = _get_scripts().rate_script(script_id, score, comment)
    if not result:
        raise HTTPException(status_code=404, detail="话术不存在或评分无效")
    return result


@router.get("/api/scripts/{script_id}/ratings")
async def api_scripts_ratings(script_id: str):
    """获取话术评分记录"""
    return {"ratings": _get_scripts().get_ratings(script_id)}
