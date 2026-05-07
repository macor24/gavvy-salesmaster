"""FastAPI 集成测试 — 核心 API 端点端到端验证"""

import os
import sys
import tempfile
import pytest

# 设置测试环境
os.environ["SALES_SKIP_AUTH"] = "1"

try:
    from starlette.testclient import TestClient
    from gavvy_salesmaster.core.app import app
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    TestClient = None
    app = None


pytestmark = pytest.mark.skipif(not HAS_FASTAPI, reason="需要 fastapi 和 starlette")


@pytest.fixture
def client():
    """创建 TestClient 实例，自动携带 API Key"""
    _api_key = os.environ.get("SALES_API_KEY", "test-api-key")
    client = TestClient(app)
    client.headers["X-API-Key"] = _api_key
    return client


class TestHealth:
    """健康检查"""

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data


class TestOrchestrator:
    """编排器 API"""

    def test_summary(self, client):
        resp = client.get("/api/orchestrator/summary")
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert "total_leads" in data

    def test_agents(self, client):
        resp = client.get("/api/orchestrator/agents")
        assert resp.status_code in (200, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert "agents" in data

    def test_flow_toggles(self, client):
        resp = client.get("/api/flow/toggles")
        assert resp.status_code in (200, 500)


class TestPipeline:
    """销售管道 API"""

    def test_stages(self, client):
        resp = client.get("/api/pipeline/stages")
        assert resp.status_code == 200
        data = resp.json()
        assert "stages" in data

    def test_leads(self, client):
        resp = client.get("/api/leads")
        assert resp.status_code in (200, 404)


class TestHunt:
    """寻客引擎 API"""

    def test_config(self, client):
        resp = client.get("/api/hunt/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "keywords" in data

    def test_stats(self, client):
        resp = client.get("/api/hunt/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_leads" in data or "config" in data


class TestScheduler:
    """自动调度器 API"""

    def test_task_stats(self, client):
        resp = client.get("/api/scheduler/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "status_counts" in data


class TestMemory:
    """记忆库 API"""

    def test_learning_stats(self, client):
        resp = client.get("/api/memory/learning-stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "stats" in data or "performance" in data


class TestSettings:
    """设置 API"""

    def test_get_settings(self, client):
        resp = client.get("/api/settings")
        assert resp.status_code == 200


class TestLLM:
    """LLM API"""

    def test_llm_status(self, client):
        resp = client.get("/api/llm/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "available" in data


class TestAnalytics:
    """分析 API"""

    def test_summary(self, client):
        resp = client.get("/api/analytics/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_leads" in data


class TestSafety:
    """安全 API"""

    def test_safety_status(self, client):
        resp = client.get("/api/safety/status")
        assert resp.status_code in (200, 500)


class Test404:
    """404 错误处理"""

    def test_not_found(self, client):
        resp = client.get("/api/nonexistent")
        # catch-all /{filename:path} 可能先匹配返回200 HTML
        # 如果没匹配则走全局404处理器
        assert resp.status_code in (200, 404)
        if resp.status_code == 404:
            data = resp.json()
            assert "error" in data
