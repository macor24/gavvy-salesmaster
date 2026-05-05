"""tianlong_salesmaster.core.routers.auth — 认证路由

用户注册、登录、登出、会话管理。
认证端点在 API Key 中间件之前注册，允许未认证访问。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(tags=["认证"])


def _get_auth():
    from ..rbac import AuthManager, UserManager
    return AuthManager(), UserManager()


@router.post("/api/auth/register")
async def api_auth_register(body: dict):
    """用户注册（创建账号）"""
    username = body.get("username", "").strip()
    password = body.get("password", "").strip()
    email = body.get("email", "").strip()
    display_name = body.get("display_name", "").strip()

    if not username or len(username) < 2:
        raise HTTPException(status_code=400, detail="用户名至少2个字符")
    if not password or len(password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6个字符")
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="请输入有效邮箱")

    auth_mgr, user_mgr = _get_auth()
    existing = user_mgr.get_user_by_username(username)
    if existing:
        raise HTTPException(status_code=409, detail="用户名已存在")

    from ..rbac import User
    password_hash = User.hash_password(password)
    user = User(
        id=str(uuid.uuid4()),
        username=username,
        email=email,
        password_hash=password_hash,
        full_name=display_name or username,
        status="active",
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    result = user_mgr.create_user(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role_id="",
        password=password,
    )
    if not result:
        raise HTTPException(status_code=500, detail="创建用户失败")

    return {
        "status": "ok",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "display_name": user.full_name,
        },
    }


@router.post("/api/auth/login")
async def api_auth_login(body: dict, request: Request):
    """用户登录，返回 session token"""
    username = body.get("username", "")
    password = body.get("password", "")
    if not username or not password:
        raise HTTPException(status_code=400, detail="需要用户名和密码")

    auth_mgr, _ = _get_auth()
    session = auth_mgr.login(
        username=username,
        password=password,
        ip_address=request.client.host if request.client else "",
        user_agent=request.headers.get("User-Agent", ""),
    )
    if not session:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    return {
        "status": "ok",
        "session": {
            "token": session.id,
            "user_id": session.user_id,
            "username": session.username,
            "created_at": session.created_at,
            "expires_at": session.expires_at,
        },
    }


@router.post("/api/auth/logout")
async def api_auth_logout(body: dict):
    """用户登出"""
    session_id = body.get("session_id", "") or body.get("token", "")
    if session_id:
        auth_mgr, _ = _get_auth()
        auth_mgr.logout(session_id)
    return {"status": "ok"}


@router.get("/api/auth/session/{session_id}")
async def api_auth_session(session_id: str):
    """验证会话"""
    auth_mgr, _ = _get_auth()
    session = auth_mgr.verify_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="会话无效或已过期")

    return {
        "valid": True,
        "session": {
            "token": session.id,
            "user_id": session.user_id,
            "username": session.username,
            "created_at": session.created_at,
            "expires_at": session.expires_at,
        },
    }


@router.get("/api/auth/me")
async def api_auth_me(session_id: str = ""):
    """当前用户信息（从 session_id 查询参数）"""
    if not session_id:
        raise HTTPException(status_code=400, detail="需要 session_id 参数")
    auth_mgr, user_mgr = _get_auth()
    session = auth_mgr.verify_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="会话无效或已过期")

    user = user_mgr.get_user(session.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 获取权限
    from ..rbac import get_permission_manager
    perm_mgr = get_permission_manager()
    permissions = perm_mgr.get_user_permissions(session.user_id)

    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "display_name": user.full_name or user.username,
            "avatar": user.avatar or "",
            "is_active": user.status == "active",
            "created_at": user.created_at,
        },
        "permissions": permissions,
    }
