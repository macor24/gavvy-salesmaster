"""测试 SaaS 集成到 app.py"""

import os
import sys
from pathlib import Path

# Add src to path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir / "src"))

def test_import():
    """测试 SaaS 模块可以被导入"""
    try:
        from gavvy_salesmaster.crm_pkg.saas import Tenant, TenantUser, TenantContext, JWTToken, RateLimiter, PlanType
        from gavvy_salesmaster.crm_pkg.saas.manager import SaaSManager, TenantStore, get_saas_manager
        print("✅ SaaS core modules: OK")
        return True
    except Exception as e:
        print(f"❌ SaaS core modules: {e}")
        return False

def test_app_file_exists():
    """测试 app.py 文件和内容检查"""
    app_path = root_dir / "src" / "gavvy_salesmaster" / "app.py"
    if not app_path.exists():
        print(f"❌ app.py not found: {app_path}")
        return False

    content = app_path.read_text(encoding="utf-8")
    checks = [
        ("SaaS 多租户" in content, "SaaS section exists"),
        ("SaaSAuthMiddleware" in content, "Middleware import"),
        ("saas_router" in content, "Router import"),
        ("SALES_USE_SAAS" in content, "Env var check"),
    ]
    all_ok = True
    for ok, msg in checks:
        if ok:
            print(f"✅ {msg}")
        else:
            print(f"❌ {msg}")
            all_ok = False
    return all_ok

def test_saas_basic():
    """测试 SaaS 基础功能（无 FastAPI）"""
    try:
        from gavvy_salesmaster.crm_pkg.saas import Tenant, TenantUser, Subscription
        from gavvy_salesmaster.crm_pkg.saas.manager import get_saas_manager

        # 创建测试租户
        tenant = Tenant.create("测试公司", "test-company", "科技有限公司")
        user = TenantUser.create(tenant.id, "test@example.com", "测试用户", "password123", "admin")

        assert tenant.slug == "test-company"
        assert user.email == "test@example.com"
        print("✅ SaaS basic functions: OK")
        return True
    except Exception as e:
        print(f"❌ SaaS basic functions: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing SaaS Integration")
    print("=" * 60)
    print()

    passed = 0
    total = 3

    if test_import():
        passed += 1
    print()

    if test_app_file_exists():
        passed += 1
    print()

    if test_saas_basic():
        passed += 1
    print()

    print("=" * 60)
    print(f"Passed: {passed}/{total}")
    print("=" * 60)

    if passed == total:
        print("\n✅ All integration tests passed!")
        print("\n📋 Usage:")
        print("  Enable SaaS: set SALES_USE_SAAS=true")
        print("  Start: python -m gavvy_salesmaster.app")
        print("  API docs: http://localhost:8877/docs")
        sys.exit(0)
    else:
        print("\n❌ Some integration tests failed!")
        sys.exit(1)
