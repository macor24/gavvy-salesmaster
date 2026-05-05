"""tianlong_salesmaster.core.routers.knowledge — 知识库路由

从 app.py 拆分。保持 100% 兼容。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["知识库"])


def _get_knowledge():
    from ..knowledge import KnowledgeBase
    return KnowledgeBase()


@router.get("/api/knowledge/categories")
async def api_knowledge_categories():
    """获取知识库分类"""
    return {"categories": _get_knowledge().get_categories()}


@router.post("/api/knowledge/categories")
async def api_knowledge_category_create(body: dict):
    """创建知识库分类"""
    from ..knowledge import Category
    kb = _get_knowledge()
    cat = kb.add_category(
        name=body.get("name", ""),
        description=body.get("description", ""),
        parent_id=body.get("parent_id", ""),
        sort_order=body.get("sort_order", 0),
    )
    return {"category": cat.to_dict()}


@router.get("/api/knowledge/items")
async def api_knowledge_items(category: str = ""):
    """获取知识条目"""
    return {"items": _get_knowledge().get_items(category=category)}


@router.get("/api/knowledge/items/{item_id}")
async def api_knowledge_item_get(item_id: str):
    """获取知识条目详情"""
    item = _get_knowledge().get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="条目不存在")
    return {"item": item.to_dict()}


@router.post("/api/knowledge/items")
async def api_knowledge_item_create(body: dict):
    """创建知识条目"""
    item = _get_knowledge().add_item(
        title=body.get("title", ""),
        content=body.get("content", ""),
        category=body.get("category", ""),
        tags=body.get("tags", []),
        priority=body.get("priority", 1),
    )
    return {"item": item.to_dict()}


@router.put("/api/knowledge/items/{item_id}")
async def api_knowledge_item_update(item_id: str, body: dict):
    """更新知识条目"""
    kb = _get_knowledge()
    item = kb.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="条目不存在")
    from dataclasses import fields
    for f in fields(item):
        if f.name in body:
            setattr(item, f.name, body[f.name])
    kb.update_item(item)
    return {"item": item.to_dict()}


@router.delete("/api/knowledge/items/{item_id}")
async def api_knowledge_item_delete(item_id: str):
    """删除知识条目"""
    if not _get_knowledge().delete_item(item_id):
        raise HTTPException(status_code=404, detail="条目不存在")
    return {"status": "ok"}


@router.post("/api/knowledge/items/{item_id}/useful")
async def api_knowledge_item_useful(item_id: str):
    """标记知识条目有用"""
    if not _get_knowledge().mark_useful(item_id):
        raise HTTPException(status_code=404, detail="条目不存在")
    return {"status": "ok"}


@router.get("/api/knowledge/faqs")
async def api_knowledge_faqs(category: str = ""):
    """获取 FAQ 列表"""
    return {"faqs": _get_knowledge().get_faqs(category=category)}


@router.post("/api/knowledge/faqs")
async def api_knowledge_faq_create(body: dict):
    """创建 FAQ"""
    faq = _get_knowledge().add_faq(
        question=body.get("question", ""),
        answer=body.get("answer", ""),
        category=body.get("category", ""),
        tags=body.get("tags", []),
    )
    return {"faq": faq.to_dict()}


@router.put("/api/knowledge/faqs/{faq_id}")
async def api_knowledge_faq_update(faq_id: str, body: dict):
    """更新 FAQ"""
    kb = _get_knowledge()
    faq = kb.get_faq(faq_id)
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ不存在")
    from dataclasses import fields
    for f in fields(faq):
        if f.name in body:
            setattr(faq, f.name, body[f.name])
    kb.update_faq(faq)
    return {"faq": faq.to_dict()}


@router.post("/api/knowledge/faqs/{faq_id}/rate")
async def api_knowledge_faq_rate(faq_id: str, body: dict):
    """评价 FAQ（有用/无用）"""
    if not _get_knowledge().rate_faq(faq_id, positive=body.get("positive", True)):
        raise HTTPException(status_code=404, detail="FAQ不存在")
    return {"status": "ok"}


@router.get("/api/knowledge/search")
async def api_knowledge_search(q: str = ""):
    """搜索知识库"""
    return {"results": [r.to_dict() for r in _get_knowledge().search(q)]}


@router.get("/api/knowledge/stats")
async def api_knowledge_stats():
    """知识库统计"""
    return _get_knowledge().get_stats()


@router.post("/api/knowledge/export")
async def api_knowledge_export():
    """导出所有知识数据"""
    return _get_knowledge().export_all()


@router.post("/api/knowledge/import")
async def api_knowledge_import(body: dict):
    """导入知识数据"""
    count, errors = _get_knowledge().import_all(body, overwrite=body.get("overwrite", False))
    return {"imported": count, "errors": errors}
