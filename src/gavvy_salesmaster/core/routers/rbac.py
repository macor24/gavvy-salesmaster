"""gavvy_salesmaster.core.routers.rbac — RBAC 路由

从 app.py 拆分。保持 100% 兼容。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["RBAC"])


def _get_rbac():
    from ..rbac import RoleManager, UserManager, AuthManager, PermissionManager
    return {
        "role": RoleManager(),
        "user": UserManager(),
        "auth": AuthManager(),
        "perm": PermissionManager(),
    }


@router.get("/api/rbac/users")
async def api_rbac_users(role_id: str = "", status: str = ""):
    """用户列表"""
    users = _get_rbac()["user"].get_users(role_id=role_id if role_id else None, status=status if status else None)
    result = []
    for u in users:
        user_dict = u.to_dict()
        user_dict.pop("password_hash", None)
        result.append(user_dict)
    return {"users": result}


@router.post("/api/rbac/users")
async def api_rbac_user_create(body: dict):
    """创建用户"""
    username = body.get("username", "")
    email = body.get("email", "")
    full_name = body.get("full_name", "") or body.get("display_name", "")
    role_id = body.get("role_id", "")
    password = body.get("password", "")
    phone = body.get("phone", "")
    department = body.get("department", "")
    position = body.get("position", "")

    if not username:
        raise HTTPException(status_code=400, detail="用户名不能为空")
    if not email:
        raise HTTPException(status_code=400, detail="邮箱不能为空")
    if not role_id:
        raise HTTPException(status_code=400, detail="角色ID不能为空")

    result = _get_rbac()["user"].create_user(
        username=username,
        email=email,
        full_name=full_name,
        role_id=role_id,
        password=password,
        phone=phone,
        department=department,
        position=position,
    )
    if not result:
        raise HTTPException(status_code=400, detail="创建用户失败")
    user_dict = result.to_dict()
    user_dict.pop("password_hash", None)
    return {"user": user_dict}


@router.put("/api/rbac/users/{user_id}")
async def api_rbac_user_update(user_id: str, body: dict):
    """更新用户"""
    um = _get_rbac()["user"]
    user = um.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    update_fields = ["username", "email", "phone", "full_name", "department", "position", "avatar", "status"]
    for field in update_fields:
        if field in body:
            setattr(user, field, body[field])
    
    um.update_user(user)
    user_dict = user.to_dict()
    user_dict.pop("password_hash", None)
    return {"user": user_dict}


@router.delete("/api/rbac/users/{user_id}")
async def api_rbac_user_delete(user_id: str):
    """删除用户"""
    if not _get_rbac()["user"].delete_user(user_id):
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"status": "ok"}


@router.post("/api/rbac/users/{user_id}/role")
async def api_rbac_user_assign_role(user_id: str, body: dict):
    """分配角色"""
    if not _get_rbac()["user"].assign_role(user_id, body.get("role_id", "")):
        raise HTTPException(status_code=400, detail="分配角色失败")
    return {"status": "ok"}


@router.post("/api/rbac/users/{user_id}/reset-password")
async def api_rbac_user_reset_password(user_id: str, body: dict):
    """重置密码"""
    if not _get_rbac()["user"].reset_password(user_id, body.get("new_password", "")):
        raise HTTPException(status_code=400, detail="重置密码失败")
    return {"status": "ok"}


@router.get("/api/rbac/roles")
async def api_rbac_roles():
    """角色列表"""
    return {"roles": [r.to_dict() for r in _get_rbac()["role"].get_roles()]}


@router.post("/api/rbac/roles")
async def api_rbac_role_create(body: dict):
    """创建角色"""
    role = _get_rbac()["role"].create_role(
        name=body.get("name", ""),
        code=body.get("code", ""),
        description=body.get("description", ""),
    )
    if not role:
        raise HTTPException(status_code=400, detail="创建角色失败")
    return {"role": role.to_dict()}


@router.put("/api/rbac/roles/{role_id}")
async def api_rbac_role_update(role_id: str, body: dict):
    """更新角色"""
    rm = _get_rbac()["role"]
    role = rm.get_role(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    from dataclasses import fields
    for f in fields(role):
        if f.name in body:
            setattr(role, f.name, body[f.name])
    rm.update_role(role)
    return {"role": role.to_dict()}


@router.delete("/api/rbac/roles/{role_id}")
async def api_rbac_role_delete(role_id: str):
    """删除角色"""
    if not _get_rbac()["role"].delete_role(role_id):
        raise HTTPException(status_code=404, detail="角色不存在")
    return {"status": "ok"}


@router.post("/api/rbac/roles/{role_id}/permissions")
async def api_rbac_role_grant_permission(role_id: str, body: dict):
    """授予权限"""
    if not _get_rbac()["role"].grant_permission(role_id, body.get("permission", "")):
        raise HTTPException(status_code=400, detail="授权失败")
    return {"status": "ok"}


@router.delete("/api/rbac/roles/{role_id}/permissions")
async def api_rbac_role_revoke_permission(role_id: str, body: dict):
    """吊销权限"""
    if not _get_rbac()["role"].revoke_permission(role_id, body.get("permission", "")):
        raise HTTPException(status_code=400, detail="吊销失败")
    return {"status": "ok"}


@router.post("/api/rbac/login")
async def api_rbac_login(body: dict):
    """用户登录"""
    result = _get_rbac()["auth"].login(
        username=body.get("username", ""),
        password=body.get("password", ""),
    )
    if not result:
        raise HTTPException(status_code=401, detail="登录失败")
    return {"session": result.to_dict()}


@router.post("/api/rbac/logout")
async def api_rbac_logout(body: dict):
    """用户登出"""
    _get_rbac()["auth"].logout(body.get("session_id", ""))
    return {"status": "ok"}


@router.get("/api/rbac/session/{session_id}")
async def api_rbac_session(session_id: str):
    """验证会话"""
    session = _get_rbac()["auth"].verify_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="会话无效或已过期")
    return {"session": session.to_dict()}


@router.get("/api/rbac/permissions/{user_id}")
async def api_rbac_user_permissions(user_id: str):
    """获取用户权限"""
    return {"permissions": _get_rbac()["perm"].get_user_permissions(user_id)}


@router.get("/api/rbac/permission-groups")
async def api_rbac_permission_groups():
    """获取权限分组（用于前端展示）"""
    from ..rbac import PERMISSION_GROUPS
    return {"groups": PERMISSION_GROUPS}
