# 📊 数据分析与智能决策系统使用文档

## 简介

数据分析与智能决策系统是销售宗师（SalesMaster）的企业级数据可视化与智能分析模块，提供完整的销售仪表盘、KPI 指标、趋势分析、客户分析、智能预测、销售建议等功能。

## 功能架构

```
数据分析与智能决策系统
├── 销售仪表盘
│   ├── KPI 指标卡片
│   ├── 趋势图表
│   ├── 业绩排名
│   └── 漏斗分析
├── 客户分析
│   ├── 客户分层
│   ├── 客户价值评估
│   └── 客户增长分析
├── 智能决策
│   ├── 销售预测
│   ├── 商机推荐
│   └── 风险预警
└── 报告生成
    ├── HTML 报告
    ├── 数据导出
    └── 定时报表
```

## 快速开始

### 基础使用

```python
from SentriKit_salesmaster.analytics import (
    DashboardManager,
    KPICalculator,
    PredictionEngine,
    ReportGenerator,
)

# 获取完整仪表盘数据
dashboard_mgr = DashboardManager()
dashboard = dashboard_mgr.get_dashboard_data()

# 查看 KPI
print(f"总营收: ¥{dashboard.kpis.total_revenue:,.0f}")
print(f"成交率: {dashboard.kpis.win_rate:.1%}")

# 查看预测
print(f"未来3个月预测营收: ¥{dashboard.predictions.predicted_revenue:,.0f}")
```

## 销售仪表盘

### 获取完整仪表盘数据

```python
from SentriKit_salesmaster.analytics import DashboardManager

dashboard_mgr = DashboardManager()
dashboard = dashboard_mgr.get_dashboard_data()

print(f"=== 销售仪表盘 ===")
print(f"周期: {dashboard.period_start} - {dashboard.period_end}")
print()

print(f"=== KPI 指标 ===")
print(f"总营收: ¥{dashboard.kpis.total_revenue:,.0f}")
print(f"总报价: {dashboard.kpis.total_quotes} 个")
print(f"总合同: {dashboard.kpis.total_contracts} 个")
print(f"总客户: {dashboard.kpis.total_customers} 个")
print(f"成交率: {dashboard.kpis.win_rate:.1%}")
print(f"平均客单价: ¥{dashboard.kpis.average_deal:,.0f}")
print(f"任务完成率: {dashboard.kpis.completion_rate:.1%}")
```

## KPI 指标管理

### 计算销售 KPI

```python
from SentriKit_salesmaster.analytics import KPICalculator

kpi_calc = KPICalculator()

# 计算本月 KPI
kpis = kpi_calc.calculate_kpis()
print(f"总营收: ¥{kpis.total_revenue:,.0f}")
print(f"成交率: {kpis.win_rate:.1%}")

# 计算指定周期
start_date = "2024-01-01"
end_date = "2024-12-31"
yearly_kpis = kpi_calc.calculate_kpis(start_date, end_date)
```

## 趋势分析

### 营收趋势分析

```python
from SentriKit_salesmaster.analytics import TrendAnalyzer

trend_analyzer = TrendAnalyzer()

# 分析营收趋势（默认6个月）
revenue_trend = trend_analyzer.analyze_revenue_trend()
print("=== 营收趋势 ===")
for t in revenue_trend:
    icon = "📈" if t.trend == "up" else "📉" if t.trend == "down" else "➡️"
    print(f"{icon} {t.date}: ¥{t.value:,.0f}")

# 分析合同趋势
contracts_trend = trend_analyzer.analyze_contracts_trend()
print("\n=== 合同趋势 ===")
for t in contracts_trend:
    icon = "📈" if t.trend == "up" else "📉" if t.trend == "down" else "➡️"
    print(f"{icon} {t.date}: {int(t.value)} 个")

# 分析更多月份
long_trend = trend_analyzer.analyze_revenue_trend(months=12)
print(f"\n12个月趋势数据: {len(long_trend)} 条")
```

## 客户分析

### 客户分层分析

```python
from SentriKit_salesmaster.analytics import CustomerAnalyzer

customer_analyzer = CustomerAnalyzer()
segments = customer_analyzer.analyze_customer_segments()

print("=== 客户分层分析 ===")
for seg in segments:
    icon = "👑" if "VIP" in seg.segment_name else "⭐" if "高" in seg.segment_name else "👥"
    print(f"{icon} {seg.segment_name}:")
    print(f"   客户数: {seg.customer_count}")
    print(f"   总营收: ¥{seg.total_revenue:,.0f}")
    print(f"   平均客单价: ¥{seg.avg_order_value:,.0f}")
    print()

# 计算总体统计
total_customers = sum(s.customer_count for s in segments)
total_revenue = sum(s.total_revenue for s in segments)
avg_order = sum(s.avg_order_value * s.customer_count for s in segments) / total_customers

print(f"总计: {total_customers} 客户, ¥{total_revenue:,.0f}")
print(f"整体平均: ¥{avg_order:,.0f}")
```

