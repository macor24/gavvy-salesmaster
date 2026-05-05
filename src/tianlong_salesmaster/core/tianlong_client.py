"""tianlong_salesmaster.core.tianlong_client — 天龙1号 API 客户端

为销售宗师提供完整的进化闭环 API 调用能力。
可直接通过 pip install tianlong-toolkit 本地调用，
也可通过 HTTP 远程调天龙1号 api.py 服务。

用法:
    client = TianlongAPIClient(api_url=\"http://127.0.0.1:8899\", api_key=\"...\")
    
    # 健康检查
    status = client.health()
    
    # 退化检测
    result = client.evaluate_metacog(
        success_rate_7d=0.75, 
        days_since_last_improvement=5,
        repeat_error_count=3,
    )
    if result[\"should_evolve\"]:
        report = client.run_evolve()
    
    # 提案评分
    grade = client.evaluate_judge(summary=\"优化客户跟进流程\")
    
    # 进化状态
    evolve_status = client.evolve_status()
    
    # 自我模型快照
    snapshot = client.selfmodel_snapshot()
    
    # 验证/反射/清理
    verify = client.verify_results()
    lessons = client.reflect_lessons()
    cleanup = client.cleanup_candidates()
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional


class TianlongAPIClient:
    """天龙1号 API 客户端，支持本地/远程双模式。"""

    def __init__(
        self,
        api_url: str = "",
        api_key: str = "",
        project_dir: str = "",
        auto_detect: bool = True,
    ):
        self.api_url = api_url.rstrip("/") if api_url else ""
        self.api_key = api_key
        self.project_dir = project_dir or os.getcwd()
        self._mode = "http" if self.api_url else ("local" if auto_detect else "http")

    # ── HTTP 请求 ─────────────────────────────────

    def _request(self, method: str, path: str, body: Optional[dict] = None) -> dict:
        url = f"{self.api_url}{path}"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if self.api_key:
            req.add_header("X-API-Key", self.api_key)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", errors="replace")
            try:
                return json.loads(msg)
            except json.JSONDecodeError:
                return {"error": f"HTTP {e.code}", "detail": msg[:200]}
        except Exception as e:
            return {"error": str(e)}

    # ── 本地调用（不走 HTTP，直接 import tianlong）──

    def _local_evolve_script(self) -> dict:
        """本地执行 evolve_loop.py"""
        import subprocess
        scripts_dir = os.path.join(self.project_dir, "scripts")
        script = os.path.join(scripts_dir, "evolve_loop.py")
        if not os.path.exists(script):
            # 尝试从 tianlong-toolkit 根目录找
            try:
                import tianlong
                tl_dir = os.path.dirname(os.path.dirname(tianlong.__file__))
                script = os.path.join(tl_dir, "scripts", "evolve_loop.py")
            except (ImportError, AttributeError):
                pass
        if os.path.exists(script):
            r = subprocess.run(
                [sys.executable, script],
                capture_output=True, text=True, timeout=120,
            )
            if r.stdout:
                return json.loads(r.stdout)
            return {"error": r.stderr[:500] if r.stderr else "no output"}
        return {"error": "evolve_loop.py not found"}

    def _local_import(self, module_path: str, names: list) -> Optional[Any]:
        """本地 import tianlong 模块"""
        try:
            sys.path.insert(0, os.path.join(self.project_dir, "src"))
            sys.path.insert(0, self.project_dir)
            mod = __import__(module_path, fromlist=names)
            return [getattr(mod, n, None) for n in names]
        except ImportError:
            return None

    # ── 统一分发 ─────────────────────────────────

    def _call(self, method: str, path: str, body: Optional[dict] = None, local_fn=None):
        if self._mode == "http" and self.api_url:
            return self._request(method, path, body)
        if local_fn:
            return local_fn()
        return {"error": "no local handler", "mode": self._mode}

    # ============================================================
    # 公开 API
    # ============================================================

    def health(self) -> dict:
        """GET /health — 服务健康检查"""
        def _local():
            try:
                modules = self._local_import("tianlong", ["__version__"])
                ver = modules[0] if modules else "unknown"
                return {"status": "ok", "service": "tianlong-local", "version": ver}
            except Exception:
                return {"status": "ok", "service": "tianlong-local"}
        return self._call("GET", "/health", local_fn=_local)

    def status(self) -> dict:
        """GET /api/status — 模块状态"""
        def _local():
            try:
                from tianlong.selfmodel import SelfModel
                from tianlong.metacog import MetaCogTrigger
                sm = SelfModel(project_dir=self.project_dir)
                mc = MetaCogTrigger()
                report = mc.evaluate()
                return {
                    "modules_available": True,
                    "selfmodel": {"decisions": len(sm.get_decisions()), "snapshots": len(sm.get_snapshots())},
                    "metacog": {"should_evolve": report.should_evolve, "score": round(report.overall_score, 3), "level": report.max_level},
                }
            except Exception as e:
                return {"modules_available": False, "error": str(e)}
        return self._call("GET", "/api/status", local_fn=_local)

    def report(self, title: str, body: str = "", highlights: list = None, action_items: list = None) -> dict:
        """POST /api/report — 汇报高亮信息"""
        data = {
            "title": title, "body": body,
            "highlights": highlights or [],
            "action_items": action_items or [],
        }
        def _local():
            try:
                from tianlong.reporter import Reporter
                r = Reporter()
                r.report_highlight(title=title, body=body, highlights=highlights or [], action_items=action_items or [])
                return {"status": "ok", "reported": True}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        return self._call("POST", "/api/report", body=data, local_fn=_local)

    def judge(self, summary: str) -> dict:
        """POST /api/judge — 评估进化方向"""
        def _local():
            try:
                from tianlong.judge import RuleBasedJudge, Proposal
                judge = RuleBasedJudge()
                import time
                p = Proposal(id=f"local_{int(time.time())}", summary=summary)
                result = judge.evaluate(p)
                return {
                    "grade": result.grade.value,
                    "total_score": round(result.total_score, 2),
                    "dimensions": [{"name": d.name, "score": d.score, "reason": d.reason} for d in result.dimensions],
                }
            except Exception as e:
                return {"error": str(e)}
        return self._call("POST", "/api/judge", body={"summary": summary}, local_fn=_local)

    # ── 完整进化闭环 API ────────────────────────

    def run_evolve(self, timeout: int = 120) -> dict:
        """POST /api/evolve/run — 触发完整进化闭环"""
        return self._call("POST", "/api/evolve/run", local_fn=lambda: self._local_evolve_script())

    def evolve_status(self) -> dict:
        """GET /api/evolve/status — 进化状态"""
        def _local():
            try:
                from tianlong.selfmodel import SelfModel
                sm = SelfModel(project_dir=self.project_dir)
                history = sm.get_history()
                snapshot = history.get("latest_snapshot", {})
                decisions = history.get("recent_decisions", [])
                last_evolve = None
                for d in reversed(decisions):
                    if d.get("decision_type") == "EVOLVE":
                        last_evolve = {"timestamp": d.get("timestamp"), "outcome": d.get("outcome"), "task": d.get("task")}
                        break
                return {
                    "last_evolve": last_evolve,
                    "overall_success_rate": snapshot.get("overall_success_rate", 0),
                    "judge_avg_score": snapshot.get("judge_avg_score", 0),
                    "error_rate_7d": snapshot.get("error_rate_7d", 0),
                    "decision_count": len(decisions),
                }
            except Exception as e:
                return {"error": str(e)}
        return self._call("GET", "/api/evolve/status", local_fn=_local)

    def evaluate_metacog(self, success_rate_7d: float = 0.85, days_since_last_improvement: int = 0, repeat_error_count: int = 0) -> dict:
        """POST /api/metacog/evaluate — 退化检测"""
        body = {
            "success_rate_7d": success_rate_7d,
            "success_rate_3d": success_rate_7d,
            "success_rate_1d": success_rate_7d * 0.9,
            "days_since_last_improvement": days_since_last_improvement,
            "repeat_error_count": repeat_error_count,
        }
        def _local():
            try:
                from tianlong.metacog import MetaCogTrigger
                t = MetaCogTrigger()
                r = t.evaluate(**body)
                return {
                    "should_evolve": r.should_evolve,
                    "score": round(r.overall_score, 3),
                    "level": r.max_level,
                    "triggers": [
                        {"signal": tr.signal_name, "triggered": tr.triggered, "reason": tr.reason, "level": tr.level.value}
                        for tr in r.triggers
                    ],
                }
            except Exception as e:
                return {"error": str(e)}
        return self._call("POST", "/api/metacog/evaluate", body=body, local_fn=_local)

    def evaluate_judge(self, summary: str, proposal_id: str = "") -> dict:
        """POST /api/judge/evaluate — 提案评分"""
        body = {"summary": summary, "id": proposal_id or f"api_{int(__import__('time').time())}"}
        def _local():
            try:
                from tianlong.judge import RuleBasedJudge, Proposal
                judge = RuleBasedJudge()
                p = Proposal(id=body["id"], summary=summary)
                result = judge.evaluate(p)
                return {
                    "grade": result.grade.value,
                    "total_score": round(result.total_score, 2),
                    "dimensions": [{"name": d.name, "score": d.score, "reason": d.reason} for d in result.dimensions],
                }
            except Exception as e:
                return {"error": str(e)}
        return self._call("POST", "/api/judge/evaluate", body=body, local_fn=_local)

    def selfmodel_snapshot(self) -> dict:
        """GET /api/selfmodel/snapshot — 自我模型快照"""
        def _local():
            try:
                from tianlong.selfmodel import SelfModel
                sm = SelfModel(project_dir=self.project_dir)
                sm.take_snapshot()
                snapshot = sm.get_history().get("latest_snapshot", {})
                return {"status": "ok", "latest_snapshot": snapshot}
            except Exception as e:
                return {"error": str(e)}
        return self._call("GET", "/api/selfmodel/snapshot", local_fn=_local)

    def verify_results(self) -> dict:
        """GET /api/verify/results — 验证结果"""
        def _local():
            try:
                import json
                verify_file = os.path.join(self.project_dir, "brain", "verify-state.json")
                if os.path.exists(verify_file):
                    with open(verify_file, encoding="utf-8") as f:
                        data = json.load(f)
                    return data if isinstance(data, dict) else {"results": data}
                return {"results": [], "note": "无验证记录"}
            except Exception as e:
                return {"error": str(e)}
        return self._call("GET", "/api/verify/results", local_fn=_local)

    def reflect_lessons(self) -> dict:
        """GET /api/reflect/lessons — 反射教训"""
        def _local():
            try:
                import json
                reflect_file = os.path.join(self.project_dir, "brain", "reflect-state.json")
                if os.path.exists(reflect_file):
                    with open(reflect_file, encoding="utf-8") as f:
                        data = json.load(f)
                    return data if isinstance(data, dict) else {"lessons": data}
                return {"lessons": [], "note": "无反省记录"}
            except Exception as e:
                return {"error": str(e)}
        return self._call("GET", "/api/reflect/lessons", local_fn=_local)

    def cleanup_candidates(self) -> dict:
        """GET /api/cleanup/candidates — 清理候选"""
        def _local():
            try:
                import json
                cleanup_file = os.path.join(self.project_dir, "brain", "cleanup-state.json")
                if os.path.exists(cleanup_file):
                    with open(cleanup_file, encoding="utf-8") as f:
                        data = json.load(f)
                    return data if isinstance(data, dict) else {"candidates": data}
                return {"candidates": [], "note": "暂无可清理项"}
            except Exception as e:
                return {"error": str(e)}
        return self._call("GET", "/api/cleanup/candidates", local_fn=_local)
