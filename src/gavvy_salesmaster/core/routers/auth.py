"""gavvy_salesmaster.core.routers.auth — 认证路由

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
    role_name = user.role_name or ""

    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name or user.username,
            "avatar": user.avatar or "",
            "role_name": role_name,
            "department": user.department or "",
            "position": user.position or "",
            "status": user.status,
            "is_active": user.status == "active",
            "last_login": user.last_login or "",
            "created_at": user.created_at,
        },
        "permissions": permissions,
        "session": {
            "token": session.id,
            "expires_at": session.expires_at,
        },
    }


@router.post("/api/auth/change-password")
async def api_auth_change_password(body: dict):
    """修改密码（需要旧密码验证）"""
    session_id = body.get("session_id", "")
    old_password = body.get("old_password", "")
    new_password = body.get("new_password", "")

    if not session_id:
        raise HTTPException(status_code=400, detail="需要 session_id")
    if not old_password:
        raise HTTPException(status_code=400, detail="需要 old_password")
    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少6个字符")

    auth_mgr, user_mgr = _get_auth()
    session = auth_mgr.verify_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="会话无效或已过期")

    if not user_mgr.change_password(session.user_id, old_password, new_password):
        raise HTTPException(status_code=400, detail="旧密码不正确")

    return {"status": "ok", "message": "密码修改成功"}


@router.post("/api/auth/refresh")
async def api_auth_refresh(body: dict):
    """刷新会话令牌（延长有效期）"""
    session_id = body.get("session_id", "")
    if not session_id:
        raise HTTPException(status_code=400, detail="需要 session_id")

    auth_mgr, user_mgr = _get_auth()
    session = auth_mgr.get_session(session_id)
    if not session or not session.is_active:
        raise HTTPException(status_code=401, detail="会话无效")

    # 创建新会话
    from ..rbac import LoginSession
    new_session = LoginSession(
        user_id=session.user_id,
        username=session.username,
        ip_address=session.ip_address,
        user_agent=session.user_agent
    )

    sessions = auth_mgr.db.get_sessions()
    # 使旧会话失效
    for i, s in enumerate(sessions):
        if s["id"] == session_id:
            s["is_active"] = False
            break
    sessions.append(new_session.to_dict())
    auth_mgr.db.save_sessions(sessions)

    return {
        "status": "ok",
        "session": {
            "token": new_session.id,
            "user_id": new_session.user_id,
            "username": new_session.username,
            "created_at": new_session.created_at,
            "expires_at": new_session.expires_at,
        },
    }


@router.get("/api/auth/sessions")
async def api_auth_sessions(session_id: str = ""):
    """获取当前用户的所有会话（用于多设备管理）"""
    if not session_id:
        raise HTTPException(status_code=400, detail="需要 session_id")

    auth_mgr, user_mgr = _get_auth()
    session = auth_mgr.verify_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="会话无效或已过期")

    sessions = auth_mgr.get_user_sessions(session.user_id)
    return {
        "count": len(sessions),
        "sessions": [
            {
                "token": s.id,
                "ip_address": s.ip_address,
                "user_agent": s.user_agent,
                "created_at": s.created_at,
                "expires_at": s.expires_at,
                "is_current": s.id == session_id,
            }
            for s in sessions
        ],
    }


@router.delete("/api/auth/sessions/{session_id_to_delete}")
async def api_auth_delete_session(session_id: str = "", session_id_to_delete: str = ""):
    """注销指定会话（用于退出其他设备）"""
    if not session_id:
        raise HTTPException(status_code=400, detail="需要 session_id")

    auth_mgr, _ = _get_auth()
    current_session = auth_mgr.verify_session(session_id)
    if not current_session:
        raise HTTPException(status_code=401, detail="会话无效")

    if session_id_to_delete == session_id:
        raise HTTPException(status_code=400, detail="不能注销当前会话，请使用登出接口")

    # 检查要删除的会话是否属于当前用户
    session_to_delete = auth_mgr.get_session(session_id_to_delete)
    if not session_to_delete or session_to_delete.user_id != current_session.user_id:
        raise HTTPException(status_code=403, detail="无权操作")

    auth_mgr.logout(session_id_to_delete)
    return {"status": "ok", "message": "会话已注销"}
