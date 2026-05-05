# 🔐 RBAC 角色权限系统使用文档

## 简介

RBAC（基于角色的访问控制）系统是销售宗师（SalesMaster）的企业级功能，提供完整的用户管理、角色权限控制、认证授权等功能。

## 功能架构

```
RBAC 权限系统
├── 角色管理（RoleManager）
│   ├── 系统预设角色（7个）
│   ├── 自定义角色
│   ├── 角色权限配置
│   └── 权限授予/撤销
├── 用户管理（UserManager）
│   ├── 用户创建/编辑/删除
│   ├── 角色分配
│   ├── 密码管理
│   └── 用户状态管理
├── 认证管理（AuthManager）
│   ├── 用户登录
│   ├── 会话管理
│   └── 令牌验证
└── 权限验证（PermissionManager）
    ├── 权限检查
    ├── 权限列表
    └── 数据范围控制
```

## 快速开始

### 基础使用

```python
from SentriKit_salesmaster.rbac import (
    RoleManager,
    UserManager,
    AuthManager,
    PermissionManager,
)

# 创建管理器
role_mgr = RoleManager()
user_mgr = UserManager()
auth_mgr = AuthManager()
perm_mgr = PermissionManager()
```

## 系统预设角色

系统初始化时自动创建以下预设角色：

| 角色 | 代码 | 权限数 | 说明 |
|------|------|--------|------|
| 管理员 | admin | 41 | 完全控制 |
| 销售总监 | sales_director | 33 | 管理所有销售业务 |
| 销售经理 | sales_manager | 26 | 管理手下销售员 |
| 销售员 | sales | 12 | 操作自己的客户 |
| 客服 | customer_service | 8 | 处理客户问题 |
| 财务 | finance | 9 | 财务相关审批 |
| 访客 | viewer | 6 | 只读访问 |

## 权限分组

| 分组 | 权限数 | 说明 |
|------|--------|------|
| 客户管理 | 4 | 客户 CRUD |
| 线索管理 | 5 | 线索 CRUD + 分配 |
| 报价管理 | 5 | 报价 CRUD + 审批 |
| 合同管理 | 5 | 合同 CRUD + 签署 |
| 任务管理 | 5 | 任务 CRUD + 分配 |
| 审批管理 | 3 | 审批查看/创建/处理 |
| 通话管理 | 3 | 通话查看/创建/听取 |
| 报表管理 | 2 | 报表查看/导出 |
| 系统管理 | 9 | 用户/角色/配置管理 |

## 角色管理

### 获取角色

```python
# 获取所有角色
roles = role_mgr.get_roles()

# 获取单个角色
role = role_mgr.get_role("role-id")

# 根据代码获取角色
role = role_mgr.get_role_by_code("sales_director")
```

### 创建自定义角色

```python
custom_role = role_mgr.create_role(
    name="高级销售",
    code="senior_sales",
    description="高级销售人员",
    permissions=[
        "lead:view", "lead:create",
        "quote:view", "quote:create",
    ],
    role_type="senior_sales"
)
```

### 权限管理

```python
# 授予权限
role_mgr.grant_permission(role.id, "contract:view")

# 撤销权限
role_mgr.revoke_permission(role.id, "contract:view")

# 检查权限
if role.has_permission("quote:approve"):
    print("有审批权限")
```

### 删除角色

```python
# 删除自定义角色（系统角色不可删除）
role_mgr.delete_role("role-id")
```

## 用户管理

### 创建用户

```python
# 获取角色
role = role_mgr.get_role_by_code("sales")

# 创建用户
user = user_mgr.create_user(
    username="zhangsan",
    email="zhangsan@example.com",
    full_name="张三",
    role_id=role.id,
    password="password123",
    department="销售部",
    position="销售员"
)
```

### 用户操作

```python
# 获取用户
user = user_mgr.get_user("user-id")
user = user_mgr.get_user_by_username("zhangsan")

# 获取用户列表
all_users = user_mgr.get_users()
sales_users = user_mgr.get_users(role_id="role-id")
active_users = user_mgr.get_users(status="active")

# 更新用户
user_mgr.update_user(user)

# 删除用户
user_mgr.delete_user("user-id")
```

### 密码管理

```python
# 修改密码（需要旧密码）
user_mgr.change_password(user.id, old_password, new_password)

# 重置密码（管理员操作）
user_mgr.reset_password(user.id, new_password)

# 验证密码
if user.check_password(password):
    print("密码正确")
```

### 角色分配

```python
# 分配角色
user_mgr.assign_role(user.id, new_role_id)
```

## 认证管理

### 用户登录

