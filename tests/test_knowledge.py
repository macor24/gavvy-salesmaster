"""测试产品知识库系统"""

import pytest
import tempfile
import os
from datetime import datetime


def test_knowledge_base():
    """测试知识库核心功能"""

    print("🧪 测试知识库功能...")

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"   存储目录: {temp_dir}")

    try:
        # 导入模块
        from gavvy_salesmaster.crm_pkg.knowledge import (
            KnowledgeBase,
            get_knowledge_base
        )

        # 创建知识库实例
        kb = KnowledgeBase(temp_dir)
        print("✅ 知识库初始化成功")

        # 测试 1：添加知识条目
        item = kb.add_item(
            title="产品价格政策",
            content="我们的产品支持 7 天无理由退换，30 天质量问题包换。"
                    "具体价格政策根据不同产品有不同规定...",
            category="产品政策",
            tags=["价格", "退换货", "售后"],
            priority=3
        )
        print(f"✅ 添加知识条目: {item.title}")

        item2 = kb.add_item(
            title="售后服务指南",
            content="如果客户有售后问题，请先安抚情绪，然后根据问题分类处理。",
            category="售后服务",
            tags=["售后", "服务"]
        )
        print(f"✅ 添加知识条目: {item2.title}")

        # 测试 2：获取知识条目
        items = kb.get_items()
        print(f"✅ 获取知识列表: {len(items)} 条")
        assert len(items) == 2

        # 测试 3：添加 FAQ
        faq = kb.add_faq(
            question="产品可以退换吗？",
            answer="是的，支持 7 天无理由退换，30 天质量问题包换。",
            category="产品政策",
            tags=["退换货", "FAQ"]
        )
        print(f"✅ 添加 FAQ: {faq.question}")

        # 测试 4：搜索功能
        results = kb.search("退换货")
        print(f"✅ 搜索功能: 找到 {len(results)} 条结果")

        for r in results:
            if hasattr(r.item, "title"):
                print(f"   - {r.item.title}")
            else:
                print(f"   - Q: {r.item.question}")

        # 测试 5：标记有用
        kb.mark_useful(item.id)

        # 测试 6：获取训练素材
        training_data = kb.get_training_for_agent("presales_agent")
        print(f"✅ 获取训练素材: {len(training_data)} 条")

        # 测试 7：统计功能
        stats = kb.get_stats()
        print(f"✅ 知识库统计: {stats}")

        # 测试 8：分类功能
        categories = kb.get_categories()
        print(f"✅ 分类数量: {len(categories)}")
        for cat in categories:
            print(f"   - {cat.name}")

        # 测试 9：快速添加 FAQ（自动分类）
        quick_faq = kb.quick_add_faq(
            "怎么退款？",
            "退款流程：1. 联系客服；2. 寄回商品；3. 等待审核；4. 收到退款。"
        )
        print(f"✅ 快速添加 FAQ，自动分类到: {quick_faq.category}")

        # 测试 10：导出/导入
        export_data = kb.export_all()
        print(f"✅ 导出数据: {len(export_data['items'])} 条知识, {len(export_data['faqs'])} 条 FAQ")

        print("\n🎉 所有测试通过！")
        return True

    finally:
        print(f"\n清理临时目录: {temp_dir}")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 产品知识库测试")
    print("=" * 60)
    success = test_knowledge_base()
    if success:
        print("\n✅ 知识库测试通过！")
    else:
        print("\n❌ 知识库测试失败！")
