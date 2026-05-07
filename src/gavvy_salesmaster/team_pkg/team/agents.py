"""gavvy_salesmaster.team_pkg.team.agents — AI 销售 Agent 实现（社区版）

包含3个核心 Agent 的完整实现：
- MarketResearchAgent（市场调研官）
- CompetitorIntelAgent（竞品分析官）
- PresalesAgent（售前谈判官）

各 Agent 使用 BaseAgent 基类，通过 LLM 引擎驱动推理。
"""

from __future__ import annotations

import json
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import BaseAgent, AgentContext, AgentResult, Kernels, is_enterprise, COMMUNITY_UPGRADE_HINT


# ── Agent 提示词 ──────────────────────────────────



# ── Agent 类定义 ───────────────────────────────
# Agent 实现
# ══════════════════════════════════════════════════


class MarketResearchAgent(BaseAgent):
    """🎯 市场调研官 — 搜索潜在客户、行业分析、线索评分"""

    @property
    def role_en(self) -> str:
        return "market_research_agent"

    @property
    def role_cn(self) -> str:
        return "市场调研官"

    @property
    def description(self) -> str:
        return "🎯 搜索潜在客户、行业分析、线索评分"

    @property
    def kernels(self) -> Kernels:
        return Kernels(
            psychologist="理解客户决策心理，判断购买意向",
            strategist="制定行业覆盖策略，优先高价值领域",
            analyst="行业数据分析，线索质量评估",
            negotiator="",
        )

    def execute(self, context: AgentContext) -> AgentResult:
        # 构建分析上下文
        industry = context.extra.get("industry", "未知")
        description = context.extra.get("description", "")

        # 使用 LLM（如可用）生成分析
        output_text = self._generate_research(
            company=context.customer_name,
            industry=industry,
            description=description,
            history=context.extra.get("agent_history", []),
        )

        # 评分
        score_val = self._calculate_score(industry, description)

        summary = (
            f"调研完成：{context.customer_name}（{industry}）"
            f" | 成熟度评分 {score_val:.1%}"
        )

        return self._make_result(
            status="success",
            action="市场调研与线索评分",
            summary=summary,
            thinking=f"分析客户 {context.customer_name} 的行业={industry}，"
                     f"描述长度={len(description)}，历史数据={len(context.extra.get('agent_history', []))}条",
            output_text=output_text,
            internal_note=f"成熟度评分: {score_val:.1%}",
            output=[{
                "company": context.customer_name,
                "industry": industry,
                "score": round(score_val, 2),
                "insights": self._extract_insights(industry, description),
            }],
        )

    def _generate_research(self, company: str, industry: str,
                           description: str, history: List[Dict]) -> str:
        """生成调研报告（社区版仅模板输出，企业版调用 LLM）"""
        # 社区版：仅模板输出，加升级提示
        if not is_enterprise():
            text = self._template_research(company, industry, description)
            return text + COMMUNITY_UPGRADE_HINT

        # 企业版：调用服务端 API
        try:
            from gavvy_salesmaster.core.enterprise_client import EnterpriseAPIClient
            client = EnterpriseAPIClient()
            context = {"company": company, "industry": industry,
                       "description": description, "agent_history": history,
                       "client_name": company or "未知客户"}
            resp = client.chat_agent("market_research_agent", context)
            if resp.get("mode") == "enterprise_api" and resp.get("content"):
                return resp["content"]
        except Exception:
            pass

        # API 失败时模板降级
        text = self._template_research(company, industry, description)
        return text

    def _template_research(self, company: str, industry: str,
                           description: str) -> str:
        """模板降级调研报告（丰富版）"""
        maturity = self._maturity_label(industry)
        security = self._security_level(industry)
        opportunity = self._opportunity_label(industry)
        entry = self._entry_point(industry)
        insights = self._extract_insights(industry, description)
        score = self._calculate_score(industry, description)

        lines = [
            f"## {company} 市场调研报告\n",
            "### 客户基本信息",
            f"- **公司**: {company}",
            f"- **行业**: {industry}",
            f"- **业务描述**: {description or '暂无详细描述'}",
            f"- **技术栈**: 基于客户行业和描述推断",
            "",
            "### AI 技术栈成熟度评估",
            f"- **成熟度等级**: {maturity}",
            "- 该行业当前 AI 渗透率呈快速上升趋势",
            "- 客户对 AI Agent 安全运维有明确需求",
            "- 建议关注客户的 LangChain 或自研 Agent 框架的使用深度",
            "",
            "### 安全与运维需求分析",
            f"- **安全需求等级**: {security}",
            "- 当前安全审计机制待完善",
            "- Agent 生产环境需要实时监控与告警",
            "- 数据隐私与合规要求为高优先级",
            "",
            "### 商机评估",
            f"- **商机等级**: {opportunity}",
            f"- **匹配度评分**: {score:.0%}",
            "- 客户痛点与我们的方案高度匹配",
            "- 预计销售周期: 2-3个月",
            f"- 建议优先级: {'高' if score > 0.6 else '中' if score > 0.4 else '普通'}",
            "",
            "### 切入点建议",
            entry,
            "",
            "### 关键洞察",
        ]
        for ins in insights:
            lines.append(f"- {ins}")
        lines += [
            "",
            "### 风险提示",
            "- 需确认客户的预算周期和决策流程",
            "- 关注竞品在客户侧的布局情况",
            "- 建议安排技术交流验证兼容性",
        ]
        if score < 0.6:
            lines.append("- 评分偏低，建议进一步收集客户信息确认匹配度")

        return "\n".join(lines)

    @staticmethod
    def _calculate_score(industry: str, description: str) -> float:
        score = 0.3  # base
        high_value = ["AI", "LLM", "Agent", "大模型", "金融", "医疗", "科技"]
        for hv in high_value:
            if hv in industry or hv in description:
                score += 0.15
                break
        if len(description) > 50:
            score += 0.1
        if len(description) > 200:
            score += 0.1
        return min(score, 1.0)

    @staticmethod
    def _maturity_label(industry: str) -> str:
        return "高" if any(kw in industry for kw in ["AI", "科技", "互联网"]) else "中"

    @staticmethod
    def _security_level(industry: str) -> str:
        return "高" if any(kw in industry for kw in ["金融", "医疗", "政务"]) else "中"

    @staticmethod
    def _opportunity_label(industry: str) -> str:
        return "大" if any(kw in industry for kw in ["AI", "Agent", "大模型"]) else "中"

    @staticmethod
    def _entry_point(industry: str) -> str:
        if "AI" in industry or "Agent" in industry:
            return "- 切入点：安全审计与合规需求\n- 推荐方案：UXU 安全扫描 + 进化闭环"
        if "金融" in industry:
            return "- 切入点：数据合规与风控\n- 推荐方案：安全监控 + 审计追踪"
        return "- 切入点：数字化转型安全需求\n- 推荐方案：基础安全运维套件"

    @staticmethod
    def _extract_insights(industry: str, description: str) -> List[str]:
        insights = []
        if industry:
            insights.append(f"{industry}行业当前AI采纳率中高")
        if "安全" in description:
            insights.append("客户有明确安全需求")
        return insights


