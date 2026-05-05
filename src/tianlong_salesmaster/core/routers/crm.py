"""tianlong_salesmaster.core.routers.crm — CRM 路由

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
async def api_crm_customers(stage: str = "", search: str = ""):
    """客户列表，支持按阶段过滤和搜索"""
    mgr = _get_crm()
    if search:
        return {"customers": mgr.search_customers(search)}
    return {"customers": mgr.list_customers(stage=stage)}


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


# ── 商机 API ──


@router.get("/api/crm/deals")
async def api_crm_deals(customer_id: str = ""):
    """商机列表"""
    return {"deals": _get_crm().list_deals(customer_id=customer_id)}


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
async def api_crm_activities(customer_id: str = ""):
    """活动记录列表"""
    return {"activities": _get_crm().list_activities(customer_id=customer_id)}


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
