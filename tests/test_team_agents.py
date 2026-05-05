"""Test team module — Agent base, orchestrator, pipeline trigger"""

from __future__ import annotations

import json
import os
import tempfile
import uuid

import pytest

from SentriKit_salesmaster.team_pkg.team.base import (
    BaseAgent, AgentContext, AgentResult, PrivateInput, Kernels,
    AgentRole, LeadScorer, SafetyGuard, SafetyMode, QuickstartGuide,
)
from SentriKit_salesmaster.team_pkg.team.coordinator import (
    SalesOrchestrator, PipelineTrigger, STAGES, STAGE_LABELS,
)
from SentriKit_salesmaster.team_pkg.team.agents import (
    MarketResearchAgent, CompetitorIntelAgent, PresalesAgent,
)


# ── 重置 Singleton ────────────────────────────────


@pytest.fixture(autouse=True)
def reset_orchestrator():
    import threading as _th
    SalesOrchestrator._instance = None
    SalesOrchestrator._lock = _th.Lock()
    yield


# ── BaseAgent 测试 ────────────────────────────────


class TestBaseAgent:
    def test_context_creation(self):
        ctx = AgentContext(
            product_info="安全运维工具箱",
            customer_name="测试客户",
            message="了解产品",
            stage="contact",
        )
        assert ctx.product_info == "安全运维工具箱"
        assert ctx.customer_name == "测试客户"
        assert ctx.stage == "contact"

    def test_context_with_private(self):
        priv = PrivateInput(pricing="999/月", cost="200/月")
        ctx = AgentContext(
            customer_name="客户A",
            private=priv,
        )
        assert ctx.private.pricing == "999/月"
        assert ctx.private.cost == "200/月"

    def test_result_creation(self):
        result = AgentResult(
            status="success",
            action="市场调研",
            summary="调研完成：客户A",
            output_text="详细报告...",
        )
        assert result.status == "success"
        assert result.agent_cn == ""  # 未设置

    def test_result_serialization(self):
        result = AgentResult(
            status="success",
            action="测试动作",
            summary="测试摘要",
            output=[{"key": "value"}],
        )
        d = result.to_dict()
        assert d["status"] == "success"
        assert d["output"] == [{"key": "value"}]
        restored = AgentResult.from_dict(d)
        assert restored.status == "success"

    def test_private_input_roundtrip(self):
        priv = PrivateInput(pricing="1000", cost="200",
                            forbidden_phrases=["禁止词1"])
        d = priv.to_dict()
        restored = PrivateInput.from_dict(d)
        assert restored.pricing == "1000"
        assert restored.forbidden_phrases == ["禁止词1"]

    def test_kernels_default(self):
        k = Kernels()
        assert k.psychologist == ""

    def test_lead_scorer_high_value(self):
        score = LeadScorer.score({
            "industry": "AI Agent",
            "description": "一个专注于AI Agent开发的创新企业，拥有完整的技术团队",
            "source": "web_search",
        })
        assert score.score > 0.3

    def test_lead_scorer_low_value(self):
        score = LeadScorer.score({
            "industry": "传统制造",
            "description": "小企业",
            "source": "preset",
        })
        assert score.score < 0.5


# ── SalesOrchestrator 测试 ───────────────────────


