"""SentriKit_salesmaster.crm_pkg.rbac.middleware — RBAC FastAPI 中间件

提供：
- 权限检查装饰器
- 角色验证装饰器
- 租户隔离装饰器
- API认证中间件
"""

from __future__ import annotations

import functools
import time
from typing import Any, Callable, Dict, List, Optional, Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from . import Permission, Role, User, RoleType, get_system_roles
from .audit import AuditLogger, get_audit_logger


class RBACContext:
    """RBAC 上下文（线程本地）"""
    _local = None

    @classmethod
    def init(cls):
        if cls._local is None:
            import threading
            cls._local = threading.local()

    @classmethod
    def set_user(cls, user_id: str, username: str, role: str, permissions: List[str], tenant_id: str = "") -> None:
        cls.init()
        cls._local.user_id = user_id
        cls._local.username = username
        cls._local.role = role
        cls._local.permissions = permissions
        cls._local.tenant_id = tenant_id

    @classmethod
    def get_user_id(cls) -> Optional[str]:
        cls.init()
        return getattr(cls._local, "user_id", None)

    @classmethod
    def get_username(cls) -> Optional[str]:
        cls.init()
        return getattr(cls._local, "username", None)

    @classmethod
    def get_role(cls) -> Optional[str]:
        cls.init()
        return getattr(cls._local, "role", None)

    @classmethod
    def get_permissions(cls) -> List[str]:
        cls.init()
        return getattr(cls._local, "permissions", [])

    @classmethod
    def get_tenant_id(cls) -> Optional[str]:
        cls.init()
        return getattr(cls._local, "tenant_id", None)

    @classmethod
    def has_permission(cls, permission: str) -> bool:
        permissions = cls.get_permissions()
        if "admin" in permissions or "*" in permissions:
            return True
        return permission in permissions

    @classmethod
    def clear(cls) -> None:
        cls.init()
        cls._local.user_id = None
        cls._local.username = None
        cls._local.role = None
        cls._local.permissions = []
        cls._local.tenant_id = None


class RBACMiddleware(BaseHTTPMiddleware):
    """RBAC 认证中间件"""

    PUBLIC_PATHS = {
        "/api/health",
        "/api/auth/login",
        "/api/auth/register",
        "/api/saas/auth/register",
        "/api/saas/auth/login",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    def __init__(self, app, audit_logger: Optional[AuditLogger] = None):
        super().__init__(app)
        self._audit = audit_logger or get_audit_logger()

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if self._is_public_path(path):
            return await call_next(request)

        if path.endswith((".css", ".js", ".html", ".json", ".png", ".jpg", ".svg", ".ico", ".woff2")):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

        if not token:
            return self._unauthorized_response("Missing token")

        user_data = self._validate_token(token)
        if not user_data:
            return self._unauthorized_response("Invalid token")

        RBACContext.set_user(
            user_id=user_data.get("user_id", ""),
            username=user_data.get("username", ""),
            role=user_data.get("role", ""),
            permissions=user_data.get("permissions", []),
            tenant_id=user_data.get("tenant_id", ""),
        )

        start_time = time.time()

        try:
            response = await call_next(request)
            duration_ms = int((time.time() - start_time) * 1000)

            if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
                self._audit.log_data_modify(
                    action=request.method.lower(),
                    user_id=user_data.get("user_id", ""),
                    username=user_data.get("username", ""),
                    tenant_id=user_data.get("tenant_id", ""),
                    resource=self._extract_resource(path),
                    resource_id=self._extract_resource_id(request),
                    details={"method": request.method, "path": path},
                    ip_address=self._get_client_ip(request),
                    duration_ms=duration_ms,
                )

            response.headers["X-User-ID"] = user_data.get("user_id", "")
            response.headers["X-User-Role"] = user_data.get("role", "")

            return response

        finally:
            RBACContext.clear()

    def _is_public_path(self, path: str) -> bool:
        for public in self.PUBLIC_PATHS:
            if path == public or path.startswith(public + "/"):
                return True
        return False

    def _validate_token(self, token: str) -> Optional[Dict]:
        try:
            from ..saas import JWTToken
            from ..saas.manager import get_saas_manager

            manager = get_saas_manager()
            payload = manager.verify_token(token)
            if not payload:
                return None

            tenant = manager._store.get_tenant(payload["tenant_id"])
            user = manager._store.get_user_by_id(payload["user_id"])
            if not user or not tenant:
                return None

            role = self._get_role_by_code(user.role)
            permissions = role.permissions if role else []

            return {
                "user_id": user.id,
                "username": user.email,
                "role": user.role,
                "permissions": permissions,
                "tenant_id": tenant.id,
            }
        except Exception:
            return None

    def _get_role_by_code(self, role_code: str) -> Optional[Role]:
        roles = get_system_roles()
        for role in roles:
            if role.code == role_code:
                return role
        return None

    def _unauthorized_response(self, message: str):
        return JSONResponse(status_code=401, content={"error": "unauthorized", "message": message})

    def _extract_resource(self, path: str) -> str:
        parts = path.strip("/").split("/")
        if len(parts) >= 2:
            return parts[1]
        return "unknown"

    def _extract_resource_id(self, request: Request) -> str:
        path = request.url.path.strip("/").split("/")
        if len(path) >= 3 and path[-1]:
            try:
                int(path[-1])
                return path[-1]
            except ValueError:
                pass
        return ""

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else ""


def require_permission(permission: str):
    """权限检查装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            if not RBACContext.has_permission(permission):
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {permission}"
                )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_permissions(*permissions: str):
    """要求所有权限（AND）"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            from fastapi import HTTPException
            user_perms = RBACContext.get_permissions()
            missing = [p for p in permissions if p not in user_perms]
            if missing:
                raise HTTPException(
                    status_code=403,
                    detail=f"Missing permissions: {', '.join(missing)}"
                )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permissions: str):
    """要求任一权限（OR）"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            from fastapi import HTTPException
            user_perms = RBACContext.get_permissions()
            if not any(p in user_perms for p in permissions):
                raise HTTPException(
                    status_code=403,
                    detail=f"Requires one of: {', '.join(permissions)}"
                )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_role(*roles: str):
    """角色检查装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            from fastapi import HTTPException
            user_role = RBACContext.get_role()
            if user_role not in roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"Requires role: {', '.join(roles)}"
                )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_tenant():
    """租户检查装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            from fastapi import HTTPException
            tenant_id = RBACContext.get_tenant_id()
            if not tenant_id:
                raise HTTPException(status_code=401, detail="Tenant context required")
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def audit_action(action: str, resource: str = ""):
    """审计动作装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            from fastapi import HTTPException
            audit = get_audit_logger()
            user_id = RBACContext.get_user_id() or ""
            username = RBACContext.get_username() or ""
            tenant_id = RBACContext.get_tenant_id() or ""

            start_time = time.time()
            try:
                result = await func(request, *args, **kwargs)
                duration_ms = int((time.time() - start_time) * 1000)

                audit.log_data_modify(
                    action=action,
                    user_id=user_id,
                    username=username,
                    tenant_id=tenant_id,
                    resource=resource or RBACContext.get_role() or "unknown",
                    resource_id=kwargs.get("id", ""),
                    status="success",
                    duration_ms=duration_ms,
                )

                return result
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                audit.log_data_modify(
                    action=action,
                    user_id=user_id,
                    username=username,
                    tenant_id=tenant_id,
                    resource=resource or RBACContext.get_role() or "unknown",
                    resource_id=kwargs.get("id", ""),
                    status="failed",
                    error_message=str(e),
                    duration_ms=duration_ms,
                )
                raise
        return wrapper
    return decorator
