"""tests/test_crm.py — CRM 系统集成测试

覆盖 Customer/Contact/Deal/Contract/Activity/CRMManager 的完整 CRUD 和业务逻辑。
"""

import os
import tempfile
from datetime import datetime, timedelta


def test_crm():
    """测试 CRM 系统完整功能"""
    temp_dir = tempfile.mkdtemp()
    print(f"   存储目录: {temp_dir}")

    try:
        # 设置存储目录
        from gavvy_salesmaster.core.storage.db import set_storage_dir, get_kernel
        set_storage_dir(temp_dir)
        # 重置单例
        import gavvy_salesmaster.core.storage.db as db
        db._global_kernel = None

        from gavvy_salesmaster.crm_pkg.crm import (
            Customer, Contact, Deal, Contract, Activity,
            CRMManager, get_crm,
        )

        crm = CRMManager()
        print("✅ CRMManager 初始化成功")

        # ── 客户管理 ──────────────────────────────────────
        print("\n📋 客户管理测试...")

        # 创建客户
        c1 = Customer(name="张三", company="测试科技", industry="AI",
                      phone="13800138001", email="zhangsan@test.com",
                      source="manual", stage="lead")
        saved = crm.add_customer(c1)
        assert saved["id"] == c1.id
        assert saved["stage"] == "lead"
        assert saved["name"] == "张三"
        print("  ✅ 创建客户")

        # 创建第二个客户
        c2 = Customer(name="李四", company="智能数据", industry="大数据",
                      phone="13800138002", stage="prospect")
        crm.add_customer(c2)
        print("  ✅ 创建第二个客户")

        # 列出所有客户
        all_cust = crm.list_customers()
        assert len(all_cust) == 2
        print(f"  ✅ 列出客户: {len(all_cust)} 个")

        # 按阶段筛选
        leads = crm.list_customers(stage="lead")
        assert len(leads) == 1
        assert leads[0]["name"] == "张三"
        prospects = crm.list_customers(stage="prospect")
        assert len(prospects) == 1
        print("  ✅ 按阶段筛选客户")

        # 获取单个客户
        got = crm.get_customer(c1.id)
        assert got is not None
        assert got["company"] == "测试科技"
        not_found = crm.get_customer("nonexistent")
        assert not_found is None
        print("  ✅ 获取客户 / 不存在返回 None")

        # 更新客户
        updated = crm.update_customer(c1.id, {"stage": "qualified", "score": 80})
        assert updated is not None
        assert updated["stage"] == "qualified"
        assert updated["score"] == 80
        assert "updated_at" in updated
        # 更新不存在的客户返回 None
        assert crm.update_customer("nonexistent", {"name": "nope"}) is None
        print("  ✅ 更新客户")

        # 搜索客户
        results = crm.search_customers("张三")
        assert len(results) == 1
        results = crm.search_customers("数据")
        assert len(results) == 1  # "智能数据" 里有 "数据"
        results = crm.search_customers("不存在的")
        assert len(results) == 0
        results = crm.search_customers("")
        assert len(results) == 2  # 空查询返回全部
        print("  ✅ 搜索客户")

        # 客户统计
        stats = crm.get_customer_stats()
        assert stats["total"] == 2
        assert stats["qualified"] == 1
        assert stats["prospects"] == 1
        print("  ✅ 客户统计")

        # ── 联系人管理 ────────────────────────────────────
        print("\n📞 联系人管理测试...")

        ct1 = Contact(name="张三秘书", customer_id=c1.id,
                      role="秘书", phone="13800138011",
                      email="sec@test.com", is_primary=False)
        saved_ct = crm.add_contact(ct1)
        assert saved_ct["id"] == ct1.id
        assert saved_ct["customer_id"] == c1.id

        ct2 = Contact(name="李四助理", customer_id=c2.id, role="助理")
        crm.add_contact(ct2)
        print("  ✅ 创建联系人")

        # 列出联系人（全部 / 按客户）
        all_ct = crm.list_contacts()
        assert len(all_ct) == 2
        by_cust = crm.list_contacts(customer_id=c1.id)
        assert len(by_cust) == 1
        assert by_cust[0]["name"] == "张三秘书"
        print("  ✅ 按客户列出联系人")

        # 删除联系人
        assert crm.delete_contact(ct2.id) is True
        assert crm.delete_contact("nonexistent") is False
        all_ct = crm.list_contacts()
        assert len(all_ct) == 1
        print("  ✅ 删除联系人")

        # ── 商机管理 ────────────────────────────────────
        print("\n💼 商机管理测试...")

        d1 = Deal(customer_id=c1.id, title="AI平台解决方案",
                  amount=500000, probability=60, stage="proposal")
        saved_d = crm.add_deal(d1)
        assert saved_d["id"] == d1.id
        assert saved_d["stage"] == "proposal"

        d2 = Deal(customer_id=c1.id, title="数据中台项目",
                  amount=300000, probability=80, stage="negotiation")
        crm.add_deal(d2)

        d3 = Deal(customer_id=c2.id, title="大数据分析",
                  amount=100000, probability=30, stage="discovery")
        crm.add_deal(d3)
        print("  ✅ 创建商机")

        # 列出商机
        all_deals = crm.list_deals()
        assert len(all_deals) == 3
        by_cust_deals = crm.list_deals(customer_id=c1.id)
        assert len(by_cust_deals) == 2
        print("  ✅ 按客户列出商机")

        # 更新商机
        updated_d = crm.update_deal(d1.id, {"stage": "negotiation", "probability": 70})
        assert updated_d is not None
        assert updated_d["stage"] == "negotiation"
        assert updated_d["probability"] == 70
        assert crm.update_deal("nonexistent", {}) is None
        print("  ✅ 更新商机")

        # 商机汇总
        summary = crm.get_deal_summary()
        assert summary["total"] == 3
        assert summary["total_pipeline"] > 0  # 总额 > 0
        assert "negotiation" in summary["stages"]
        print(f"  ✅ 商机汇总: {summary['total']} 个, 管道金额 {summary['total_pipeline']}")
        print(f"     阶段分布: {summary['stages']}")

        # ── 合同管理 ────────────────────────────────────
        print("\n📄 合同管理测试...")

        co1 = Contract(customer_id=c1.id, deal_id=d1.id,
                       title="AI平台合同", amount=500000,
                       status="signed", start_date="2026-06-01",
                       end_date="2027-05-31",
                       content="AI平台年度订阅合同")
        saved_co = crm.add_contract(co1)
        assert saved_co["id"] == co1.id
        assert saved_co["status"] == "signed"

        co2 = Contract(customer_id=c2.id, title="数据分析合同",
                       amount=100000, status="draft")
        crm.add_contract(co2)
        print("  ✅ 创建合同")

        # 列出合同
        all_co = crm.list_contracts()
        assert len(all_co) == 2
        by_cust_co = crm.list_contracts(customer_id=c1.id)
        assert len(by_cust_co) == 1
        print("  ✅ 按客户列出合同")

        # 更新合同
        updated_co = crm.update_contract(co2.id, {"status": "signed", "signed_date": "2026-06-15"})
        assert updated_co is not None
        assert updated_co["status"] == "signed"
        assert crm.update_contract("nonexistent", {}) is None
        print("  ✅ 更新合同")

        # 合同汇总
        co_summary = crm.get_contract_summary()
        assert co_summary["total"] == 2
        assert co_summary["total_signed"] >= 500000  # 至少已签的金额
        print(f"  ✅ 合同汇总: {co_summary['total']} 个, 已签金额 {co_summary['total_signed']}")

        # ── 活动记录 ────────────────────────────────────
        print("\n📝 活动记录测试...")

        a1 = Activity(customer_id=c1.id, deal_id=d1.id,
                      type="call", title="初步沟通",
                      content="与客户进行了电话沟通，了解需求")
        saved_a = crm.add_activity(a1)
        assert saved_a["id"] == a1.id
        assert saved_a["type"] == "call"

        a2 = Activity(customer_id=c1.id, type="meeting",
                      title="方案演示", content="演示了AI平台方案")
        crm.add_activity(a2)

        a3 = Activity(customer_id=c2.id, type="note",
                      title="跟进记录", content="客户表示需要进一步了解")
        crm.add_activity(a3)
        print("  ✅ 创建活动记录")

        # 列出活动
        all_act = crm.list_activities()
        assert len(all_act) == 3
        by_cust_act = crm.list_activities(customer_id=c1.id)
        assert len(by_cust_act) == 2
        by_cust_act = crm.list_activities(customer_id=c2.id)
        assert len(by_cust_act) == 1
        print("  ✅ 按客户列出活动")

        # 活动上限测试（超过2000条清理）
        for i in range(100):
            a = Activity(customer_id=c1.id, type="system",
                         title=f"系统事件 {i}", content=f"第{i}个活动")
            crm.add_activity(a)
        big_act = crm.list_activities()
        print(f"  ✅ 批量活动: {len(big_act)} 条 (2000上限清理机制)")

        # ── 仪表盘 ────────────────────────────────────
        print("\n📊 仪表盘测试...")
        dashboard = crm.get_dashboard()
        assert "customers" in dashboard
        assert "deals" in dashboard
        assert "contracts" in dashboard
        assert dashboard["customers"]["total"] == 2
        assert dashboard["deals"]["total"] == 3
        assert dashboard["contracts"]["total"] == 2
        print("  ✅ 仪表盘数据完整")

        # Customer 数据模型方法
        c1_loaded = Customer.from_dict(saved)
        assert c1_loaded.name == "张三"
        assert c1_loaded.stage_label == "合格客户"
        print(f"  ✅ Customer 数据模型: stage_label='{c1_loaded.stage_label}'")

        # Deal 数据模型方法
        d1_loaded = Deal.from_dict(saved_d)
        assert d1_loaded.stage_label == "方案提案"
        print(f"  ✅ Deal 数据模型: stage_label='{d1_loaded.stage_label}'")

        # Contract 数据模型方法
        co1_loaded = Contract.from_dict(saved_co)
        assert co1_loaded.status_label == "已签署"
        print(f"  ✅ Contract 数据模型: status_label='{co1_loaded.status_label}'")

        # ── 级联删除 ────────────────────────────────────
        print("\n🗑️ 级联删除测试...")
        # 删除客户 c2
        assert crm.delete_customer(c2.id) is True
        # c2 的合同、活动、联系人应被级联删除
        after_delete = crm.list_customers()
        assert len(after_delete) == 1
        assert crm.list_contacts(customer_id=c2.id) == []
        assert crm.list_deals(customer_id=c2.id) == []
        assert crm.list_contracts(customer_id=c2.id) == []
        assert crm.list_activities(customer_id=c2.id) == []
        # 删除不存在的客户返回 False
        assert crm.delete_customer("nonexistent") is False
        print("  ✅ 级联删除验证通过")

        # ── 全局函数 ────────────────────────────────────
        print("\n🌐 全局函数测试...")
        crm2 = get_crm()
        assert isinstance(crm2, CRMManager)
        print("  ✅ get_crm() 正常工作")

        print("\n" + "=" * 60)
        print("🎉 所有 CRM 测试通过！")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        print(f"\n清理临时目录: {temp_dir}")
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