class CompetitorIntelAgent(BaseAgent):
    """🔍 竞品分析官 — 竞品对标、差异化策略、市场定位"""

    @property
    def role_en(self) -> str:
        return "competitor_intel_agent"

    @property
    def role_cn(self) -> str:
        return "竞品分析官"

    @property
    def description(self) -> str:
        return "🔍 竞品对标、差异化策略、市场定位"

    @property
    def kernels(self) -> Kernels:
        return Kernels(
            psychologist="理解竞品定位背后的客户心理",
            strategist="制定差异化竞争策略",
            analyst="竞品数据对比分析",
            negotiator="",
        )

    def execute(self, context: AgentContext) -> AgentResult:
        competitor_name = context.customer_name
        industry = context.extra.get("industry", "未知")
        description = context.extra.get("description", "")
        history = context.extra.get("agent_history", [])

        output_text = self._generate_analysis(
            competitor=competitor_name,
            industry=industry,
            description=description,
            history=history,
        )

        diff_score = self._differentiation_score(industry)

        summary = (
            f"竞品分析完成：{competitor_name}"
            f" | 差异化空间 {diff_score:.0%}"
        )

        return self._make_result(
            status="success",
            action="竞品对标与差异化分析",
            summary=summary,
            thinking=f"分析竞品 {competitor_name}，行业={industry}，"
                     f"差异化评分={diff_score:.0%}",
            output_text=output_text,
            internal_note=f"差异化空间: {diff_score:.0%}",
            output=[{
                "competitor": competitor_name,
                "industry": industry,
                "diff_score": round(diff_score, 2),
                "strengths": self._competitor_strengths(competitor_name),
                "weaknesses": self._competitor_weaknesses(competitor_name),
                "our_advantage": self._our_advantage(competitor_name),
            }],
        )

    def _generate_analysis(self, competitor: str, industry: str,
                           description: str, history: List[Dict]) -> str:
        """生成竞品分析（社区版仅模板输出，企业版调用 LLM）"""
        # 社区版：仅模板输出，加升级提示
        if not is_enterprise():
            text = self._template_analysis(competitor, industry, description)
            return text + COMMUNITY_UPGRADE_HINT

        # 企业版：调用服务端 API
        try:
            from gavvy_salesmaster.core.enterprise_client import EnterpriseAPIClient
            client = EnterpriseAPIClient()
            context = {"competitor_name": competitor, "industry": industry,
                       "description": description, "agent_history": history}
            resp = client.chat_agent("competitor_intel_agent", context)
            if resp.get("mode") == "enterprise_api" and resp.get("content"):
                return resp["content"]
        except Exception:
            pass

        # API 失败时模板降级
        text = self._template_analysis(competitor, industry, description)
        return text

    def _template_analysis(self, competitor: str, industry: str,
                           description: str) -> str:
        """模板降级竞品分析"""
        return (
            f"## {competitor} 竞品分析报告\n\n"
            f"**行业**: {industry}\n"
            f"**定位**: {description or 'AI 工具/平台'}\n\n"
            f"### 差异化分析\n"
            f"- 优势领域: {', '.join(self._competitor_strengths(competitor))}\n"
            f"- 弱点领域: {', '.join(self._competitor_weaknesses(competitor))}\n"
            f"- 我们的优势: {', '.join(self._our_advantage(competitor))}\n\n"
            f"### 竞争策略\n"
            f"1. 聚焦安全运维差异化\n"
            f"2. 强调全生命周期管理\n"
            f"3. 突出中文生态优化"
        )

    @staticmethod
    def _differentiation_score(industry: str) -> float:
        return 0.6

    @staticmethod
    def _competitor_strengths(name: str) -> List[str]:
        db = {
            "LangChain": ["生态丰富", "社区活跃", "集成广泛"],
            "CrewAI": ["多Agent架构", "快速上手"],
            "AutoGPT": ["品牌知名度", "自主性"],
            "Hugging Face": ["模型生态", "数据科学社区"],
        }
        return db.get(name, ["技术积累", "市场认知"])

    @staticmethod
    def _competitor_weaknesses(name: str) -> List[str]:
        db = {
            "LangChain": ["安全审计缺失", "运维复杂"],
            "CrewAI": ["生产级部署弱", "监控不足"],
            "AutoGPT": ["稳定性差", "企业级功能少"],
            "Hugging Face": ["非运维工具", "安全功能有限"],
        }
        return db.get(name, ["安全运维能力弱", "中文支持不足"])

    @staticmethod
    def _our_advantage(name: str) -> List[str]:
        return ["安全审计能力", "全生命周期管理", "进化闭环", "中文生态"]


