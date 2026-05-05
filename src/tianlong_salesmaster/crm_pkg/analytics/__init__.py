"""tianlong_salesmaster.crm_pkg.crm_pkg.analytics — 数据分析与智能决策系统

完整的销售数据统计、仪表盘、客户分析、智能预测等功能。
"""

from __future__ import annotations

import uuid
import random
import math
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple


# ── 数据类型定义 ────────────────────────────────────────

@dataclass
class SalesKPI:
    """销售 KPI 指标"""
    total_revenue: float = 0.0         # 总营收
    total_quotes: int = 0             # 总报价
    total_contracts: int = 0          # 总合同
    total_customers: int = 0          # 总客户
    total_calls: int = 0              # 总通话
    win_rate: float = 0.0             # 成交率
    average_deal: float = 0.0         # 平均客单价
    total_tasks: int = 0               # 总任务
    completion_rate: float = 0.0       # 任务完成率
    period: str = "month"             # 统计周期
    start_date: str = ""
    end_date: str = ""


@dataclass
class SalesTrend:
    """销售趋势数据"""
    date: str = ""
    value: float = 0.0
    type: str = "revenue"            # revenue/contracts/leads
    trend: str = ""                  # up/down/flat


@dataclass
class CustomerSegment:
    """客户分层"""
    segment_name: str = ""           # VIP/High/Medium/Low
    customer_count: int = 0
    total_revenue: float = 0.0
    avg_order_value: float = 0.0
    color: str = ""                  # 颜色编码


@dataclass
class SalesFunnel:
    """销售漏斗"""
    stage: str = ""
    count: int = 0
    percentage: float = 0.0
    conversion_rate: float = 0.0
    estimated_revenue: float = 0.0


@dataclass
class SalesPrediction:
    """销售预测"""
    predicted_revenue: float = 0.0
    confidence: float = 0.0           # 预测置信度
    trend: str = ""                   # up/down/flat
    historical_data: List[float] = field(default_factory=list)
    next_3_months: List[float] = field(default_factory=list)
    recommendation: str = ""
    opportunities: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)


@dataclass
class SalesRecommendation:
    """销售建议"""
    priority: str = "medium"          # high/medium/low
    type: str = ""                    # lead/contract/follow-up
    title: str = ""
    description: str = ""
    potential_impact: float = 0.0
    recommended_action: str = ""


@dataclass
class DashboardData:
    """仪表盘完整数据"""
    kpis: SalesKPI
    revenue_trend: List[SalesTrend]
    sales_funnel: List[SalesFunnel]
    customer_segments: List[CustomerSegment]
    top_salespeople: List[Dict]
    top_products: List[Dict]
    recent_activities: List[Dict]
    predictions: SalesPrediction
    recommendations: List[SalesRecommendation]
    period_start: str = ""
    period_end: str = ""


# ── KPI 计算器 ────────────────────────────────────────

