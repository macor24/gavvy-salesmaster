"""tianlong_salesmaster.crm_pkg.rbac — 角色权限管理系统

完整的 RBAC（基于角色的访问控制）系统。
"""

from __future__ import annotations

import uuid
import secrets
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set


# ── 枚举定义 ────────────────────────────────────────

class Permission(Enum):
    """系统权限"""
    # 客户管理
    CUSTOMER_VIEW = "customer:view"
    CUSTOMER_CREATE = "customer:create"
    CUSTOMER_EDIT = "customer:edit"
    CUSTOMER_DELETE = "customer:delete"

    # 线索管理
    LEAD_VIEW = "lead:view"
    LEAD_CREATE = "lead:create"
    LEAD_EDIT = "lead:edit"
    LEAD_DELETE = "lead:delete"
    LEAD_ASSIGN = "lead:assign"

    # 报价管理
    QUOTE_VIEW = "quote:view"
    QUOTE_CREATE = "quote:create"
    QUOTE_EDIT = "quote:edit"
    QUOTE_DELETE = "quote:delete"
    QUOTE_APPROVE = "quote:approve"

    # 合同管理
    CONTRACT_VIEW = "contract:view"
    CONTRACT_CREATE = "contract:create"
    CONTRACT_EDIT = "contract:edit"
    CONTRACT_DELETE = "contract:delete"
    CONTRACT_SIGN = "contract:sign"

    # 任务管理
    TASK_VIEW = "task:view"
    TASK_CREATE = "task:create"
    TASK_EDIT = "task:edit"
    TASK_DELETE = "task:delete"
    TASK_ASSIGN = "task:assign"

    # 审批管理
    APPROVAL_VIEW = "approval:view"
    APPROVAL_CREATE = "approval:create"
    APPROVAL_PROCESS = "approval:process"

    # 通话管理
    CALL_VIEW = "call:view"
    CALL_CREATE = "call:create"
    CALL_LISTEN = "call:listen"

    # 报表管理
    REPORT_VIEW = "report:view"
    REPORT_EXPORT = "report:export"

    # 系统管理
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_EDIT = "user:edit"
    USER_DELETE = "user:delete"
    ROLE_VIEW = "role:view"
    ROLE_CREATE = "role:create"
    ROLE_EDIT = "role:edit"
    ROLE_DELETE = "role:delete"
    SYSTEM_CONFIG = "system:config"


class RoleType(Enum):
    """预设角色类型"""
    ADMIN = "admin"           # 管理员
    SALES_DIRECTOR = "sales_director"  # 销售总监
    SALES_MANAGER = "sales_manager"    # 销售经理
    SALES = "sales"           # 销售员
    CUSTOMER_SERVICE = "customer_service"  # 客服
    FINANCE = "finance"       # 财务
    VIEWER = "viewer"        # 访客


# ── 数据类型定义 ────────────────────────────────────────

@dataclass
class PermissionItem:
    """权限项"""
    code: str = ""
    name: str = ""
    group: str = ""           # 权限分组
    description: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "PermissionItem":
        return PermissionItem(**data)


@dataclass
class Role:
    """角色"""
    id: str = ""
    name: str = ""
    code: str = ""            # 角色代码（唯一）
    role_type: str = ""      # 角色类型
    description: str = ""
    permissions: List[str] = field(default_factory=list)  # 权限代码列表
    is_system: bool = False   # 是否系统预设角色
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:12]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def has_permission(self, permission: str) -> bool:
        """检查是否拥有指定权限"""
        return permission in self.permissions

    def grant_permission(self, permission: str) -> None:
        """授予权限"""
        if permission not in self.permissions:
            self.permissions.append(permission)

    def revoke_permission(self, permission: str) -> None:
        """撤销权限"""
        if permission in self.permissions:
            self.permissions.remove(permission)

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "Role":
        return Role(**data)


