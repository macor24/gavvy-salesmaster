"""SentriKit_salesmaster.core.api — [已弃用] SalesMaster HTTP API 服务

⚠️ 此文件已弃用，请使用 app.py（FastAPI 统一服务）。
    保留以兼容旧版调用，新代码请使用:
    
    from SentriKit_salesmaster.core.app import app, start_app
    
    CLI: SentriKit-sales-fastapi
    
纯标准库实现（零外部依赖），基于 http.server。
通过 API Key 认证对外提供销售引擎能力。

用法:
    # CLI 启动（默认 0.0.0.0:8877）
    SentriKit-sales-api

    # 环境变量配置
    export SALES_API_KEY=my-secret-key   # 自定义 API Key（默认自动生成随机 key）
    export SALES_API_PORT=8877           # 端口（可选）
    export SALES_API_HOST=0.0.0.0        # 监听地址（可选）

    # Python 直接使用
    from SentriKit_salesmaster.core.api import start_sales_api
    start_sales_api(host="0.0.0.0", port=8877)

API 端点:
    # 认证：所有 API 端点需在请求头带 X-API-Key: <your-key>
    # 无 Key 时可通过 http://localhost:8877/ 查看服务状态

    # ── SalesMaster 六维引擎 ──
    POST   /api/analyze              — 分析客户输入（SalesMaster 六维分析）
    POST   /api/generate_strategy    — 生成销售策略
    POST   /api/start_deal           — 开启新交易
    POST   /api/session_summary      — 当前会话摘要
    POST   /api/report               — 生成销售策略报告

    # ── SalesPipeline ──
    POST   /api/pipeline/run         — 运行完整销售Pipeline
    POST   /api/pipeline/lead        — 添加潜在客户
    GET    /api/pipeline/leads       — 获取潜在客户列表

    # ── SalesOrchestrator（v2.0 AI 销售团队） ──
    POST   /api/orchestrator/lead    — 向编排器添加潜在客户
    POST   /api/orchestrator/dispatch— 自动调度 Agent 处理潜在客户
    GET    /api/orchestrator/lead    — 获取潜在客户详情
    GET    /api/orchestrator/leads   — 列出所有潜在客户
    POST   /api/orchestrator/agent   — 指定 Agent 执行任务
    GET    /api/orchestrator/agents  — 列出已注册 Agent
    GET    /api/orchestrator/summary — 获取编排器统计摘要
    POST   /api/orchestrator/persist — 持久化当前状态
    POST   /api/orchestrator/restore — 恢复持久化状态

    # ── 评分与洞察引擎 (v2.5+) ──
    GET    /api/orchestrator/lead/score    — 获取单个潜在客户评分
    GET    /api/orchestrator/scores        — 获取所有潜在客户评分
    GET    /api/orchestrator/lead/insight  — 获取单个潜在客户洞察
    GET    /api/orchestrator/insights      — 获取所有潜在客户洞察

    # ── 会话记忆管理 (v2.5+) ──
    POST   /api/session/create        — 创建新会话
    POST   /api/session/message       — 添加消息到会话
    GET    /api/session               — 获取会话详情(含评分/洞察缓存)
    GET    /api/sessions              — 列出所有会话
    POST   /api/session/analyze       — 使用会话上下文执行分析
    POST   /api/session/dispatch      — 使用会话上下文调度Agent
    DELETE /api/session               — 删除会话

    GET    /health                   — 服务健康检查（无需认证）
"""

from __future__ import annotations

import json
import os
import secrets
import sys
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any, Dict, Optional


# ── 默认配置 ─────────────────────────────────────────

DEFAULT_PORT = 8877
DEFAULT_HOST = "0.0.0.0"
ENV_KEY_NAME = "SALES_API_KEY"

# 运行时持有的 SalesMaster 实例（由请求创建）
_sales_instances: Dict[str, Any] = {}
_next_instance_id = 0


# ── API Key 管理 ─────────────────────────────────────

def _get_api_key() -> str:
    """获取 API Key，优先从环境变量读取，否则自动生成。"""
    key = os.environ.get(ENV_KEY_NAME, "")
    if not key:
        # 自动生成 32 字符随机 key
        key = secrets.token_hex(16)
        os.environ[ENV_KEY_NAME] = key  # 缓存，重复调用返回同个 key
    return key


def _validate_api_key(request_key: Optional[str]) -> bool:
    """验证 API Key。"""
    if not request_key:
        return False
    expected = _get_api_key()
    # 恒定时间比较防时序攻击
    if len(request_key) != len(expected):
        return False
    result = 0
    for a, b in zip(request_key, expected):
        result |= ord(a) ^ ord(b)
    return result == 0