```python
# 登录
session = auth_mgr.login(
    username="zhangsan",
    password="password123",
    ip_address="127.0.0.1",
    user_agent="Mozilla/5.0"
)

if session:
    print(f"登录成功，会话ID: {session.id}")
    print(f"Token: {session.token}")
```

### 会话管理

```python
# 验证会话
session = auth_mgr.verify_session(session.id)
if session:
    print("会话有效")

# 登出
auth_mgr.logout(session.id)

# 获取用户的所有会话
sessions = auth_mgr.get_user_sessions(user.id)

# 清理过期会话
expired_count = auth_mgr.clean_expired_sessions()
```

## 权限验证

### 检查权限

```python
# 检查单个权限
if perm_mgr.check_permission(user.id, "quote:approve"):
    print("可以审批报价")

# 获取用户所有权限
permissions = perm_mgr.get_user_permissions(user.id)
print(f"拥有 {len(permissions)} 个权限")

# 按分组获取权限
perms_by_group = perm_mgr.get_user_permissions_by_group(user.id)
for group, perms in perms_by_group.items():
    print(f"{group}: {', '.join(perms)}")
```

### 数据范围控制

```python
# 检查是否能访问特定客户
if perm_mgr.can_access_customer(user.id, customer_id):
    print("可以访问该客户")
```

## 完整示例

```python
from SentriKit_salesmaster.rbac import (
    RoleManager,
    UserManager,
    AuthManager,
    PermissionManager,
)

# 1. 创建管理器
role_mgr = RoleManager()
user_mgr = UserManager()
auth_mgr = AuthManager()
perm_mgr = PermissionManager()

# 2. 创建自定义角色
custom_role = role_mgr.create_role(
    name="VIP销售",
    code="vip_sales",
    description="VIP客户销售专员",
    permissions=["customer:view", "customer:create", "quote:view", "quote:create"],
    role_type="vip_sales"
)
print(f"创建角色: {custom_role.name}")

# 3. 创建用户
user = user_mgr.create_user(
    username="vip_sales01",
    email="vip@example.com",
    full_name="VIP销售员",
    role_id=custom_role.id,
    password="secure123",
    department="VIP销售部",
    position="VIP销售专员"
)
print(f"创建用户: {user.username}")

# 4. 用户登录
session = auth_mgr.login("vip_sales01", "secure123")
if session:
    print(f"登录成功: {session.token[:20]}...")

    # 5. 检查权限
    can_approve = perm_mgr.check_permission(user.id, "quote:approve")
    can_view = perm_mgr.check_permission(user.id, "customer:view")
    print(f"审批报价: {'有' if can_approve else '无'}")
    print(f"查看客户: {'有' if can_view else '无'}")

    # 6. 登出
    auth_mgr.logout(session.id)
    print("登出成功")
```

## 管理员默认账号

系统初始化时自动创建管理员账号：

- **用户名**: admin
- **密码**: admin123
- **角色**: 管理员

⚠️ 请及时修改默认密码！

## 最佳实践

### 1. 角色设计
- 遵循最小权限原则
- 角色职责单一
- 定期审核权限配置

### 2. 密码安全
- 使用强密码（8位以上，包含大小写、数字、特殊字符）
- 定期更换密码
- 不要共享账号

### 3. 会话管理
- 定期清理过期会话
- 敏感操作后登出
- 监控异常登录

### 4. 权限检查
- 所有敏感操作前检查权限
- 记录权限验证日志
- 防止越权访问

## 数据类型

### Role（角色）

```python
@dataclass
class Role:
    id: str
    name: str                    # 角色名称
    code: str                    # 角色代码（唯一）
    role_type: str              # 角色类型
    description: str            # 描述
    permissions: List[str]      # 权限列表
    is_system: bool              # 是否系统预设
    is_active: bool              # 是否激活
```

### User（用户）

```python
@dataclass
class User:
    id: str
    username: str                # 用户名
    email: str                   # 邮箱
    phone: str                   # 电话
    full_name: str               # 全名
    role_id: str                 # 角色ID
    role_name: str              # 角色名称
    department: str              # 部门
    position: str               # 职位
    status: str                  # 状态
    last_login: str             # 最后登录
```

### LoginSession（会话）

```python
@dataclass
class LoginSession:
    id: str
    user_id: str
    username: str
    token: str                  # 访问令牌
    ip_address: str             # IP 地址
    user_agent: str            # 用户代理
    created_at: str
    expires_at: str             # 过期时间
    is_active: bool
```

## 下一步

- 查看完整测试案例：`tests/test_rbac.py`
- 学习通话与录音系统：`docs/CALLS.md`

---

**祝您使用愉快！🎉**