@dataclass
class User:
    """用户"""
    id: str = ""
    username: str = ""
    email: str = ""
    phone: str = ""
    full_name: str = ""
    role_id: str = ""         # 角色ID
    role_name: str = ""      # 角色名称（冗余存储）
    department: str = ""     # 部门
    position: str = ""       # 职位
    avatar: str = ""         # 头像URL
    status: str = "active"   # active/inactive/locked
    last_login: str = ""     # 最后登录时间
    password_hash: str = ""  # 密码哈希
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:12]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    @staticmethod
    def hash_password(password: str) -> str:
        """密码哈希"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${hash_obj.hex()}"

    def check_password(self, password: str) -> bool:
        """验证密码"""
        try:
            salt, stored_hash = self.password_hash.split("$")
            hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return hash_obj.hex() == stored_hash
        except Exception:
            return False

    def set_password(self, password: str) -> None:
        """设置密码"""
        self.password_hash = self.hash_password(password)

    @property
    def is_active(self) -> bool:
        """是否激活"""
        return self.status == "active"

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "User":
        return User(**data)


@dataclass
class LoginSession:
    """登录会话"""
    id: str = ""
    user_id: str = ""
    username: str = ""
    token: str = ""
    ip_address: str = ""
    user_agent: str = ""
    created_at: str = ""
    expires_at: str = ""
    is_active: bool = True

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:12]
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.created_at:
            self.created_at = now
        # 默认24小时过期
        if not self.expires_at:
            exp = datetime.now().timestamp() + 86400
            self.expires_at = datetime.fromtimestamp(exp).strftime("%Y-%m-%d %H:%M:%S")

    @property
    def is_expired(self) -> bool:
        """是否过期"""
        try:
            exp = datetime.fromisoformat(self.expires_at)
            return datetime.now() > exp
        except Exception:
            return True

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "LoginSession":
        return LoginSession(**data)


# ── 权限定义 ────────────────────────────────────────

PERMISSION_GROUPS = {
    "客户管理": ["customer:view", "customer:create", "customer:edit", "customer:delete"],
    "线索管理": ["lead:view", "lead:create", "lead:edit", "lead:delete", "lead:assign"],
    "报价管理": ["quote:view", "quote:create", "quote:edit", "quote:delete", "quote:approve"],
    "合同管理": ["contract:view", "contract:create", "contract:edit", "contract:delete", "contract:sign"],
    "任务管理": ["task:view", "task:create", "task:edit", "task:delete", "task:assign"],
    "审批管理": ["approval:view", "approval:create", "approval:process"],
    "通话管理": ["call:view", "call:create", "call:listen"],
    "报表管理": ["report:view", "report:export"],
    "系统管理": ["user:view", "user:create", "user:edit", "user:delete", "role:view", "role:create", "role:edit", "role:delete", "system:config"],
}

ALL_PERMISSIONS = []
for perms in PERMISSION_GROUPS.values():
    ALL_PERMISSIONS.extend(perms)


# ── 系统预设角色 ────────────────────────────────────────

def get_system_roles() -> List[Role]:
    """获取系统预设角色"""
    return [
        Role(
            name="管理员",
            code="admin",
            role_type="admin",
            description="系统管理员，拥有所有权限",
            permissions=ALL_PERMISSIONS.copy(),
            is_system=True
        ),
        Role(
            name="销售总监",
            code="sales_director",
            role_type="sales_director",
            description="销售总监，管理销售团队和所有销售相关业务",
            permissions=[
                # 全部客户
                "customer:view", "customer:create", "customer:edit", "customer:delete",
                # 全部线索
                "lead:view", "lead:create", "lead:edit", "lead:delete", "lead:assign",
                # 全部报价
                "quote:view", "quote:create", "quote:edit", "quote:delete", "quote:approve",
                # 全部合同
                "contract:view", "contract:create", "contract:edit", "contract:delete", "contract:sign",
                # 任务
                "task:view", "task:create", "task:edit", "task:delete", "task:assign",
                # 审批
                "approval:view", "approval:create", "approval:process",
                # 通话
                "call:view", "call:create", "call:listen",
                # 报表
                "report:view", "report:export",
                # 用户查看
                "user:view",
            ],
            is_system=True
        ),
        Role(
            name="销售经理",
            code="sales_manager",
            role_type="sales_manager",
            description="销售经理，管理手下销售员",
            permissions=[
                # 全部客户
                "customer:view", "customer:create", "customer:edit",
                # 全部线索
                "lead:view", "lead:create", "lead:edit", "lead:assign",
                # 全部报价
                "quote:view", "quote:create", "quote:edit", "quote:approve",
                # 合同查看和创建
                "contract:view", "contract:create", "contract:edit",
                # 任务
                "task:view", "task:create", "task:edit", "task:assign",
                # 审批
                "approval:view", "approval:create", "approval:process",
                # 通话
                "call:view", "call:create", "call:listen",
                # 报表
                "report:view", "report:export",
            ],
            is_system=True
        ),
        Role(
            name="销售员",
            code="sales",
            role_type="sales",
            description="普通销售员，只能操作自己的客户",
            permissions=[
                # 客户查看和创建
                "customer:view", "customer:create",
                # 线索查看和创建
                "lead:view", "lead:create",
                # 报价查看和创建
                "quote:view", "quote:create",
                # 合同查看
                "contract:view",
                # 任务
                "task:view", "task:create",
                # 通话
                "call:view", "call:create",
                # 报表查看
                "report:view",
            ],
            is_system=True
        ),
        Role(
            name="客服",
            code="customer_service",
            role_type="customer_service",
            description="客服人员",
            permissions=[
                # 客户查看
                "customer:view",
                # 线索查看
                "lead:view",
                # 任务
                "task:view", "task:create",
                # 通话
                "call:view", "call:create", "call:listen",
                # 报表
                "report:view",
            ],
            is_system=True
        ),
        Role(
            name="财务",
            code="finance",
            role_type="finance",
            description="财务人员",
            permissions=[
                # 客户查看
                "customer:view",
                # 报价查看
                "quote:view", "quote:approve",
                # 合同查看和签署
                "contract:view", "contract:sign",
                # 审批
                "approval:view", "approval:process",
                # 报表
                "report:view", "report:export",
            ],
            is_system=True
        ),
        Role(
            name="访客",
            code="viewer",
            role_type="viewer",
            description="只读访客",
            permissions=[
                "customer:view",
                "lead:view",
                "quote:view",
                "contract:view",
                "task:view",
                "report:view",
            ],
            is_system=True
        ),
    ]


# ── 角色管理器 ────────────────────────────────────────

class RoleManager:
    """角色管理器"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_rbac_kernel
        self.db = get_rbac_kernel(storage_dir)
        self._init_system_roles()

    def _init_system_roles(self) -> None:
        """初始化系统预设角色"""
        roles = self.db.get_roles()
        if not roles:
            system_roles = get_system_roles()
            for role in system_roles:
                roles.append(role.to_dict())
            self.db.save_roles(roles)

    def create_role(self, name: str, code: str, description: str = "",
                   permissions: Optional[List[str]] = None,
                   role_type: str = "") -> Role:
        """创建角色"""
        role = Role(
            name=name,
            code=code,
            role_type=role_type,
            description=description,
            permissions=permissions or [],
            is_system=False
        )
        roles = self.db.get_roles()
        roles.append(role.to_dict())
        self.db.save_roles(roles)
        return role

    def get_role(self, role_id: str) -> Optional[Role]:
        """获取角色"""
        roles = self.db.get_roles()
        for data in roles:
            if data["id"] == role_id:
                return Role.from_dict(data)
        return None

    def get_role_by_code(self, code: str) -> Optional[Role]:
        """根据代码获取角色"""
        roles = self.db.get_roles()
        for data in roles:
            if data["code"] == code:
                return Role.from_dict(data)
        return None

    def get_roles(self, is_active: bool = True) -> List[Role]:
        """获取角色列表"""
        roles = [Role.from_dict(r) for r in self.db.get_roles()]
        if is_active:
            roles = [r for r in roles if r.is_active]
        return roles

    def update_role(self, role: Role) -> bool:
        """更新角色"""
        role.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        roles = self.db.get_roles()
        for i, data in enumerate(roles):
            if data["id"] == role.id:
                roles[i] = role.to_dict()
                self.db.save_roles(roles)
                return True
        return False

    def delete_role(self, role_id: str) -> bool:
        """删除角色（系统角色不可删除）"""
        role = self.get_role(role_id)
        if not role:
            return False
        if role.is_system:
            return False
        roles = self.db.get_roles()
        for i, data in enumerate(roles):
            if data["id"] == role_id:
                del roles[i]
                self.db.save_roles(roles)
                return True
        return False

    def grant_permission(self, role_id: str, permission: str) -> bool:
        """授予权限"""
        role = self.get_role(role_id)
        if not role:
            return False
        role.grant_permission(permission)
        return self.update_role(role)

    def revoke_permission(self, role_id: str, permission: str) -> bool:
        """撤销权限"""
        role = self.get_role(role_id)
        if not role:
            return False
        role.revoke_permission(permission)
        return self.update_role(role)