# ── HTTP 处理器 ──────────────────────────────────────

class _Handler(BaseHTTPRequestHandler):
    """销售 API HTTP 请求处理器。"""

    # 可被 start_sales_api 注入的配置
    api_key: str = ""
    salesmaster_cls: Any = None
    pipeline_cls: Any = None

    # ── 路由 ─────────────────────────────────────────

    def _route(self) -> Optional[Dict]:
        method = self.command
        # 去掉 query string 用于路由匹配
        raw_path = self.path.rstrip("/")
        path = raw_path.split("?")[0] if "?" in raw_path else raw_path

        # GET / — 服务信息（无需认证）
        if method == "GET" and path == "":
            return self._json_ok({
                "service": "SentriKit-sales-api",
                "version": "2.5.0",
                "status": "running",
                "auth_required": True,
                "endpoints": [
                    "GET  /health",
                    "POST /api/analyze",
                    "POST /api/generate_strategy",
                    "POST /api/start_deal",
                    "POST /api/session_summary",
                    "POST /api/report",
                    "POST /api/pipeline/run",
                    "POST /api/pipeline/lead",
                    "GET  /api/pipeline/leads",
                    # Orchestrator
                    "POST /api/orchestrator/lead",
                    "POST /api/orchestrator/dispatch",
                    "GET  /api/orchestrator/leads",
                    "POST /api/orchestrator/agent",
                    # 评分与洞察 (v2.5+)
                    "GET  /api/orchestrator/lead/score",
                    "GET  /api/orchestrator/scores",
                    "GET  /api/orchestrator/lead/insight",
                    "GET  /api/orchestrator/insights",
                    # 会话记忆 (v2.5+)
                    "POST /api/session/create",
                    "POST /api/session/message",
                    "GET  /api/session",
                    "GET  /api/sessions",
                    "POST /api/session/analyze",
                    "POST /api/session/dispatch",
                    "DELETE /api/session",
                    # 配置
                    "GET  /api/config",
                    "POST /api/config",
                ],
            })

        # GET /health（无需认证）
        if method == "GET" and path == "/health":
            return self._json_ok({
                "status": "ok",
                "service": "SentriKit-sales-api",
            })

        # ── 以下端点均需认证 ──

        if not self._authenticate():
            return None  # _authenticate 已发送 401

        # POST /api/analyze — 分析客户输入
        if method == "POST" and path == "/api/analyze":
            return self._handle_analyze()

        # POST /api/generate_strategy — 生成策略
        if method == "POST" and path == "/api/generate_strategy":
            return self._handle_generate_strategy()

        # POST /api/start_deal — 开启新交易
        if method == "POST" and path == "/api/start_deal":
            return self._handle_start_deal()

        # POST /api/session_summary — 会话摘要
        if method == "POST" and path == "/api/session_summary":
            return self._handle_session_summary()

        # POST /api/report — 销售策略报告
        if method == "POST" and path == "/api/report":
            return self._handle_report()

        # POST /api/pipeline/run — 运行完整 Pipeline
        if method == "POST" and path == "/api/pipeline/run":
            return self._handle_pipeline_run()

        # POST /api/pipeline/lead — 添加潜在客户
        if method == "POST" and path == "/api/pipeline/lead":
            return self._handle_pipeline_add_lead()

        # GET /api/pipeline/leads — 列出潜在客户
        if method == "GET" and path == "/api/pipeline/leads":
            return self._handle_pipeline_leads()

        # ── SalesOrchestrator v2.0 AI 销售团队 ──

        # POST /api/orchestrator/lead
        if method == "POST" and path == "/api/orchestrator/lead":
            return self._handle_orch_add_lead()

        # GET /api/orchestrator/lead?lead_id=xxx
        if method == "GET" and path == "/api/orchestrator/lead":
            return self._handle_orch_get_lead()

        # GET /api/orchestrator/leads
        if method == "GET" and path == "/api/orchestrator/leads":
            return self._handle_orch_list_leads()

        # POST /api/orchestrator/dispatch
        if method == "POST" and path == "/api/orchestrator/dispatch":
            return self._handle_orch_dispatch()

        # POST /api/orchestrator/agent
        if method == "POST" and path == "/api/orchestrator/agent":
            return self._handle_orch_assign_agent()

        # GET /api/orchestrator/agents
        if method == "GET" and path == "/api/orchestrator/agents":
            return self._handle_orch_agents()

        # GET /api/orchestrator/summary
        if method == "GET" and path == "/api/orchestrator/summary":
            return self._handle_orch_summary()

        # POST /api/orchestrator/persist
        if method == "POST" and path == "/api/orchestrator/persist":
            return self._handle_orch_persist()

        # POST /api/orchestrator/restore
        if method == "POST" and path == "/api/orchestrator/restore":
            return self._handle_orch_restore()

        # ── 评分与洞察引擎 (v2.5+) ──

        # GET /api/orchestrator/lead/score?lead_id=xxx
        if method == "GET" and path == "/api/orchestrator/lead/score":
            return self._handle_orch_lead_score()

        # GET /api/orchestrator/scores
        if method == "GET" and path == "/api/orchestrator/scores":
            return self._handle_orch_all_scores()

        # GET /api/orchestrator/lead/insight?lead_id=xxx
        if method == "GET" and path == "/api/orchestrator/lead/insight":
            return self._handle_orch_lead_insight()

        # GET /api/orchestrator/insights
        if method == "GET" and path == "/api/orchestrator/insights":
            return self._handle_orch_all_insights()

        # ── 会话记忆管理 (v2.5+) ──

        # POST /api/session/create
        if method == "POST" and path == "/api/session/create":
            return self._handle_session_create()

        # POST /api/session/message
        if method == "POST" and path == "/api/session/message":
            return self._handle_session_message()

        # GET /api/session?session_id=xxx
        if method == "GET" and path == "/api/session":
            return self._handle_session_get()

        # GET /api/sessions
        if method == "GET" and path == "/api/sessions":
            return self._handle_session_list()

        # POST /api/session/analyze
        if method == "POST" and path == "/api/session/analyze":
            return self._handle_session_analyze()

        # POST /api/session/dispatch
        if method == "POST" and path == "/api/session/dispatch":
            return self._handle_session_dispatch()

        # DELETE /api/session
        if method == "DELETE" and path == "/api/session":
            return self._handle_session_delete()

        # ── API 配置管理 ──

        # GET /api/config — 获取当前 API 配置（隐藏 Key）
        if method == "GET" and path == "/api/config":
            return self._handle_get_config()

        # POST /api/config — 更新 API 配置
        if method == "POST" and path == "/api/config":
            return self._handle_update_config()

        # GET /api/config/llm-status — LLM 连接状态
        if method == "GET" and path == "/api/config/llm-status":
            return self._handle_llm_status()

        return self._json_error(404, f"未找到: {method} {path}")

    # ── 认证 ─────────────────────────────────────────

    def _authenticate(self) -> bool:
        """检查请求头中的 API Key。"""
        req_key = self.headers.get("X-API-Key", "")
        if _validate_api_key(req_key):
            return True
        self.send_response(401)
        self._json_response({
            "error": "未授权: 请提供有效的 X-API-Key 请求头",
            "hint": f"设置环境变量 {ENV_KEY_NAME}=<你的 key>，或查看服务启动日志获取 key",
        })
        return False

    # ── API 处理器 ─────────────────────────────────

    def _ensure_salesmaster(self, body: Dict) -> Any:
        """获取或创建 SalesMaster 实例。"""
        global _next_instance_id

        instance_id = body.get("instance_id", "")
        if instance_id and instance_id in _sales_instances:
            return _sales_instances[instance_id], instance_id

        # 创建新实例
        company = body.get("company", "")
        industry = body.get("industry", "")
        sm = self.salesmaster_cls(company_name=company, industry=industry)

        _next_instance_id += 1
        new_id = f"sm_{_next_instance_id}"
        _sales_instances[new_id] = sm
        return sm, new_id

    def _ensure_pipeline(self, body: Dict) -> Any:
        """获取或创建 SalesPipeline 实例。"""
        project_dir = body.get("project_dir", ".")
        product_name = body.get("product_name", "SentriKit")
        product_tagline = body.get("product_tagline", "AI Agent 安全运维工具箱")
        product_description = body.get("product_description", "")

        pipeline = self.pipeline_cls(
            project_dir=project_dir,
            product_name=product_name,
            product_tagline=product_tagline,
            product_description=product_description,
        )
        return pipeline

    def _handle_analyze(self) -> Dict:
        body = self._body()
        text = body.get("text", "")
        if not text:
            return self._json_error(400, "缺少 text 字段")

        customer = body.get("customer", "客户")
        pause_sec = float(body.get("pause_sec", 0))
        sentiment = body.get("sentiment", "neutral")

        sm, instance_id = self._ensure_salesmaster(body)
        sm.start_deal(customer)
        result = sm.process_customer_input(
            text=text,
            pause_sec=pause_sec,
            sentiment=sentiment,
        )
        result["instance_id"] = instance_id
        return self._json_ok(result)

    def _handle_generate_strategy(self) -> Dict:
        body = self._body()
        sm, instance_id = self._ensure_salesmaster(body)
        strategy = sm.generate_sales_strategy_report()
        return self._json_ok({
            "instance_id": instance_id,
            "strategy_report": strategy,
        })

    def _handle_start_deal(self) -> Dict:
        body = self._body()
        customer = body.get("customer", "")
        if not customer:
            return self._json_error(400, "缺少 customer 字段")

        sm, instance_id = self._ensure_salesmaster(body)
        sm.start_deal(customer)
        return self._json_ok({
            "instance_id": instance_id,
            "message": f"交易已开启: {customer}",
            "session_summary": sm.get_session_summary(),
        })

    def _handle_session_summary(self) -> Dict:
        body = self._body()
        sm, instance_id = self._ensure_salesmaster(body)
        summary = sm.get_session_summary()
        summary["instance_id"] = instance_id
        return self._json_ok(summary)

    def _handle_report(self) -> Dict:
        body = self._body()
        sm, instance_id = self._ensure_salesmaster(body)
        report = sm.generate_sales_strategy_report()
        return self._json_ok({
            "instance_id": instance_id,
            "report": report,
        })

    def _handle_pipeline_run(self) -> Dict:
        body = self._body()
        pipeline = self._ensure_pipeline(body)
        # 支持自定义预设公司
        presets = body.get("preset_companies", None)
        if presets:
            pipeline._custom_presets = presets
        report = pipeline.run_full_cycle()
        return self._json_ok({
            "timestamp": report.timestamp,
            "leads_found": report.leads_found,
            "leads": [l.to_dict() for l in report.leads],
            "proposals_generated": report.proposals_generated,
            "proposals": report.proposals,
            "summary": report.summary,
        })

    def _handle_pipeline_add_lead(self) -> Dict:
        body = self._body()
        company = body.get("company", "")
        if not company:
            return self._json_error(400, "缺少 company 字段")

        pipeline = self._ensure_pipeline(body)
        lead = pipeline.add_lead(
            company=company,
            industry=body.get("industry", ""),
            description=body.get("description", ""),
            source=body.get("source", "api"),
        )
        return self._json_ok({
            "company": lead.company,
            "industry": lead.industry,
            "status": lead.status,
            "priority": lead.priority,
            "created_at": lead.created_at,
        })

    def _handle_pipeline_leads(self) -> Dict:
        body = self._body()
        pipeline = self._ensure_pipeline(body)
        leads = pipeline.get_active_leads()
        return self._json_ok({
            "count": len(leads),
            "leads": [l.to_dict() for l in leads],
        })

    # ── SalesOrchestrator ─────────────────────────────────

    def _ensure_orchestrator(self) -> Any:
        """获取 SalesOrchestrator 单例。"""
        orch = getattr(self.__class__, "_orchestrator_instance", None)
        if orch is None:
            cls = getattr(self.__class__, "orchestrator_cls", None)
            if cls is None:
                return None
            orch = cls()
            self.__class__._orchestrator_instance = orch
        return orch

    def _handle_orch_add_lead(self) -> Dict:
        body = self._body()
        lead_id = body.get("lead_id", "")
        if not lead_id:
            return self._json_error(400, "缺少 lead_id 字段")
        orch = self._ensure_orchestrator()
        if not orch:
            return self._json_error(503, "SalesOrchestrator 未加载")
        info = body.get("info", {})
        lead = orch.add_lead(lead_id, info)
        return self._json_ok(lead)

    def _handle_orch_get_lead(self) -> Dict:
        import urllib.parse
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        lead_ids = params.get("lead_id", [])
        if not lead_ids:
            return self._json_error(400, "缺少 lead_id 查询参数")
        orch = self._ensure_orchestrator()
        if not orch:
            return self._json_error(503, "SalesOrchestrator 未加载")
        lead = orch.get_lead(lead_ids[0])
        if lead is None:
            return self._json_error(404, f"未找到 lead: {lead_ids[0]}")
        return self._json_ok(lead)

    def _handle_orch_list_leads(self) -> Dict:
        orch = self._ensure_orchestrator()
        if not orch:
            return self._json_error(503, "SalesOrchestrator 未加载")
        return self._json_ok({
            "count": orch.lead_count,
            "leads": list(orch.leads.values()),
        })

    def _handle_orch_dispatch(self) -> Dict:
        body = self._body()
        lead_id = body.get("lead_id", "")
        if not lead_id:
            return self._json_error(400, "缺少 lead_id 字段")
        orch = self._ensure_orchestrator()
        if not orch:
            return self._json_error(503, "SalesOrchestrator 未加载")
        result = orch.auto_dispatch(lead_id)
        if result is None:
            return self._json_error(400, f"无法调度 lead: {lead_id}")
        return self._json_ok({"result": result.to_dict()})

    def _handle_orch_assign_agent(self) -> Dict:
        body = self._body()
        lead_id = body.get("lead_id", "")
        agent_name = body.get("agent_name", "")
        if not lead_id or not agent_name:
            return self._json_error(400, "缺少 lead_id 或 agent_name 字段")
        orch = self._ensure_orchestrator()
        if not orch:
            return self._json_error(503, "SalesOrchestrator 未加载")
        ctx = self._build_agent_context(body, lead_id)
        result = orch.assign_task(lead_id, agent_name, ctx)
        if result is None:
            return self._json_error(400, f"Agent '{agent_name}' 未找到或任务失败")
        return self._json_ok({"result": result.to_dict()})

    def _build_agent_context(self, body: Dict, lead_id: str) -> Any:
        """从请求体构建 AgentContext。"""
        from .team.base import AgentContext
        return AgentContext(
            product_info=body.get("product_info", ""),
            customer_id=lead_id,
            customer_name=body.get("customer_name", ""),
            conversation_history=body.get("history", []),
            extra=body.get("extra", {}),
        )

    def _handle_orch_agents(self) -> Dict:
        orch = self._ensure_orchestrator()
        if not orch:
            return self._json_error(503, "SalesOrchestrator 未加载")
        agents_info = {}
        for name, agent in orch.agents.items():
            agents_info[name] = {
                "role_en": getattr(agent, "role_en", name),
                "display_name": getattr(agent, "role_cn", name),
                "description": getattr(agent, "description", ""),
            }
        return self._json_ok({"agents": agents_info})

    def _handle_orch_summary(self) -> Dict:
        orch = self._ensure_orchestrator()
        if not orch:
            return self._json_error(503, "SalesOrchestrator 未加载")
        return self._json_ok(orch.get_summary())

    def _handle_orch_persist(self) -> Dict:
        orch = self._ensure_orchestrator()
        if not orch:
            return self._json_error(503, "SalesOrchestrator 未加载")
        orch.persist()
        return self._json_ok({"status": "ok", "message": "状态已持久化"})

    def _handle_orch_restore(self) -> Dict:
        orch = self._ensure_orchestrator()
        if not orch:
            return self._json_error(503, "SalesOrchestrator 未加载")
        orch.restore()
        return self._json_ok({"status": "ok", "message": "状态已恢复"})

    # ── 评分与洞察引擎 (v2.5+) ─────────────────────────

    def _handle_orch_lead_score(self) -> Dict:
        """获取单个潜在客户的多维度加权评分"""
        import urllib.parse
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        lead_ids = params.get("lead_id", [])
        if not lead_ids:
            return self._json_error(400, "缺少 lead_id 查询参数")
        orch = self._ensure_orchestrator()
        if not orch:
            return self._json_error(503, "SalesOrchestrator 未加载")
        score = orch.get_lead_score(lead_ids[0])
        if score is None:
            return self._json_error(404, f"未找到 lead: {lead_ids[0]}")
        return self._json_ok({"lead_id": lead_ids[0], "score": score})

    def _handle_orch_all_scores(self) -> Dict:
        """获取所有潜在客户的多维度加权评分"""
        orch = self._ensure_orchestrator()
        if not orch:
            return self._json_error(503, "SalesOrchestrator 未加载")
        scores = orch.get_all_scores()
        return self._json_ok({
            "count": len(scores),
            "scores": scores,
        })

    def _handle_orch_lead_insight(self) -> Dict:
        """获取单个潜在客户的可执行洞察"""
        import urllib.parse
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        lead_ids = params.get("lead_id", [])
        if not lead_ids:
            return self._json_error(400, "缺少 lead_id 查询参数")
        orch = self._ensure_orchestrator()
        if not orch:
            return self._json_error(503, "SalesOrchestrator 未加载")
        insight = orch.get_lead_insights(lead_ids[0])
        if insight is None:
            return self._json_error(404, f"未找到 lead: {lead_ids[0]}")
        return self._json_ok({"lead_id": lead_ids[0], "insight": insight})

    def _handle_orch_all_insights(self) -> Dict:
        """获取所有潜在客户的可执行洞察"""
        orch = self._ensure_orchestrator()
        if not orch:
            return self._json_error(503, "SalesOrchestrator 未加载")
        insights = orch.get_all_insights()
        return self._json_ok({
            "count": len(insights),
            "insights": insights,
        })

    # ── 会话记忆管理 (v2.5+) ─────────────────────────

    def _get_session_memory(self):
        """延迟获取会话记忆实例"""
        from .team.session import get_session_memory
        return get_session_memory()

    def _handle_session_create(self) -> Dict:
        """创建新会话"""
        body = self._body()
        session_id = body.get("session_id", "")
        if not session_id:
            import uuid
            session_id = f"session-{uuid.uuid4().hex[:8]}"
        lead_id = body.get("lead_id", "")
        lead_name = body.get("lead_name", "")
        product_info = body.get("product_info", "")

        mem = self._get_session_memory()
        session = mem.create_session(
            session_id=session_id,
            lead_id=lead_id,
            lead_name=lead_name,
            product_info=product_info,
        )
        return self._json_ok({
            "session_id": session.session_id,
            "created_at": session.created_at,
            "message": f"会话已创建: {session_id}",
        })

    def _handle_session_message(self) -> Dict:
        """添加消息到会话"""
        body = self._body()
        session_id = body.get("session_id", "")
        if not session_id:
            return self._json_error(400, "缺少 session_id 字段")
        role = body.get("role", "user")
        content = body.get("content", "")
        if not content:
            return self._json_error(400, "缺少 content 字段")
        agent_name = body.get("agent_name", "")

        mem = self._get_session_memory()
        session = mem.get_session(session_id)
        if session is None:
            return self._json_error(404, f"会话未找到: {session_id}")

        mem.add_message(session_id, role, content, agent_name)
        return self._json_ok({
            "session_id": session_id,
            "message_count": len(session.messages),
            "role": role,
            "timestamp": session.updated_at,
        })

    def _handle_session_get(self) -> Dict:
        """获取会话详情（含评分/洞察缓存）"""
        import urllib.parse
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        ids = params.get("session_id", [])
        if not ids:
            return self._json_error(400, "缺少 session_id 查询参数")

        mem = self._get_session_memory()
        session = mem.get_session(ids[0])
        if session is None:
            return self._json_error(404, f"会话未找到: {ids[0]}")
        return self._json_ok(session.to_full_dict())

    def _handle_session_list(self) -> Dict:
        """列出所有会话"""
        mem = self._get_session_memory()
        sessions = mem.list_sessions()
        return self._json_ok({
            "count": len(sessions),
            "sessions": sessions,
        })

    def _handle_session_analyze(self) -> Dict:
        """使用会话上下文执行 SalesMaster 分析"""
        body = self._body()
        session_id = body.get("session_id", "")
        if not session_id:
            return self._json_error(400, "缺少 session_id 字段")
        text = body.get("text", "")
        if not text:
            return self._json_error(400, "缺少 text 字段")

        mem = self._get_session_memory()
        session = mem.get_session(session_id)
        if session is None:
            return self._json_error(404, f"会话未找到: {session_id}")

        # 使用会话上下文信息增强分析
        mem.add_message(session_id, "user", text, metadata={"action": "analyze"})

        # 执行分析
        from .master import SalesMaster
        sm = SalesMaster(
            company_name=session.lead_name or body.get("company", ""),
            industry=body.get("industry", ""),
        )
        if session.lead_id:
            sm.start_deal(session.lead_name or session.lead_id)

        result = sm.process_customer_input(
            text=text,
            pause_sec=float(body.get("pause_sec", 0)),
            sentiment=body.get("sentiment", "neutral"),
        )

        # 缓存结果到会话
        result["session_id"] = session_id
        mem.add_message(session_id, "agent", str(result.get("recommended_response", "")),
                        agent_name="salesmaster", metadata={"analysis": True})

        return self._json_ok(result)

    def _handle_session_dispatch(self) -> Dict:
        """使用会话上下文调度 Agent"""
        body = self._body()
        session_id = body.get("session_id", "")
        if not session_id:
            return self._json_error(400, "缺少 session_id 字段")
        lead_id = body.get("lead_id", "")
        if not lead_id:
            return self._json_error(400, "缺少 lead_id 字段")

        mem = self._get_session_memory()
        session = mem.get_session(session_id)
        if session is None:
            return self._json_error(404, f"会话未找到: {session_id}")

        orch = self._ensure_orchestrator()
        if not orch:
            return self._json_error(503, "SalesOrchestrator 未加载")

        # 检查lead是否存在，不存在则自动创建
        lead = orch.get_lead(lead_id)
        if lead is None:
            info = {
                "name": session.lead_name or body.get("customer_name", lead_id),
                "product": session.product_info or body.get("product_info", ""),
            }
            lead = orch.add_lead(lead_id, info)

        mem.add_message(session_id, "system",
                        f"调度Agent处理 {lead_id}",
                        metadata={"action": "dispatch"})

        result = orch.auto_dispatch(lead_id)
        if result is None:
            return self._json_error(400, f"无法调度 lead: {lead_id}")

        # 将Agent结果写入会话记忆
        mem.add_agent_result(session_id, {
            "agent": result.agent_name,
            "summary": result.summary,
            "action": result.action,
            "status": result.status,
            "timestamp": result.timestamp,
        })

        # 自动评分 + 洞察
        score = orch.get_lead_score(lead_id)
        if score:
            mem.set_score(session_id, score)
        insight = orch.get_lead_insights(lead_id)
        if insight:
            mem.set_insight(session_id, insight)

        return self._json_ok({
            "session_id": session_id,
            "result": result.to_dict(),
            "has_score": score is not None,
            "has_insight": insight is not None,
        })

    def _handle_session_delete(self) -> Dict:
        """删除会话"""
        body = self._body()
        session_id = body.get("session_id", "")
        if not session_id:
            return self._json_error(400, "缺少 session_id 字段")
        mem = self._get_session_memory()
        if mem.delete_session(session_id):
            return self._json_ok({"message": f"会话已删除: {session_id}"})
        return self._json_error(404, f"会话未找到: {session_id}")

    # ── API 配置管理 ───────────────────────────────────

    def _handle_get_config(self) -> Dict:
        """获取当前 API 配置（隐藏敏感信息）"""
        try:
            from .team.api_config import APIConfigManager
            mgr = APIConfigManager()
            return self._json_ok(mgr.to_dict())
        except ImportError:
            return self._json_ok({"error": "api_config 模块未加载"})

    def _handle_update_config(self) -> Dict:
        """更新 LLM API 配置"""
        body = self._body()
        llm_cfg = body.get("llm", {})
        if not llm_cfg:
            return self._json_error(400, "缺少 llm 配置字段")

        try:
            from .team.api_config import update_llm_config
            update_llm_config(**llm_cfg)
            return self._json_ok({
                "status": "ok",
                "message": "LLM 配置已更新",
            })
        except ImportError:
            return self._json_error(503, "api_config 模块未加载")

    def _handle_llm_status(self) -> Dict:
        """检查 LLM 连接状态"""
        try:
            from .team.api_config import is_llm_ready, get_api_config
            ready = is_llm_ready()
            cfg = get_api_config()
            return self._json_ok({
                "configured": ready,
                "provider": cfg.llm.base_url if ready else None,
                "model": cfg.llm.model if ready else None,
            })
        except ImportError:
            return self._json_ok({"configured": False, "error": "api_config 未加载"})

    # ── HTTP 基础 ──────────────────────────────────

    def _body(self) -> Dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {"_raw": raw.decode("utf-8", errors="replace")}

    def _json_ok(self, data: Any, status: int = 200) -> Dict:
        self.send_response(status)
        return self._json_response(data)

    def _json_error(self, status: int, message: str) -> Dict:
        self.send_response(status)
        return self._json_response({"error": message})

    def _json_response(self, data: Any) -> Dict:
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
        return data

    # ── HTTP 方法入口 ──────────────────────────────

    def do_GET(self):
        try:
            self._route()
        except Exception as e:
            self._json_error(500, f"内部错误: {e}")
            traceback.print_exc()

    def do_POST(self):
        try:
            self._route()
        except Exception as e:
            self._json_error(500, f"内部错误: {e}")
            traceback.print_exc()

    def do_OPTIONS(self):
        """CORS preflight"""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key")
        self.end_headers()

    def do_DELETE(self):
        try:
            self._route()
        except Exception as e:
            self._json_error(500, f"内部错误: {e}")
            traceback.print_exc()

    def log_message(self, format, *args):
        sys.stderr.write(f"[SalesAPI] {self.command} {self.path} - {args[0]}\n")