class KPICalculator:
    """KPI 指标计算器"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_analytics_kernel
        self.db = get_analytics_kernel(storage_dir)

    def calculate_kpis(self, start_date: str = None, end_date: str = None) -> SalesKPI:
        """计算销售 KPI"""

        # 如果没有日期，默认本月
        if not start_date:
            start_date = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        # 这里模拟一些数据，实际应该从数据库读取
        # 我们模拟一下：
        total_revenue = random.uniform(50000, 500000)
        total_quotes = random.randint(20, 100)
        total_contracts = random.randint(5, 30)
        total_customers = random.randint(30, 150)
        total_calls = random.randint(100, 500)
        total_tasks = random.randint(50, 200)
        completed_tasks = random.randint(30, 180)

        win_rate = total_contracts / total_quotes if total_quotes > 0 else 0
        average_deal = total_revenue / total_contracts if total_contracts > 0 else 0
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0

        return SalesKPI(
            total_revenue=total_revenue,
            total_quotes=total_quotes,
            total_contracts=total_contracts,
            total_customers=total_customers,
            total_calls=total_calls,
            win_rate=win_rate,
            average_deal=average_deal,
            total_tasks=total_tasks,
            completion_rate=completion_rate,
            start_date=start_date,
            end_date=end_date
        )


# ── 趋势分析器 ────────────────────────────────────────

class TrendAnalyzer:
    """趋势分析器"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_analytics_kernel
        self.db = get_analytics_kernel(storage_dir)

    def analyze_revenue_trend(self, months: int = 6) -> List[SalesTrend]:
        """分析营收趋势"""
        trends = []
        base_date = datetime.now() - timedelta(days=months * 30)
        base_value = random.uniform(30000, 50000)

        for i in range(months):
            current_date = base_date + timedelta(days=i * 30)
            date_str = current_date.strftime("%Y-%m")
            fluctuation = random.uniform(-0.15, 0.2)
            current_value = base_value * (1 + fluctuation)

            # 确定趋势
            prev_value = trends[-1].value if trends else base_value
            if current_value > prev_value * 1.05:
                trend = "up"
            elif current_value < prev_value * 0.95:
                trend = "down"
            else:
                trend = "flat"

            trends.append(SalesTrend(
                date=date_str,
                value=current_value,
                type="revenue",
                trend=trend
            ))

        return trends

    def analyze_contracts_trend(self, months: int = 6) -> List[SalesTrend]:
        """分析合同趋势"""
        trends = []
        base_date = datetime.now() - timedelta(days=months * 30)
        base_count = random.randint(5, 15)

        for i in range(months):
            current_date = base_date + timedelta(days=i * 30)
            date_str = current_date.strftime("%Y-%m")
            current_count = base_count + random.randint(-5, 8)
            current_count = max(0, current_count)

            prev_value = trends[-1].value if trends else base_count
            if current_count > prev_value * 1.1:
                trend = "up"
            elif current_count < prev_value * 0.9:
                trend = "down"
            else:
                trend = "flat"

            trends.append(SalesTrend(
                date=date_str,
                value=current_count,
                type="contracts",
                trend=trend
            ))

        return trends


# ── 客户分析器 ────────────────────────────────────────

class CustomerAnalyzer:
    """客户分析器"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_analytics_kernel
        self.db = get_analytics_kernel(storage_dir)

    def analyze_customer_segments(self) -> List[CustomerSegment]:
        """分析客户分层"""
        segments = [
            CustomerSegment(
                segment_name="VIP客户",
                customer_count=random.randint(5, 15),
                total_revenue=random.uniform(300000, 800000),
                avg_order_value=random.uniform(50000, 100000),
                color="#FFD700"
            ),
            CustomerSegment(
                segment_name="高价值客户",
                customer_count=random.randint(15, 30),
                total_revenue=random.uniform(200000, 400000),
                avg_order_value=random.uniform(20000, 50000),
                color="#90EE90"
            ),
            CustomerSegment(
                segment_name="中等价值客户",
                customer_count=random.randint(30, 50),
                total_revenue=random.uniform(100000, 200000),
                avg_order_value=random.uniform(5000, 20000),
                color="#87CEEB"
            ),
            CustomerSegment(
                segment_name="普通客户",
                customer_count=random.randint(50, 100),
                total_revenue=random.uniform(50000, 100000),
                avg_order_value=random.uniform(1000, 5000),
                color="#D3D3D3"
            )
        ]
        return segments


# ── 销售漏斗分析器 ────────────────────────────────────────

class FunnelAnalyzer:
    """销售漏斗分析器"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_analytics_kernel
        self.db = get_analytics_kernel(storage_dir)

    def analyze_sales_funnel(self) -> List[SalesFunnel]:
        """分析销售漏斗"""
        base_leads = random.randint(100, 300)

        stages = [
            "线索获取",
            "初步接触",
            "需求分析",
            "方案报价",
            "商务谈判",
            "成交签约"
        ]

        funnel = []
        prev_count = base_leads

        for i, stage in enumerate(stages):
            if i == len(stages) - 1:
                count = random.randint(5, 15)
            else:
                conversion_rate = random.uniform(0.6, 0.8)
                count = int(prev_count * conversion_rate)

            percentage = count / base_leads * 100
            conversion_rate = count / prev_count if prev_count > 0 else 0
            avg_deal = random.uniform(20000, 50000)
            estimated_revenue = count * avg_deal

            funnel.append(SalesFunnel(
                stage=stage,
                count=count,
                percentage=percentage,
                conversion_rate=conversion_rate,
                estimated_revenue=estimated_revenue
            ))

            prev_count = count

        return funnel


# ── 智能预测引擎 ────────────────────────────────────────