class PresalesAgent(BaseAgent):
    """💬 售前谈判官 — 客户接触、价值传递、异议处理、促成成交"""

    @property
    def role_en(self) -> str:
        return "presales_agent"

    @property
    def role_cn(self) -> str:
        return "售前谈判官"

    @property
    def description(self) -> str:
        return "💬 客户接触、价值传递、异议处理、促成成交"

    @property
    def kernels(self) -> Kernels:
        return Kernels(
            psychologist="感知客户情绪和购买意愿",
            strategist="制定谈判策略和报价方案",
            analyst="分析客户需求和预算",
            negotiator="处理异议、引导成交",
        )

    def execute(self, context: AgentContext) -> AgentResult:
        message = context.message or "了解产品"
        stage = context.stage

        output_text = self._generate_response(
            customer=context.customer_name,
            product=context.product_info,
            message=message,
            stage=stage,
            history=context.extra.get("agent_history", []),
            pricing=context.private.pricing,
        )

        # 检测动作类型
        action = self._detect_action(stage, message)
        deal_readiness = self._deal_readiness(stage, message)

        summary = (
            f"售前跟进：{context.customer_name}"
            f" | 动作: {action}"
            f" | 成交意愿: {deal_readiness:.0%}"
        )

        return self._make_result(
            status="success",
            action=action,
            summary=summary,
            thinking=f"售前处理：客户={context.customer_name}，阶段={stage}，"
                     f"消息='{message[:50]}'",
            output_text=output_text,
            internal_note=f"成交意愿: {deal_readiness:.0%}",
            output=[{
                "customer": context.customer_name,
                "stage": stage,
                "action": action,
                "deal_readiness": round(deal_readiness, 2),
            }],
        )

    def _generate_response(self, customer: str, product: str,
                           message: str, stage: str,
                           history: List[Dict], pricing: str) -> str:
        """生成售前回复（社区版仅模板输出，企业版调用 LLM）"""
        # 社区版：仅模板输出，加升级提示
        if not is_enterprise():
            text = self._template_response(customer, message, stage)
            return text + COMMUNITY_UPGRADE_HINT

        # 企业版：调用服务端 API
        try:
            from gavvy_salesmaster.core.enterprise_client import EnterpriseAPIClient
            client = EnterpriseAPIClient()
            private_info = f"\n内部参考 - 定价: {pricing}" if pricing else ""
            context = {"customer_name": customer, "product_info": product,
                       "message": message, "stage": stage,
                       "agent_history": history, "private_info": private_info}
            resp = client.chat_agent("presales_agent", context)
            if resp.get("mode") == "enterprise_api" and resp.get("content"):
                return resp["content"]
        except Exception:
            pass

        # API 失败时模板降级
        text = self._template_response(customer, message, stage)
        return text

    def _template_response(self, customer: str, message: str,
                           stage: str) -> str:
        """模板降级售前回复（丰富版）"""
        lines = [f"您好 {customer}！"]

        if stage == "negotiation":
            if "价格" in message or "贵" in message or "优惠" in message:
                lines += [
                    f"感谢您的坦诚反馈。关于价格，我理解这是您关心的问题。",
                    "",
                    "我们的方案提供的是全生命周期价值，包括：",
                    "- 安全审计（36条规则覆盖OWASP LLM Top 10）",
                    "- 自动进化闭环（Ralph Loop持续优化）",
                    "- 运维监控与告警（8项健康检查）",
                    "- 记忆库与自我学习系统",
                    "",
                    "相比单点工具，我们的平台帮您节省：",
                    "- 运维人力成本约60%（自动化替代人工巡检）",
                    "- 安全合规成本约40%（内置审计框架）",
                    "- 工具集成成本约70%（一站式平台）",
                    "",
                    "我们可以提供：",
                    "1. 灵活的付款方案（季付/年付均有折扣）",
                    "2. 先POC后付费（验证效果再决策）",
                    "3. 根据实际需求定制套餐",
                    "",
                    "建议安排一次15分钟的技术交流，我可以根据您的具体场景定制方案。",
                ]
            elif "功能" in message or "介绍" in message or "方案" in message:
                lines += [
                    f"感谢关注！我们是一站式AI Agent安全运维平台。",
                    "",
                    "核心能力：",
                    "- UXU安全审计：36条规则，覆盖OWASP LLM Top 10",
                    "- 进化闭环：Ralph Loop持续自我优化",
                    "- 运维监控：8项健康检查+Dashboard",
                    "- 记忆系统：4层记忆架构+自我学习",
                    "",
                    f"请问您最关注哪个方面？我可以针对性地做详细介绍。",
                ]
            else:
                lines += [
                    f"感谢您的消息。我理解您目前处于{ { 'discovery': '初步了解', 'research': '调研评估', 'contact': '接触了解', 'negotiation': '谈判议价', 'closing': '成交决策' }.get(stage, '了解') }阶段。",
                    "",
                    "为了更好地帮到您，想了解一下：",
                    "1. 您目前主要关注哪些业务场景？",
                    "2. 当前团队规模和技术栈是怎样的？",
                    "3. 有没有明确的预算和时间规划？",
                ]
        elif stage == "contact":
            lines += [
                f"感谢关注！很荣幸能与您交流。",
                f"我们的解决方案在{ '您的行业' }有成熟应用经验。",
                "",
                "方便的话，您可以分享一下当前的主要需求和挑战，",
                "我可以为您提供针对性的建议和方案。",
            ]
        elif stage == "closing":
            lines += [
                "很高兴能达成共识！接下来我们将：",
                "1. 安排上线演示（约30分钟）",
                "2. 提供部署方案和周期预估",
                "3. 准备合同与订单",
                "",
                "最快本周即可开始部署。请问您方便什么时间？",
            ]
        else:
            lines += [
                f"收到您的消息。请问有什么可以帮助您的？",
            ]

        return "\n".join(lines)

    @staticmethod
    def _detect_action(stage: str, message: str) -> str:
        if stage == "closing":
            return "促成成交"
        if "价格" in message or "多少" in message:
            return "报价与议价"
        if "介绍" in message or "功能" in message:
            return "产品方案介绍"
        return "客户跟进与沟通"

    @staticmethod
    def _deal_readiness(stage: str, message: str) -> float:
        stage_scores = {"closing": 0.8, "negotiation": 0.6,
                         "contact": 0.3, "discovery": 0.1}
        base = stage_scores.get(stage, 0.3)
        # 正面信号加分
        positive = ["好", "可以", "试试", "报价", "合同", "方案"]
        for p in positive:
            if p in message:
                base += 0.1
                break
        return min(base, 1.0)


