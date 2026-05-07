"""测试 PostgreSQL 数据库层"""

import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir / "src"))


def test_database_import():
    """测试数据库模型导入"""
    try:
        from gavvy_salesmaster.core.storage.database import (
            Base, Tenant, TenantUser,
            Customer, Lead, Deal, Quote, Contract, Payment,
            AuditLog, WorkflowInstance,
            engine, SessionLocal,
        )

        assert Base is not None
        assert Tenant is not None
        assert TenantUser is not None
        assert Customer is not None
        assert Lead is not None
        assert Deal is not None
        assert Quote is not None
        assert Contract is not None
        assert Payment is not None
        assert AuditLog is not None

        print("✅ Database models import: OK")
        return True
    except ImportError as e:
        if "sqlalchemy" in str(e):
            print("⏭️  Database models import: SKIP (sqlalchemy not installed)")
            return True
        print(f"❌ Database models import: {e}")
        return False
    except Exception as e:
        print(f"❌ Database models import: {e}")
        return False


def test_repository_import():
    """测试 Repository 导入"""
    try:
        from gavvy_salesmaster.core.storage.pgrepo import (
            CustomerRepository, LeadRepository, DealRepository,
            QuoteRepository, ContractRepository, AuditLogRepository,
            get_customer_repository, get_audit_log_repository,
        )

        assert CustomerRepository is not None
        assert LeadRepository is not None
        assert AuditLogRepository is not None

        print("✅ Repository import: OK")
        return True
    except Exception as e:
        print(f"❌ Repository import: {e}")
        return False


def test_migration_import():
    """测试迁移工具导入"""
    try:
        from gavvy_salesmaster.core.storage.migration import (
            DataMigrator, migrate_to_postgres, MigrationRecord,
        )

        assert DataMigrator is not None
        assert migrate_to_postgres is not None

        print("✅ Migration tool import: OK")
        return True
    except Exception as e:
        print(f"❌ Migration tool import: {e}")
        return False


def test_database_models():
    """测试数据库模型结构"""
    try:
        from gavvy_salesmaster.core.storage.database import (
            Tenant, TenantUser, Customer, Lead, Deal,
            Quote, Contract, Payment, AuditLog,
        )

        assert hasattr(Tenant, "__tablename__")
        assert hasattr(TenantUser, "tenant_id")
        assert hasattr(Customer, "tenant_id")
        assert hasattr(Lead, "tenant_id")
        assert hasattr(AuditLog, "created_at")

        assert Tenant.__tablename__ == "tenants"
        assert Customer.__tablename__ == "customers"
        assert AuditLog.__tablename__ == "audit_logs"

        print("✅ Database models structure: OK")
        return True
    except Exception as e:
        print(f"❌ Database models structure: {e}")
        return False


def test_jsonb_support():
    """测试 JSONB 列支持"""
    try:
        from gavvy_salesmaster.core.storage.database import Customer

        from sqlalchemy import inspect

        mapper = inspect(Customer)
        custom_fields_col = mapper.columns.get("custom_fields")

        assert custom_fields_col is not None
        assert "jsonb" in str(custom_fields_col.type).lower()

        print("✅ JSONB support: OK")
        return True
    except Exception as e:
        print(f"❌ JSONB support: {e}")
        return False


def test_partition_info():
    """测试分区表信息"""
    try:
        from gavvy_salesmaster.core.storage.database import AuditLog

        assert hasattr(AuditLog, "__table_args__")

        table_args = AuditLog.__table_args__
        has_partition = False
        for arg in table_args:
            arg_str = str(arg)
            if "partition" in arg_str.lower():
                has_partition = True
                break

        assert has_partition, "AuditLog should be partitioned"

        print("✅ Partition table: OK")
        return True
    except Exception as e:
        print(f"❌ Partition table: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Testing PostgreSQL Database Layer")
    print("=" * 60)
    print()

    tests = [
        ("Database models import", test_database_import),
        ("Repository import", test_repository_import),
        ("Migration tool import", test_migration_import),
        ("Database models structure", test_database_models),
        ("JSONB support", test_jsonb_support),
        ("Partition table", test_partition_info),
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
        print("\n✅ All database tests passed!")
        print("\n📋 To initialize PostgreSQL database:")
        print("   1. Install dependencies: pip install sqlalchemy psycopg2-binary")
        print("   2. Set DATABASE_URL environment variable")
        print("   3. Run: python -c 'from gavvy_salesmaster.core.storage.database import init_database; init_database()'")
        sys.exit(0)
    else:
        print(f"\n⚠️ {len(tests) - passed} test(s) failed")
        sys.exit(1)
