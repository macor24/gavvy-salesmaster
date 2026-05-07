"""gavvy_salesmaster.core.app — FastAPI 统一 API + Web 服务

合并 API（8877端口）和 Web 管理后台（8878端口）
为一个 FastAPI 应用，统一监听 8877 端口。

依赖: pip install fastapi uvicorn
用法: gavvy-sales-fastapi
"""

from __future__ import annotations

import json
import os
import secrets
import sys
import uuid
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import defaultdict

try:
    from dotenv import load_dotenv
    load_dotenv()  # 自动加载 .env 文件
except ImportError:
    pass

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# ── SaaS 多租户 ─────────────────────────────────────
try:
    from gavvy_salesmaster.crm_pkg.saas.middleware import SaaSAuthMiddleware, TenantDataMiddleware
    from gavvy_salesmaster.crm_pkg.saas.routes import router as saas_router
    _HAS_SAAS = True
except ImportError:
    _HAS_SAAS = False

# ── 路径 ────────────────────────────────────────────

_HERE = Path(__file__).parent
_WEB_DIR = _HERE / "web"

# ── API Key 管理 ─────────────────────────────────────

ENV_KEY_NAME = "SALES_API_KEY"
DEFAULT_PORT = 8877
DEFAULT_HOST = "0.0.0.0"

def _get_api_key() -> str:
    key = os.environ.get(ENV_KEY_NAME, "")
    if not key:
        key = secrets.token_hex(16)
        os.environ[ENV_KEY_NAME] = key
    return key


# ── FastAPI 应用 ────────────────────────────────────

app = FastAPI(
    title="Chat Sales API",
    description="开源销售引擎 — gavvy 六维能力 + 7-Agent 销售团队 + Pipeline 4步流程",
    version="2.6.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── 认证路由（必须放在 API Key 中间件之前） ──────
from .routers.auth import router as auth_router
app.include_router(auth_router)

# ── 注册路由模块（逐步从 app.py 拆分） ──────────
from .routers.crm import router as crm_router
from .routers.rbac import router as rbac_router
from .routers.knowledge import router as knowledge_router
from .routers.scripts import router as scripts_router
from .routers.channels import router as channels_router
from .routers.payment import router as payment_router
app.include_router(crm_router)
app.include_router(rbac_router)
app.include_router(knowledge_router)
app.include_router(scripts_router)
app.include_router(channels_router)
app.include_router(payment_router)

# ── 进化闭环路由 ────────────────────────────


@app.post("/api/evolve/run")
async def api_evolve_run():
    """触发 SentriKit 完整进化闭环"""
    from .master import SentriKit_run_evolve
    return SentriKit_run_evolve()


@app.get("/api/evolve/status")
async def api_evolve_status():
    """SentriKit 进化状态"""
    from .master import SentriKit_evolve_status
    return SentriKit_evolve_status()


@app.post("/api/evolve/metacog")
async def api_evolve_metacog(body: dict):
    """退化检测"""
    from .master import SentriKit_evaluate_metacog
    return SentriKit_evaluate_metacog(
        success_rate_7d=body.get("success_rate_7d", 0.85),
        days_since_last_improvement=body.get("days_since_last_improvement", 0),
        repeat_error_count=body.get("repeat_error_count", 0),
    )


@app.post("/api/evolve/judge")
async def api_evolve_judge(body: dict):
    """提案评分"""
    from .master import SentriKit_evaluate_judge
    return SentriKit_evaluate_judge(summary=body.get("summary", ""))


@app.post("/api/evolve/auto-check")
async def api_evolve_auto_check():
    """自动检查+触发进化"""
    from .master import SentriKit_auto_check
    return SentriKit_auto_check()

# CORS 配置 - 生产环境建议限制来源
_CORS_ORIGINS = os.environ.get("SALES_CORS_ORIGINS", "").split(",")
_CORS_ORIGINS = [origin.strip() for origin in _CORS_ORIGINS if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS if _CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 全局 API 限流中间件 ─────────────────────────

_RATE_LIMIT = int(os.environ.get("SALES_RATE_LIMIT", "100"))  # 默认每分钟100次
_RATE_WINDOW = 60  # 窗口大小（秒）
_request_counts: Dict[str, List[float]] = defaultdict(list)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """简单的内存限流中间件
    配置环境变量: SALES_RATE_LIMIT=100
    """
    if _RATE_LIMIT <= 0:
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    # 清理过期请求记录
    _request_counts[client_ip] = [
        t for t in _request_counts[client_ip]
        if t > now - _RATE_WINDOW
    ]

    # 检查是否超限
    if len(_request_counts[client_ip]) >= _RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"status": "error", "message": "Too Many Requests"}
        )

    # 记录本次请求
    _request_counts[client_ip].append(now)

    return await call_next(request)


# ── 安全响应头中间件 ─────────────────────────

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """添加安全响应头"""
    response = await call_next(request)

    # X-Frame-Options - 防止点击劫持
    response.headers["X-Frame-Options"] = "SAMEORIGIN"

    # X-Content-Type-Options - 防止 MIME 类型嗅探
    response.headers["X-Content-Type-Options"] = "nosniff"

    # X-XSS-Protection - XSS 防护
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Referrer-Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # HSTS - 仅在 HTTPS 下启用
    # 生产环境建议配置
    # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


# ── SaaS 多租户中间件 ─────────────────────────

if _HAS_SAAS:
    # 可选：启用SaaS认证模式（设置SALES_USE_SAAS=true）
    _USE_SAAS = os.environ.get("SALES_USE_SAAS", "false").lower() == "true"
    if _USE_SAAS:
        app.add_middleware(TenantDataMiddleware)
        app.include_router(saas_router)
        _API_KEY_MANAGEMENT = _get_api_key()


# ── API Key 认证中间件 ─────────────────────────

_API_KEY = _get_api_key()
_SKIP_AUTH = os.environ.get("SALES_SKIP_AUTH", "false").lower() == "true"
_PUBLIC_PATHS = {
    "/api/health",
    "/api/health/detailed",
    "/health",
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/landing",
    "/demo",
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/logout",
    "/api/auth/session/",
    "/api/auth/me",
}


@app.middleware("http")
async def api_key_auth(request: Request, call_next):
    """API Key 认证中间件"""
    path = request.url.path

    # 如果设置了跳过认证，直接放行
    if _SKIP_AUTH:
        return await call_next(request)

    # 公开路径放行
    if path in _PUBLIC_PATHS:
        return await call_next(request)

    # 静态文件放行（HTML 前端页面）
    if any(path.endswith(ext) for ext in (".css", ".js", ".html",
                                           ".json", ".png", ".jpg",
                                           ".svg", ".ico", ".woff2")):
        return await call_next(request)

    # API 文档页面放行
    if path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi.json"):
        return await call_next(request)

    # 检查 API Key
    api_key = request.headers.get("X-API-Key", "")
    # 同时从 Cookie 读取（前端页面已通过保密验证）
    if not api_key:
        api_key = request.cookies.get("api_key", "")

    if api_key != _API_KEY:
        # 如果是前端页面请求（Accept: text/html），放行
        accept = request.headers.get("accept", "")
        if "text/html" in accept and path == "/":
            return await call_next(request)

        return JSONResponse(
            status_code=401,
            content={"error": "Unauthorized", "message": "请提供有效的 API Key (请求头 X-API-Key)"},
        )

    return await call_next(request)


