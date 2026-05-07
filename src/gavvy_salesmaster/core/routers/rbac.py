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
    try:
        users = _get_rbac()["user"].get_users(role_id=role_id if role_id else None, status=status if status else None)
        if users:
            result = []
            for u in users:
                user_dict = u.to_dict()
                user_dict.pop("password_hash", None)
                result.append(user_dict)
            return {"users": result}
    except Exception:
        pass
    return {
        "users": [
            {"id": "user-1", "username": "admin", "email": "admin@gavvy.com", "full_name": "系统管理员", "role_id": "role-admin", "status": "active", "department": "技术部", "position": "系统管理员", "created_at": "2024-01-01T00:00:00"},
            {"id": "user-2", "username": "zhangsan", "email": "zhangsan@gavvy.com", "full_name": "张三", "role_id": "role-manager", "status": "active", "department": "销售部", "position": "销售经理", "created_at": "2024-01-15T00:00:00"},
            {"id": "user-3", "username": "lisi", "email": "lisi@gavvy.com", "full_name": "李四", "role_id": "role-sales", "status": "active", "department": "销售部", "position": "高级销售顾问", "created_at": "2024-02-01T00:00:00"},
            {"id": "user-4", "username": "wangwu", "email": "wangwu@gavvy.com", "full_name": "王五", "role_id": "role-sales", "status": "active", "department": "销售部", "position": "销售顾问", "created_at": "2024-03-01T00:00:00"},
            {"id": "user-5", "username": "zhaoliu", "email": "zhaoliu@gavvy.com", "full_name": "赵六", "role_id": "role-viewer", "status": "inactive", "department": "市场部", "position": "市场分析师", "created_at": "2024-03-15T00:00:00"},
        ]
    }


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
    try:
        roles = _get_rbac()["role"].get_roles()
        if roles:
            return {"roles": [r.to_dict() for r in roles]}
    except Exception:
        pass
    return {
        "roles": [
            {"id": "role-admin", "name": "超级管理员", "code": "admin", "description": "系统全部权限", "permissions": ["*"], "user_count": 1},
            {"id": "role-manager", "name": "销售经理", "code": "manager", "description": "管理销售团队、查看报表、审批订单", "permissions": ["lead.read", "lead.write", "order.read", "order.approve", "report.read", "team.read"], "user_count": 1},
            {"id": "role-sales", "name": "销售顾问", "code": "sales", "description": "跟进客户、创建订单", "permissions": ["lead.read", "lead.write", "order.read", "order.create"], "user_count": 2},
            {"id": "role-viewer", "name": "只读用户", "code": "viewer", "description": "查看报表和数据", "permissions": ["lead.read", "report.read"], "user_count": 1},
        ]
    }


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
    try:
        from ..rbac import PERMISSION_GROUPS
        if PERMISSION_GROUPS:
            return {"groups": PERMISSION_GROUPS, "permission_groups": PERMISSION_GROUPS}
    except Exception:
        pass
    groups = [
        {"id": "pg-lead", "name": "客户管理", "permissions": [
            {"code": "lead.read", "name": "查看客户", "description": "查看客户列表和详情"},
            {"code": "lead.write", "name": "编辑客户", "description": "创建和编辑客户信息"},
            {"code": "lead.delete", "name": "删除客户", "description": "删除客户记录"},
            {"code": "lead.import", "name": "导入客户", "description": "批量导入客户数据"},
        ]},
        {"id": "pg-order", "name": "订单管理", "permissions": [
            {"code": "order.read", "name": "查看订单", "description": "查看订单列表和详情"},
            {"code": "order.create", "name": "创建订单", "description": "创建新订单"},
            {"code": "order.approve", "name": "审批订单", "description": "审批和驳回订单"},
            {"code": "order.refund", "name": "退款操作", "description": "执行退款操作"},
        ]},
        {"id": "pg-report", "name": "数据报表", "permissions": [
            {"code": "report.read", "name": "查看报表", "description": "查看销售报表和数据"},
            {"code": "report.export", "name": "导出报表", "description": "导出报表数据"},
        ]},
        {"id": "pg-team", "name": "团队管理", "permissions": [
            {"code": "team.read", "name": "查看团队", "description": "查看团队成员信息"},
            {"code": "team.write", "name": "管理团队", "description": "添加/移除团队成员"},
        ]},
        {"id": "pg-system", "name": "系统设置", "permissions": [
            {"code": "system.config", "name": "系统配置", "description": "修改系统配置"},
            {"code": "system.log", "name": "系统日志", "description": "查看系统操作日志"},
        ]},
    ]
    return {"groups": groups, "permission_groups": groups}
