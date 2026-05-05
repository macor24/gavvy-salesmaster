"""tianlong_salesmaster — Chat Sales 开源销售引擎

让任何人都能拥有自己的 Chat Sales。
全自动化销售Pipeline: Lead → Research → Proposal → Report

架构:
    SalesPipeline  — 主控制器，串联4步
    SalesMaster    — 六维销售能力引擎（心理博弈/多线程谈判/价值量化/风险管控/语言操作/策略进化）

可选集成:
    如果安装了 tianlong-toolkit，SalesPipeline 自动集成 CodeVigil 安全审计、
    竞品情报、健康监控等数据到销售提案中，大幅提升提案说服力。
    不装也不影响核心功能。
"""

from __future__ import annotations

import json
import os
import re
import warnings
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── 企业版检测（通过 API Key 而非闭源包） ─────

SALES_EDITION = "community"  # community / enterprise
_HAS_ENTERPRISE = False
_ENTERPRISE_IMPORT_ERROR = ""

# 企业版通过 TIANLONG_API_KEY 环境变量激活，不依赖闭源包
try:
    from .core.enterprise_client import EnterpriseConfig
    _cfg = EnterpriseConfig.from_env()
    _HAS_ENTERPRISE = _cfg.is_enterprise
    SALES_EDITION = "enterprise" if _cfg.is_enterprise else "community"
    if not _cfg.is_enterprise:
        _ENTERPRISE_IMPORT_ERROR = (
            "社区版模式。设置 TIANLONG_API_KEY 环境变量激活企业版 SaaS API。"
        )
except ImportError:
    _ENTERPRISE_IMPORT_ERROR = "社区版模式"


# ── 可选检测 tianlong ─────────────────────────────

_HAS_TIANLONG = False
try:
    import tianlong  # noqa: F401
    _HAS_TIANLONG = True
except ImportError:
    pass


# ── 数据类型 ─────────────────────────────────────

@dataclass
class Lead:
    """一个潜在客户"""
    company: str = ""
    industry: str = ""
    description: str = ""
    source: str = "manual"     # manual / web_search / preset
    priority: str = "medium"   # high / medium / low
    status: str = "new"        # new / researching / proposal_ready / contacted / converted / lost
    contact: str = ""          # 联系方式（邮箱/LinkedIn/官网）
    ai_readiness: str = ""     # 初步AI成熟度评估
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    def brief(self) -> str:
        return f"[{self.status}] {self.company} ({self.industry})"


@dataclass
class SalesReport:
    """一次销售流程的完整报告"""
    timestamp: str = ""
    leads_found: int = 0
    leads: List[Lead] = field(default_factory=list)
    proposals_generated: int = 0
    proposals: List[str] = field(default_factory=list)
    summary: str = ""


# ── 潜在客户来源 ─────────────────────────────

INDUSTRY_TARGETS: List[str] = [
    "AI Agent", "LLM", "大模型", "人工智能", "智能客服",
    "金融科技", "FinTech", "医疗AI", "AI医疗",
    "智能驾驶", "自动驾驶", "机器人",
]

PRESET_COMPANIES: List[Dict] = [
    {"company": "LangChain", "industry": "AI Agent框架",
     "description": "最流行的LLM应用框架，生态中有大量Agent开发者"},
    {"company": "CrewAI", "industry": "AI Agent框架",
     "description": "多Agent协作框架，用户群体快速增长"},
    {"company": "AutoGPT", "industry": "AI Agent",
     "description": "最早的自主Agent之一，开源社区活跃"},
    {"company": "Hugging Face", "industry": "AI平台",
     "description": "最大的ML模型托管平台，Agent相关工具生态丰富"},
]


# ── 默认产品信息（用户可替换） ─────────────────

DEFAULT_PRODUCT_NAME = "天龙工具箱"
DEFAULT_PRODUCT_TAGLINE = "AI Agent 安全运维工具箱"
DEFAULT_PRODUCT_DESCRIPTION = "开源 AI Agent 安全审计、健康监控、进化评估工具集"