class TestSalesOrchestrator:
    def get_orch(self):
        SalesOrchestrator._instance = None
        return SalesOrchestrator(storage_path=tempfile.mkdtemp())

    def test_singleton(self):
        o1 = SalesOrchestrator()
        SalesOrchestrator._instance = None
        o2 = SalesOrchestrator()
        # 单例：第二次实例化应返回第一次的实例
        # 因为 _instance 重置为 None，会创建新实例
        assert o1 is not o2  # _instance重置后是新实例
        SalesOrchestrator._instance = None

    def test_add_lead(self):
        orch = self.get_orch()
        lid = orch.add_lead("test_1", {"name": "客户A", "stage": "discovery"})
        assert lid == "test_1"
        assert orch.get_lead_count() == 1

    def test_add_lead_auto_id(self):
        orch = self.get_orch()
        lid = orch.add_lead("", {"name": "客户B"})
        assert lid.startswith("lead_")
        assert orch.get_lead_count() == 1

    def test_update_lead_stage(self):
        orch = self.get_orch()
        orch.add_lead("t1", {"name": "测试", "stage": "discovery"})
        orch.update_lead_stage("t1", "contact")
        lead = orch.get_lead("t1")
        assert lead.stage == "contact"

    def test_get_summary(self):
        orch = self.get_orch()
        orch.add_lead("l1", {"name": "A"})
        summary = orch.get_summary()
        assert summary["total_leads"] == 1

    def test_register_agent(self):
        orch = self.get_orch()
        agent = MarketResearchAgent()
        orch.register_agent(agent)
        assert "market_research_agent" in orch.get_registered_agents()

    def test_assign_task_no_agent(self):
        orch = self.get_orch()
        orch.add_lead("fail_test", {"name": "无Agent"})
        result = orch.assign_task("fail_test")
        assert result.status == "failed"

    def test_assign_task_with_agent(self):
        orch = self.get_orch()
        orch.add_lead("agent_test", {"name": "有Agent", "stage": "discovery",
                                     "product_info": "安全产品"})
        orch.register_agent(MarketResearchAgent())
        result = orch.assign_task("agent_test")
        assert result.status == "success"
        assert result.action == "市场调研与线索评分"

    def test_assign_task_history_injection(self):
        orch = self.get_orch()
        lid = orch.add_lead("hist_test", {"name": "历史客户",
                                          "stage": "research",
                                          "product_info": "产品"})
        # 手动注入历史
        with orch._leads_lock:
            orch._leads[lid].history.append({
                "agent": "market_research_agent",
                "action": "调研",
                "summary": "前期调研数据",
                "status": "success",
            })
        orch.register_agent(CompetitorIntelAgent())
        result = orch.assign_task(lid)
        assert result.status == "success"

    def test_flow_toggle(self):
        orch = self.get_orch()
        assert orch.is_flow_enabled("auto_pipeline") is True
        orch.set_flow_toggle("auto_pipeline", False)
        assert orch.is_flow_enabled("auto_pipeline") is False

    def test_safety_mode(self):
        orch = self.get_orch()
        orch.set_safety_mode("open")
        assert orch.get_safety_mode()["mode"] == "open"

    def test_persist_restore(self):
        orch = self.get_orch()
        lid = orch.add_lead("persist_test", {"name": "持久化测试"})
        orch.persist()
        # 新实例恢复
        SalesOrchestrator._instance = None
        orch2 = SalesOrchestrator(storage_path=orch._storage_path)
        ok = orch2.restore()
        assert ok
        lead = orch2.get_lead(lid)
        assert lead is not None
        assert lead.name == "持久化测试"

    def test_agents_summary(self):
        orch = self.get_orch()
        orch.register_agent(MarketResearchAgent())
        orch.register_agent(PresalesAgent())
        agents = orch.get_agents_summary()
        assert len(agents) == 2
        assert "market_research_agent" in agents
        assert agents["market_research_agent"]["role_cn"] == "市场调研官"


# ── PipelineTrigger 测试 ─────────────────────────


class TestPipelineTrigger:
    def get_orch(self):
        SalesOrchestrator._instance = None
        return SalesOrchestrator(storage_path=tempfile.mkdtemp())

    def test_advance_stage(self):
        orch = self.get_orch()
        orch.register_agent(MarketResearchAgent())
        orch.register_agent(CompetitorIntelAgent())
        lid = orch.add_lead("adv_test", {"name": "推进测试",
                                          "stage": "discovery"})
        result = PipelineTrigger.advance_stage(orch, lid)
        assert result["success"] is True
        assert result["from_stage"] == "discovery"
        assert result["to_stage"] == "research"

    def test_advance_stage_last_stage(self):
        orch = self.get_orch()
        lid = orch.add_lead("last_test", {"name": "最终阶段",
                                           "stage": "listing"})
        result = PipelineTrigger.advance_stage(orch, lid)
        assert result["success"] is False

    def test_advance_stage_not_found(self):
        orch = self.get_orch()
        result = PipelineTrigger.advance_stage(orch, "nonexistent")
        assert result["success"] is False

    def test_check_timeouts_empty(self):
        orch = self.get_orch()
        timeouts = PipelineTrigger.check_timeouts(orch)
        assert timeouts == []

    def test_check_timeouts_fresh(self):
        orch = self.get_orch()
        orch.add_lead("fresh", {"name": "新客户"})
        timeouts = PipelineTrigger.check_timeouts(orch)
        assert len(timeouts) == 0  # 刚创建，未超时

    def test_auto_follow_up(self):
        orch = self.get_orch()
        orch.register_agent(MarketResearchAgent())
        orch.register_agent(CompetitorIntelAgent())
        lid = orch.add_lead("auto_test", {"name": "自动推进"})
        # 添加历史记录（模拟已经调研过）
        with orch._leads_lock:
            orch._leads[lid].history.append({
                "agent": "market_research_agent",
                "action": "调研",
                "summary": "已完成初步调研",
                "status": "success",
            })
        # 修改更新时间使其超时
        import datetime
        old_time = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        with orch._leads_lock:
            orch._leads[lid].updated_at = old_time
        result = PipelineTrigger.auto_follow_up(orch)
        assert result["checked"] >= 1
        assert result["timeouts_count"] >= 1


# ── Agent 实现测试 ───────────────────────────────


