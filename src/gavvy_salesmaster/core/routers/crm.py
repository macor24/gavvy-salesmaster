"""gavvy_salesmaster.core.routers.crm — CRM 路由

从 app.py 拆分而来。保持 100% 兼容。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["CRM"])


def _get_crm():
    from ..crm import CRMManager
    return CRMManager()


@router.get("/api/crm/overview")
async def api_crm_overview():
    """CRM 概览仪表盘（缓存30秒）"""
    from ..cache import get_cache as _gc
    cache = _gc("crm")
    cached = cache.get("crm_overview")
    if cached is not None:
        return cached
    result = _get_crm().get_dashboard()
    cache.set("crm_overview", result, ttl=30)
    return result


@router.get("/api/crm/customers")
async def api_crm_customers(
    stage: str = "",
    search: str = "",
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "",
    industry: str = "",
    source: str = ""
):
    """客户列表，支持模糊搜索、高级筛选、排序和分页"""
    mgr = _get_crm()
    customers = mgr.list_customers()
    
    # 构建筛选条件
    filters = {
        "operator": "and",
        "conditions": []
    }
    
    if stage:
        filters["conditions"].append({
            "field": "stage",
            "operator": "eq",
            "value": stage
        })
    
    if industry:
        filters["conditions"].append({
            "field": "industry",
            "operator": "eq",
            "value": industry
        })
    
    if source:
        filters["conditions"].append({
            "field": "source",
            "operator": "eq",
            "value": source
        })
    
    # 解析排序参数
    sort_config = []
    if sort_by:
        parts = sort_by.split(",")
        for part in parts:
            field, direction = part.split(":") if ":" in part else (part, "desc")
            sort_config.append({"field": field.strip(), "direction": direction.strip()})
    
    # 执行搜索
    from ..search import search_items
    result = search_items(
        customers,
        query=search,
        filters=filters if filters["conditions"] else None,
        sort_by=sort_config if sort_config else [{"field": "created_at", "direction": "desc"}],
        page=page,
        page_size=page_size,
        search_fields=["name", "company", "phone", "email", "tags", "notes"],
        field_weights=[2.0, 1.5, 1.0, 1.0, 0.5, 0.5]
    )
    
    return {
        "customers": result.items,
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size,
        "has_more": result.has_more
    }


@router.get("/api/crm/customers/{customer_id}")
async def api_crm_customer_detail(customer_id: str):
    """客户详情（含联系人、商机、合同、活动）"""
    mgr = _get_crm()
    customer = mgr.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    return {
        "customer": customer,
        "contacts": mgr.list_contacts(customer_id),
        "deals": mgr.list_deals(customer_id),
        "contracts": mgr.list_contracts(customer_id),
        "activities": mgr.list_activities(customer_id),
    }


@router.post("/api/crm/customers")
async def api_crm_customer_create(body: dict):
    """创建客户"""
    from ..crm import Customer
    customer = Customer(
        name=body.get("name", ""),
        company=body.get("company", ""),
        industry=body.get("industry", ""),
        source=body.get("source", "manual"),
        stage=body.get("stage", "lead"),
        tags=body.get("tags", []),
        phone=body.get("phone", ""),
        email=body.get("email", ""),
        address=body.get("address", ""),
        website=body.get("website", ""),
        notes=body.get("notes", ""),
    )
    return _get_crm().add_customer(customer)


@router.put("/api/crm/customers/{customer_id}")
async def api_crm_customer_update(customer_id: str, body: dict):
    """更新客户信息"""
    result = _get_crm().update_customer(customer_id, body)
    if not result:
        raise HTTPException(status_code=404, detail="客户不存在")
    return result


@router.delete("/api/crm/customers/{customer_id}")
async def api_crm_customer_delete(customer_id: str):
    """删除客户（级联删除联系人/商机/合同/活动）"""
    if not _get_crm().delete_customer(customer_id):
        raise HTTPException(status_code=404, detail="客户不存在")
    return {"status": "ok"}


# ── 联系人 API ──


@router.post("/api/crm/contacts")
async def api_crm_contact_create(body: dict):
    """创建联系人"""
    from ..crm import Contact
    contact = Contact(
        customer_id=body.get("customer_id", ""),
        name=body.get("name", ""),
        role=body.get("role", ""),
        phone=body.get("phone", ""),
        email=body.get("email", ""),
        wechat=body.get("wechat", ""),
        is_primary=body.get("is_primary", False),
        notes=body.get("notes", ""),
    )
    return _get_crm().add_contact(contact)


@router.delete("/api/crm/contacts/{contact_id}")
async def api_crm_contact_delete(contact_id: str):
    """删除联系人"""
    if not _get_crm().delete_contact(contact_id):
        raise HTTPException(status_code=404, detail="联系人不存在")
    return {"status": "ok"}


# ── 图表数据 API ──


@router.get("/api/crm/analytics/dashboard")
async def api_crm_analytics_dashboard():
    """获取仪表盘数据"""
    return {
        "stats": {
            "new_leads": {"value": "128", "label": "今日新增线索", "trend": "↑ 15%"},
            "month_revenue": {"value": "¥28.5万", "label": "本月成交额", "trend": "↑ 23%"},
            "pending_leads": {"value": "32", "label": "待跟进线索", "trend": "↓ 8%"},
            "pending_orders": {"value": "5", "label": "待审核订单", "trend": "↑ 5"}
        },
        "leads": [
            {"id": "1", "name": "张经理", "score": 85, "tags": ["IT行业", "高意向", "北京"], "description": "对企业版产品感兴趣，需要安排产品演示..."},
            {"id": "2", "name": "李总监", "score": 72, "tags": ["金融", "中意向", "上海"], "description": "已发送报价单，等待反馈中..."}
        ],
        "customers": [
            {"id": "1", "name": "华腾科技", "company": "深圳华腾科技有限公司", "status": "成交"},
            {"id": "2", "name": "创新电子", "company": "北京创新电子科技", "status": "跟进中"},
            {"id": "3", "name": "智联网络", "company": "广州智联网络科技", "status": "待报价"}
        ]
    }


@router.get("/api/crm/analytics/charts")
async def api_crm_analytics_charts():
    """获取图表数据"""
    return {
        "sales_trend": {
            "months": ["1月", "2月", "3月", "4月", "5月", "6月"],
            "revenue": [120, 150, 180, 220, 280, 350],
            "orders": [45, 58, 68, 82, 95, 110],
            "leads": [120, 145, 168, 195, 220, 258]
        },
        "customer_distribution": {
            "industries": ["IT行业", "金融", "制造业", "电商", "教育", "其他"],
            "counts": [156, 89, 124, 98, 67, 45]
        },
        "sales_funnel": {
            "stages": ["线索", "商机", "报价", "谈判", "成交"],
            "counts": [258, 145, 89, 45, 23]
        },
        "conversion_rate": {
            "labels": ["本周", "上周", "本月", "上月"],
            "rates": [23.5, 21.2, 22.8, 19.5]
        }
    }


# ── 商机 API ──


@router.get("/api/crm/deals")
async def api_crm_deals(
    customer_id: str = "",
    search: str = "",
    stage: str = "",
    page: int = 1,
    page_size: int = 20,
    sort_by: str = ""
):
    """商机列表，支持模糊搜索、高级筛选、排序和分页"""
    mgr = _get_crm()
    deals = mgr.list_deals()
    
    # 构建筛选条件
    filters = {
        "operator": "and",
        "conditions": []
    }
    
    if customer_id:
        filters["conditions"].append({
            "field": "customer_id",
            "operator": "eq",
            "value": customer_id
        })
    
    if stage:
        filters["conditions"].append({
            "field": "stage",
            "operator": "eq",
            "value": stage
        })
    
    # 解析排序参数
    sort_config = []
    if sort_by:
        parts = sort_by.split(",")
        for part in parts:
            field, direction = part.split(":") if ":" in part else (part, "desc")
            sort_config.append({"field": field.strip(), "direction": direction.strip()})
    
    # 执行搜索
    from ..search import search_items
    result = search_items(
        deals,
        query=search,
        filters=filters if filters["conditions"] else None,
        sort_by=sort_config if sort_config else [{"field": "created_at", "direction": "desc"}],
        page=page,
        page_size=page_size,
        search_fields=["title", "product_info", "notes"]
    )
    
    return {
        "deals": result.items,
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size,
        "has_more": result.has_more
    }


@router.post("/api/crm/deals")
async def api_crm_deal_create(body: dict):
    """创建商机"""
    from ..crm import Deal
    deal = Deal(
        customer_id=body.get("customer_id", ""),
        title=body.get("title", ""),
        value=body.get("value", 0.0),
        stage=body.get("stage", "discovery"),
        probability=body.get("probability", 0),
        expected_close=body.get("expected_close", ""),
        notes=body.get("notes", ""),
    )
    return _get_crm().add_deal(deal)


@router.put("/api/crm/deals/{deal_id}")
async def api_crm_deal_update(deal_id: str, body: dict):
    """更新商机"""
    result = _get_crm().update_deal(deal_id, body)
    if not result:
        raise HTTPException(status_code=404, detail="商机不存在")
    return result


# ── 合同 API ──


@router.get("/api/crm/contracts")
async def api_crm_contracts(customer_id: str = ""):
    """合同列表"""
    return {"contracts": _get_crm().list_contracts(customer_id=customer_id)}


@router.post("/api/crm/contracts")
async def api_crm_contract_create(body: dict):
    """创建合同"""
    from ..crm import Contract
    contract = Contract(
        customer_id=body.get("customer_id", ""),
        deal_id=body.get("deal_id", ""),
        title=body.get("title", ""),
        amount=body.get("amount", 0.0),
        status=body.get("status", "draft"),
        signed_date=body.get("signed_date", ""),
        expiry_date=body.get("expiry_date", ""),
        notes=body.get("notes", ""),
    )
    return _get_crm().add_contract(contract)


# ── 活动记录 API ──


@router.get("/api/crm/activities")
async def api_crm_activities(
    customer_id: str = "",
    search: str = "",
    type: str = "",
    page: int = 1,
    page_size: int = 20,
    sort_by: str = ""
):
    """活动记录列表，支持模糊搜索、高级筛选、排序和分页"""
    mgr = _get_crm()
    activities = mgr.list_activities()
    
    # 构建筛选条件
    filters = {
        "operator": "and",
        "conditions": []
    }
    
    if customer_id:
        filters["conditions"].append({
            "field": "customer_id",
            "operator": "eq",
            "value": customer_id
        })
    
    if type:
        filters["conditions"].append({
            "field": "type",
            "operator": "eq",
            "value": type
        })
    
    # 解析排序参数
    sort_config = []
    if sort_by:
        parts = sort_by.split(",")
        for part in parts:
            field, direction = part.split(":") if ":" in part else (part, "desc")
            sort_config.append({"field": field.strip(), "direction": direction.strip()})
    
    # 执行搜索
    from ..search import search_items
    result = search_items(
        activities,
        query=search,
        filters=filters if filters["conditions"] else None,
        sort_by=sort_config if sort_config else [{"field": "created_at", "direction": "desc"}],
        page=page,
        page_size=page_size,
        search_fields=["title", "content"]
    )
    
    return {
        "activities": result.items,
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size,
        "has_more": result.has_more
    }


# ── 高级搜索 API ──


@router.post("/api/crm/search")
async def api_crm_advanced_search(body: dict):
    """
    高级搜索 API - 支持复杂筛选条件
    
    请求体格式：
    {
        "query": "搜索关键词",
        "type": "customers|deals|contracts|activities",
        "filters": {
            "operator": "and|or",
            "conditions": [
                {"field": "stage", "operator": "eq", "value": "customer"},
                {"field": "amount", "operator": "gte", "value": 10000},
                {
                    "operator": "or",
                    "conditions": [
                        {"field": "industry", "operator": "in", "value": ["IT", "金融"]}
                    ]
                }
            ]
        },
        "sort_by": [{"field": "created_at", "direction": "desc"}],
        "page": 1,
        "page_size": 20,
        "search_fields": ["name", "company", "email"]
    }
    """
    from ..search import search_items
    
    query = body.get("query", "")
    entity_type = body.get("type", "customers")
    filters = body.get("filters")
    sort_by = body.get("sort_by", [{"field": "created_at", "direction": "desc"}])
    page = body.get("page", 1)
    page_size = body.get("page_size", 20)
    search_fields = body.get("search_fields")
    
    # 获取数据源
    mgr = _get_crm()
    if entity_type == "deals":
        items = mgr.list_deals()
        default_fields = ["title", "product_info", "notes"]
    elif entity_type == "contracts":
        items = mgr.list_contracts()
        default_fields = ["title", "content", "notes"]
    elif entity_type == "activities":
        items = mgr.list_activities()
        default_fields = ["title", "content"]
    else:  # customers
        items = mgr.list_customers()
        default_fields = ["name", "company", "phone", "email", "tags", "notes"]
    
    # 执行搜索
    result = search_items(
        items,
        query=query,
        filters=filters,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
        search_fields=search_fields or default_fields
    )
    
    return {
        entity_type: result.items,
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size,
        "has_more": result.has_more,
        "query": query,
        "type": entity_type
    }


@router.get("/api/crm/autocomplete")
async def api_crm_autocomplete(
    field: str = "name",
    query: str = "",
    type: str = "customers",
    limit: int = 10
):
    """
    自动补全 API
    
    :param field: 字段名
    :param query: 输入前缀
    :param type: 实体类型
    :param limit: 返回数量
    """
    from ..search import get_search_manager
    
    mgr = _get_crm()
    if type == "deals":
        items = mgr.list_deals()
    elif type == "contracts":
        items = mgr.list_contracts()
    else:
        items = mgr.list_customers()
    
    search_mgr = get_search_manager()
    suggestions = search_mgr.autocomplete(items, query, field, limit)
    
    return {"suggestions": suggestions}


@router.post("/api/crm/activities")
async def api_crm_activity_create(body: dict):
    """创建活动记录"""
    from ..crm import Activity
    activity = Activity(
        customer_id=body.get("customer_id", ""),
        contact_id=body.get("contact_id", ""),
        type=body.get("type", "call"),
        subject=body.get("subject", ""),
        description=body.get("description", ""),
        outcome=body.get("outcome", ""),
        scheduled_at=body.get("scheduled_at", ""),
        completed_at=body.get("completed_at", ""),
    )
    return _get_crm().add_activity(activity)
