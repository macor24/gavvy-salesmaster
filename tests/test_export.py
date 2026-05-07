"""测试导出功能"""

import tempfile
import os
from datetime import datetime, timedelta


def test_export():
    """测试导出功能"""

    print("=" * 60)
    print("🧪 测试导出功能")
    print("=" * 60)

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"   输出目录: {temp_dir}")

    try:
        # 导入模块
        from gavvy_salesmaster.crm_pkg.export import ExportManager
        from gavvy_salesmaster.crm_pkg.quotes import (
            ProductManager,
            QuoteManager,
            ContractManager,
        )

        # 创建管理器
        exporter = ExportManager()
        pm = ProductManager()
        qm = QuoteManager()
        cm = ContractManager()

        print("✅ 管理器初始化成功")

        # 创建测试数据
        print("\n📦 创建测试数据...")

        product = pm.create_product(
            name="企业版套餐",
            description="为企业客户提供的完整解决方案",
            sku="ENT-2024-001",
            unit_price=50000.0,
            category="软件产品"
        )
        print(f"✅ 创建产品: {product.name}")

        quote = qm.create_quote(
            title="客户A企业方案",
            customer_name="客户A科技有限公司",
            salesperson="销售员A",
            valid_days=30
        )

        qm.add_quote_item(
            quote_id=quote.id,
            product_id=product.id,
            product_name=product.name,
            quantity=2,
            unit_price=product.unit_price,
            discount_percent=10.0,
            tax_percent=13.0
        )
        print(f"✅ 创建报价单: {quote.quote_number}")

        qm.update_quote_status(quote.id, "accepted")
        contract = cm.create_contract_from_quote(quote.id, title="客户A技术服务合同")
        print(f"✅ 创建合同: {contract.contract_number}")

        # ── 测试 Excel 导出 ──────────────────────────────────

        print("\n📊 测试 Excel 导出...")

        quote_excel = os.path.join(temp_dir, f"报价单_{quote.quote_number}.csv")
        exporter.export_quote_to_excel(quote, quote_excel)
        print(f"✅ 报价单导出 Excel: {os.path.basename(quote_excel)}")

        contract_excel = os.path.join(temp_dir, f"合同_{contract.contract_number}.csv")
        exporter.export_contract_to_excel(contract, contract_excel)
        print(f"✅ 合同导出 Excel: {os.path.basename(contract_excel)}")

        products_excel = os.path.join(temp_dir, "产品目录.csv")
        exporter.export_products_to_excel([product], products_excel)
        print(f"✅ 产品目录导出 Excel: {os.path.basename(products_excel)}")

        # ── 测试 HTML 导出 ──────────────────────────────────

        print("\n🌐 测试 HTML 导出...")

        quote_html = os.path.join(temp_dir, f"报价单_{quote.quote_number}.html")
        exporter.export_quote_to_html(quote, quote_html)
        print(f"✅ 报价单导出 HTML: {os.path.basename(quote_html)}")

        contract_html = os.path.join(temp_dir, f"合同_{contract.contract_number}.html")
        exporter.export_contract_to_html(contract, contract_html)
        print(f"✅ 合同导出 HTML: {os.path.basename(contract_html)}")

        # ── 测试 Word 导出 ──────────────────────────────────

        print("\n📝 测试 Word 导出...")

        quote_word = os.path.join(temp_dir, f"报价单_{quote.quote_number}.doc")
        exporter.export_quote_to_word(quote, quote_word)
        print(f"✅ 报价单导出 Word: {os.path.basename(quote_word)}")

        contract_word = os.path.join(temp_dir, f"合同_{contract.contract_number}.doc")
        exporter.export_contract_to_word(contract, contract_word)
        print(f"✅ 合同导出 Word: {os.path.basename(contract_word)}")

        # ── 测试 PDF 导出 ──────────────────────────────────

        print("\n📄 测试 PDF 导出...")

        quote_pdf = os.path.join(temp_dir, f"报价单_{quote.quote_number}.pdf")
        result = exporter.export_quote_to_pdf(quote, quote_pdf)
        print(f"✅ 报价单导出 PDF: {os.path.basename(result)}")

        contract_pdf = os.path.join(temp_dir, f"合同_{contract.contract_number}.pdf")
        result = exporter.export_contract_to_pdf(contract, contract_pdf)
        print(f"✅ 合同导出 PDF: {os.path.basename(result)}")

        # ── 测试自动格式检测 ──────────────────────────────────

        print("\n🔍 测试自动格式检测...")

        auto_excel = exporter.export_quote(quote, os.path.join(temp_dir, "auto.csv"))
        print(f"✅ 自动检测 CSV: {os.path.basename(auto_excel)}")

        auto_html = exporter.export_quote(quote, os.path.join(temp_dir, "auto.html"))
        print(f"✅ 自动检测 HTML: {os.path.basename(auto_html)}")

        # ── 显示输出文件列表 ──────────────────────────────────

        print("\n📁 生成的文件:")
        for f in sorted(os.listdir(temp_dir)):
            filepath = os.path.join(temp_dir, f)
            size = os.path.getsize(filepath)
            print(f"   {f} ({size:,} bytes)")

        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
        print(f"\n输出目录: {temp_dir}")

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_export()
    if success:
        print("\n✅ 导出功能测试通过！")
    else:
        print("\n❌ 导出功能测试失败！")