# ══════════════════════════════════════════════════
# AftersalesAgent
# ══════════════════════════════════════════════════


class AftersalesAgent(BaseAgent):
    """🤝 售后维系官 — 售后支持、客户续约、推荐裂变"""

    @property
    def role_en(self) -> str:
        return "aftersales_agent"

    @property
    def role_cn(self) -> str:
        return "售后维系官"

    @property
    def description(self) -> str:
        return "🤝 售后支持、客户续约、推荐裂变"

    @property
    def kernels(self) -> Kernels:
        return Kernels(
            psychologist="感知客户满意度，判断流失风险",
            strategist="制定续约策略，设计推荐计划",
            analyst="分析使用数据，识别高价值客户",
            negotiator="处理售后异议，引导正面评价",
        )

    def execute(self, context: AgentContext) -> AgentResult:
        message = context.message or "售后支持"
        output_text = self._generate_response(
            customer=context.customer_name,
            message=message,
            product=context.product_info,
            history=context.extra.get("agent_history", []),
        )
        return self._make_result(
            status="success",
            action="售后支持与客户维系",
            summary=f"售后跟进：{context.customer_name} | 消息: {message[:30]}",
            thinking=f"售后处理：客户={context.customer_name}，消息='{message[:50]}'",
            output_text=output_text,
            output=[{
                "customer": context.customer_name,
                "action": "aftersales_support",
            }],
        )

    def _generate_response(self, customer: str, message: str,
                           product: str, history: List[Dict]) -> str:
        if not is_enterprise():
            text = self._template_response(customer, message)
            return text + COMMUNITY_UPGRADE_HINT
        try:
            from gavvy_salesmaster.core.enterprise_client import EnterpriseAPIClient
            client = EnterpriseAPIClient()
            context = {"customer_name": customer, "message": message}
            resp = client.chat_agent("aftersales_agent", context)
            if resp.get("mode") == "enterprise_api" and resp.get("content"):
                return resp["content"]
        except Exception:
            pass
        return self._template_response(customer, message)

    @staticmethod
    def _template_response(customer: str, message: str) -> str:
        return (
            f"您好 {customer}，感谢您使用我们的产品！\\n\\n"
            f"收到您的消息：{message[:100]}\\n"
            f"我们会尽快处理您的问题。如果遇到紧急情况，可以联系专属客服。"
        )