# ── 销售Pipeline ──────────────────────────────

class SalesPipeline:
    """销售Pipeline核心控制器。

    4步流程:
    1. 搜索潜在客户（从预设/搜索结果/web）
    2. 调研客户背景和需求
    3. 生成定制化销售提案
    4. 保存客户跟踪记录

    可自定义卖的产品:
        pipeline = SalesPipeline(
            product_name="我的AI产品",
            product_tagline="AI客服系统",
            preset_companies=[...],
        )
        report = pipeline.run_full_cycle()
    """

    def __init__(
        self,
        project_dir: str = ".",
        product_name: str = DEFAULT_PRODUCT_NAME,
        product_tagline: str = DEFAULT_PRODUCT_TAGLINE,
        product_description: str = DEFAULT_PRODUCT_DESCRIPTION,
        preset_companies: Optional[List[Dict]] = None,
    ):
        self.project_dir = Path(project_dir)
        self.product_name = product_name
        self.product_tagline = product_tagline
        self.product_description = product_description
        self._custom_presets = preset_companies
        self._leads_file = self.project_dir / "brain" / "leads.md"
        self._output_dir = self.project_dir / "sales-output"
        self._output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def has_tianlong(self) -> bool:
        """检查是否安装了 tianlong-toolkit（用于提案中展示安全数据）。"""
        return _HAS_TIANLONG

    def run_full_cycle(self) -> SalesReport:
        """执行完整销售周期：搜索 -> 调研 -> 提案 -> 保存"""
        start = datetime.now()
        report = SalesReport(timestamp=start.strftime("%Y-%m-%d %H:%M:%S"))

        # Step 1: 获取潜在客户
        leads = self._find_leads()
        report.leads_found = len(leads)
        report.leads = leads

        # Step 2: 调研
        for lead in leads:
            self._research_lead(lead)
            lead.status = "researching"

        # Step 3: 生成提案
        for lead in leads:
            if lead.priority in ("high", "medium"):
                proposal_path = self._generate_proposal(lead)
                if proposal_path:
                    report.proposals_generated += 1
                    report.proposals.append(proposal_path)
                    lead.status = "proposal_ready"

        # Step 4: 保存 leads
        self._save_leads(leads)
        report.summary = self._build_summary(report)
        print(f"[SalesPipeline] 周期完成: {report.leads_found}个客户, {report.proposals_generated}个提案")
        return report

    def add_lead(self, company: str, industry: str = "",
                 description: str = "", source: str = "manual") -> Lead:
        """手动添加一个潜在客户"""
        lead = Lead(
            company=company, industry=industry,
            description=description, source=source,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            updated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )
        self._append_lead_to_file(lead)
        print(f"[SalesPipeline] + 新客户: {company}")
        return lead

    def get_active_leads(self) -> List[Lead]:
        """获取当前活跃客户列表"""
        return self._load_leads()

    # ── 内部方法 ──

    def _find_leads(self) -> List[Lead]:
        """从多个来源收集潜在客户"""
        leads: List[Lead] = []
        seen = set()

        # 1. 从预设公司列表（自定义优先，否则默认）
        sources = self._custom_presets if self._custom_presets is not None else PRESET_COMPANIES
        for p in sources:
            if p["company"] not in seen:
                seen.add(p["company"])
                leads.append(Lead(
                    company=p["company"],
                    industry=p.get("industry", ""),
                    description=p.get("description", ""),
                    source="preset",
                    priority="high" if "Agent" in p.get("industry", "") else "medium",
                    created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    updated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
                ))

        # 2. 从已有的leads.md加载已有客户
        existing = self._load_leads()
        for ex in existing:
            if ex.company not in seen:
                seen.add(ex.company)
                leads.append(ex)

        return leads

    def _research_lead(self, lead: Lead) -> str:
        """为单个客户生成调研文档"""
        from .core.templates import SALES_RESEARCH_TEMPLATE
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        report_path = self._output_dir / f"research_{lead.company.replace(' ', '_')}.md"

        content = SALES_RESEARCH_TEMPLATE.format(
            company_name=lead.company,
            product_name=self.product_name,
            basic_info=f"行业: {lead.industry}\n描述: {lead.description}\n来源: {lead.source}",
            ai_maturity=f"初步评估: {lead.ai_readiness or '待评估'}\n(使用 Sales Agent research 获取深度分析)",
            security_needs="安全需求: 数据安全/合规/权限管控" if not self.has_tianlong else self._tianlong_security_text(),
            opportunity_assessment=f"优先级: {lead.priority}\n建议: 生成定制化销售提案",
            entry_point=f"通过 {lead.contact or '官网/社区'} 触达",
        )
        report_path.write_text(content, encoding="utf-8")
        lead.notes += f"\n调研报告: {report_path.name}"
        print(f"  📋 调研完成: {lead.company} -> {report_path.name}")
        return str(report_path)

    def _generate_proposal(self, lead: Lead) -> Optional[str]:
        """为单客户生成销售提案"""
        from .core.templates import SALES_PROPOSAL_TEMPLATE
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        filename = f"proposal_{lead.company.replace(' ', '_')}.md"
        proposal_path = self._output_dir / filename

        content = SALES_PROPOSAL_TEMPLATE.format(
            company_name=lead.company,
            product_name=self.product_name,
            company_profile=lead.description or f"{lead.company} — {lead.industry}领域公司",
            needs_analysis=self._needs_analysis_text(lead),
            value_proposition=self._value_proposition_text(),
            recommended_solution=self._recommended_solution_text(),
            contact_strategy=f"通过 {lead.contact or '官网/社区'} 触达",
            follow_up_plan=self._follow_up_plan_text(),
            generated_at=ts,
        )
        proposal_path.write_text(content, encoding="utf-8")
        print(f"  📝 提案生成: {lead.company} -> {proposal_path.name}")
        return str(proposal_path)

    def _save_leads(self, leads: List[Lead]) -> None:
        """保存leads到文件"""
        lines = [
            f"# {self.product_name} 潜在客户跟踪 (Leads)",
            "",
            f"> 更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"> 活跃客户: {len(leads)}",
            "",
            "| 公司 | 行业 | 来源 | 优先级 | 状态 | 联系方式 |",
            "|------|------|------|--------|------|----------|",
        ]
        for lead in leads:
            lines.append(
                f"| {lead.company} | {lead.industry} | {lead.source} "
                f"| {lead.priority} | {lead.status} | {lead.contact or '待确认'} |"
            )

        lines.append("")
        lines.append("## 客户详情")
        for lead in leads:
            lines.append(f"\n### [{lead.status}] {lead.company}")
            lines.append(f"- 行业: {lead.industry}")
            lines.append(f"- 描述: {lead.description}")
            lines.append(f"- 优先级: {lead.priority}")
            lines.append(f"- 创建: {lead.created_at}")
            if lead.notes:
                lines.append(f"- 备注: {lead.notes}")

        self._leads_file.parent.mkdir(parents=True, exist_ok=True)
        self._leads_file.write_text("\n".join(lines), encoding="utf-8")

    def _append_lead_to_file(self, lead: Lead) -> None:
        leads = self._load_leads()
        leads.append(lead)
        self._save_leads(leads)

    def _load_leads(self) -> List[Lead]:
        if not self._leads_file.exists():
            return []

        content = self._leads_file.read_text(encoding="utf-8")
        leads: List[Lead] = []
        current: Optional[Lead] = None

        for line in content.split("\n"):
            m = re.match(r'^### \[(\w+)\] (.+)', line)
            if m:
                if current:
                    leads.append(current)
                current = Lead(status=m.group(1), company=m.group(2))
            elif current:
                if line.startswith("- 行业:"):
                    current.industry = line[4:].strip()
                elif line.startswith("- 描述:"):
                    current.description = line[4:].strip()
                elif line.startswith("- 优先级:"):
                    current.priority = line[5:].strip()
                elif line.startswith("- 创建:"):
                    current.created_at = line[4:].strip()
                elif line.startswith("- 备注:"):
                    current.notes = line[4:].strip()

        if current:
            leads.append(current)
        return leads

    # ── 模板文本生成（根据是否安装了tianlong自动调整） ──

    def _tianlong_security_text(self) -> str:
        """从 tianlong-toolkit 获取安全能力展示（轻量，不做全量扫描）。"""
        try:
            # 检测版本和可用模块（轻量）
            import tianlong
            version = getattr(tianlong, '__version__', '?')
            return (
                f"AI Agent 安全审计（天龙工具箱 v{version}）:\n"
                f"- 30 条安全规则（IS×10 + SI×10 + PM×10）\n"
                f"- OWASP LLM Top 10 合规映射\n"
                f"- AST 解析 + 数据流追踪\n"
                f"- 三柱加权评分体系\n\n"
                f"快速体验: pip install tianlong-toolkit && tianlong-uxu scan ."
            )
        except Exception:
            pass
        return (
            f"AI Agent 安全需求: 提示注入/记忆注入/工具权限/数据泄露\n"
            f"合规需求: OWASP LLM Top 10\n"
            f"使用 {self.product_name} 一键审计: pip install tianlong-toolkit && tianlong-uxu scan ."
        )

    def _compintel_text(self, lead: Lead) -> str:
        """从 tianlong-toolkit 获取竞品情报数据。"""
        try:
            from tianlong.compintel import CompIntelTracker
            tracker = CompIntelTracker(project_dir=str(self.project_dir))
            competitors = tracker.competitors
            if competitors:
                lines = ["竞品格局分析（来自天龙工具箱竞品情报）:"]
                for c in competitors[:3]:
                    act = c.activity_score or 50
                    risk = c.risk_score or 50
                    lines.append(f"  - {c.name}: 活跃度{act:.0f}/100 威胁{risk:.0f}/100")
                return "\n".join(lines)
        except Exception:
            pass
        return ""

    def _needs_analysis_text(self, lead: Lead) -> str:
        if self.has_tianlong:
            security_data = self._tianlong_security_text()
            return (
                f"作为{lead.industry}领域公司，您可能面临以下挑战:\n"
                f"1. 🔴 Agent安全风险 — 提示注入/记忆篡改/工具滥用\n"
                f"2. 🟡 合规压力 — OWASP LLM Top 10 审计要求\n"
                f"3. 🟢 效率提升 — {self.product_name}提供完整解决方案。\n\n"
                f"📊 数据支撑:\n{security_data}"
            )
        return (
            f"作为{lead.industry}领域公司，{lead.company}可能面临以下挑战:\n"
            "1. 市场竞争加剧，需要提升产品差异化\n"
            "2. 客户需求变化，需要快速迭代\n"
            f"3. {self.product_name}可以帮助您应对这些挑战。"
        )

    def _value_proposition_text(self) -> str:
        if self.has_tianlong:
            compintel_data = ""
            try:
                import tianlong
                version = getattr(tianlong, '__version__', '?')
                compintel_data = f"\n\n竞品情报: 集成天龙工具箱 v{version} 竞品追踪"
            except Exception:
                pass

            return (
                f"| 特性 | {self.product_name} | 通用方案 |\n"
                "|------|-----------|-------------|\n"
                "| AI Agent专用 | ✅ 专用规则 | ❌ 通用 |\n"
                "| 安装 | pip install | 复杂部署 |\n"
                "| 健康监控 | ✅ 专项检查 | ❌ 无 |\n"
                "| 进化评估 | ✅ 多维评分 | ❌ 无 |\n"
                f"| 价格 | 🆓 MIT免费 | 💰 付费 |"
                f"{compintel_data}"
            )
        return f"{self.product_name}: {self.product_tagline} — {self.product_description}"

    def _recommended_solution_text(self) -> str:
        if self.has_tianlong:
            return (
                f"Step 1: pip install tianlong-toolkit\n"
                f"Step 2: tianlong-uxu scan . --severity high\n"
                "Step 3: 集成到CI — tianlong-audit -d .\n"
                "全程免费开源，5分钟完成安全审计。"
            )
        return (
            f"推荐方案: 使用 {self.product_name}\n"
            f"详情请咨询。"
        )

    def _follow_up_plan_text(self) -> str:
        return (
            "Day 1: 发送产品介绍\n"
            "Day 3: 跟进客户需求\n"
            "Day 7: 提供试用/演示\n"
            "Day 14: 推进合作"
        )

    @staticmethod
    def _build_summary(report: SalesReport) -> str:
        by_status: Dict[str, int] = {}
        for lead in report.leads:
            s = lead.status
            by_status[s] = by_status.get(s, 0) + 1

        return (
            f"销售周期完成 | "
            f"客户: {report.leads_found}个 | "
            f"提案: {report.proposals_generated}个 | "
            f"状态分布: {by_status}"
        )


