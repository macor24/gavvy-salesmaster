"""SentriKit_salesmaster.crm_pkg.saas.middleware — FastAPI SaaS 中间件

提供：
- JWT认证中间件
- 租户上下文注入
- API限流
- 租户数据隔离
"""

from __future__ import annotations

import os
import time
from typing import Any, Callable, Dict, Optional

from starlette.middleware.base import BaseHTTPMiddleware

from . import TenantContext, Tenant, TenantUser, PlanType
from .manager import get_saas_manager, SaaSManager


def _get_fastapi():
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.responses import JSONResponse
    return FastAPI, Request, HTTPException, JSONResponse


class SaaSAuthMiddleware(BaseHTTPMiddleware):
    """SaaS 认证中间件"""

    PUBLIC_PATHS = {
        "/api/health",
        "/api/auth/register",
        "/api/auth/login",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    def __init__(self, app: FastAPI, saas_manager: Optional[SaaSManager] = None):
        super().__init__(app)
        self._saas = saas_manager or get_saas_manager()

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        path = request.url.path

        if path in self.PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        if path.endswith((".css", ".js", ".html", ".json", ".png", ".jpg", ".svg", ".ico", ".woff2")):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

        if not token:
            token = request.cookies.get("saas_token", "")

        if not token:
            return JSONResponse(status_code=401, content={"error": "unauthorized", "message": "需要登录"})

        payload = self._saas.verify_token(token)
        if not payload:
            return JSONResponse(status_code=401, content={"error": "invalid_token", "message": "Token无效或已过期"})

        tenant = self._saas._store.get_tenant(payload["tenant_id"])
        if not tenant:
            return JSONResponse(status_code=401, content={"error": "tenant_not_found", "message": "租户不存在"})

        if tenant.status != "active":
            return JSONResponse(status_code=403, content={"error": "tenant_inactive", "message": f"租户已{tenant.status}"})

        user = self._saas._store.get_user_by_id(payload["user_id"])
        if not user:
            return JSONResponse(status_code=401, content={"error": "user_not_found", "message": "用户不存在"})

        if user.status != "active":
            return JSONResponse(status_code=403, content={"error": "user_inactive", "message": "用户已停用"})

        TenantContext.set_tenant(tenant.id)
        TenantContext.set_user(user.id, user.role)

        try:
            if not self._saas.check_rate_limit(token):
                remaining = self._saas.get_rate_limit_remaining(token)
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": "请求过于频繁，请稍后再试",
                        "retry_after": 60,
                        "remaining": remaining,
                    },
                    headers={"Retry-After": "60", "X-RateLimit-Remaining": str(remaining)},
                )

            response = await call_next(request)

            remaining = self._saas.get_rate_limit_remaining(token)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-Tenant-ID"] = tenant.id
            response.headers["X-Plan"] = tenant.subscription.plan

            return response

        finally:
            TenantContext.clear()


class TenantDataMiddleware(BaseHTTPMiddleware):
    """租户数据隔离中间件"""

    def __init__(self, app: FastAPI):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        tenant_id = TenantContext.get_tenant()
        if tenant_id:
            request.state.tenant_id = tenant_id
            user_ctx = TenantContext.get_user()
            if user_ctx:
                request.state.user_id = user_ctx["id"]
                request.state.user_role = user_ctx["role"]

        return await call_next(request)


def require_permission(permission: str):
    """权限检查装饰器（用于FastAPI路由）"""
    def decorator(func: Callable) -> Callable:
        async def wrapper(request: Request, *args, **kwargs):
            user_role = getattr(request.state, "user_role", None)
            if user_role == "admin":
                return await func(request, *args, **kwargs)
            raise HTTPException(status_code=403, detail=f"需要权限: {permission}")
        return wrapper
    return decorator


def require_tenant():
    """租户检查装饰器"""
    def decorator(func: Callable) -> Callable:
        async def wrapper(request: Request, *args, **kwargs):
            if not hasattr(request.state, "tenant_id"):
                raise HTTPException(status_code=401, detail="需要有效租户")
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