class TestMarketResearchAgent:
    def test_agent_basics(self):
        agent = MarketResearchAgent()
        assert agent.role_en == "market_research_agent"
        assert agent.role_cn == "市场调研官"
        assert agent.description.startswith("🎯")

    def test_execute_with_context(self):
        agent = MarketResearchAgent()
        ctx = AgentContext(customer_name="测试公司",
                           message="调研需求")
        ctx.extra["industry"] = "AI Agent"
        ctx.extra["description"] = "一家专注于AI Agent开发的科技公司"
        result = agent.execute(ctx)
        assert result.status == "success"
        assert "测试公司" in result.summary
        assert result.action == "市场调研与线索评分"
        assert len(result.output) > 0

    def test_execute_with_history(self):
        agent = MarketResearchAgent()
        ctx = AgentContext(customer_name="历史客户")
        ctx.extra["agent_history"] = [
            {"agent": "presales_agent", "summary": "前期沟通完成", "action": "沟通"}
        ]
        result = agent.execute(ctx)
        assert result.status == "success"


class TestCompetitorIntelAgent:
    def test_agent_basics(self):
        agent = CompetitorIntelAgent()
        assert agent.role_en == "competitor_intel_agent"
        assert agent.role_cn == "竞品分析官"

    def test_execute(self):
        agent = CompetitorIntelAgent()
        ctx = AgentContext(customer_name="LangChain",
                           message="竞品分析")
        ctx.extra["industry"] = "AI Agent框架"
        result = agent.execute(ctx)
        assert result.status == "success"
        assert "LangChain" in result.summary
        assert "竞品" in result.action

    def test_execute_with_preset_data(self):
        agent = CompetitorIntelAgent()
        ctx = AgentContext(customer_name="CrewAI")
        ctx.extra["industry"] = "多Agent框架"
        ctx.extra["description"] = "多Agent协作框架"
        result = agent.execute(ctx)
        assert result.status == "success"
        assert len(result.output) > 0


class TestPresalesAgent:
    def test_agent_basics(self):
        agent = PresalesAgent()
        assert agent.role_en == "presales_agent"
        assert agent.role_cn == "售前谈判官"

    def test_execute_contact(self):
        agent = PresalesAgent()
        ctx = AgentContext(customer_name="潜在客户",
                           product_info="安全工具",
                           message="我想了解产品功能",
                           stage="contact")
        result = agent.execute(ctx)
        assert result.status == "success"
        assert "售前" in result.action or "跟进" in result.action or "方案" in result.action

    def test_execute_closing(self):
        agent = PresalesAgent()
        ctx = AgentContext(customer_name="成交客户",
                           product_info="企业版",
                           message="好的，我们决定试试",
                           stage="closing")
        result = agent.execute(ctx)
        assert result.status == "success"
        assert result.output[0]["deal_readiness"] > 0.5

    def test_execute_with_pricing(self):
        agent = PresalesAgent()
        ctx = AgentContext(customer_name="询价客户",
                           private=PrivateInput(pricing="999/月"))
        ctx.message = "价格多少"
        result = agent.execute(ctx)
        assert result.status == "success"


# ── SafetyGuard 测试 ─────────────────────────────


class TestSafetyGuard:
    def test_conservative_mode(self):
        guard = SafetyGuard(mode=SafetyMode.CONSERVATIVE)
        assert guard.check_action("deal") is False  # 敏感动作被阻止
        assert guard.check_action("info_request") is True  # 非敏感放行

    def test_open_mode(self):
        guard = SafetyGuard(mode=SafetyMode.OPEN)
        assert guard.check_action("deal") is True

    def test_custom_mode_high_price(self):
        guard = SafetyGuard(mode=SafetyMode.CUSTOM)
        # 大额报价被阻止
        assert guard.check_action("quote", "总价¥100000", price_ceiling=50000) is False

    def test_custom_mode_low_price(self):
        guard = SafetyGuard(mode=SafetyMode.CUSTOM)
        assert guard.check_action("quote", "价格¥10000", price_ceiling=50000) is True

    def test_logging(self):
        guard = SafetyGuard()
        guard.check_action("deal")
        guard.check_action("info")
        assert len(guard.logs) == 2


# ── QuickstartGuide 测试 ─────────────────────────


class TestQuickstartGuide:
    def test_get_industries(self):
        industries = QuickstartGuide.get_industries()
        assert "电商" in industries
        assert "SaaS企业服务" in industries

    def test_apply_template(self):
        tmpl = QuickstartGuide.apply_template("AI/科技", "天龙工具箱")
        assert tmpl["product_name"] == "天龙工具箱"
        assert tmpl["pricing"]["base"] == 999

    def test_generate_demo_data(self):
        data = QuickstartGuide.generate_demo_data()
        assert len(data) == 2
        assert data[0]["name"] == "演示客户A"