# ── 启动函数 ─────────────────────────────────────────

def start_sales_api(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> HTTPServer:
    """启动销售 API HTTP 服务器。

    Args:
        host: 监听地址
        port: 监听端口

    Returns:
        HTTPServer 实例（可调用 server.shutdown() 关闭）
    """
    # 延迟导入，避免模块级依赖
    from .master import SalesMaster
    from . import SalesPipeline

    _Handler.salesmaster_cls = SalesMaster
    _Handler.pipeline_cls = SalesPipeline

    # 尝试导入 SalesOrchestrator（可选，v2.0 新功能）
    try:
        from .team.coordinator import SalesOrchestrator
        _Handler.orchestrator_cls = SalesOrchestrator
        _Handler._orchestrator_instance = SalesOrchestrator()
        has_orch = True
    except ImportError:
        _Handler.orchestrator_cls = None
        _Handler._orchestrator_instance = None
        has_orch = False

    api_key = _get_api_key()
    server = HTTPServer((host, port), _Handler)

    print(f"🚀 SalesMaster API 服务启动: http://{host}:{port}")
    print(f"   API Key: {api_key}")
    print(f"   认证方式: 请求头 X-API-Key: {api_key}")
    print(f"")
    print(f"   端点列表:")
    print(f"     GET  /health                   — 健康检查（无需认证）")
    print(f"     POST /api/analyze              — 分析客户输入")
    print(f"     POST /api/generate_strategy    — 生成销售策略")
    print(f"     POST /api/start_deal           — 开启新交易")
    print(f"     POST /api/session_summary      — 会话摘要")
    print(f"     POST /api/report               — 销售策略报告")
    print(f"     POST /api/pipeline/run         — 运行销售Pipeline")
    print(f"     POST /api/pipeline/lead        — 添加潜在客户")
    print(f"     GET  /api/pipeline/leads       — 潜在客户列表")
    if has_orch:
        print(f"")
        print(f"   SalesOrchestrator (v2.0 AI 销售团队):")
        print(f"     POST /api/orchestrator/lead    - 添加潜在客户")
        print(f"     GET  /api/orchestrator/lead    - 获取潜在客户详情")
        print(f"     GET  /api/orchestrator/leads   - 列出所有潜在客户")
        print(f"     POST /api/orchestrator/dispatch- 自动调度 Agent 处理")
        print(f"     POST /api/orchestrator/agent   - 指定 Agent 执行任务")
        print(f"     GET  /api/orchestrator/agents  - 列出已注册 Agent")
        print(f"     GET  /api/orchestrator/summary - 编排器统计摘要")
        print(f"     POST /api/orchestrator/persist - 持久化状态")
        print(f"     POST /api/orchestrator/restore - 恢复状态")
        print(f"")
        print(f"   🎯 评分与洞察引擎 (v2.5+):")
        print(f"     GET  /api/orchestrator/lead/score   - 潜在客户评分")
        print(f"     GET  /api/orchestrator/scores       - 所有客户评分")
        print(f"     GET  /api/orchestrator/lead/insight - 潜在客户洞察")
        print(f"     GET  /api/orchestrator/insights     - 所有客户洞察")
        print(f"")
        print(f"   💬 会话记忆管理 (v2.5+):")
        print(f"     POST /api/session/create       - 创建会话")
        print(f"     POST /api/session/message      - 添加消息")
        print(f"     GET  /api/session              - 获取会话详情")
        print(f"     GET  /api/sessions             - 列出会话")
        print(f"     POST /api/session/analyze      - 会话上下文分析")
        print(f"     POST /api/session/dispatch     - 会话上下文调度")
        print(f"     DELETE /api/session            - 删除会话")
        print(f"")
        print(f"   配置管理:")
        print(f"     GET  /api/config            - 查看API配置状态")
        print(f"     POST /api/config            - 更新LLM配置")
        print(f"     GET  /api/config/llm-status - LLM连接状态检查")
        print(f"")
        orch = _Handler._orchestrator_instance
        if orch and orch.agents:
            print(f"   🤖 已加载 {len(orch.agents)} 个销售Agent:")
            for name, agent in orch.agents.items():
                cn = getattr(agent, "role_cn", name)
                print(f"      - {cn} ({name})")
    print(f"")
    print(f"   示例:")
    print(f'     curl -X POST http://{host}:{port}/api/analyze \\')
    print(f'       -H "Content-Type: application/json" \\')
    print(f'       -H "X-API-Key: {api_key}" \\')
    print(f'       -d \'{{"text":"我们正在寻找AI安全方案","customer":"某科技公司"}}\'')
    print(f"   按 Ctrl+C 停止")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务停止")
        server.server_close()
    return server


# ── CLI 入口 ─────────────────────────────────────────

def main(argv: Optional[list[str]] = None) -> int:
    """CLI 入口: SentriKit-sales-api"""
    import argparse

    parser = argparse.ArgumentParser(
        prog="SentriKit-sales-api",
        description="Gavvy 销售引擎 — SalesMaster HTTP API 服务",
    )
    parser.add_argument("--host", type=str, default=None,
                        help=f"监听地址 (默认: {DEFAULT_HOST}，也可通过 SALES_API_HOST 环境变量设置)")
    parser.add_argument("--port", "-p", type=int, default=None,
                        help=f"监听端口 (默认: {DEFAULT_PORT}，也可通过 SALES_API_PORT 环境变量设置)")

    args = parser.parse_args(argv)

    host = args.host or os.environ.get("SALES_API_HOST", DEFAULT_HOST)
    port = args.port or int(os.environ.get("SALES_API_PORT", str(DEFAULT_PORT)))

    start_sales_api(host=host, port=port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