# ── 用户管理器 ────────────────────────────────────────

class UserManager:
    """用户管理器"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_rbac_kernel
        self.db = get_rbac_kernel(storage_dir)
        self._init_admin_user()

    def _init_admin_user(self) -> None:
        """初始化管理员用户"""
        users = self.db.get_users()
        if not users:
            # 获取管理员角色
            role_mgr = RoleManager()
            admin_role = role_mgr.get_role_by_code("admin")
            if admin_role:
                admin = User(
                    username="admin",
                    email="admin@example.com",
                    full_name="系统管理员",
                    role_id=admin_role.id,
                    role_name=admin_role.name,
                    department="IT",
                    position="系统管理员"
                )
                admin.set_password("admin123")
                admin.status = "active"
                users.append(admin.to_dict())
                self.db.save_users(users)

    def create_user(self, username: str, email: str,
                   full_name: str, role_id: str,
                   password: str = "",
                   phone: str = "",
                   department: str = "",
                   position: str = "") -> User:
        """创建用户"""
        role_mgr = RoleManager()
        role = role_mgr.get_role(role_id)

        user = User(
            username=username,
            email=email,
            phone=phone,
            full_name=full_name,
            role_id=role_id,
            role_name=role.name if role else "",
            department=department,
            position=position
        )

        if password:
            user.set_password(password)
        else:
            user.set_password(secrets.token_urlsafe(12))

        users = self.db.get_users()
        users.append(user.to_dict())
        self.db.save_users(users)
        return user

    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户"""
        users = self.db.get_users()
        for data in users:
            if data["id"] == user_id:
                return User.from_dict(data)
        return None

    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        users = self.db.get_users()
        for data in users:
            if data["username"] == username:
                return User.from_dict(data)
        return None

    def get_users(self, role_id: Optional[str] = None,
                 status: Optional[str] = None) -> List[User]:
        """获取用户列表"""
        users = [User.from_dict(u) for u in self.db.get_users()]

        if role_id:
            users = [u for u in users if u.role_id == role_id]
        if status:
            users = [u for u in users if u.status == status]

        return users

    def update_user(self, user: User) -> bool:
        """更新用户"""
        user.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        users = self.db.get_users()
        for i, data in enumerate(users):
            if data["id"] == user.id:
                users[i] = user.to_dict()
                self.db.save_users(users)
                return True
        return False

    def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        users = self.db.get_users()
        for i, data in enumerate(users):
            if data["id"] == user_id:
                del users[i]
                self.db.save_users(users)
                return True
        return False

    def change_password(self, user_id: str, old_password: str,
                       new_password: str) -> bool:
        """修改密码"""
        user = self.get_user(user_id)
        if not user:
            return False
        if old_password and not user.check_password(old_password):
            return False
        user.set_password(new_password)
        return self.update_user(user)

    def reset_password(self, user_id: str, new_password: str) -> bool:
        """重置密码（管理员操作）"""
        user = self.get_user(user_id)
        if not user:
            return False
        user.set_password(new_password)
        return self.update_user(user)

    def assign_role(self, user_id: str, role_id: str) -> bool:
        """分配角色"""
        user = self.get_user(user_id)
        if not user:
            return False
        role_mgr = RoleManager()
        role = role_mgr.get_role(role_id)
        if not role:
            return False
        user.role_id = role_id
        user.role_name = role.name
        return self.update_user(user)

    def update_login_time(self, user_id: str) -> bool:
        """更新最后登录时间"""
        user = self.get_user(user_id)
        if not user:
            return False
        user.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.update_user(user)