# ══════════════════════════════════════════════════
# ProcurementAgent
# ══════════════════════════════════════════════════


class ProcurementAgent(BaseAgent):
    """💰 采购供应链官 — 成本分析、供应商匹配、利润核算"""

    @property
    def role_en(self) -> str:
        return "procurement_agent"

    @property
    def role_cn(self) -> str:
        return "采购供应链官"

    @property
    def description(self) -> str:
        return "💰 成本分析、供应商匹配、利润核算"

    @property
    def kernels(self) -> Kernels:
        return Kernels(
            psychologist="判断供应商谈判意愿和底线",
            strategist="制定采购策略和备选方案",
            analyst="成本结构分析与利润测算",
            negotiator="合同条款谈判，争取最优条件",
        )

    def execute(self, context: AgentContext) -> AgentResult:
        requirements = context.extra.get("requirements", context.message or "采购需求")
        pricing = context.private.pricing or "未提供"
        cost = context.private.cost or "未提供"
        output_text = self._generate_analysis(
            requirements=requirements, pricing=pricing, cost=cost,
        )
        return self._make_result(
            status="success",
            action="采购供应链分析",
            summary=f"采购分析：{context.customer_name} | 成本核算完成",
            thinking=f"采购分析：需求='{requirements[:50]}'，定价={pricing}",
            output_text=output_text,
            output=[{"requirements": requirements}],
        )

    def _generate_analysis(self, requirements: str, pricing: str, cost: str) -> str:
        if not is_enterprise():
            text = self._template_analysis(requirements)
            return text + COMMUNITY_UPGRADE_HINT
        try:
            from gavvy_salesmaster.core.enterprise_client import EnterpriseAPIClient
            client = EnterpriseAPIClient()
            context = {"requirements": requirements, "pricing": pricing, "cost": cost}
            resp = client.chat_agent("procurement_agent", context)
            if resp.get("mode") == "enterprise_api" and resp.get("content"):
                return resp["content"]
        except Exception:
            pass
        return self._template_analysis(requirements)

    @staticmethod
    def _template_analysis(requirements: str) -> str:
        return f"## 采购分析报告\\n\\n**需求**: {requirements}\\n\\n### 建议\\n- 推荐3家以上供应商比价\\n- 关注总拥有成本(TCO)\\n- 签订保价条款"