# 导出 Chat Sales
from .core.master import SalesMaster  # noqa: E402
from .core.master import CustomerEmotion  # noqa: E402
from .core.psychology import PsychologicalEngine  # noqa: E402
from .core.multithread import MultiThreadManager, CustomerRole, CustomerContact  # noqa: E402
from .core.value import ValueConsultant  # noqa: E402
from .core.risk import RiskManager  # noqa: E402
from .core.language import LanguageMaster  # noqa: E402
from .core.evolver import StrategyEvolver  # noqa: E402

# 导出知识库系统
from .crm_pkg.knowledge import KnowledgeBase  # noqa: E402
from .crm_pkg.knowledge import get_knowledge_base  # noqa: E402

# 导出任务与审批系统
from .crm_pkg.tasks import TaskManager  # noqa: E402
from .crm_pkg.tasks import ApprovalManager  # noqa: E402
from .crm_pkg.tasks import NotificationManager  # noqa: E402
from .crm_pkg.tasks import get_task_manager  # noqa: E402
from .crm_pkg.tasks import get_approval_manager  # noqa: E402
from .crm_pkg.tasks import get_notification_manager  # noqa: E402

# 导出报价与合同系统
from .crm_pkg.quotes import ProductManager  # noqa: E402
from .crm_pkg.quotes import QuoteManager  # noqa: E402
from .crm_pkg.quotes import ContractManager  # noqa: E402
from .crm_pkg.quotes import TemplateManager  # noqa: E402
from .crm_pkg.quotes import get_product_manager  # noqa: E402
from .crm_pkg.quotes import get_quote_manager  # noqa: E402
from .crm_pkg.quotes import get_contract_manager  # noqa: E402

