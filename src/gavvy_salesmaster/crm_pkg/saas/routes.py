"""gavvy_salesmaster.crm_pkg.saas.routes — SaaS API 路由

提供租户注册、用户认证、订阅管理等API。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr

from . import TenantContext, PlanType
from .manager import get_saas_manager


router = APIRouter(prefix="/api/saas", tags=["saas"])


class RegisterRequest(BaseModel):
    name: str
    slug: str
    company: str = ""
    admin_email: EmailStr
    admin_name: str = ""
    admin_password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SubscriptionUpdateRequest(BaseModel):
    plan: str
    seats: Optional[int] = None


class UserCreateRequest(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: str = "member"


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


@router.post("/auth/register")
async def register(req: RegisterRequest):
    """注册新租户"""
    saas = get_saas_manager()
    result = saas.register_tenant(
        name=req.name,
        slug=req.slug,
        company=req.company,
        admin_email=req.admin_email,
        admin_name=req.admin_name,
        admin_password=req.admin_password,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail={"errors": result.get("errors", [])})
    return result


class DemoTrialRequest(BaseModel):
    company: str
    name: str
    email: str
    size: str


@router.post("/auth/demo-trial")
async def demo_trial(req: DemoTrialRequest):
    """申请演示试用 - 简化注册流程"""
    import uuid
    from datetime import datetime, timedelta
    from . import Tenant, TenantUser, TenantStatus, UserStatus, Subscription, PlanType, JWTToken

    saas = get_saas_manager()

    # 生成唯一的租户标识
    slug = f"demo-{uuid.uuid4().hex[:8]}"
    tenant_id = str(uuid.uuid4())
    now = datetime.now()
    trial_expires = now + timedelta(days=14)

    # 创建租户
    tenant = Tenant(
        id=tenant_id,
        name=req.company,
        slug=slug,
        company=req.company,
        size=req.size,
        status=TenantStatus.ACTIVE.value,
        subscription=Subscription(
            plan=PlanType.PROFESSIONAL.value,
            seats=10,
            storage_mb=1024,
            api_calls_per_month=10000,
            started_at=now.isoformat(),
            expires_at=trial_expires.isoformat(),
            auto_renew=False,
        ),
        settings={
            "company_size": req.size,
            "contact_name": req.name,
            "contact_email": req.email,
        },
        created_at=now.isoformat(),
        updated_at=now.isoformat(),
    )

    # 保存租户
    saas._store.create_tenant(tenant)

    # 创建管理员用户
    user = TenantUser(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        email=req.email,
        name=req.name,
        role="admin",
        status=UserStatus.ACTIVE.value,
        created_at=now.isoformat(),
        updated_at=now.isoformat(),
    )
    user.set_password("demo1234")
    saas._store.create_user(user)

    # 生成访问凭证
    token = JWTToken.generate(tenant_id, user.id, os.environ.get("GAVVY_TENANT_SECRET", "gavvy-secret-key-2024"))

    return {
        "success": True,
        "message": "试用账号创建成功",
        "data": {
            "tenant_id": tenant_id,
            "slug": slug,
            "plan": "professional",
            "trial_days": 14,
            "expires_at": trial_expires.isoformat(),
            "admin_url": "/?tenant=" + slug,
            "api_endpoint": "/api/saas",
            "token": token,
            "demo_credentials": {
                "email": req.email,
                "password": "demo1234",
            }
        }
    }


@router.post("/auth/login")
async def login(req: LoginRequest, request: Request):
    """用户登录"""
    saas = get_saas_manager()
    result = saas.authenticate(req.email, req.password)
    if not result:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    return result


@router.get("/auth/me")
async def get_current_user(request: Request):
    """获取当前用户信息"""
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(status_code=401, detail="未登录")
    saas = get_saas_manager()
    tenant = saas._store.get_tenant(request.state.tenant_id)
    user = saas._store.get_user_by_id(request.state.user_id)
    return {
        "user": user.to_dict() if user else None,
        "tenant": tenant.to_dict() if tenant else None,
    }


@router.get("/tenant")
async def get_tenant(request: Request):
    """获取租户信息"""
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(status_code=401, detail="未登录")
    saas = get_saas_manager()
    tenant = saas._store.get_tenant(request.state.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    return tenant.to_dict()


@router.put("/tenant")
async def update_tenant(settings: Dict[str, Any], request: Request):
    """更新租户设置"""
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(status_code=401, detail="未登录")
    if request.state.user_role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    saas = get_saas_manager()
    tenant = saas._store.get_tenant(request.state.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    if "name" in settings:
        tenant.name = settings["name"]
    if "company" in settings:
        tenant.company = settings["company"]
    if "settings" in settings:
        tenant.settings.update(settings["settings"])
    tenant.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    saas._store.update_tenant(tenant)
    return tenant.to_dict()


@router.get("/subscription")
async def get_subscription(request: Request):
    """获取订阅信息"""
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(status_code=401, detail="未登录")
    saas = get_saas_manager()
    tenant = saas._store.get_tenant(request.state.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    quota = saas.check_quota(request.state.tenant_id)
    return {
        "plan": tenant.subscription.plan,
        "seats": tenant.subscription.seats,
        "storage_mb": tenant.subscription.storage_mb,
        "api_calls_per_month": tenant.subscription.api_calls_per_month,
        "started_at": tenant.subscription.started_at,
        "expires_at": tenant.subscription.expires_at,
        "quota": quota,
    }


@router.put("/subscription")
async def update_subscription(req: SubscriptionUpdateRequest, request: Request):
    """更新订阅套餐"""
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(status_code=401, detail="未登录")
    if request.state.user_role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    saas = get_saas_manager()
    success = saas.update_subscription(request.state.tenant_id, req.plan, req.seats)
    if not success:
        raise HTTPException(status_code=400, detail="更新失败")
    return {"success": True}


@router.get("/quota")
async def get_quota(request: Request):
    """获取配额使用情况"""
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(status_code=401, detail="未登录")
    saas = get_saas_manager()
    return saas.check_quota(request.state.tenant_id)


@router.get("/users")
async def list_users(request: Request):
    """列出租户用户"""
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(status_code=401, detail="未登录")
    saas = get_saas_manager()
    users = saas._store.get_tenant_users(request.state.tenant_id)
    return [u.to_dict() for u in users]


@router.post("/users")
async def create_user(req: UserCreateRequest, request: Request):
    """创建用户"""
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(status_code=401, detail="未登录")
    if request.state.user_role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    saas = get_saas_manager()
    quota = saas.check_quota(request.state.tenant_id)
    if quota["seats"]["over_quota"]:
        raise HTTPException(status_code=403, detail="用户数已达上限，请升级套餐")
    from . import TenantUser
    user = TenantUser.create(
        tenant_id=request.state.tenant_id,
        email=req.email,
        name=req.name,
        password=req.password,
        role=req.role,
    )
    success = saas._store.create_user(user)
    if not success:
        raise HTTPException(status_code=400, detail="用户已存在")
    return user.to_dict()


@router.put("/users/{user_id}")
async def update_user(user_id: str, req: UserUpdateRequest, request: Request):
    """更新用户"""
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(status_code=401, detail="未登录")
    if request.state.user_role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    saas = get_saas_manager()
    user = saas._store.get_user_by_id(user_id)
    if not user or user.tenant_id != request.state.tenant_id:
        raise HTTPException(status_code=404, detail="用户不存在")
    if req.name is not None:
        user.name = req.name
    if req.password is not None:
        user.set_password(req.password)
    if req.role is not None:
        user.role = req.role
    if req.status is not None:
        user.status = req.status
    saas._store.update_user(user)
    return user.to_dict()


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, request: Request):
    """删除用户"""
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(status_code=401, detail="未登录")
    if request.state.user_role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    if request.state.user_id == user_id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    saas = get_saas_manager()
    user = saas._store.get_user_by_id(user_id)
    if not user or user.tenant_id != request.state.tenant_id:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.status = "deleted"
    saas._store.update_user(user)
    return {"success": True}


@router.get("/plans")
async def list_plans():
    """列出可用套餐"""
    return [
        {
            "id": "free",
            "name": "免费版",
            "price": 0,
            "seats": 3,
            "storage_mb": 100,
            "api_calls_per_month": 1000,
            "features": ["基础CRM", "3个用户", "100MB存储"],
        },
        {
            "id": "starter",
            "name": "入门版",
            "price": 99,
            "seats": 10,
            "storage_mb": 1024,
            "api_calls_per_month": 10000,
            "features": ["完整CRM", "10个用户", "1GB存储", "邮件支持"],
        },
        {
            "id": "professional",
            "name": "专业版",
            "price": 399,
            "seats": 50,
            "storage_mb": 10240,
            "api_calls_per_month": 100000,
            "features": ["高级CRM", "50个用户", "10GB存储", "优先支持", "API接入"],
        },
        {
            "id": "enterprise",
            "name": "企业版",
            "price": 999,
            "seats": -1,
            "storage_mb": 102400,
            "api_calls_per_month": -1,
            "features": ["无限用户", "100GB存储", "专属支持", "私有部署"],
        },
    ]