# ══════════════════════════════════════════════════
# OperationsAgent
# ══════════════════════════════════════════════════


class OperationsAgent(BaseAgent):
    """📊 运营增长官 — 客户分层、话术迭代、渠道优化"""

    @property
    def role_en(self) -> str:
        return "operations_agent"

    @property
    def role_cn(self) -> str:
        return "运营增长官"

    @property
    def description(self) -> str:
        return "📊 客户分层、话术迭代、渠道优化"

    @property
    def kernels(self) -> Kernels:
        return Kernels(
            psychologist="理解客户行为背后的动机",
            strategist="制定增长策略和渠道矩阵",
            analyst="数据驱动的效果分析",
            negotiator="",
        )

    def execute(self, context: AgentContext) -> AgentResult:
        data_summary = context.extra.get("data_summary", context.message or "运营数据")
        output_text = self._generate_report(data_summary)
        return self._make_result(
            status="success",
            action="运营增长分析",
            summary=f"运营分析：{context.customer_name} | 数据评估完成",
            thinking=f"运营分析：数据摘要='{data_summary[:50]}'",
            output_text=output_text,
            output=[{"data_summary": data_summary}],
        )

    def _generate_report(self, data_summary: str) -> str:
        if not is_enterprise():
            text = self._template_report(data_summary)
            return text + COMMUNITY_UPGRADE_HINT
        try:
            from gavvy_salesmaster.core.enterprise_client import EnterpriseAPIClient
            client = EnterpriseAPIClient()
            context = {"data_summary": data_summary}
            resp = client.chat_agent("operations_agent", context)
            if resp.get("mode") == "enterprise_api" and resp.get("content"):
                return resp["content"]
        except Exception:
            pass
        return self._template_report(data_summary)

    @staticmethod
    def _template_report(data_summary: str) -> str:
        return f"## 运营增长报告\\n\\n**数据**: {data_summary}\\n\\n### 建议\\n- A/B测试关键转化节点\\n- 优化高流失率环节\\n- 加大高ROI渠道投入"