# ── 延迟初始化的全局实例 ──────────────────────────

_orchestrator_instance: Any = None
_salesmaster_cls: Any = None
_pipeline_cls: Any = None


def _get_orch():
    global _orchestrator_instance
    if _orchestrator_instance is None:
        from gavvy_salesmaster.team_pkg.team.coordinator import SalesOrchestrator
        _orchestrator_instance = SalesOrchestrator()
    return _orchestrator_instance


def _get_session_memory():
    from .team.session import get_session_memory
    return get_session_memory()


# ── API Key 认证依赖 ───────────────────────────────

def _check_api_key(request: Request):
    """验证 X-API-Key 请求头。public 路由不检查。"""
    path = request.url.path
    # 公开端点（无需认证）
    public_paths = {
        "/health", "/", "/docs", "/redoc", "/openapi.json",
        "/api/leads/from_widget",  # 外部网页嵌入，无 API Key
    }
    if path in public_paths or path.startswith("/api/pipeline/") or path.startswith("/api/customers") or path.startswith("/api/analytics/"):
        return True
    # 静态文件公开
    if path.startswith("/static/"):
        return True

    req_key = request.headers.get("X-API-Key", "")
    expected = _get_api_key()
    if not req_key or len(req_key) != len(expected):
        raise HTTPException(status_code=401, detail={
            "error": "未授权: 请提供有效的 X-API-Key 请求头",
            "hint": f"设置环境变量 {ENV_KEY_NAME}=<你的 key>",
        })
    result = 0
    for a, b in zip(req_key, expected):
        result |= ord(a) ^ ord(b)
    if result != 0:
        raise HTTPException(status_code=401, detail="API Key 无效")
    return True


# ── 静态文件服务 ───────────────────────────────────

# 挂载 /static/ 路径到 web 目录的静态文件
_static_path = str(_WEB_DIR.absolute())
app.mount("/static", StaticFiles(directory=_static_path), name="static")


@app.get("/")
async def root():
    """Web 管理后台首页"""
    index_file = _WEB_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({
        "service": "gavvy-sales-fastapi",
        "version": "2.6.0",
        "docs": "/docs",
    })


@app.get("/landing")
async def landing_page():
    """SaaS 演示落地页"""
    landing_file = _WEB_DIR / "landing.html"
    if landing_file.exists():
        return FileResponse(str(landing_file))
    return JSONResponse({
        "status": "redirect",
        "message": "落地页未找到",
        "admin": "/"
    })


