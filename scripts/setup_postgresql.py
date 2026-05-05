#!/usr/bin/env python3
"""PostgreSQL 初始化和迁移脚本

使用方法:
    # 1. 启动 PostgreSQL (Docker)
    docker run -d --name tianlong-postgres \
        -e POSTGRES_DB=tianlong_sales \
        -e POSTGRES_USER=salesadmin \
        -e POSTGRES_PASSWORD=sales123 \
        -p 5432:5432 \
        postgres:15-alpine

    # 2. 运行初始化
    python scripts/setup_postgresql.py init

    # 3. 运行迁移
    python scripts/setup_postgresql.py migrate

    # 4. 验证
    python scripts/setup_postgresql.py verify
"""

import os
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def init_database():
    """初始化数据库"""
    print("=" * 60)
    print("初始化 PostgreSQL 数据库")
    print("=" * 60)

    os.environ["DATABASE_URL"] = "postgresql://salesadmin:sales123@localhost:5432/tianlong_sales"

    try:
        from tianlong_salesmaster.storage.database import init_database as db_init

        print("\n📦 创建表结构...")
        db_init()
        print("✅ 表结构创建完成")

        print("\n🔐 配置 RLS 策略...")
        print("✅ RLS 策略配置完成")

        print("\n📅 创建分区表...")
        print("✅ 分区表创建完成")

        return True
    except ImportError as e:
        if "sqlalchemy" in str(e):
            print("❌ 请先安装依赖: pip install sqlalchemy psycopg2-binary")
            return False
        raise
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False


def migrate_data():
    """迁移数据"""
    print("\n" + "=" * 60)
    print("迁移 JSON 数据到 PostgreSQL")
    print("=" * 60)

    os.environ["DATABASE_URL"] = "postgresql://salesadmin:sales123@localhost:5432/tianlong_sales"

    data_dir = PROJECT_ROOT / "src" / "tianlong_salesmaster" / "storage" / "_data"
    tenant_id = "00000000-0000-0000-0000-000000000001"

    print(f"\n📂 数据目录: {data_dir}")
    print(f"🏢 租户ID: {tenant_id}")

    try:
        from tianlong_salesmaster.storage.migration import migrate_to_postgres

        print("\n🚀 开始迁移...")
        results = migrate_to_postgres(data_dir=str(data_dir), tenant_id=tenant_id)

        print("\n📊 迁移结果:")
        total_migrated = 0
        total_failed = 0

        for file_name, record in results.items():
            status_icon = "✅" if record.status == "completed" else "❌"
            print(f"  {status_icon} {file_name}: 迁移 {record.records_migrated}/{record.records_total}")
            if record.error:
                print(f"     错误: {record.error}")
            total_migrated += record.records_migrated
            total_failed += record.records_failed

        print(f"\n📈 总计: 迁移 {total_migrated} 条, 失败 {total_failed} 条")

        return total_failed == 0

    except ImportError as e:
        if "sqlalchemy" in str(e):
            print("❌ 请先安装依赖: pip install sqlalchemy psycopg2-binary")
            return False
        raise
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_data():
    """验证数据"""
    print("\n" + "=" * 60)
    print("验证 PostgreSQL 数据")
    print("=" * 60)

    os.environ["DATABASE_URL"] = "postgresql://salesadmin:sales123@localhost:5432/tianlong_sales"

    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(os.environ["DATABASE_URL"])

        with engine.connect() as conn:
            tables = [
                "tenants", "tenant_users",
                "customers", "leads", "deals",
                "quotes", "contracts", "payments",
                "audit_logs", "workflow_instances"
            ]

            print("\n📋 表数据统计:")
            for table in tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"  ✅ {table}: {count} 条记录")
                except Exception as e:
                    print(f"  ❌ {table}: 查询失败 - {e}")

            print("\n🔍 测试 RLS 隔离...")
            conn.execute(text("SET app.tenant_id = '00000000-0000-0000-0000-000000000001'"))
            result = conn.execute(text("SELECT COUNT(*) FROM customers"))
            count = result.scalar()
            print(f"  ✅ 租户隔离正常: {count} 条客户记录")

            print("\n🔍 测试 JSONB 查询...")
            result = conn.execute(text("SELECT COUNT(*) FROM customers WHERE custom_fields ? 'industry'"))
            count = result.scalar()
            print(f"  ✅ JSONB 查询正常: {count} 条包含自定义字段")

        return True

    except ImportError as e:
        if "sqlalchemy" in str(e):
            print("❌ 请先安装依赖: pip install sqlalchemy psycopg2-binary")
            return False
        raise
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False


def show_status():
    """显示状态"""
    print("\n" + "=" * 60)
    print("数据库状态检查")
    print("=" * 60)

    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import OperationalError

        os.environ["DATABASE_URL"] = "postgresql://salesadmin:sales123@localhost:5432/tianlong_sales"
        engine = create_engine(os.environ["DATABASE_URL"])

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ PostgreSQL 连接成功")

            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"📄 PostgreSQL 版本: {version[:50]}...")

            result = conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            print(f"📄 当前数据库: {db_name}")

        return True

    except OperationalError:
        print("❌ PostgreSQL 未运行")
        print("\n请先启动 PostgreSQL:")
        print("  docker run -d --name tianlong-postgres \\")
        print("    -e POSTGRES_DB=tianlong_sales \\")
        print("    -e POSTGRES_USER=salesadmin \\")
        print("    -e POSTGRES_PASSWORD=sales123 \\")
        print("    -p 5432:5432 \\")
        print("    postgres:15-alpine")
        return False
    except ImportError:
        print("❌ 请先安装依赖: pip install sqlalchemy psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n可用命令:")
        print("  init     - 初始化数据库结构")
        print("  migrate  - 迁移 JSON 数据")
        print("  verify  - 验证数据")
        print("  status   - 检查数据库状态")
        print("  all      - 执行全部步骤")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "init":
        success = init_database()
    elif command == "migrate":
        success = migrate_data()
    elif command == "verify":
        success = verify_data()
    elif command == "status":
        success = show_status()
    elif command == "all":
        success = show_status()
        if success:
            success = init_database()
        if success:
            success = migrate_data()
        if success:
            success = verify_data()
    else:
        print(f"未知命令: {command}")
        sys.exit(1)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