# ══════════════════════════════════════════════════
# PlatformOpsAgent
# ══════════════════════════════════════════════════


class PlatformOpsAgent(BaseAgent):
    """📋 运营助理 — 商品上架审核、平台规则检查、违禁词检测"""

    @property
    def role_en(self) -> str:
        return "platform_ops_agent"

    @property
    def role_cn(self) -> str:
        return "运营助理"

    @property
    def description(self) -> str:
        return "📋 商品上架审核、平台规则检查、违禁词检测"

    @property
    def kernels(self) -> Kernels:
        return Kernels(
            psychologist="",
            strategist="",
            analyst="规则合规性分析",
            negotiator="",
        )

    def execute(self, context: AgentContext) -> AgentResult:
        product_info = context.extra.get("product_info", context.message or "商品信息")
        forbidden = context.private.forbidden_phrases or []
        output_text = self._check_compliance(product_info, forbidden)
        is_compliant = "合规" in output_text
        return self._make_result(
            status="success",
            action="商品合规检查",
            summary=f"合规检查：{context.customer_name} | {'✅ 合规' if is_compliant else '⚠️ 需修改'}",
            thinking=f"平台合规检查：商品='{product_info[:50]}'，违禁词={forbidden}",
            output_text=output_text,
            output=[{"compliant": is_compliant, "product": context.customer_name}],
        )

    def _check_compliance(self, product_info: str, forbidden_phrases: List[str]) -> str:
        if not is_enterprise():
            text = self._template_check(product_info, forbidden_phrases)
            return text + COMMUNITY_UPGRADE_HINT
        try:
            from gavvy_salesmaster.core.enterprise_client import EnterpriseAPIClient
            client = EnterpriseAPIClient()
            context = {"product_info": product_info, "forbidden_phrases": forbidden_phrases}
            resp = client.chat_agent("platform_ops_agent", context)
            if resp.get("mode") == "enterprise_api" and resp.get("content"):
                return resp["content"]
        except Exception:
            pass
        return self._template_check(product_info, forbidden_phrases)

    def _template_check(self, product_info: str, forbidden_phrases: List[str]) -> str:
        hits = [f for f in forbidden_phrases if f in product_info]
        if hits:
            return f"## 合规检查结果\\n\\n⚠️ **发现违禁词**: {', '.join(hits)}\\n请修改后重新提交审核。"
        return "## 合规检查结果\\n\\n✅ **合规**\\n商品信息通过平台规则检查。"