## 销售漏斗分析

### 分析销售漏斗

```python
from SentriKit_salesmaster.analytics import FunnelAnalyzer

funnel_analyzer = FunnelAnalyzer()
funnel = funnel_analyzer.analyze_sales_funnel()

print("=== 销售漏斗分析 ===")
for i, stage in enumerate(funnel):
    icon = "🔴" if i == 0 else "🟡" if i == len(funnel) - 1 else "🟢"
    print(f"{icon} {stage.stage}")
    print(f"   数量: {stage.count} 个 ({stage.percentage:.1f}%)")
    print(f"   转化率: {stage.conversion_rate:.1%}")
    print(f"   预估营收: ¥{stage.estimated_revenue:,.0f}")
    print()

# 漏斗总体指标
total_leads = funnel[0].count
total_closed = funnel[-1].count
overall_conversion = total_closed / total_leads if total_leads > 0 else 0
total_value = sum(s.estimated_revenue for s in funnel)

print(f"整体转化率: {overall_conversion:.1%}")
print(f"漏斗总价值: ¥{total_value:,.0f}")
```

## 智能预测

### 销售预测

```python
from SentriKit_salesmaster.analytics import PredictionEngine

prediction_engine = PredictionEngine()
prediction = prediction_engine.predict_sales()

print("=== 销售预测 ===")
print(f"预测未来3个月营收: ¥{prediction.predicted_revenue:,.0f}")
print(f"预测置信度: {prediction.confidence:.1%}")
print(f"趋势: {'📈 增长' if prediction.trend == 'up' else '📉 下降' if prediction.trend == 'down' else '➡️ 持平'}")

print(f"\n历史数据（最近6个月）:")
for i, value in enumerate(prediction.historical_data):
    print(f"   月{i+1}: ¥{value:,.0f}")

print(f"\n未来3个月预测:")
for i, value in enumerate(prediction.next_3_months):
    print(f"   月{i+1}: ¥{value:,.0f}")
```

### 销售机会与风险

```python
print("=== 销售机会 ===")
for i, opportunity in enumerate(prediction.opportunities):
    print(f"  💎 {i+1}. {opportunity}")

print("\n=== 潜在风险 ===")
for i, risk in enumerate(prediction.risks):
    print(f"  ⚠️ {i+1}. {risk}")

print(f"\n总体建议: {prediction.recommendation}")
```

### 智能销售建议

```python
recommendations = prediction_engine.generate_recommendations()
print("=== 智能销售建议 ===")

for rec in recommendations:
    priority_icon = "🔴" if rec.priority == "high" else "🟡" if rec.priority == "medium" else "🟢"
    type_icon = "🎯" if rec.type == "lead" else "📝" if rec.type == "contract" else "📞"
    print(f"{priority_icon} {type_icon} [{rec.priority.upper()}] {rec.title}")
    print(f"   {rec.description}")
    print(f"   潜在影响: ¥{rec.potential_impact:,.0f}")
    print(f"   建议行动: {rec.recommended_action}")
    print()
```

## 业绩排名

### 销售人员排名

```python
from SentriKit_salesmaster.analytics import RankingGenerator

ranking_generator = RankingGenerator()

top_sales = ranking_generator.get_top_salespeople(count=5)
print("=== 销售人员排名 ===")
for sp in top_sales:
    rank_icon = "🥇" if sp['rank'] == 1 else "🥈" if sp['rank'] == 2 else "🥉" if sp['rank'] == 3 else "🏅"
    change_icon = "🔺" if sp['change'] > 0 else "🔻" if sp['change'] < 0 else "➡️"
    change_text = f"{change_icon}{abs(sp['change'])}" if sp['change'] != 0 else ""
    print(f"{rank_icon} {sp['rank']}. {sp['name']}")
    print(f"   营收: ¥{sp['revenue']:,.0f}")
    print(f"   单数: {sp['deals']} 单")
    print(f"   成率: {sp['win_rate']:.1%}")
    if change_text:
        print(f"   排名变化: {change_text}")
    print()
```

### 产品销售排名