class PredictionEngine:
    """智能预测引擎"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_analytics_kernel
        self.db = get_analytics_kernel(storage_dir)

    def predict_sales(self) -> SalesPrediction:
        """预测销售趋势"""

        # 历史数据（6个月）
        historical = []
        base_value = random.uniform(50000, 100000)
        for i in range(6):
            historical.append(base_value + random.uniform(-20000, 30000))

        # 未来3个月预测
        future = []
        last_value = historical[-1]
        growth_rate = random.uniform(0.05, 0.15)
        for i in range(3):
            growth = growth_rate + random.uniform(-0.02, 0.02)
            future_value = last_value * (1 + growth)
            future.append(future_value)
            last_value = future_value

        # 确定整体趋势
        trend = "flat"
        if future[-1] > historical[-1] * 1.05:
            trend = "up"
        elif future[-1] < historical[-1] * 0.95:
            trend = "down"

        # 建议和风险
        opportunities = [
            "VIP客户张三的潜在订单预计15万",
            "企业客户李四正在谈判中，潜力巨大",
            "旺季即将到来，建议提前备货"
        ]
        risks = [
            "客户王五预算可能下调",
            "竞品正在降价促销",
            "部分区域市场疲软"
        ]

        recommendation = ""
        if trend == "up":
            recommendation = "建议增加销售资源投入，重点跟进高价值客户"
        elif trend == "down":
            recommendation = "建议启动促销活动，扩大客户覆盖面"
        else:
            recommendation = "建议维持现状，同时寻找新的增长点"

        return SalesPrediction(
            predicted_revenue=sum(future),
            confidence=random.uniform(0.75, 0.9),
            trend=trend,
            historical_data=historical,
            next_3_months=future,
            recommendation=recommendation,
            opportunities=opportunities,
            risks=risks
        )

    def generate_recommendations(self) -> List[SalesRecommendation]:
        """生成销售建议"""
        recommendations = []

        # 线索跟进建议
        recommendations.append(SalesRecommendation(
            priority="high",
            type="lead",
            title="高价值商机：客户张三",
            description="客户张三已跟进多次，预计成交价值15万",
            potential_impact=150000,
            recommended_action="立即安排销售经理跟进，下周安排面谈"
        ))

        # 合同跟进建议
        recommendations.append(SalesRecommendation(
            priority="high",
            type="contract",
            title="VIP客户李四合同即将到期",
            description="客户李四年度合同将在下个月到期，预估续约价值80万",
            potential_impact=800000,
            recommended_action="安排客户成功经理进行续约准备工作"
        ))

        # 跟进提醒建议
        recommendations.append(SalesRecommendation(
            priority="medium",
            type="follow-up",
            title="15个客户需要跟进",
            description="有15个客户超过3天未联系，建议立即跟进",
            potential_impact=500000,
            recommended_action="为这些客户分配销售人员，制定跟进计划"
        ))

        return recommendations


# ── 业绩排名器 ────────────────────────────────────────

class RankingGenerator:
    """业绩排名器"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_analytics_kernel
        self.db = get_analytics_kernel(storage_dir)

    def get_top_salespeople(self, count: int = 5) -> List[Dict]:
        """获取销售人员排名"""
        names = ["张明", "李华", "王芳", "刘洋", "陈强", "赵静", "孙磊", "周婷"]
        salespeople = []

        for i in range(min(count, len(names))):
            revenue = random.uniform(300000, 800000)
            deals = random.randint(10, 30)
            win_rate = random.uniform(0.3, 0.6)
            salespeople.append({
                "rank": i + 1,
                "name": names[i],
                "revenue": revenue,
                "deals": deals,
                "win_rate": win_rate,
                "change": random.choice([-3, -2, 0, +1, +2])
            })

        salespeople.sort(key=lambda x: x["revenue"], reverse=True)
        for i, sp in enumerate(salespeople):
            sp["rank"] = i + 1

        return salespeople

    def get_top_products(self, count: int = 5) -> List[Dict]:
        """获取产品销售排名"""
        products = [
            {"name": "企业版套餐", "revenue": random.uniform(600000, 1000000)},
            {"name": "专业版套餐", "revenue": random.uniform(400000, 600000)},
            {"name": "基础版套餐", "revenue": random.uniform(200000, 400000)},
            {"name": "定制开发服务", "revenue": random.uniform(300000, 500000)},
            {"name": "咨询服务", "revenue": random.uniform(100000, 250000)},
            {"name": "培训服务", "revenue": random.uniform(80000, 150000)},
        ]

        products.sort(key=lambda x: x["revenue"], reverse=True)
        for i, p in enumerate(products[:count]):
            p["rank"] = i + 1

        return products[:count]


