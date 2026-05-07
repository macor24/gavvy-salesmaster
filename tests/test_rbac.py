"""测试 RBAC 角色权限系统"""

import tempfile
import os
from datetime import datetime


def test_rbac():
    """测试 RBAC 功能"""

    print("=" * 60)
    print("🧪 测试 RBAC 角色权限系统")
    print("=" * 60)

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"   存储目录: {temp_dir}")

    try:
        # 导入模块
        from gavvy_salesmaster.crm_pkg.rbac import (
            RoleManager,
            UserManager,
            AuthManager,
            PermissionManager,
            Role,
            User,
            get_system_roles,
            PERMISSION_GROUPS,
        )

        print("✅ 模块导入成功")

        # ── 角色管理测试 ──────────────────────────────────

        print("\n👥 角色管理测试...")

        # 创建角色管理器
        role_mgr = RoleManager(temp_dir)

        # 获取系统预设角色
        system_roles = get_system_roles()
        print(f"✅ 系统预设角色: {len(system_roles)} 个")
        for role in system_roles:
            print(f"   - [{role.code}] {role.name} ({len(role.permissions)} 权限)")

        # 从管理器获取角色
        roles = role_mgr.get_roles()
        print(f"✅ 已加载角色: {len(roles)} 个")

        # 获取销售总监角色
        director_role = role_mgr.get_role_by_code("sales_director")
        print(f"✅ 获取销售总监角色: {director_role.name}")

        # 创建自定义角色
        custom_role = role_mgr.create_role(
            name="高级销售",
            code="senior_sales",
            description="高级销售人员",
            permissions=["lead:view", "lead:create", "quote:view", "quote:create"],
            role_type="senior_sales"
        )
        print(f"✅ 创建自定义角色: {custom_role.name}")

        # 授予权限
        role_mgr.grant_permission(custom_role.id, "contract:view")
        updated_role = role_mgr.get_role(custom_role.id)
        print(f"✅ 授予权限后: {len(updated_role.permissions)} 个权限")

        # 撤销权限
        role_mgr.revoke_permission(custom_role.id, "contract:view")
        updated_role = role_mgr.get_role(custom_role.id)
        print(f"✅ 撤销权限后: {len(updated_role.permissions)} 个权限")

        # ── 用户管理测试 ──────────────────────────────────

        print("\n👤 用户管理测试...")

        # 创建用户管理器
        user_mgr = UserManager(temp_dir)

        # 获取管理员
        admin = user_mgr.get_user_by_username("admin")
        if admin:
            print(f"✅ 获取管理员: {admin.username} ({admin.full_name})")

        # 创建新用户
        new_user = user_mgr.create_user(
            username="zhangsan",
            email="zhangsan@example.com",
            full_name="张三",
            role_id=director_role.id,
            password="password123",
            department="销售部",
            position="销售员"
        )
        print(f"✅ 创建用户: {new_user.username} ({new_user.full_name})")
        print(f"   部门: {new_user.department}")
        print(f"   职位: {new_user.position}")

        # 获取用户列表
        users = user_mgr.get_users()
        print(f"✅ 用户总数: {len(users)}")

        # 根据角色筛选
        sales_users = user_mgr.get_users(role_id=director_role.id)
        print(f"✅ 销售总监角色用户: {len(sales_users)}")

        # 修改密码
        old_pwd = "password123"
        new_pwd = "newpassword456"
        success = user_mgr.change_password(new_user.id, old_pwd, new_pwd)
        print(f"✅ 修改密码: {'成功' if success else '失败'}")

        # 验证新密码
        updated_user = user_mgr.get_user(new_user.id)
        if updated_user and updated_user.check_password(new_pwd):
            print(f"✅ 密码验证: 通过")

        # 分配角色
        sales_role = role_mgr.get_role_by_code("sales")
        if sales_role:
            user_mgr.assign_role(new_user.id, sales_role.id)
            updated_user = user_mgr.get_user(new_user.id)
            print(f"✅ 分配角色: {updated_user.role_name}")

        # ── 认证测试 ──────────────────────────────────

        print("\n🔐 认证测试...")

        # 创建认证管理器
        auth_mgr = AuthManager(temp_dir)

        # 登录
        session = auth_mgr.login("zhangsan", new_pwd, ip_address="127.0.0.1")
        if session:
            print(f"✅ 登录成功")
            print(f"   会话ID: {session.id}")
            print(f"   Token: {session.token[:20]}...")
            print(f"   过期时间: {session.expires_at}")
        else:
            print(f"❌ 登录失败")

        # 验证会话
        verified = auth_mgr.verify_session(session.id)
        if verified:
            print(f"✅ 会话验证: 通过")

        # 获取用户会话
        user_sessions = auth_mgr.get_user_sessions(new_user.id)
        print(f"✅ 用户会话数: {len(user_sessions)}")

        # 登出
        auth_mgr.logout(session.id)
        print(f"✅ 登出成功")

        # 登出后会话失效
        verified = auth_mgr.verify_session(session.id)
        print(f"✅ 登出后会话验证: {'通过' if verified else '失效'}")

        # ── 权限验证测试 ──────────────────────────────────

        print("\n🔑 权限验证测试...")

        # 创建权限管理器
        perm_mgr = PermissionManager(temp_dir)

        # 重新登录
        session = auth_mgr.login("zhangsan", new_pwd)
        if session:
            user_id = new_user.id

            # 检查权限
            can_view_quote = perm_mgr.check_permission(user_id, "quote:view")
            can_edit_quote = perm_mgr.check_permission(user_id, "quote:edit")
            can_delete_user = perm_mgr.check_permission(user_id, "user:delete")

            print(f"✅ 查看报价权限: {'有' if can_view_quote else '无'}")
            print(f"✅ 编辑报价权限: {'有' if can_edit_quote else '无'}")
            print(f"✅ 删除用户权限: {'有' if can_delete_user else '无'}")

            # 获取用户权限列表
            perms = perm_mgr.get_user_permissions(user_id)
            print(f"✅ 用户总权限数: {len(perms)}")

            # 按分组获取权限
            perms_by_group = perm_mgr.get_user_permissions_by_group(user_id)
            print(f"✅ 权限分组:")
            for group, group_perms in perms_by_group.items():
                print(f"   - {group}: {len(group_perms)} 个权限")

        # ── 清理过期会话测试 ──────────────────────────────────

        print("\n🧹 清理过期会话测试...")

        expired_count = auth_mgr.clean_expired_sessions()
        print(f"✅ 清理过期会话: {expired_count} 个")

        # ── 权限分组展示 ──────────────────────────────────

        print("\n📋 系统权限分组:")
        for group, perms in PERMISSION_GROUPS.items():
            print(f"   {group}: {len(perms)} 个权限")

        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        print(f"\n清理临时目录: {temp_dir}")


if __name__ == "__main__":
    success = test_rbac()
    if success:
        print("\n✅ RBAC 系统测试通过！")
    else:
        print("\n❌ RBAC 系统测试失败！")
