#!/usr/bin/env python3
"""测试 SaaS 模块"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from SentriKit_salesmaster.crm_pkg.saas import (
    Tenant, TenantUser, Subscription, PlanType,
    TenantStatus, UserStatus, JWTToken, RateLimiter,
)
from SentriKit_salesmaster.crm_pkg.saas.manager import TenantStore, SaaSManager


def test_tenant_create():
    """测试租户创建"""
    tenant = Tenant.create("测试公司", "test-company", company="测试公司")
    assert tenant.id is not None
    assert tenant.slug == "test-company"
    assert tenant.status == TenantStatus.PENDING.value
    assert tenant.subscription.plan == PlanType.FREE.value
    print("✅ test_tenant_create")


def test_user_password():
    """测试用户密码"""
    user = TenantUser.create("test-tenant", "user@test.com", "测试用户", "123456", "admin")
    assert user.check_password("123456") is True
    assert user.check_password("wrong") is False
    print("✅ test_user_password")


def test_jwt_token():
    """测试 JWT Token"""
    token = JWTToken.generate("tenant1", "user1", "secret")
    assert token is not None
    parts = token.split(".")
    assert len(parts) == 4
    payload = JWTToken.verify(token, "secret")
    assert payload is not None
    assert payload["tenant_id"] == "tenant1"
    assert payload["user_id"] == "user1"
    invalid = JWTToken.verify(token + "x", "secret")
    assert invalid is None
    print("✅ test_jwt_token")


def test_rate_limiter():
    """测试限流器"""
    key = "test:api"
    for i in range(10):
        ok = RateLimiter.check(key, 10)
        assert ok is True
    ok = RateLimiter.check(key, 10)
    assert ok is False
    remaining = RateLimiter.get_remaining(key, 10)
    assert remaining == 0
    print("✅ test_rate_limiter")


def test_saas_manager():
    """测试 SaaS 管理器（使用临时目录）"""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        from SentriKit_salesmaster.crm_pkg.saas.manager import TenantStore
        store = TenantStore(data_dir=tmpdir)
        manager = SaaSManager(store=store)
        result = manager.register_tenant(
            name="我的公司",
            slug="mycompany",
            admin_email="admin@mycompany.com",
            admin_name="管理员",
            admin_password="mypassword",
        )
        assert result["success"] is True
        tenant_id = result["tenant_id"]
        user_id = result["user_id"]
        assert tenant_id is not None
        assert user_id is not None
        login_result = manager.authenticate("admin@mycompany.com", "mypassword")
        assert login_result is not None
        assert login_result["tenant"]["id"] == tenant_id
        print("✅ test_saas_manager")


def run_all_tests():
    """运行所有测试"""
    print("\n=== 测试 SaaS 模块 ===\n")
    try:
        test_tenant_create()
        test_user_password()
        test_jwt_token()
        test_rate_limiter()
        test_saas_manager()
        print("\n🎉 所有测试通过！\n")
        return 0
    except Exception as e:
        print(f"\n❌ 测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
