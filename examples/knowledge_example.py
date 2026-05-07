#!/usr/bin/env python3
"""
📚 产品知识库使用示例
========================

本示例展示如何使用产品知识库系统。

功能包括：
- 添加知识条目和 FAQ
- 智能搜索
- Agent 训练
- 分类管理

"""

from __future__ import annotations


def main():
    """知识库系统使用示例"""
    print("=" * 60)
    print("📚 产品知识库示例")
    print("=" * 60)
    print()

    try:
        # 导入模块
        from gavvy_salesmaster.knowledge import KnowledgeBase

        # 创建知识库实例
        print("👉 1. 初始化知识库...")
        kb = KnowledgeBase()
        print(f"   知识库已创建: {kb}")
        print()

        # 添加示例知识条目
        print("👉 2. 添加示例知识条目...")

        # 产品政策类
        kb.add_item(
            title="产品价格政策",
            content="我们的产品支持7天无理由退换，30天质量问题包换。具体价格根据不同产品有不同规定。"
            "价格折扣政策：批量购买享受9折优惠，年度会员享受8折优惠。",
            category="产品政策",
            tags=["价格", "退换货", "折扣", "售后"],
            priority=3
        )

        kb.add_item(
            title="会员权益说明",
            content="会员用户享受：专属客服、优先发货、生日礼包、积分兑换。",
            category="产品政策",
            tags=["会员", "权益", "服务"],
            priority=2
        )

        # 售后服务类
        kb.add_item(
            title="售后服务指南",
            content="如果客户有售后问题，请先安抚情绪，然后分类处理。"
                    "一般问题: 提供解决方案。复杂问题: 请转人工。",
            category="售后服务",
            tags=["售后", "服务", "客服"],
            priority=2
        )

        kb.add_item(
            title="退款流程说明",
            content="退款流程：1. 联系客服；2. 寄回商品；3. 等待审核；4. 收到退款。"
            "注意：原包装退回且商品不影响二次销售。",
            category="售后服务",
            tags=["退款", "退货", "售后"],
            priority=3
        )

        # 技术规格类
        kb.add_item(
            title="产品规格参数",
            content="本产品支持主流平台：Windows 10+/MacOS 10.15+/Linux（主流发行版）。"
            "硬件要求：4GB 内存、10GB 可用空间。",
            category="技术规格",
            tags=["技术", "系统", "参数"],
            priority=2
        )

        print("✅ 已添加 5 条知识条目")
        print()

        # 添加 FAQ
        print("👉 3. 添加 FAQ...")

        kb.add_faq(
            question="产品可以退换吗？",
            answer="是的，支持 7 天无理由退换，30 天质量问题包换。",
            category="常见问题",
            tags=["退换货", "售后"]
        )

        kb.add_faq(
            question="支持哪些操作系统？",
            answer="支持 Windows 10+、MacOS 10.15+、Linux 主流发行版。",
            category="常见问题",
            tags=["技术", "系统"]
        )

        kb.add_faq(
            question="价格有什么优惠？",
            answer="批量购买享受 9 折优惠，年度会员享受 8 折优惠。",
            category="常见问题",
            tags=["价格", "优惠", "折扣"]
        )

        kb.quick_add_faq(
            "怎么退款？",
            "退款流程：联系客服→寄回商品→等待审核→收到退款。"
        )

        print("✅ 已添加 4 条 FAQ")
        print()

        # 查看知识库统计
        print("👉 4. 知识库统计...")
        stats = kb.get_stats()
        print(f"   知识条目: {stats['total_items']}")
        print(f"   FAQ数量: {stats['total_faqs']}")
        print(f"   分类数量: {stats['total_categories']}")
        print()

        # 分类列表
        print("👉 5. 分类列表...")
        categories = kb.get_categories()
        for cat in categories:
            print(f"   - {cat.name} (数量: {cat.item_count})")
        print()

        # 搜索功能演示
        print("👉 6. 搜索 '退换货'...")
        results = kb.search("退换货", limit=5)
        for r in results:
            if hasattr(r.item, "title"):
                print(f"   [{r.match_type}] {r.item.title}")
            else:
                print(f"   [{r.match_type}] Q: {r.item.question}")
        print()

        print("👉 7. 搜索 '价格'...")
        results = kb.search("价格", limit=5)
        for r in results:
            if hasattr(r.item, "title"):
                print(f"   [{r.match_type}] {r.item.title}")
        print()

        # 获取训练素材
        print("👉 8. 获取售前 Agent 训练素材...")
        training_data = kb.get_training_for_agent("presales_agent")
        print(f"   训练素材: {len(training_data)} 条")
        print()

        # 训练 Agent 提示词生成
        print("👉 9. 生成 Agent 训练提示词...")
        training_prompt = kb.train_agent_with_knowledge("presales_agent")
        if training_prompt:
            print("   🎉 Agent 训练提示词已生成!")
        print()

        # 测试导出功能
        print("👉 10. 测试导出功能...")
        export_data = kb.export_all()
        print(f"   导出数据: {len(export_data)} 条知识, {len(export_data)} 条 FAQ")
        print()

        # 完成!
        print("=" * 60)
        print("🎉 知识库示例完成！")
        print("=" * 60)
        print()
        print("📌 使用技巧:")
        print("- 使用 kb.search('关键词') 快速搜索")
        print("- 使用 kb.add_faq(...) 添加常见问题")
        print("- 使用 kb.get_stats() 查看统计")
        print("- 使用 kb.export_all() 导出数据备份")
        print()

    except Exception as e:
        print(f"❌ 示例运行出错: {e}")
        print()


if __name__ == "__main__":
    main()