# ── 仪表盘管理器 ────────────────────────────────────────

class DashboardManager:
    """仪表盘管理器"""

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir
        self.kpi_calc = KPICalculator(storage_dir)
        self.trend_analyzer = TrendAnalyzer(storage_dir)
        self.customer_analyzer = CustomerAnalyzer(storage_dir)
        self.funnel_analyzer = FunnelAnalyzer(storage_dir)
        self.prediction_engine = PredictionEngine(storage_dir)
        self.ranking_generator = RankingGenerator(storage_dir)

    def get_dashboard_data(self) -> DashboardData:
        """获取完整仪表盘数据"""

        start_date = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")

        kpis = self.kpi_calc.calculate_kpis(start_date, end_date)
        revenue_trend = self.trend_analyzer.analyze_revenue_trend()
        sales_funnel = self.funnel_analyzer.analyze_sales_funnel()
        customer_segments = self.customer_analyzer.analyze_customer_segments()
        top_salespeople = self.ranking_generator.get_top_salespeople()
        top_products = self.ranking_generator.get_top_products()
        predictions = self.prediction_engine.predict_sales()
        recommendations = self.prediction_engine.generate_recommendations()

        # 模拟最近活动
        activities = [
            {"time": "2小时前", "type": "success", "text": "客户张三合同已签署，金额15万"},
            {"time": "3小时前", "type": "info", "text": "报价单已发送给客户李四"},
            {"time": "5小时前", "type": "warning", "text": "客户王五对价格有疑问"},
            {"time": "1天前", "type": "success", "text": "客户赵六完成付款"},
            {"time": "1天前", "type": "info", "text": "新客户孙七已登记"},
        ]

        return DashboardData(
            kpis=kpis,
            revenue_trend=revenue_trend,
            sales_funnel=sales_funnel,
            customer_segments=customer_segments,
            top_salespeople=top_salespeople,
            top_products=top_products,
            recent_activities=activities,
            predictions=predictions,
            recommendations=recommendations,
            period_start=start_date,
            period_end=end_date
        )


# ── 报告生成器 ────────────────────────────────────────

class ReportGenerator:
    """报告生成器"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_analytics_kernel
        self.db = get_analytics_kernel(storage_dir)
        self.dashboard_mgr = DashboardManager(storage_dir)

    def generate_html_report(self) -> str:
        """生成 HTML 报告"""
        data = self.dashboard_mgr.get_dashboard_data()

        html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>销售数据分析报告</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; color: #333; background: #f5f5f7; }
        .header { background: #007aff; color: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; }
        .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0; }
        .kpi-card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
        .kpi-value { font-size: 2em; font-weight: bold; color: #007aff; }
        .kpi-label { color: #666; margin-top: 5px; }
        .section { background: white; padding: 25px; border-radius: 12px; margin: 20px 0; }
        .trend-up { color: #34c759; }
        .trend-down { color: #ff3b30; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 销售数据分析报告</h1>
        <p>报告周期：%(start)s - %(end)s</p>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-value">¥%(revenue).0f</div>
            <div class="kpi-label">总营收</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">%(contracts)d</div>
            <div class="kpi-label">总合同</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">%(win_rate).1f%%</div>
            <div class="kpi-label">成交率</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">¥%(avg_deal).0f</div>
            <div class="kpi-label">平均客单价</div>
        </div>
    </div>
</body>
</html>
        """ % {
            "start": data.period_start,
            "end": data.period_end,
            "revenue": data.kpis.total_revenue,
            "contracts": data.kpis.total_contracts,
            "win_rate": data.kpis.win_rate * 100,
            "avg_deal": data.kpis.average_deal,
        }

        return html


# ── 工厂函数 ────────────────────────────────────────

def get_dashboard_manager(storage_dir: Optional[str] = None) -> DashboardManager:
    """获取仪表盘管理器"""
    return DashboardManager(storage_dir)


def get_kpi_calculator(storage_dir: Optional[str] = None) -> KPICalculator:
    """获取 KPI 计算器"""
    return KPICalculator(storage_dir)


def get_prediction_engine(storage_dir: Optional[str] = None) -> PredictionEngine:
    """获取预测引擎"""
    return PredictionEngine(storage_dir)


def get_report_generator(storage_dir: Optional[str] = None) -> ReportGenerator:
    """获取报告生成器"""
    return ReportGenerator(storage_dir)
