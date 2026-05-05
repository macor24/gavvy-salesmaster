"""测试报价与合同管理系统"""

import tempfile
import os
from datetime import datetime, timedelta


def test_quotes_and_contracts():
    """测试报价与合同管理"""

    print("=" * 60)
    print("🧪 测试报价与合同管理系统")
    print("=" * 60)

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"   存储目录: {temp_dir}")

    try:
        # 导入模块
        from SentriKit_salesmaster.crm_pkg.quotes import (
            ProductManager,
            QuoteManager,
            ContractManager,
            TemplateManager,
        )

        # 创建管理器实例
        pm = ProductManager(temp_dir)
        qm = QuoteManager(temp_dir)
        cm = ContractManager(temp_dir)
        tmpl_mgr = TemplateManager(temp_dir)

        print("✅ 管理器初始化成功")

        # ── 产品管理测试 ──────────────────────────────────

        print("\n📦 产品管理测试...")

        # 创建产品
        product1 = pm.create_product(
            name="企业版套餐",
            description="为企业客户提供的完整解决方案",
            sku="ENT-2024-001",
            unit_price=50000.0,
            cost_price=25000.0,
            category="软件产品",
            tags=["企业", "套餐"]
        )
        print(f"✅ 创建产品: {product1.name}")

        product2 = pm.create_product(
            name="专业版套餐",
            description="为中大型客户提供的专业解决方案",
            sku="PRO-2024-001",
            unit_price=30000.0,
            cost_price=15000.0,
            category="软件产品",
            tags=["专业", "套餐"]
        )
        print(f"✅ 创建产品: {product2.name}")

        # 获取产品列表
        products = pm.get_products()
        print(f"✅ 产品总数: {len(products)}")

        # 更新产品
        product1.description = "为企业客户提供的完整解决方案（更新）"
        pm.update_product(product1)
        print(f"✅ 更新产品: {product1.name}")

        # ── 报价管理测试 ──────────────────────────────────

        print("\n💰 报价管理测试...")

        # 创建报价单
        quote = qm.create_quote(
            title="客户A企业方案",
            customer_id="CUST-001",
            customer_name="客户A科技有限公司",
            salesperson="销售员A",
            valid_days=30
        )
        print(f"✅ 创建报价单: {quote.quote_number}")

        # 添加报价明细
        qm.add_quote_item(
            quote_id=quote.id,
            product_id=product1.id,
            product_name=product1.name,
            quantity=2,
            unit_price=product1.unit_price,
            discount_percent=10.0,
            tax_percent=13.0
        )
        print(f"✅ 添加报价明细: 企业版 x2")

        qm.add_quote_item(
            quote_id=quote.id,
            product_id=product2.id,
            product_name=product2.name,
            quantity=1,
            unit_price=product2.unit_price,
            discount_percent=5.0,
            tax_percent=13.0
        )
        print(f"✅ 添加报价明细: 专业版 x1")

        # 重新获取报价查看总价
        updated_quote = qm.get_quote(quote.id)
        print(f"   报价总额: {updated_quote.total_amount:.2f}")

        # 更新状态：待审批 → 审批 → 发送 → 接受
        qm.update_quote_status(quote.id, "pending_approval")
        print(f"✅ 状态更新: 待审批")

        qm.update_quote_status(quote.id, "approved")
        print(f"✅ 状态更新: 已审批")

        qm.update_quote_status(quote.id, "sent")
        print(f"✅ 状态更新: 已发送")

        qm.update_quote_status(quote.id, "accepted")
        print(f"✅ 状态更新: 已接受")

        # 报价统计
        quote_stats = qm.get_stats()
        print(f"✅ 报价统计: {quote_stats}")

        # ── 合同管理测试 ──────────────────────────────────

        print("\n📝 合同管理测试...")

        # 从报价单创建合同
        contract = cm.create_contract_from_quote(
            quote_id=quote.id,
            title="客户A技术服务合同",
            salesperson="销售员A"
        )
        print(f"✅ 创建合同: {contract.contract_number}")
        print(f"   合同总额: {contract.total_amount:.2f}")

        # 更新状态
        cm.update_contract_status(contract.id, "pending_approval")
        print(f"✅ 合同状态: 待审批")

        cm.update_contract_status(contract.id, "signed")
        print(f"✅ 合同状态: 已签署")

        cm.update_contract_status(contract.id, "fulfilling")
        print(f"✅ 合同状态: 履行中")

        # 添加自定义付款计划
        cm.add_payment_plan(
            contract_id=contract.id,
            description="额外服务费用",
            amount=10000.0
        )
        print(f"✅ 添加付款计划")

        # 标记第一期付款完成
        first_plan = contract.payment_plans[0] if contract.payment_plans else None
        if first_plan:
            cm.mark_payment_paid(contract.id, first_plan.id)
            print(f"✅ 标记付款完成: {first_plan.description}")

        # 合同统计
        contract_stats = cm.get_stats()
        print(f"✅ 合同统计: {contract_stats}")

        # ── 模板管理测试 ──────────────────────────────────

        print("\n📄 模板管理测试...")

        # 获取默认模板
        default_quote_template = tmpl_mgr.get_default_quote_template()
        if default_quote_template:
            print(f"✅ 默认报价模板: {default_quote_template.name}")

        # 获取所有模板
        quote_templates = tmpl_mgr.get_quote_templates()
        contract_templates = tmpl_mgr.get_contract_templates()
        print(f"   报价模板数: {len(quote_templates)}")
        print(f"   合同模板数: {len(contract_templates)}")

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
    success = test_quotes_and_contracts()
    if success:
        print("\n✅ 报价与合同管理系统测试通过！")
    else:
        print("\n❌ 报价与合同管理系统测试失败！")
