"""测试 RBAC + Audit 系统"""

import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir / "src"))


def test_rbac_permissions():
    """测试权限定义"""
    from tianlong_salesmaster.crm_pkg.rbac import Permission, PERMISSION_GROUPS, ALL_PERMISSIONS

    assert len(ALL_PERMISSIONS) > 0
    assert "customer:view" in ALL_PERMISSIONS
    assert "user:delete" in ALL_PERMISSIONS
    assert len(PERMISSION_GROUPS) > 0

    print("✅ RBAC permissions: OK")
    return True


def test_rbac_roles():
    """测试角色定义"""
    from tianlong_salesmaster.crm_pkg.rbac import Role, get_system_roles

    roles = get_system_roles()
    assert len(roles) >= 5

    admin_role = None
    for role in roles:
        if role.code == "admin":
            admin_role = role
            break

    assert admin_role is not None
    assert len(admin_role.permissions) > 10
    assert admin_role.has_permission("user:delete")
    assert admin_role.has_permission("customer:view")

    sales_role = None
    for role in roles:
        if role.code == "sales":
            sales_role = role
            break

    assert sales_role is not None
    assert sales_role.has_permission("customer:view")
    assert not sales_role.has_permission("user:delete")

    print("✅ RBAC roles: OK")
    return True


def test_audit_logger():
    """测试审计日志"""
    from tianlong_salesmaster.crm_pkg.rbac.audit import AuditLogger, AuditQuery, AuditLevel, get_audit_logger

    audit = get_audit_logger()
    audit._logs.clear()

    log = audit.log(
        action="login",
        user_id="user_001",
        username="admin@example.com",
        tenant_id="tenant_001",
        resource="session",
        level=AuditLevel.INFO.value,
        status="success",
    )

    assert log.id is not None
    assert log.action == "login"
    assert log.user_id == "user_001"

    log2 = audit.log_login(
        username="test@example.com",
        success=False,
        ip_address="192.168.1.1",
    )

    assert log2.action == "login_failed"
    assert log2.level == AuditLevel.WARNING.value

    print("✅ Audit logger: OK")
    return True


def test_audit_query():
    """测试审计查询"""
    from tianlong_salesmaster.crm_pkg.rbac.audit import get_audit_logger, AuditQuery

    audit = get_audit_logger()
    audit._logs.clear()

    for i in range(10):
        audit.log(
            action="view" if i % 2 == 0 else "create",
            user_id=f"user_{i % 3}",
            username=f"user{i % 3}@example.com",
            tenant_id="tenant_001",
            resource="customer",
            resource_id=f"cust_{i}",
        )

    query = AuditQuery(user_id="user_0", tenant_id="tenant_001", limit=100)
    results = audit.query(query)
    assert len(results) == 4

    query2 = AuditQuery(action="create", limit=100)
    results2 = audit.query(query2)
    assert len(results2) == 5

    print("✅ Audit query: OK")
    return True


def test_audit_compliance_report():
    """测试合规报告"""
    from tianlong_salesmaster.crm_pkg.rbac.audit import get_audit_logger

    audit = get_audit_logger()
    audit._logs.clear()

    audit.log_login("admin@example.com", True, "192.168.1.1", tenant_id="tenant_001")
    audit.log_login("user@example.com", False, "192.168.1.2", tenant_id="tenant_001")

    audit.log_sensitive(
        action="data_export",
        user_id="user_001",
        username="admin@example.com",
        tenant_id="tenant_001",
        resource="customer",
        resource_id="cust_123",
    )

    report = audit.generate_compliance_report(
        tenant_id="tenant_001",
        start_date="2024-01-01T00:00:00",
        end_date="2099-12-31T23:59:59",
    )

    assert report["summary"]["total_operations"] == 3
    assert report["summary"]["successful_operations"] == 2
    assert report["security_events"]["failed_logins"] == 1
    assert report["security_events"]["sensitive_operations"] == 1

    print("✅ Audit compliance report: OK")
    return True


def test_rbac_context():
    """测试 RBAC 上下文"""
    try:
        from starlette.middleware.base import BaseHTTPMiddleware
    except ImportError:
        print("⏭️  RBAC context (starlette not available): SKIP")
        return True

    from tianlong_salesmaster.crm_pkg.rbac.middleware import RBACContext

    RBACContext.set_user(
        user_id="user_001",
        username="admin@example.com",
        role="admin",
        permissions=["user:view", "user:edit", "*"],
        tenant_id="tenant_001",
    )

    assert RBACContext.get_user_id() == "user_001"
    assert RBACContext.get_username() == "admin@example.com"
    assert RBACContext.get_role() == "admin"
    assert RBACContext.get_tenant_id() == "tenant_001"
    assert RBACContext.has_permission("user:view")
    assert RBACContext.has_permission("user:delete")
    assert RBACContext.has_permission("*")

    RBACContext.clear()
    assert RBACContext.get_user_id() is None

    print("✅ RBAC context: OK")
    return True


def test_audit_user_activity():
    """测试用户活动记录"""
    from tianlong_salesmaster.crm_pkg.rbac.audit import get_audit_logger

    audit = get_audit_logger()
    audit._logs.clear()

    for i in range(5):
        audit.log(
            action="view",
            user_id="user_001",
            username="user@example.com",
            tenant_id="tenant_001",
            resource="customer",
            resource_id=f"cust_{i}",
        )

    for i in range(3):
        audit.log(
            action="create",
            user_id="user_002",
            username="admin@example.com",
            tenant_id="tenant_001",
            resource="customer",
            resource_id=f"cust_new_{i}",
        )

    activity = audit.get_user_activity("user_001", days=30)
    assert len(activity) == 5

    activity2 = audit.get_user_activity("user_002", days=30)
    assert len(activity2) == 3

    print("✅ User activity: OK")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Testing RBAC + Audit System")
    print("=" * 60)
    print()

    tests = [
        ("RBAC permissions", test_rbac_permissions),
        ("RBAC roles", test_rbac_roles),
        ("Audit logger", test_audit_logger),
        ("Audit query", test_audit_query),
        ("Audit compliance report", test_audit_compliance_report),
        ("RBAC context", test_rbac_context),
        ("User activity", test_audit_user_activity),
    ]

    passed = 0
    for name, test_func in tests:
        print(f"Testing {name}...")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {name}: {e}")
            import traceback
            traceback.print_exc()
        print()

    print("=" * 60)
    print(f"Passed: {passed}/{len(tests)}")
    print("=" * 60)

    if passed == len(tests):
        print("\n✅ All RBAC + Audit tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️ {len(tests) - passed} test(s) failed")
        sys.exit(1)
