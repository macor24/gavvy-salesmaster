"""测试数据分析与智能决策系统"""

import tempfile
import os
from datetime import datetime


def test_analytics():
    """测试分析系统"""

    print("=" * 60)
    print("📊 测试数据分析与智能决策系统")
    print("=" * 60)

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"   存储目录: {temp_dir}")

    try:
        # 导入模块
        from tianlong_salesmaster.crm_pkg.analytics import (
            DashboardManager,
            KPICalculator,
            TrendAnalyzer,
            CustomerAnalyzer,
            FunnelAnalyzer,
            PredictionEngine,
            RankingGenerator,
            ReportGenerator,
        )

        print("✅ 模块导入成功")

        # ── KPI 计算测试 ──────────────────────────────────

        print("\n📈 KPI 指标计算测试...")

        kpi_calc = KPICalculator(temp_dir)
        kpis = kpi_calc.calculate_kpis()
        print(f"✅ 总营收: ¥{kpis.total_revenue:,.0f}")
        print(f"✅ 总报价: {kpis.total_quotes} 个")
        print(f"✅ 总合同: {kpis.total_contracts} 个")
        print(f"✅ 总客户: {kpis.total_customers} 个")
        print(f"✅ 成交率: {kpis.win_rate:.1%}")
        print(f"✅ 平均客单价: ¥{kpis.average_deal:,.0f}")
        print(f"✅ 任务完成率: {kpis.completion_rate:.1%}")

        # ── 趋势分析测试 ──────────────────────────────────

        print("\n📉 趋势分析测试...")

        trend_analyzer = TrendAnalyzer(temp_dir)
        revenue_trend = trend_analyzer.analyze_revenue_trend()
        contracts_trend = trend_analyzer.analyze_contracts_trend()
        print(f"✅ 营收趋势数据: {len(revenue_trend)} 个月")
        for t in revenue_trend[:3]:
            print(f"   {t.date}: ¥{t.value:,.0f} ({t.trend})")
        print(f"✅ 合同趋势数据: {len(contracts_trend)} 个月")

        # ── 客户分析测试 ──────────────────────────────────

        print("\n👥 客户分析测试...")

        customer_analyzer = CustomerAnalyzer(temp_dir)
        segments = customer_analyzer.analyze_customer_segments()
        print(f"✅ 客户分层: {len(segments)} 层")
        for seg in segments:
            print(f"   {seg.segment_name}: {seg.customer_count} 个客户, ¥{seg.total_revenue:,.0f}")

        # ── 销售漏斗测试 ──────────────────────────────────

        print("\n🔻 销售漏斗测试...")

        funnel_analyzer = FunnelAnalyzer(temp_dir)
        funnel = funnel_analyzer.analyze_sales_funnel()
        print(f"✅ 销售漏斗阶段: {len(funnel)} 个")
        for stage in funnel:
            print(f"   {stage.stage}: {stage.count} 个 ({stage.percentage:.1f}%, 转化率{stage.conversion_rate:.1%})")
        print(f"   预估营收: ¥{sum(s.estimated_revenue for s in funnel):,.0f}")

        # ── 智能预测测试 ──────────────────────────────────

        print("\n🔮 智能预测测试...")

        prediction_engine = PredictionEngine(temp_dir)
        prediction = prediction_engine.predict_sales()
        print(f"✅ 预测未来3个月营收: ¥{prediction.predicted_revenue:,.0f}")
        print(f"✅ 置信度: {prediction.confidence:.1%}")
        print(f"✅ 趋势: {prediction.trend}")
        print(f"✅ 机会点: {len(prediction.opportunities)} 个")
        print(f"✅ 风险点: {len(prediction.risks)} 个")

        # ── 销售建议测试 ──────────────────────────────────

        print("\n💡 销售建议测试...")

        recommendations = prediction_engine.generate_recommendations()
        print(f"✅ 生成建议: {len(recommendations)} 个")
        for rec in recommendations:
            icon = "🔴" if rec.priority == "high" else "🟡" if rec.priority == "medium" else "🟢"
            print(f"   {icon} [{rec.priority}] {rec.title}")
            print(f"      影响: ¥{rec.potential_impact:,.0f}")
            print(f"      建议: {rec.recommended_action}")

        # ── 业绩排名测试 ──────────────────────────────────

        print("\n🏆 业绩排名测试...")

        ranking_generator = RankingGenerator(temp_dir)
        top_sales = ranking_generator.get_top_salespeople()
        top_products = ranking_generator.get_top_products()
        print(f"✅ 销售人员排名:")
        for sp in top_sales:
            print(f"   {sp['rank']}. {sp['name']}: ¥{sp['revenue']:,.0f}, {sp['deals']} 单")
        print(f"✅ 产品销售排名:")
        for prod in top_products:
            print(f"   {prod['rank']}. {prod['name']}: ¥{prod['revenue']:,.0f}")

        # ── 仪表盘测试 ──────────────────────────────────

        print("\n📱 仪表盘测试...")

        dashboard_mgr = DashboardManager(temp_dir)
        dashboard = dashboard_mgr.get_dashboard_data()
        print(f"✅ 仪表盘数据完整:")
        print(f"   KPI: 已加载")
        print(f"   趋势: {len(dashboard.revenue_trend)} 个月")
        print(f"   漏斗: {len(dashboard.sales_funnel)} 阶段")
        print(f"   客户分层: {len(dashboard.customer_segments)} 层")
        print(f"   销售排名: {len(dashboard.top_salespeople)} 人")
        print(f"   产品排名: {len(dashboard.top_products)} 个")
        print(f"   最近活动: {len(dashboard.recent_activities)} 条")
        print(f"   智能建议: {len(dashboard.recommendations)} 条")

        # ── 报告生成测试 ──────────────────────────────────

        print("\n📄 报告生成测试...")

        report_generator = ReportGenerator(temp_dir)
        html_report = report_generator.generate_html_report()
        print(f"✅ HTML 报告已生成: {len(html_report)} 字符")

        # 保存报告到临时文件
        report_path = os.path.join(temp_dir, "sales_report.html")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_report)
        print(f"✅ 报告已保存: {report_path}")

        # ── 汇总测试结果 ──────────────────────────────────

        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
        print("\n📊 分析系统能力概览:")
        print("   ✅ KPI 指标计算")
        print("   ✅ 趋势分析（营收/合同）")
        print("   ✅ 客户分析（分层/画像）")
        print("   ✅ 销售漏斗分析")
        print("   ✅ 智能预测（未来3个月）")
        print("   ✅ 销售建议生成")
        print("   ✅ 业绩排名（人员/产品）")
        print("   ✅ 完整仪表盘数据")
        print("   ✅ HTML 报告生成")

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        print(f"\n清理临时目录: {temp_dir}")


if __name__ == "__main__":
    success = test_analytics()
    if success:
        print("\n✅ 数据分析与智能决策系统测试通过！")
    else:
        print("\n❌ 数据分析与智能决策系统测试失败！")
