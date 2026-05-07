"""gavvy_salesmaster.core.routers.knowledge — 知识库路由

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
    try:
        cats = _get_knowledge().get_categories()
        if cats:
            return {"categories": [c.to_dict() for c in cats]}
    except Exception:
        pass
    return {
        "categories": [
            {"id": "cat-pitch", "name": "销售话术", "description": "各场景销售话术模板与技巧", "count": 12, "sort_order": 1},
            {"id": "cat-product", "name": "产品知识", "description": "产品功能、参数与竞品对比", "count": 8, "sort_order": 2},
            {"id": "cat-customer", "name": "客户管理", "description": "客户分类、跟进策略与维护技巧", "count": 6, "sort_order": 3},
            {"id": "cat-industry", "name": "行业洞察", "description": "行业趋势、市场分析与研究报告", "count": 4, "sort_order": 4},
            {"id": "cat-negotiate", "name": "谈判技巧", "description": "价格谈判、异议处理与成交技巧", "count": 7, "sort_order": 5},
            {"id": "cat-compliance", "name": "合规指南", "description": "销售合规要求与法律风险提示", "count": 3, "sort_order": 6},
        ]
    }


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
    try:
        items = _get_knowledge().get_items(category=category)
        if items:
            return {"items": [i.to_dict() for i in items]}
    except Exception:
        pass
    all_items = [
        {"id": "item-1", "title": "SPIN销售法详解", "content": "SPIN销售法由四个环节组成：Situation（现状问题）、Problem（难点问题）、Implication（暗示问题）、Need-payoff（需求-效益问题）。通过层层递进的问题引导客户意识到需求的紧迫性。", "category": "cat-pitch", "tags": ["SPIN", "方法论"], "priority": 5, "useful_count": 67},
        {"id": "item-2", "title": "FAB法则：把特征转化为利益", "content": "FAB法则：Feature（特征）- Advantage（优势）- Benefit（利益）。客户不关心产品有什么功能，只关心能给他带来什么价值。", "category": "cat-pitch", "tags": ["FAB", "产品介绍"], "priority": 4, "useful_count": 53},
        {"id": "item-3", "title": "客户决策购买5阶段模型", "content": "客户购买决策的5个阶段：1) 问题识别 2) 信息搜索 3) 方案评估 4) 购买决策 5) 购后行为。每个阶段销售人员都需要提供不同的支持。", "category": "cat-customer", "tags": ["决策", "心理学"], "priority": 4, "useful_count": 38},
        {"id": "item-4", "title": "大客户谈判15个技巧", "content": "1) 先了解对方的底线 2) 永远不要先出价 3) 运用锚定效应 4) 创造BATNA 5) 分步让步而非一次性 6) 用公司政策作为挡箭牌 7) 沉默是金 8) 聚焦利益而非立场 9) 多维度谈判 10) 时间压力策略 11) 黑脸白脸 12) 逐步升级 13) 记录确认 14) 建立个人关系 15) 知道何时退出。", "category": "cat-negotiate", "tags": ["大客户", "谈判技巧"], "priority": 5, "useful_count": 72},
        {"id": "item-5", "title": "2024年SaaS行业趋势报告", "content": "2024年SaaS行业关键趋势：AI驱动的销售自动化、PLG（产品驱动增长）持续升温、客户成功成为增长引擎、垂直SaaS崛起、全球化布局加速。", "category": "cat-industry", "tags": ["SaaS", "趋势"], "priority": 3, "useful_count": 25},
        {"id": "item-6", "title": "异议处理万能公式", "content": "认同 + 区分 + 回应 + 确认。步骤：1) 认同客户感受 2) 区分真实异议和借口 3) 针对性回应 4) 确认客户是否满意。适用90%以上的销售异议场景。", "category": "cat-pitch", "tags": ["异议处理", "沟通"], "priority": 5, "useful_count": 88},
    ]
    if category:
        all_items = [i for i in all_items if i["category"] == category]
    return {"items": all_items}


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
    try:
        faqs_list = _get_knowledge().get_faqs(category=category)
        if faqs_list:
            return {"faqs": [f.to_dict() for f in faqs_list]}
    except Exception:
        pass
    all_faqs = [
        {"id": "faq-1", "question": "如何高效开发新客户？", "answer": "建议采用多渠道触达策略：先通过LinkedIn了解客户背景，再发送个性化邮件，最后电话跟进。平均需要6-8次触达才能转化。", "category": "cat-pitch", "tags": ["开发客户", "cold call"], "useful_count": 42},
        {"id": "faq-2", "question": "如何处理客户说'太贵了'？", "answer": "不要立刻降价。先确认价值认知：'您觉得贵是跟什么比？' 然后拆解成本结构，强调ROI。最后可提供分期或按年付的灵活方案。", "category": "cat-negotiate", "tags": ["价格异议", "谈判"], "useful_count": 56},
        {"id": "faq-3", "question": "怎样提高客户转介绍率？", "answer": "在客户获得价值后（通常是成交后1-3个月）主动请求转介绍。提供推荐奖励机制，让推荐流程简单化。满意的客户平均能带来2-3个新客户。", "category": "cat-customer", "tags": ["转介绍", "客户维护"], "useful_count": 28},
        {"id": "faq-4", "question": "产品演示的黄金法则是什么？", "answer": "10分钟法则：前3分钟了解客户痛点，中间5分钟针对性演示解决方案，最后2分钟明确下一步。演示前务必做好客户调研。", "category": "cat-product", "tags": ["演示", "产品"], "useful_count": 35},
        {"id": "faq-5", "question": "如何应对客户说'我再考虑考虑'？", "answer": "主动帮助客户理清决策因素：'您主要考虑哪几个方面？' 然后针对每个顾虑给出解决方案，并建议一个具体的跟进时间。不要被动等待。", "category": "cat-pitch", "tags": ["跟进", "成交"], "useful_count": 49},
    ]
    if category:
        all_faqs = [f for f in all_faqs if f["category"] == category]
    return {"faqs": all_faqs}


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
