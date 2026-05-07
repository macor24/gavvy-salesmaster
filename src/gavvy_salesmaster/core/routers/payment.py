"""gavvy_salesmaster.core.routers.payment — 合同支付路由

从 app.py 拆分。保持 100% 兼容。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["合同支付"])


def _get_payment():
    from ..payment import PaymentManager, ContractPayment
    return {"payment": PaymentManager(), "contract_payment": ContractPayment()}


@router.post("/api/payment/orders")
async def api_payment_create_order(body: dict):
    """创建支付订单"""
    result = _get_payment()["payment"].create_order(
        title=body.get("title", ""),
        amount=body.get("amount", 0.0),
        customer_id=body.get("customer_id", ""),
        order_type=body.get("order_type", "one_time"),
    )
    return {"order": result.to_dict()}


@router.post("/api/payment/orders/{order_id}/pay")
async def api_payment_initiate(order_id: str):
    """发起支付"""
    pm = _get_payment()["payment"]
    order = pm.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    result = pm.initiate_payment(order)
    return {"result": result.to_dict()}


@router.get("/api/payment/orders/{order_id}/status")
async def api_payment_status(order_id: str):
    """查询支付状态"""
    status = _get_payment()["payment"].query_status(order_id)
    return {"order_id": order_id, "status": status.value}


@router.post("/api/payment/orders/{order_id}/refund")
async def api_payment_refund(order_id: str, body: dict):
    """退款"""
    result = _get_payment()["payment"].refund(
        order_id,
        amount=body.get("amount", 0.0),
        reason=body.get("reason", ""),
    )
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or "退款失败")
    return {"result": result.to_dict()}


@router.post("/api/payment/contract")
async def api_payment_contract_pay(body: dict):
    """为合同创建支付"""
    from ..quotes import ContractManager
    cm = ContractManager()
    contract = cm.get_contract(body.get("contract_id", ""))
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    order, result = _get_payment()["contract_payment"].create_payment_for_contract(
        contract, payment_plan=None,
    )
    return {"order": order.to_dict(), "payment": result.to_dict()}


@router.get("/api/payment/orders")
async def api_payment_orders():
    """获取所有支付订单"""
    return {"orders": []}