@app.get("/demo")
async def demo_page():
    """SaaS 演示入口 - 跳转到落地页"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/landing")


# ── 健康检查 ──────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "gavvy-sales-fastapi"}


# ── gavvy 六维引擎 ──────────────────────────

_instances: Dict[str, Any] = {}
_next_id = 0


def _ensure_sm(body: dict) -> tuple:
    global _next_id
    instance_id = body.get("instance_id", "")
    if instance_id and instance_id in _instances:
        return _instances[instance_id], instance_id
    from .master import SalesMaster
    company = body.get("company", "")
    industry = body.get("industry", "")
    sm = SalesMaster(company_name=company, industry=industry)
    _next_id += 1
    new_id = f"sm_{_next_id}"
    _instances[new_id] = sm
    return sm, new_id


def _ensure_pipeline(body: dict):
    from . import SalesPipeline
    return SalesPipeline(
        project_dir=body.get("project_dir", "."),
        product_name=body.get("product_name", "SentriKit"),
        product_tagline=body.get("product_tagline", "AI Agent 安全运维工具箱"),
        product_description=body.get("product_description", ""),
    )


@app.post("/api/analyze")
async def api_analyze(body: dict):
    text = body.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="缺少 text 字段")
    customer = body.get("customer", "客户")
    pause_sec = float(body.get("pause_sec", 0))
    sentiment = body.get("sentiment", "neutral")
    sm, instance_id = _ensure_sm(body)
    sm.start_deal(customer)
    result = sm.process_customer_input(text=text, pause_sec=pause_sec, sentiment=sentiment)
    result["instance_id"] = instance_id
    return result


@app.post("/api/generate_strategy")
async def api_generate_strategy(body: dict):
    sm, instance_id = _ensure_sm(body)
    strategy = sm.generate_sales_strategy_report()
    return {"instance_id": instance_id, "strategy_report": strategy}


@app.post("/api/start_deal")
async def api_start_deal(body: dict):
    customer = body.get("customer", "")
    if not customer:
        raise HTTPException(status_code=400, detail="缺少 customer 字段")
    sm, instance_id = _ensure_sm(body)
    sm.start_deal(customer)
    return {"instance_id": instance_id, "message": f"交易已开启: {customer}", "session_summary": sm.get_session_summary()}


@app.post("/api/session_summary")
async def api_session_summary(body: dict):
    sm, instance_id = _ensure_sm(body)
    summary = sm.get_session_summary()
    summary["instance_id"] = instance_id
    return summary


@app.post("/api/report")
async def api_report(body: dict):
    sm, instance_id = _ensure_sm(body)
    report = sm.generate_sales_strategy_report()
    return {"instance_id": instance_id, "report": report}


@app.post("/api/pipeline/run")
async def api_pipeline_run(body: dict):
    pipeline = _ensure_pipeline(body)
    presets = body.get("preset_companies")
    if presets:
        pipeline._custom_presets = presets
    report = pipeline.run_full_cycle()
    return {
        "timestamp": report.timestamp, "leads_found": report.leads_found,
        "leads": [l.to_dict() for l in report.leads],
        "proposals_generated": report.proposals_generated,
        "proposals": report.proposals, "summary": report.summary,
    }


@app.post("/api/pipeline/lead")
async def api_pipeline_lead(body: dict):
    company = body.get("company", "")
    if not company:
        raise HTTPException(status_code=400, detail="缺少 company 字段")
    pipeline = _ensure_pipeline(body)
    lead = pipeline.add_lead(company=company, industry=body.get("industry", ""),
                              description=body.get("description", ""), source=body.get("source", "api"))
    return {"company": lead.company, "industry": lead.industry, "status": lead.status,
            "priority": lead.priority, "created_at": lead.created_at}


@app.get("/api/pipeline/leads")
async def api_pipeline_leads(request: Request, body: dict = {}):
    pipeline = _ensure_pipeline(body)
    leads = pipeline.get_active_leads()
    return {"count": len(leads), "leads": [l.to_dict() for l in leads]}


# ── SalesOrchestrator v2.0 AI 销售团队 ──────────

@app.post("/api/orchestrator/lead")
async def api_orch_add_lead(body: dict):
    lead_id = body.get("lead_id", "")
    if not lead_id:
        raise HTTPException(status_code=400, detail="缺少 lead_id 字段")
    orch = _get_orch()
    info = body.get("info", {})
    lead = orch.add_lead(lead_id, info)
    return lead


@app.get("/api/orchestrator/lead")
async def api_orch_get_lead(lead_id: str = ""):
    if not lead_id:
        raise HTTPException(status_code=400, detail="缺少 lead_id 查询参数")
    orch = _get_orch()
    lead = orch.get_lead(lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail=f"未找到 lead: {lead_id}")
    return lead


@app.get("/api/orchestrator/leads")
async def api_orch_list_leads():
    orch = _get_orch()
    return {"count": orch.lead_count, "leads": list(orch.leads.values())}


@app.post("/api/orchestrator/dispatch")
async def api_orch_dispatch(body: dict):
    lead_id = body.get("lead_id", "")
    if not lead_id:
        raise HTTPException(status_code=400, detail="缺少 lead_id 字段")
    orch = _get_orch()
    result = orch.auto_dispatch(lead_id)
    if result is None:
        raise HTTPException(status_code=400, detail=f"无法调度 lead: {lead_id}")
    return {"result": result.to_dict()}


@app.post("/api/orchestrator/agent")
async def api_orch_assign_agent(body: dict):
    lead_id = body.get("lead_id", "")
    agent_name = body.get("agent_name", "")
    if not lead_id or not agent_name:
        raise HTTPException(status_code=400, detail="缺少 lead_id 或 agent_name 字段")
    orch = _get_orch()
    from .team.base import AgentContext
    ctx = AgentContext(
        product_info=body.get("product_info", ""),
        customer_id=lead_id,
        customer_name=body.get("customer_name", ""),
        conversation_history=body.get("history", []),
        extra=body.get("extra", {}),
    )
    result = orch.assign_task(lead_id, agent_name, ctx)
    if result is None:
        raise HTTPException(status_code=400, detail=f"Agent '{agent_name}' 未找到或任务失败")
    return {"result": result.to_dict()}


@app.get("/api/orchestrator/agents")
async def api_orch_agents():
    orch = _get_orch()
    agents_info = {}
    for name, agent in orch.agents.items():
        agents_info[name] = {
            "role_en": getattr(agent, "role_en", name),
            "display_name": getattr(agent, "role_cn", name),
            "description": getattr(agent, "description", ""),
        }
    return {"agents": agents_info}


@app.get("/api/orchestrator/agent/enabled")
async def api_orch_agent_enabled():
    """获取所有 Agent 的启用状态"""
    orch = _get_orch()
    states = {}
    for name, agent in orch.agents.items():
        states[name] = {
            "enabled": agent.enabled,
            "role_cn": getattr(agent, "role_cn", name),
        }
    return {"agents": states}


@app.post("/api/orchestrator/agent/toggle")
async def api_orch_agent_toggle(body: dict):
    """切换指定 Agent 的启用/禁用状态"""
    agent_name = body.get("agent_name", "")
    if not agent_name:
        raise HTTPException(status_code=400, detail="缺少 agent_name 字段")
    action = body.get("action", "toggle")
    orch = _get_orch()
    if action == "enable":
        ok = orch.enable_agent(agent_name)
    elif action == "disable":
        ok = orch.disable_agent(agent_name)
    else:
        result = orch.toggle_agent(agent_name)
        if result is None:
            ok = False
        else:
            return {"agent_name": agent_name, "enabled": result}
        ok = result is not None
    if not ok:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' 未找到")
    agent = orch.get_agent(agent_name)
    return {"agent_name": agent_name, "enabled": agent.enabled}


@app.get("/api/orchestrator/summary")
async def api_orch_summary():
    orch = _get_orch()
    return orch.get_summary()


@app.post("/api/orchestrator/persist")
async def api_orch_persist():
    orch = _get_orch()
    orch.persist()
    return {"status": "ok", "message": "状态已持久化"}


@app.post("/api/orchestrator/restore")
async def api_orch_restore():
    orch = _get_orch()
    orch.restore()
    return {"status": "ok", "message": "状态已恢复"}


# ── 评分与洞察引擎 (v2.5+) ─────────────────────

@app.get("/api/orchestrator/lead/score")
async def api_orch_lead_score(lead_id: str = ""):
    if not lead_id:
        raise HTTPException(status_code=400, detail="缺少 lead_id 查询参数")
    orch = _get_orch()
    score = orch.get_lead_score(lead_id)
    if score is None:
        raise HTTPException(status_code=404, detail=f"未找到 lead: {lead_id}")
    return {"lead_id": lead_id, "score": score}


@app.get("/api/orchestrator/scores")
async def api_orch_all_scores():
    orch = _get_orch()
    scores = orch.get_all_scores()
    return {"count": len(scores), "scores": scores}


@app.get("/api/orchestrator/lead/insight")
async def api_orch_lead_insight(lead_id: str = ""):
    if not lead_id:
        raise HTTPException(status_code=400, detail="缺少 lead_id 查询参数")
    orch = _get_orch()
    insight = orch.get_lead_insights(lead_id)
    if insight is None:
        raise HTTPException(status_code=404, detail=f"未找到 lead: {lead_id}")
    return {"lead_id": lead_id, "insight": insight}


@app.get("/api/orchestrator/insights")
async def api_orch_all_insights():
    orch = _get_orch()
    insights = orch.get_all_insights()
    return {"count": len(insights), "insights": insights}


# ── 会话记忆管理 (v2.5+) ─────────────────────────

@app.post("/api/session/create")
async def api_session_create(body: dict):
    session_id = body.get("session_id", "")
    if not session_id:
        session_id = f"session-{uuid.uuid4().hex[:8]}"
    lead_id = body.get("lead_id", "")
    lead_name = body.get("lead_name", "")
    product_info = body.get("product_info", "")
    mem = _get_session_memory()
    session = mem.create_session(session_id=session_id, lead_id=lead_id,
                                 lead_name=lead_name, product_info=product_info)
    return {"session_id": session.session_id, "created_at": session.created_at,
            "message": f"会话已创建: {session_id}"}


@app.post("/api/session/message")
async def api_session_message(body: dict):
    session_id = body.get("session_id", "")
    if not session_id:
        raise HTTPException(status_code=400, detail="缺少 session_id 字段")
    role = body.get("role", "user")
    content = body.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="缺少 content 字段")
    agent_name = body.get("agent_name", "")
    mem = _get_session_memory()
    session = mem.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"会话未找到: {session_id}")
    mem.add_message(session_id, role, content, agent_name)
    return {"session_id": session_id, "message_count": len(session.messages),
            "role": role, "timestamp": session.updated_at}


@app.get("/api/session")
async def api_session_get(session_id: str = ""):
    if not session_id:
        raise HTTPException(status_code=400, detail="缺少 session_id 查询参数")
    mem = _get_session_memory()
    session = mem.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"会话未找到: {session_id}")
    return session.to_full_dict()


@app.get("/api/sessions")
async def api_session_list():
    mem = _get_session_memory()
    sessions = mem.list_sessions()
    return {"count": len(sessions), "sessions": sessions}


@app.post("/api/session/analyze")
async def api_session_analyze(body: dict):
    session_id = body.get("session_id", "")
    if not session_id:
        raise HTTPException(status_code=400, detail="缺少 session_id 字段")
    text = body.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="缺少 text 字段")
    mem = _get_session_memory()
    session = mem.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"会话未找到: {session_id}")
    mem.add_message(session_id, "user", text, metadata={"action": "analyze"})
    from .master import SalesMaster
    sm = SalesMaster(company_name=session.lead_name or body.get("company", ""),
                     industry=body.get("industry", ""))
    if session.lead_id:
        sm.start_deal(session.lead_name or session.lead_id)
    result = sm.process_customer_input(text=text,
        pause_sec=float(body.get("pause_sec", 0)),
        sentiment=body.get("sentiment", "neutral"))
    result["session_id"] = session_id
    mem.add_message(session_id, "agent", str(result.get("recommended_response", "")),
                    agent_name="salesmaster", metadata={"analysis": True})
    return result


@app.post("/api/session/dispatch")
async def api_session_dispatch(body: dict):
    session_id = body.get("session_id", "")
    if not session_id:
        raise HTTPException(status_code=400, detail="缺少 session_id 字段")
    lead_id = body.get("lead_id", "")
    if not lead_id:
        raise HTTPException(status_code=400, detail="缺少 lead_id 字段")
    mem = _get_session_memory()
    session = mem.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"会话未找到: {session_id}")
    orch = _get_orch()
    lead = orch.get_lead(lead_id)
    if lead is None:
        info = {"name": session.lead_name or body.get("customer_name", lead_id),
                "product": session.product_info or body.get("product_info", "")}
        lead = orch.add_lead(lead_id, info)
    mem.add_message(session_id, "system", f"调度Agent处理 {lead_id}", metadata={"action": "dispatch"})
    result = orch.auto_dispatch(lead_id)
    if result is None:
        raise HTTPException(status_code=400, detail=f"无法调度 lead: {lead_id}")
    mem.add_agent_result(session_id, {"agent": result.agent_name, "summary": result.summary,
                                       "action": result.action, "status": result.status,
                                       "timestamp": result.timestamp})
    score = orch.get_lead_score(lead_id)
    if score:
        mem.set_score(session_id, score)
    insight = orch.get_lead_insights(lead_id)
    if insight:
        mem.set_insight(session_id, insight)
    return {"session_id": session_id, "result": result.to_dict(),
            "has_score": score is not None, "has_insight": insight is not None}


@app.delete("/api/session")
async def api_session_delete(body: dict):
    session_id = body.get("session_id", "")
    if not session_id:
        raise HTTPException(status_code=400, detail="缺少 session_id 字段")
    mem = _get_session_memory()
    if mem.delete_session(session_id):
        return {"message": f"会话已删除: {session_id}"}
    raise HTTPException(status_code=404, detail=f"会话未找到: {session_id}")


# ── API 配置管理 ──────────────────────────────────

@app.get("/api/config")
async def api_get_config():
    try:
        from .team.api_config import APIConfigManager
        mgr = APIConfigManager()
        return mgr.to_dict()
    except ImportError:
        return {"error": "api_config 模块未加载"}


@app.post("/api/config")
async def api_update_config(body: dict):
    llm_cfg = body.get("llm", {})
    if not llm_cfg:
        raise HTTPException(status_code=400, detail="缺少 llm 配置字段")
    try:
        from .team.api_config import update_llm_config
        update_llm_config(**llm_cfg)
        return {"status": "ok", "message": "LLM 配置已更新"}
    except ImportError:
        raise HTTPException(status_code=503, detail="api_config 模块未加载")


@app.get("/api/config/llm-status")
async def api_llm_status():
    try:
        from .team.api_config import is_llm_ready, get_api_config
        ready = is_llm_ready()
        cfg = get_api_config()
        return {"configured": ready, "provider": cfg.llm.base_url if ready else None,
                "model": cfg.llm.model if ready else None}
    except ImportError:
        return {"configured": False, "error": "api_config 未加载"}


# ── Web 管理后台端点 ──────────────────────────────

_settigns_file: Optional[str] = None


def _get_settings_file():
    global _settigns_file
    if _settigns_file is None:
        _settigns_file = str(_WEB_DIR / "_settings.json")
    return _settigns_file

# 内存缓存，减少文件IO
_SETTINGS_CACHE: Optional[dict] = None
_SETTINGS_CACHE_TIME: float = 0
_SETTINGS_CACHE_TTL: float = 5.0

def _load_settings() -> dict:
    global _SETTINGS_CACHE, _SETTINGS_CACHE_TIME
    now = time.time()
    if _SETTINGS_CACHE is not None and (now - _SETTINGS_CACHE_TIME) < _SETTINGS_CACHE_TTL:
        return _SETTINGS_CACHE
    fp = _get_settings_file()
    if not os.path.exists(fp):
        _SETTINGS_CACHE = {"api_keys": {}, "platforms": {}, "config": {}}
        _SETTINGS_CACHE_TIME = now
        return _SETTINGS_CACHE
    try:
        with open(fp, "r", encoding="utf-8") as f:
            _SETTINGS_CACHE = json.load(f)
            _SETTINGS_CACHE_TIME = now
            return _SETTINGS_CACHE
    except (json.JSONDecodeError, IOError):
        _SETTINGS_CACHE = {"api_keys": {}, "platforms": {}, "config": {}}
        _SETTINGS_CACHE_TIME = now
        return _SETTINGS_CACHE


def _save_settings(data: dict) -> None:
    global _SETTINGS_CACHE, _SETTINGS_CACHE_TIME
    _SETTINGS_CACHE = data
    _SETTINGS_CACHE_TIME = time.time()
    with open(_get_settings_file(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── 客户数据持久化 ─────────────────────────────

_CUSTOMERS_FILE: Optional[str] = None
_CUSTOMERS_CACHE: Optional[list] = None
_CUSTOMERS_CACHE_TIME: float = 0
_CUSTOMERS_CACHE_TTL: float = 5.0

def _get_customers_file():
    global _CUSTOMERS_FILE
    if _CUSTOMERS_FILE is None:
        _CUSTOMERS_FILE = str(_WEB_DIR / "_customers.json")
    return _CUSTOMERS_FILE

def _load_customers() -> list:
    global _CUSTOMERS_CACHE, _CUSTOMERS_CACHE_TIME
    now = time.time()
    if _CUSTOMERS_CACHE is not None and (now - _CUSTOMERS_CACHE_TIME) < _CUSTOMERS_CACHE_TTL:
        return _CUSTOMERS_CACHE
    fp = _get_customers_file()
    if not os.path.exists(fp):
        _CUSTOMERS_CACHE = [
            {"id":"z","name":"张先生","intent":"高意向","status":"谈判中","lastMsg":"这个价格还能再优惠吗？","lastTime":"14:28"},
            {"id":"l","name":"李女士","intent":"跟进中","status":"需求分析","lastMsg":"好的，我先了解一下","lastTime":"14:15"},
            {"id":"w","name":"王先生","intent":"已成交","status":"已成交","lastMsg":"已付款，谢谢！","lastTime":"13:52"},
            {"id":"zhao","name":"赵先生","intent":"新客户","status":"初步沟通","lastMsg":"你们产品主要用在哪些场景？","lastTime":"13:30"},
            {"id":"liu","name":"刘女士","intent":"跟进中","status":"需求分析","lastMsg":"价格能不能再低点？","lastTime":"12:45"},
        ]
        _CUSTOMERS_CACHE_TIME = now
        return _CUSTOMERS_CACHE
    try:
        with open(fp, "r", encoding="utf-8") as f:
            _CUSTOMERS_CACHE = json.load(f)
            _CUSTOMERS_CACHE_TIME = now
            return _CUSTOMERS_CACHE
    except (json.JSONDecodeError, IOError):
        _CUSTOMERS_CACHE = []
        _CUSTOMERS_CACHE_TIME = now
        return _CUSTOMERS_CACHE

def _save_customers(data: list) -> None:
    global _CUSTOMERS_CACHE, _CUSTOMERS_CACHE_TIME
    _CUSTOMERS_CACHE = data
    _CUSTOMERS_CACHE_TIME = time.time()
    with open(_get_customers_file(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── 消息记录持久化 ─────────────────────────────

_MESSAGES_DIR: Optional[str] = None

def _get_messages_dir():
    global _MESSAGES_DIR
    if _MESSAGES_DIR is None:
        _MESSAGES_DIR = str(_WEB_DIR / "_messages")
        os.makedirs(_MESSAGES_DIR, exist_ok=True)
    return _MESSAGES_DIR

def _load_messages(customer_id: str) -> list:
    fp = os.path.join(_get_messages_dir(), f"{customer_id}.json")
    if not os.path.exists(fp):
        msgs = _get_default_messages(customer_id)
        if msgs:
            _save_messages(customer_id, msgs)  # 落地到磁盘
        return msgs
    try:
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return _get_default_messages(customer_id)

def _save_messages(customer_id: str, messages: list) -> None:
    fp = os.path.join(_get_messages_dir(), f"{customer_id}.json")
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

def _get_default_messages(customer_id: str) -> list:
    defaults = {
        "z": [
            {"role":"agent","sender":"售前谈判官","text":"张先生您好！很高兴为您服务～ 我注意到您对我们的专业版套餐很感兴趣，这款产品非常适合追求高效运营的企业。","time":"14:23"},
            {"role":"customer","text":"你好，我想了解一下你们这款产品的具体功能和价格","time":"14:25"},
            {"role":"agent","sender":"售前谈判官","text":"好的张先生！我们的专业版套餐包含以下核心功能：\n- 全职能虚拟销售团队（7大岗位）\n- 四位一体能力底座\n- 智能客户匹配\n- 自动报价成交\n- 7×24小时服务\n\n原价 ¥5999/年，现在预约可享受 8折优惠～","time":"14:26"},
            {"role":"customer","text":"这个价格还能再优惠吗？","time":"14:28"},
        ],
        "l": [
            {"role":"agent","sender":"售前谈判官","text":"李女士您好！有什么可以帮助您的？","time":"14:10"},
            {"role":"customer","text":"你好，我想了解一下你们的产品","time":"14:12"},
            {"role":"agent","sender":"售前谈判官","text":"好的，我们主要是做AI销售助手，帮助企业提升销售转化率的。","time":"14:13"},
            {"role":"customer","text":"好的，我先了解一下","time":"14:15"},
        ],
        "w": [
            {"role":"customer","text":"你好，我要下单购买","time":"13:40"},
            {"role":"agent","sender":"售前谈判官","text":"感谢您选择我们的产品！马上为您生成订单。","time":"13:42"},
            {"role":"agent","sender":"售前谈判官","text":"订单已生成，总计 ¥4799，付款后即可开通全部功能。","time":"13:45"},
            {"role":"customer","text":"已付款，谢谢！","time":"13:52"},
        ],
        "zhao": [
            {"role":"customer","text":"你们产品主要用在哪些场景？","time":"13:30"},
        ],
        "liu": [
            {"role":"agent","sender":"售前谈判官","text":"刘女士您好！我是您的专属销售顾问，很高兴为您服务！","time":"12:40"},
            {"role":"customer","text":"价格能不能再低点？","time":"12:45"},
        ],
    }
    return defaults.get(customer_id, [])


@app.get("/api/health")
async def api_health():
    """简单健康检查"""
    return {"status": "ok", "service": "salesmaster-web"}


@app.get("/api/health/detailed")
async def api_health_detailed():
    """详细健康检查"""
    import sys
    from pathlib import Path

    checks = {}
    healthy = True

    # 检查数据目录
    try:
        data_dir = Path(os.environ.get("SALES_DATA_DIR", "./data"))
        exists = data_dir.exists()
        checks["data_dir"] = {
            "status": "ok" if exists else "error",
            "path": str(data_dir.resolve())
        }
        if not exists:
            healthy = False
    except Exception as e:
        checks["data_dir"] = {"status": "error", "message": str(e)}
        healthy = False

    # 检查 API Key
    checks["api_key"] = {
        "status": "ok" if _API_KEY else "warning",
        "has_key": bool(_API_KEY)
    }

    # CORS 配置
    checks["cors"] = {
        "status": "ok",
        "origins": _CORS_ORIGINS
    }

    # 限流配置
    checks["rate_limit"] = {
        "status": "ok",
        "limit": _RATE_LIMIT,
        "window_seconds": _RATE_WINDOW
    }

    return {
        "status": "ok" if healthy else "degraded",
        "service": "salesmaster-web",
        "version": "2.6.0",
        "python_version": sys.version,
        "timestamp": datetime.now().isoformat(),
        "checks": checks
    }


@app.get("/api/quickstart/status")
async def api_qs_status():
    from .team.quickstart import QuickstartGuide
    return QuickstartGuide().get_status()


@app.get("/api/quickstart/industries")
async def api_qs_industries():
    from .team.quickstart import QuickstartGuide
    return QuickstartGuide().get_industries()


@app.post("/api/quickstart/apply")
async def api_qs_apply(body: dict):
    from .team.quickstart import QuickstartGuide
    industry = body.get("industry", "")
    product = body.get("product_name", "")
    return QuickstartGuide().apply_template(industry, product)


@app.post("/api/quickstart/complete")
async def api_qs_complete():
    from .team.quickstart import QuickstartGuide
    return {"status": "ok", "config": QuickstartGuide().complete().to_dict()}


@app.post("/api/quickstart/demo")
async def api_qs_demo():
    from .team.quickstart import QuickstartGuide
    return QuickstartGuide().generate_demo_data()


@app.get("/api/safety/status")
async def api_safety_status():
    orch = _get_orch()
    if hasattr(orch, "safety"):
        try:
            status = orch.safety.get_status()
            status["logs"] = orch.safety.logger.to_text(10)
            return status
        except Exception:
            pass
    return {"mode": "conservative"}


@app.post("/api/safety/mode")
async def api_safety_mode(body: dict):
    mode = body.get("mode", "conservative")
    orch = _get_orch()
    if hasattr(orch, "safety"):
        try:
            if orch.safety.set_mode(mode):
                return {"status": "ok", "mode": orch.safety.mode.value}
        except Exception:
            pass
    raise HTTPException(status_code=400, detail="设置失败")


@app.get("/api/SentriKit/status")
async def api_SentriKit_status():
    from .master import get_SentriKit_status
    return get_SentriKit_status()


@app.post("/api/SentriKit/toggle")
async def api_SentriKit_toggle(body: dict):
    enabled = body.get("enabled", True)
    from .master import set_SentriKit_enabled
    return {"enabled": set_SentriKit_enabled(enabled)}


@app.get("/api/memory/stats")
async def api_memory_stats():
    from gavvy_salesmaster.team_pkg.memory import get_memory_store
    return get_memory_store().get_stats()


@app.get("/api/memory/skills")
async def api_memory_skills(agent: str = ""):
    from gavvy_salesmaster.team_pkg.memory import get_memory_store
    store = get_memory_store()
    skills = store.list_skills(agent=agent) if agent else store.list_skills()
    return {"skills": skills}


@app.get("/api/memory/insights")
async def api_memory_insights(category: str = ""):
    from gavvy_salesmaster.team_pkg.memory import get_memory_store
    store = get_memory_store()
    insights = store.list_insights(category=category) if category else store.list_insights()
    return {"insights": insights}


@app.get("/api/memory/evolution")
async def api_memory_evolution():
    from gavvy_salesmaster.team_pkg.memory import get_memory_store
    return {"log": get_memory_store().get_evolution_log()}


@app.get("/api/memory/performance")
async def api_memory_performance():
    from gavvy_salesmaster.team_pkg.memory import get_memory_store
    return {"performance": get_memory_store().get_performance()}


@app.post("/api/memory/evolve")
async def api_memory_evolve():
    from gavvy_salesmaster.team_pkg.memory import get_memory_store, get_learner, get_evolver
    return get_evolver().evolve_all()


@app.post("/api/chat/send")
async def api_chat_send(body: dict):
    message = body.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="缺少 message 字段")
    customer = body.get("customer", "在线客户")
    orch = _get_orch()
    from .team.base import AgentContext, PrivateInput
    ctx = AgentContext(
        product_info=body.get("product", "通用咨询"),
        customer_name=customer,
        message=message,
        private=PrivateInput(),
    )
    result = orch.assign_task("chat_" + str(hash(message) & 0xFFFFFF), "presales_agent", ctx)
    reply_text = None
    agent_name = "售前谈判官"
    action = result.action if result and result.status == "success" else "人工回复"

    # 如果 LLM 可用，用 LLM 生成更智能的回复
    if result and result.status == "success":
        reply_text = result.output_text or result.summary
    else:
        # LLM 兜底
        from .llm.deepseek import DeepSeekEngine
        llm = DeepSeekEngine()
        if llm.available:
            try:
                llm_reply = llm.generate_sales_message(body.get("product", "通用咨询"), customer)
                if llm_reply:
                    reply_text = llm_reply
            except Exception:
                pass

    if result and result.status == "success":
        try:
            from gavvy_salesmaster.team_pkg.memory import get_memory_store, get_learner
            learner = get_learner()
            learner.learn_from_result("presales_agent",
                {"customer_name": customer, "message": message},
                {"status": "success", "action": result.action, "summary": result.summary})
        except Exception:
            pass
        return {"reply": reply_text or result.output_text or result.summary or "收到咨询，正在分析...",
                "agent": agent_name, "action": result.action, "summary": result.summary}
    return {"reply": reply_text or "好的，我理解您的需求。让我为您详细介绍一下相关方案。",
            "agent": agent_name, "action": action, "summary": result.summary if result else ""}


@app.post("/api/leads")
async def api_leads_create(body: dict):
    orch = _get_orch()
    lead_id = body.get("id", f"lead_{orch.lead_count + 1}")
    return orch.add_lead(lead_id, body.get("info", {}))


@app.post("/api/leads/from_widget")
async def api_leads_from_widget(body: dict):
    """从外部网页嵌入的小部件创建客户/Lead"""
    name = body.get("name", "访客")
    contact = body.get("contact", "")
    source = body.get("source", "widget")
    site = body.get("site", "未知来源")
    customer_id = body.get("customer_id", f"widget_{int(__import__('time').time())}")

    # 创建客户记录
    customers = _load_customers()
    # 检查是否已存在同名客户
    existing = None
    for c in customers:
        if c["id"] == customer_id:
            existing = c
            break
    if existing:
        existing["lastTime"] = "刚刚"
        existing["lastMsg"] = f"来自 {site} 的咨询"
    else:
        customers.insert(0, {
            "id": customer_id,
            "name": name,
            "intent": "新客户",
            "status": "初步沟通",
            "lastMsg": f"来自 {site} 的咨询",
            "lastTime": "刚刚",
        })
    _save_customers(customers)

    # 创建欢迎消息
    welcome = f"👋 欢迎{name}！来自{site}，联系方式：{contact}"
    _save_messages(customer_id, [
        {"role": "customer", "text": welcome, "time": "刚刚"},
    ])

    # 同时添加到 Orchestrator
    try:
        orch = _get_orch()
        orch.add_lead(customer_id, {"name": name, "contact": contact, "source": source, "site": site})
        orch.auto_dispatch(customer_id)
    except Exception:
        pass

    return {"status": "ok", "lead_id": customer_id, "name": name}


@app.post("/api/leads/import_csv")
async def api_leads_import_csv(body: dict):
    """批量导入客户（JSON数组格式，CSV在前端解析后提交）"""
    leads = body.get("leads", [])
    if not leads or not isinstance(leads, list):
        raise HTTPException(status_code=400, detail="需要 leads 数组")
    imported = []
    for item in leads:
        name = item.get("name", "").strip()
        contact = item.get("contact", "").strip()
        if not name:
            continue
        customer_id = f"csv_{int(__import__('time').time())}_{len(imported)}"
        # 添加到客户列表
        customers = _load_customers()
        customers.insert(0, {
            "id": customer_id,
            "name": name,
            "intent": item.get("intent", "新客户"),
            "status": item.get("status", "初步沟通"),
            "lastMsg": "CSV批量导入",
            "lastTime": "刚刚",
        })
        _save_customers(customers)
        # 创建欢迎消息
        welcome = f"📥 CSV导入客户：{name}"
        _save_messages(customer_id, [
            {"role": "customer", "text": welcome, "time": "刚刚"},
        ])
        # 同步到 orchestrator
        try:
            orch = _get_orch()
            orch.add_lead(customer_id, {"name": name, "contact": contact, "source": "csv"})
        except Exception:
            pass
        imported.append({"id": customer_id, "name": name})
    if imported:
        try:
            _get_orch().persist()
        except Exception:
            pass
    return {"status": "ok", "imported": len(imported), "leads": imported}


@app.post("/api/leads/dispatch")
async def api_leads_dispatch(body: dict):
    lead_id = body.get("lead_id", "")
    if not lead_id:
        raise HTTPException(status_code=400, detail="缺少 lead_id 字段")
    orch = _get_orch()
    result = orch.auto_dispatch(lead_id)
    if result:
        return {"result": result.to_dict()}
    raise HTTPException(status_code=400, detail="调度失败")


# ── Pipeline 管道自动触发 API ─────────────────


@app.get("/api/pipeline/stages")
async def api_pipeline_stages():
    """获取管道各阶段客户分布"""
    orch = _get_orch()
    summary = orch.get_summary()
    stages = []
    for s in orch.STAGES:
        count = summary.get("stage_counts", {}).get(s, 0)
        stage_labels = {
            "discovery": "初步发现", "research": "调研分析", "contact": "接触沟通",
            "negotiation": "谈判议价", "closing": "成交", "after_sales": "售后",
            "listing": "上架运营",
        }
        stages.append({
            "id": s,
            "name": stage_labels.get(s, s),
            "count": count,
            "total": summary.get("total_leads", 0),
        })
    return {"stages": stages, "total": summary.get("total_leads", 0),
            "total_agents": summary.get("agent_count", 0)}


@app.post("/api/pipeline/advance")
async def api_pipeline_advance(body: dict):
    """手动推进客户到下一阶段"""
    lead_id = body.get("lead_id", "")
    if not lead_id:
        raise HTTPException(status_code=400, detail="缺少 lead_id")
    from .team.coordinator import PipelineTrigger
    orch = _get_orch()
    result = PipelineTrigger.advance_stage(orch, lead_id)
    orch.persist()
    return result


@app.get("/api/flow/toggles")
async def api_flow_toggles():
    """获取所有流程开关状态"""
    orch = _get_orch()
    return {"toggles": orch.get_flow_toggles()}


@app.post("/api/flow/toggle")
async def api_flow_toggle(body: dict):
    """切换指定流程的开关"""
    name = body.get("name", "")
    enabled = body.get("enabled", None)
    if not name:
        raise HTTPException(status_code=400, detail="缺少 name 字段")
    orch = _get_orch()
    if enabled is not None:
        ok = orch.set_flow_toggle(name, enabled)
    else:
        ok = orch.set_flow_toggle(name, not orch.is_flow_enabled(name))
    if not ok:
        raise HTTPException(status_code=400, detail=f"无效的流程名称: {name}")
    return {"name": name, "enabled": orch.is_flow_enabled(name)}


@app.post("/api/pipeline/auto")
async def api_pipeline_auto():
    """触发全量管道检查：超时检测+自动推进"""
    from .team.coordinator import PipelineTrigger
    orch = _get_orch()
    # 先同步 lead 数据到 orchestrator
    try:
        orch.restore()
    except Exception:
        pass
    result = PipelineTrigger.auto_follow_up(orch, external_save_func=orch.persist)
    return result


@app.get("/api/pipeline/timeouts")
async def api_pipeline_timeouts():
    """获取超时未跟进的客户列表"""
    from .team.coordinator import PipelineTrigger
    orch = _get_orch()
    alerts = PipelineTrigger.check_timeouts(orch)
    return {"timeouts": alerts, "count": len(alerts)}


# ── 记忆库-销售闭环 API ─────────────────────


@app.get("/api/memory/learning-stats")
async def api_memory_learning_stats():
    """获取记忆库学习统计（洞察数、技能数、模式数、Agent绩效）"""
    from gavvy_salesmaster.team_pkg.memory import get_memory_store, get_learner, get_evolver
    store = get_memory_store()
    stats = store.get_stats()
    perf = {}
    for agent_name in ["market_research_agent", "competitor_intel_agent", "presales_agent",
                        "aftersales_agent", "procurement_agent", "operations_agent", "platform_ops_agent"]:
        p = store.get_performance(agent_name)
        if p:
            perf[agent_name] = p
    return {
        "stats": stats,
        "performance": perf,
        "insights_count": len(store.list_insights()),
        "skills_count": len(store.list_skills()),
        "patterns_count": len(store.list_patterns()),
        "episodes_count": len(store.list_episodes(limit=999)),
        "rules_count": len(store.list_rules()),
    }


@app.post("/api/memory/auto-evolve")
async def api_memory_auto_evolve():
    """触发记忆库自动进化：洞察→技能、技能优化、低分淘汰"""
    from gavvy_salesmaster.team_pkg.memory import get_memory_store, get_evolver
    evolver = get_evolver()
    result = evolver.evolve_all()
    return result


# ── 分析 Dashboard API ───────────────────────


@app.get("/api/analytics/summary")
async def api_analytics_summary():
    """获取分析页面汇总数据（缓存60秒）"""
    from .cache import get_cache as _gc
    cache = _gc("analytics")
    cached = cache.get("analytics_summary")
    if cached is not None:
        return cached
    from gavvy_salesmaster.team_pkg.memory import get_memory_store
    store = get_memory_store()
    mem_stats = store.get_stats()
    orch = _get_orch()
    pipeline = orch.get_summary()

    # 漏斗：Pipeline 各阶段数量
    stage_labels = {
        "discovery": "初步发现", "research": "调研分析", "contact": "接触沟通",
        "negotiation": "谈判议价", "closing": "成交", "after_sales": "售后", "listing": "上架运营",
    }
    stage_colors = {
        "discovery": "#3b82f6", "research": "#60a5fa", "contact": "#f59e0b",
        "negotiation": "#f97316", "closing": "#22c55e", "after_sales": "#8b5cf6", "listing": "#06b6d4",
    }
    stages = pipeline.get("stage_counts", {})
    total_leads = pipeline.get("total_leads", 0)
    funnel = []
    for sid, label in stage_labels.items():
        count = stages.get(sid, 0)
        pct = round(count / max(total_leads, 1) * 100, 1)
        funnel.append({"id": sid, "name": label, "count": count, "pct": pct, "color": stage_colors.get(sid, "#94a3b8")})

    # Agent 效能
    agent_names = {
        "market_research_agent": "市场调研官", "competitor_intel_agent": "竞品分析官",
        "presales_agent": "售前谈判官", "aftersales_agent": "售后维系官",
        "procurement_agent": "采购供应链官", "operations_agent": "运营增长官", "platform_ops_agent": "运营助理",
    }
    agents = []
    for key, cn in agent_names.items():
        p = store.get_performance(key)
        agents.append({
            "id": key, "name": cn,
            "total": p.get("total", 0) if p else 0,
            "success": p.get("success", 0) if p else 0,
            "fail": p.get("fail", 0) if p else 0,
            "rate": round(p.get("success", 0) / max(p.get("total", 0), 1) * 100, 1) if p else 0,
        })

    # 转化率：closing / total
    closing_count = stages.get("closing", 0)
    conversion = round(closing_count / max(total_leads, 1) * 100, 1)

    # 平均评分
    avg_score = 0
    try:
        scores = orch.get_all_scores()
        if scores:
            avg_score = round(sum(s.get("total", 0) for s in scores.values()) / len(scores), 1)
    except Exception:
        pass

    result = {
        "total_leads": total_leads,
        "avg_score": avg_score,
        "conversion": conversion,
        "skills_count": mem_stats.get("skills", 0),
        "funnel": funnel,
        "agent_performance": agents,
    }
    cache.set("analytics_summary", result, ttl=60)
    return result


# ── 客户管理 API ──────────────────────────────


@app.get("/api/customers")
async def api_customers_list():
    """获取所有客户列表及会话概要"""
    customers = _load_customers()
    for c in customers:
        msgs = _load_messages(c["id"])
        if msgs:
            last = msgs[-1]
            c["lastMsg"] = last.get("text", "")[:30]
            c["lastTime"] = last.get("time", "")
    return {"customers": customers}


@app.get("/api/customers/{customer_id}/messages")
async def api_customer_messages(customer_id: str):
    """获取指定客户的消息历史"""
    msgs = _load_messages(customer_id)
    return {"messages": msgs, "customer_id": customer_id}


@app.post("/api/customers/{customer_id}/messages")
async def api_customer_messages_add(customer_id: str, body: dict):
    """添加一条消息到指定客户"""
    msgs = _load_messages(customer_id)
    msg = {
        "role": body.get("role", "customer"),
        "sender": body.get("sender", ""),
        "text": body.get("text", ""),
        "time": body.get("time", ""),
    }
    msgs.append(msg)
    _save_messages(customer_id, msgs)
    customers = _load_customers()
    for c in customers:
        if c["id"] == customer_id:
            c["lastMsg"] = msg["text"][:30]
            c["lastTime"] = msg["time"]
            break
    _save_customers(customers)
    return {"status": "ok", "message": "消息已保存"}


@app.get("/api/settings")
async def api_settings_get():
    return _load_settings()


@app.post("/api/settings")
async def api_settings_save(body: dict):
    _save_settings(body)
    return {"status": "ok", "saved": True}


# ── 能力底座 API ──────────────────────────────


@app.get("/api/abilities")
async def api_abilities():
    """返回系统当前所有能力（种子能力 + 进化技能）"""
    from gavvy_salesmaster.team_pkg.memory import get_memory_store, get_capabilities
    return {"abilities": get_capabilities()}


# ── LLM 配置 API ──────────────────────────────


@app.post("/api/llm/config")
async def api_llm_config(body: dict):
    """设置 LLM API Key"""
    api_key = body.get("api_key", "").strip()
    if api_key:
        os.environ["LLM_API_KEY"] = api_key
        # 同时保存到 settings 配置
        settings = _load_settings()
        if "llm" not in settings:
            settings["llm"] = {}
        settings["llm"]["api_key"] = api_key
        _save_settings(settings)
        return {"status": "ok", "message": "LLM API Key 已设置"}
    return {"status": "error", "message": "请提供 api_key"}


@app.get("/api/llm/status")
async def api_llm_status():
    """检查 LLM 是否可用"""
    from .llm.deepseek import DeepSeekEngine
    engine = DeepSeekEngine()
    return {
        "available": engine.available,
        "configured": bool(os.environ.get("LLM_API_KEY", "")),
    }


# ── 训练会话 API ──


@app.post("/api/scripts/training/start")
async def api_training_start(body: dict):
    """开始训练会话"""
    scenario = body.get("scenario", "")
    script_id = body.get("script_id", "")
    result = _get_scripts().start_training(scenario, script_id)
    if not result:
        raise HTTPException(status_code=400, detail="无效的场景")
    return result


@app.post("/api/scripts/training/{session_id}/step")
async def api_training_step(session_id: str, body: dict):
    """训练会话步骤"""
    message = body.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="缺少 message 字段")
    result = _get_scripts().training_step(session_id, message)
    if not result:
        raise HTTPException(status_code=404, detail="训练会话不存在或已结束")
    return result


@app.post("/api/scripts/training/{session_id}/complete")
async def api_training_complete(session_id: str, body: dict):
    """完成训练会话"""
    score = body.get("score", 0)
    feedback = body.get("feedback", "")
    result = _get_scripts().complete_training(session_id, score, feedback)
    if not result:
        raise HTTPException(status_code=404, detail="训练会话不存在")
    return result


@app.get("/api/scripts/training/sessions")
async def api_training_sessions(scenario: str = ""):
    """训练会话历史"""
    return {"sessions": _get_scripts().list_training_sessions(scenario=scenario)}


@app.get("/api/scripts/stats")
async def api_scripts_stats():
    """话术训练系统统计"""
    return _get_scripts().get_stats()


# ── 静态文件回退（必须在所有 API 路由之后）─


@app.get("/{filename:path}")
async def static_fallback(filename: str):
    """通配符静态文件回退 — styles.css / api_client.js / script.js 等"""
    if not any(filename.endswith(ext) for ext in (".css", ".js", ".json", ".png", ".jpg", ".svg", ".ico", ".woff2", ".html")):
        index_file = _WEB_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return JSONResponse({"service": "gavvy-sales-fastapi", "version": "2.5.0", "docs": "/docs"})
    file_path = _WEB_DIR / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    # 返回 SPA 友好的 404 页面
    not_found = _WEB_DIR / "index.html"
    if not_found.exists():
        return FileResponse(str(not_found), status_code=404)
    return JSONResponse({"error": "Not Found", "service": "gavvy-sales-fastapi", "version": "2.5.0", "docs": "/docs"}, status_code=404)


# ── 启动函数与 CLI ────────────────────────────────


def start_app(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    """启动 FastAPI 应用的 uvicorn 服务器。"""
    import uvicorn

    # 设置 LLM 环境变量（如果通过 config 或环境已有则跳过）
    if not os.environ.get("LLM_API_KEY"):
        # 尝试从配置文件读取
        settings = _load_settings()
        llm_key = settings.get("llm", {}).get("api_key", "") or os.environ.get("OPENAI_API_KEY", "")
        if llm_key:
            os.environ["LLM_API_KEY"] = llm_key

    api_key = _get_api_key()

    # SaaS 状态显示
    if _HAS_SAAS:
        _USE_SAAS = os.environ.get("SALES_USE_SAAS", "false").lower() == "true"
        if _USE_SAAS:
            print(f"   🌐 SaaS模式: 已启用")
            print(f"   📋 SaaS API: /api/saas/*")
        else:
            print(f"   🌐 SaaS模式: 已禁用 (设置 SALES_USE_SAAS=true 启用)")

    # 自动恢复 orchestrator 持久化数据
    try:
        orch = _get_orch()
        orch.restore()
        # 如果 leads 为空，从 _customers.json 同步
        if orch.lead_count == 0:
            customers = _load_customers()
            for c in customers:
                orch.add_lead(c["id"], {"name": c["name"], "intent": c["intent"]})
            orch.persist()
            print(f"   📦 已同步 {len(customers)} 位客户到 Pipeline")
    except Exception:
        pass

    print(f"🚀 Chat Sales FastAPI 启动: http://{host}:{port}")
    print(f"   API Key: {api_key}")
    print(f"   认证方式: 请求头 X-API-Key: {api_key}")
    print(f"   📖 API 文档: http://{host}:{port}/docs")
    print(f"   📖 ReDoc:    http://{host}:{port}/redoc")
    print(f"   🌐 Web 管理后台: http://{host}:{port}/")
    print(f"   按 Ctrl+C 停止")

    uvicorn.run(app, host=host, port=port, log_level="info")


def main(argv: Optional[list[str]] = None) -> int:
    """CLI 入口: gavvy-sales-fastapi"""
    import argparse

    parser = argparse.ArgumentParser(
        prog="gavvy-sales-fastapi",
        description="Chat Sales FastAPI 统一服务 — API + Web 管理后台",
    )
    parser.add_argument("--host", type=str, default=None,
                        help=f"监听地址 (默认: {DEFAULT_HOST})")
    parser.add_argument("--port", "-p", type=int, default=None,
                        help=f"监听端口 (默认: {DEFAULT_PORT})")

    args = parser.parse_args(argv)
    host = args.host or os.environ.get("SALES_API_HOST", DEFAULT_HOST)
    port = args.port or int(os.environ.get("SALES_API_PORT", str(DEFAULT_PORT)))
    start_app(host=host, port=port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