# 导出导出系统
from .crm_pkg.export import ExportManager  # noqa: E402
from .crm_pkg.export import get_export_manager  # noqa: E402

# 导出通话与录音系统
from .crm_pkg.calls import CallManager  # noqa: E402
from .crm_pkg.calls import RecordingManager  # noqa: E402
from .crm_pkg.calls import ScriptManager  # noqa: E402
from .crm_pkg.calls import AnalysisManager  # noqa: E402
from .crm_pkg.calls import get_call_manager  # noqa: E402
from .crm_pkg.calls import get_recording_manager  # noqa: E402
from .crm_pkg.calls import get_script_manager  # noqa: E402
from .crm_pkg.calls import get_analysis_manager  # noqa: E402

# 导出 RBAC 权限系统
from .crm_pkg.rbac import RoleManager  # noqa: E402
from .crm_pkg.rbac import UserManager  # noqa: E402
from .crm_pkg.rbac import AuthManager  # noqa: E402
from .crm_pkg.rbac import PermissionManager  # noqa: E402
from .crm_pkg.rbac import get_role_manager  # noqa: E402
from .crm_pkg.rbac import get_user_manager  # noqa: E402
from .crm_pkg.rbac import get_auth_manager  # noqa: E402
from .crm_pkg.rbac import get_permission_manager  # noqa: E402
from .crm_pkg.rbac import Permission, Role, User, RoleType, PERMISSION_GROUPS, ALL_PERMISSIONS  # noqa: E402
from .crm_pkg.rbac.audit import AuditLog, AuditLogger, AuditQuery, AuditLevel, get_audit_logger  # noqa: E402