```python
top_products = ranking_generator.get_top_products(count=5)
print("=== 产品销售排名 ===")
for prod in top_products:
    rank_icon = "🥇" if prod['rank'] == 1 else "🥈" if prod['rank'] == 2 else "🥉" if prod['rank'] == 3 else "🏅"
    print(f"{rank_icon} {prod['rank']}. {prod['name']}")
    print(f"   营收: ¥{prod['revenue']:,.0f}")
    print()
```

## 报告生成

### 生成 HTML 报告

```python
from SentriKit_salesmaster.analytics import ReportGenerator

report_generator = ReportGenerator()

# 生成 HTML 报告
html_report = report_generator.generate_html_report()

# 保存到文件
with open("sales_report.html", "w", encoding="utf-8") as f:
    f.write(html_report)
print("报告已保存: sales_report.html")

# 在浏览器中打开
import webbrowser
webbrowser.open("sales_report.html")
```

### 报告内容包含

- 📊 报告标题与周期
- 🏆 KPI 指标卡片（营收/合同/成交率/客单价）
- 📈 营收趋势图表
- 🔻 销售漏斗分析
- 👥 客户分层分析
- 🏅 业绩排名
- 💡 智能建议

## 完整示例

```python
from SentriKit_salesmaster.analytics import DashboardManager

print("="*60)
print("📊 销售仪表盘 - 完整数据报告")
print("="*60)

dashboard_mgr = DashboardManager()
dashboard = dashboard_mgr.get_dashboard_data()

# 1. KPI 指标
print(f"\n1. KPI 指标卡片")
print(f"   ├─ 总营收: ¥{dashboard.kpis.total_revenue:,.0f}")
print(f"   ├─ 总合同: {dashboard.kpis.total_contracts} 个")
print(f"   ├─ 成交率: {dashboard.kpis.win_rate:.1%}")
print(f"   ├─ 客单价: ¥{dashboard.kpis.average_deal:,.0f}")
print(f"   └─ 任务完成率: {dashboard.kpis.completion_rate:.1%}")

# 2. 最近活动
print(f"\n2. 最近活动")
for i, activity in enumerate(dashboard.recent_activities):
    print(f"   {i+1}. {activity['time']} - {activity['text']}")

# 3. 智能建议
print(f"\n3. 智能建议")
for i, rec in enumerate(dashboard.recommendations):
    icon = "🔴" if rec.priority == "high" else "🟡" if rec.priority == "medium" else "🟢"
    print(f"   {icon} {i+1}. {rec.title} - 影响: ¥{rec.potential_impact:,.0f}")
    print(f"      建议: {rec.recommended_action}")

# 4. 预测信息
print(f"\n4. 销售预测")
trend_icon = "📈" if dashboard.predictions.trend == "up" else "📉"
print(f"   未来3个月预测营收: ¥{dashboard.predictions.predicted_revenue:,.0f}")
print(f"   置信度: {dashboard.predictions.confidence:.1%}")
print(f"   趋势: {trend_icon} {dashboard.predictions.trend}")
print(f"   建议: {dashboard.predictions.recommendation}")

print("\n" + "="*60)
print("📈 分析完成！")
print("="*60)
```

## 数据类型

### SalesKPI (KPI 指标)

```python
@dataclass
class SalesKPI:
    total_revenue: float         # 总营收
    total_quotes: int           # 总报价
    total_contracts: int        # 总合同
    total_customers: int        # 总客户
    win_rate: float             # 成交率
    average_deal: float         # 平均客单价
    completion_rate: float      # 任务完成率
```

### SalesPrediction (销售预测)

```python
@dataclass
class SalesPrediction:
    predicted_revenue: float    # 预测营收
    confidence: float           # 置信度
    trend: str                  # 趋势 (up/down/flat)
    historical_data: List[float] # 历史数据
    next_3_months: List[float] # 未来3个月预测
    opportunities: List[str]    # 机会点
    risks: List[str]            # 风险点
    recommendation: str         # 建议
```

## 最佳实践

### 1. 定期查看仪表盘

建议每天查看仪表盘，及时了解销售状况，发现问题快速响应

### 2. 关注销售漏斗

定期分析漏斗转化情况，优化每个阶段的流程，提升整体转化率

### 3. 重视客户分层

针对不同价值层次的客户制定差异化策略，重点维护 VIP 客户

### 4. 利用智能建议

系统生成的建议有数据支撑，建议优先处理高优先级事项

### 5. 定期生成报告

每周/每月生成销售报告，向上汇报，存档管理

## 下一步

- 查看完整测试案例：`tests/test_analytics.py`
- 学习通话与录音系统：`docs/CALLS.md`
- 学习 RBAC 权限系统：`docs/RBAC.md`

---

**祝您使用愉快！🎉**