# ── 认证管理器 ────────────────────────────────────────

class AuthManager:
    """认证管理器"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_rbac_kernel
        self.db = get_rbac_kernel(storage_dir)
        self.user_mgr = UserManager(storage_dir)
        self.role_mgr = RoleManager(storage_dir)

    def login(self, username: str, password: str,
             ip_address: str = "", user_agent: str = "") -> Optional[LoginSession]:
        """用户登录"""
        user = self.user_mgr.get_user_by_username(username)
        if not user:
            return None
        if not user.is_active:
            return None
        if not user.check_password(password):
            return None

        # 创建会话
        session = LoginSession(
            user_id=user.id,
            username=user.username,
            ip_address=ip_address,
            user_agent=user_agent
        )

        sessions = self.db.get_sessions()
        sessions.append(session.to_dict())
        self.db.save_sessions(sessions)

        # 更新最后登录时间
        self.user_mgr.update_login_time(user.id)

        return session

    def logout(self, session_id: str) -> bool:
        """用户登出"""
        sessions = self.db.get_sessions()
        for i, data in enumerate(sessions):
            if data["id"] == session_id:
                data["is_active"] = False
                self.db.save_sessions(sessions)
                return True
        return False

    def verify_session(self, session_id: str) -> Optional[LoginSession]:
        """验证会话"""
        sessions = self.db.get_sessions()
        for data in sessions:
            if data["id"] == session_id:
                session = LoginSession.from_dict(data)
                if session.is_active and not session.is_expired:
                    return session
        return None

    def get_session(self, session_id: str) -> Optional[LoginSession]:
        """获取会话"""
        sessions = self.db.get_sessions()
        for data in sessions:
            if data["id"] == session_id:
                return LoginSession.from_dict(data)
        return None

    def get_user_sessions(self, user_id: str) -> List[LoginSession]:
        """获取用户的所有会话"""
        sessions = [LoginSession.from_dict(s) for s in self.db.get_sessions()]
        return [s for s in sessions if s.user_id == user_id and s.is_active]

    def clean_expired_sessions(self) -> int:
        """清理过期会话"""
        sessions = self.db.get_sessions()
        expired = 0
        for i, data in enumerate(sessions):
            session = LoginSession.from_dict(data)
            if session.is_expired:
                data["is_active"] = False
                expired += 1
        if expired > 0:
            self.db.save_sessions(sessions)
        return expired


# ── 权限验证管理器 ────────────────────────────────────────

class PermissionManager:
    """权限验证管理器"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_rbac_kernel
        self.db = get_rbac_kernel(storage_dir)
        self.role_mgr = RoleManager(storage_dir)
        self.user_mgr = UserManager(storage_dir)

    def check_permission(self, user_id: str, permission: str) -> bool:
        """检查用户是否有指定权限"""
        user = self.user_mgr.get_user(user_id)
        if not user or not user.is_active:
            return False

        role = self.role_mgr.get_role(user.role_id)
        if not role:
            return False

        return role.has_permission(permission)

    def get_user_permissions(self, user_id: str) -> List[str]:
        """获取用户的所有权限"""
        user = self.user_mgr.get_user(user_id)
        if not user:
            return []

        role = self.role_mgr.get_role(user.role_id)
        if not role:
            return []

        return role.permissions.copy()

    def get_user_permissions_by_group(self, user_id: str) -> Dict[str, List[str]]:
        """按分组获取用户权限"""
        permissions = self.get_user_permissions(user_id)
        result = {}
        for group, perms in PERMISSION_GROUPS.items():
            group_perms = [p for p in permissions if p in perms]
            if group_perms:
                result[group] = group_perms
        return result

    def can_access_customer(self, user_id: str, customer_id: str) -> bool:
        """检查是否能访问客户（数据范围控制）"""
        user = self.user_mgr.get_user(user_id)
        if not user:
            return False

        role = self.role_mgr.get_role(user.role_id)
        if not role:
            return False

        # 管理员和销售总监可以访问所有
        if role.code in ("admin", "sales_director"):
            return True

        # 其他人只能访问自己的
        # 这里可以添加额外的数据范围检查逻辑
        return True


# ── 工厂函数 ────────────────────────────────────────

def get_role_manager(storage_dir: Optional[str] = None) -> RoleManager:
    """获取角色管理器"""
    return RoleManager(storage_dir)

def get_user_manager(storage_dir: Optional[str] = None) -> UserManager:
    """获取用户管理器"""
    return UserManager(storage_dir)

def get_auth_manager(storage_dir: Optional[str] = None) -> AuthManager:
    """获取认证管理器"""
    return AuthManager(storage_dir)

def get_permission_manager(storage_dir: Optional[str] = None) -> PermissionManager:
    """获取权限管理器"""
    return PermissionManager(storage_dir)