# 导出 数据分析与智能决策系统
from .crm_pkg.analytics import DashboardManager  # noqa: E402
from .crm_pkg.analytics import KPICalculator  # noqa: E402
from .crm_pkg.analytics import TrendAnalyzer  # noqa: E402
from .crm_pkg.analytics import CustomerAnalyzer  # noqa: E402
from .crm_pkg.analytics import FunnelAnalyzer  # noqa: E402
from .crm_pkg.analytics import PredictionEngine  # noqa: E402
from .crm_pkg.analytics import RankingGenerator  # noqa: E402
from .crm_pkg.analytics import ReportGenerator  # noqa: E402
from .crm_pkg.analytics import get_dashboard_manager  # noqa: E402
from .crm_pkg.analytics import get_kpi_calculator  # noqa: E402
from .crm_pkg.analytics import get_prediction_engine  # noqa: E402
from .crm_pkg.analytics import get_report_generator  # noqa: E402

# 导出工作流引擎
from .core.workflow import (  # noqa: E402
    EventType, FlowStatus, StepStatus,
    Workflow, WorkflowStep, WorkflowEvent, WorkflowTemplate,
    EventBus, get_event_bus,
)
from .core.workflow.engine import WorkflowEngine, get_workflow_engine  # noqa: E402
from .core.workflow.listeners import WorkflowListener, get_workflow_listener  # noqa: E402

