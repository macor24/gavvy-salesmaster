#!/usr/bin/env python
"""验证数据库迁移结果"""

from gavvy_salesmaster.storage import get_db_context
from gavvy_salesmaster.storage.db_sqlite import Customer, Lead, Deal, Quote, Contract

print("=" * 60)
print("数据库验证")
print("=" * 60)

with get_db_context() as db:
    print(f"\n客户表记录数: {db.query(Customer).count()}")
    print(f"交易表记录数: {db.query(Deal).count()}")
    print(f"报价单记录数: {db.query(Quote).count()}")
    print(f"合同表记录数: {db.query(Contract).count()}")
    
    print("\n客户列表:")
    customers = db.query(Customer).all()
    for c in customers:
        print(f"  - {c.name} (ID: {c.id[:8]}...)")

print("\n" + "=" * 60)
print("验证完成！")
print("=" * 60)