# 导出 SaaS 多租户系统
from .crm_pkg.saas import (  # noqa: E402
    Tenant, TenantUser, Subscription, UsageRecord,
    TenantStatus, UserStatus, PlanType,
    TenantContext, JWTToken, RateLimiter,
)
from .crm_pkg.saas.manager import SaaSManager, TenantStore, get_saas_manager  # noqa: E402

# 导出智能寻客系统
from .crm_pkg.lead_gen import (  # noqa: E402
    DataMiningService, get_data_mining_service,
    LeadScoringService, get_lead_scoring_service,
    LeadAssignmentService, get_lead_assignment_service,
    Lead, LeadStatus, LeadPriority,
    Salesperson, AssignmentRule, AssignmentStrategy,
    CompanyInfo, TenderInfo, RecruitmentInfo,
)

# 导出自动化跟进系统
from .crm_pkg.followup import (  # noqa: E402
    FollowupService, get_followup_service,
    CommunicationAssistant, get_communication_assistant,
    TaskAutomationService, get_task_automation_service,
    TriggerType, ActionType, EventType, BehaviorType,
    FollowupStep, FollowupSequence,
    ChannelType, FAQItem, MessageTemplate,
    Task, TaskStatus, TaskPriority, TaskType,
)

# 导出销售预测系统
from .crm_pkg.prediction import (  # noqa: E402
    SalesPredictionService, get_sales_prediction_service,
    RiskManagementService, get_risk_management_service,
    SmartRecommendationService, get_smart_recommendation_service,
    Deal, DealStage, PredictionResult,
    RiskAlert, RiskLevel, RiskType,
    Recommendation, RecommendationType,
)
