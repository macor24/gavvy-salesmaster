"""gavvy_salesmaster.core.storage.repository — 数据仓库层

统一管理销售宗师所有数据的 CRUD 操作。
建立在对 DatabaseKernel 之上，提供高层语义接口。

功能:
    - Lead 管理（增删改查、按阶段/优先级过滤）
    - Session 管理（创建、更新、删除）
    - Score 记录管理（保存、查询历史）
    - Insight 记录管理（保存、查询历史）
    - Safety Log 管理（追加、查询）
    - Product Config 管理
"""

from __future__ import annotations

import threading
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Set

from .compliance import ComplianceGuard, RetentionPolicy, get_compliance_guard
from .db import DatabaseKernel, get_kernel


class DataRepository:
    """数据仓库 — 销售宗师所有数据的统一读写接口。"""

    COLL_LEADS = "leads"
    COLL_SESSIONS = "sessions"
    COLL_SCORES = "scores"
    COLL_INSIGHTS = "insights"
    COLL_SAFETY_LOGS = "safety_logs"
    COLL_PRODUCT_CONFIG = "product_config"
    COLL_PRODUCT_PRICING = "product_pricing"

    def __init__(self, kernel: Optional[DatabaseKernel] = None):
        self._kernel = kernel or get_kernel()
        self._compliance = get_compliance_guard()

    # ── Lead 管理（合规脱敏） ─────────────────────────

    def save_lead(self, lead: Dict) -> None:
        """保存一个 lead（自动脱敏 PII）"""
        clean = self._compliance.sanitize_lead(lead)
        key = lead.get("id") or lead.get("company", "")
        if not key:
            return
        self._kernel.update(self.COLL_LEADS, key, clean)

    def get_lead(self, lead_id: str) -> Optional[Dict]:
        """获取单个 lead"""
        leads = self._kernel.get(self.COLL_LEADS)
        return leads.get(lead_id)

    def list_leads(
        self,
        stage: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """列出 leads，支持按阶段/优先级/状态过滤"""
        leads = self._kernel.get(self.COLL_LEADS)
        result = []
        for lead in leads.values():
            if stage and lead.get("stage") != stage:
                continue
            if priority and lead.get("priority") != priority:
                continue
            if status and lead.get("status") != status:
                continue
            result.append(lead)

        # 按更新时间倒序
        result.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return result[:limit]

    def delete_lead(self, lead_id: str) -> bool:
        """删除一个 lead"""
        try:
            self._kernel.delete(self.COLL_LEADS, lead_id)
            return True
        except Exception:
            return False

    def count_leads(self) -> int:
        """统计 lead 总数"""
        leads = self._kernel.get(self.COLL_LEADS)
        return len(leads)

    # ── Session 管理（合规脱敏） ───────────────────────

    def save_session(self, session: Dict) -> None:
        """保存一个 session（自动脱敏 PII）"""
        clean = self._compliance.sanitize_session(session)
        sid = session.get("session_id") or session.get("id", "")
        if not sid:
            return
        self._kernel.update(self.COLL_SESSIONS, sid, clean)

    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取单个 session"""
        sessions = self._kernel.get(self.COLL_SESSIONS)
        return sessions.get(session_id)

    def list_sessions(self, limit: int = 50) -> List[Dict]:
        """列出所有 session，按更新时间倒序"""
        sessions = self._kernel.get(self.COLL_SESSIONS)
        result = list(sessions.values())
        result.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return result[:limit]

    def delete_session(self, session_id: str) -> bool:
        """删除一个 session"""
        try:
            self._kernel.delete(self.COLL_SESSIONS, session_id)
            return True
        except Exception:
            return False

    def count_sessions(self) -> int:
        sessions = self._kernel.get(self.COLL_SESSIONS)
        return len(sessions)

    # ── Score 记录管理 ────────────────────────────

    def save_score(self, score: Dict) -> None:
        """保存一条评分记录（追加）"""
        record = {
            **score,
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if "timestamp" not in record:
            record["timestamp"] = record["saved_at"]
        self._kernel.append(self.COLL_SCORES, record)

    def list_scores(
        self, lead_id: Optional[str] = None, limit: int = 50
    ) -> List[Dict]:
        """列出评分记录，可筛选 lead"""
        scores = self._kernel.get(self.COLL_SCORES)
        if lead_id:
            filtered = [s for s in scores if s.get("lead_id") == lead_id]
        else:
            filtered = list(scores)
        filtered.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return filtered[:limit]

    def count_scores(self) -> int:
        scores = self._kernel.get(self.COLL_SCORES)
        return len(scores)

    # ── Insight 记录管理 ──────────────────────────

    def save_insight(self, insight: Dict) -> None:
        """保存一条洞察记录（追加）"""
        record = {
            **insight,
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if "timestamp" not in record:
            record["timestamp"] = record["saved_at"]
        self._kernel.append(self.COLL_INSIGHTS, record)

    def list_insights(
        self,
        lead_id: Optional[str] = None,
        insight_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """列出洞察记录，可筛选 lead 和类型"""
        insights = self._kernel.get(self.COLL_INSIGHTS)
        filtered: List[Dict] = []
        for ins in insights:
            if lead_id and ins.get("lead_id") != lead_id:
                continue
            if insight_type and ins.get("type") != insight_type:
                continue
            filtered.append(ins)
        filtered.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return filtered[:limit]

    def count_insights(self) -> int:
        insights = self._kernel.get(self.COLL_INSIGHTS)
        return len(insights)

    # ── Safety Log 管理（合规脱敏） ────────────────────

    def save_safety_log(self, log_entry: Dict) -> None:
        """保存一条安全日志（自动脱敏客户名）"""
        clean = self._compliance.sanitize_safety_log(log_entry)
        record = {
            **clean,
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if "timestamp" not in record:
            record["timestamp"] = record["saved_at"]
        self._kernel.append(self.COLL_SAFETY_LOGS, record)

    def list_safety_logs(
        self,
        agent_name: Optional[str] = None,
        approved: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """列出安全日志，可筛选 Agent 和审批状态"""
        logs = self._kernel.get(self.COLL_SAFETY_LOGS)
        filtered: List[Dict] = []
        for log in logs:
            if agent_name and log.get("agent") != agent_name:
                continue
            if approved is not None and log.get("approved") != approved:
                continue
            filtered.append(log)
        filtered.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return filtered[:limit]

    def count_safety_logs(self) -> int:
        logs = self._kernel.get(self.COLL_SAFETY_LOGS)
        return len(logs)

    def count_today_rejected(self) -> int:
        """统计今日被拦截的日志数"""
        today = date.today().isoformat()
        logs = self._kernel.get(self.COLL_SAFETY_LOGS)
        return sum(
            1 for log in logs
            if log.get("timestamp", "").startswith(today)
            and not log.get("approved", True)
        )

    def count_today_approved(self) -> int:
        """统计今日通过的日志数"""
        today = date.today().isoformat()
        logs = self._kernel.get(self.COLL_SAFETY_LOGS)
        return sum(
            1 for log in logs
            if log.get("timestamp", "").startswith(today)
            and log.get("approved", False)
        )

    # ── Product Config ────────────────────────────

    def save_product_config(self, config: Dict) -> None:
        """保存产品配置"""
        self._kernel.write(self.COLL_PRODUCT_CONFIG, config)

    def get_product_config(self) -> Dict:
        """获取产品配置"""
        return self._kernel.get(self.COLL_PRODUCT_CONFIG)

    def save_product_pricing(self, pricing: Dict) -> None:
        """保存定价配置"""
        self._kernel.write(self.COLL_PRODUCT_PRICING, pricing)

    def get_product_pricing(self) -> Dict:
        """获取定价配置"""
        return self._kernel.get(self.COLL_PRODUCT_PRICING)

    # ── 批量操作 ───────────────────────────────────

    def import_leads(self, leads: List[Dict]) -> int:
        """批量导入 leads，返回导入数量"""
        count = 0
        for lead in leads:
            key = lead.get("id") or lead.get("company", "")
            if key:
                self.save_lead(lead)
                count += 1
        return count

    def clear_all_data(self) -> None:
        """清空所有数据（危险操作）"""
        for coll in [
            self.COLL_LEADS,
            self.COLL_SESSIONS,
            self.COLL_SCORES,
            self.COLL_INSIGHTS,
            self.COLL_SAFETY_LOGS,
        ]:
            self._kernel.clear(coll)

    # ── 存储信息 ───────────────────────────────────

    def get_storage_info(self) -> Dict:
        """获取存储统计信息"""
        return {
            "storage_dir": self._kernel.storage_dir,
            "leads": self.count_leads(),
            "sessions": self.count_sessions(),
            "scores": self.count_scores(),
            "insights": self.count_insights(),
            "safety_logs": self.count_safety_logs(),
            "files": self._kernel.get_collection_files(),
        }

    def __repr__(self) -> str:
        info = self.get_storage_info()
        return (
            f"<DataRepository dir={info['storage_dir']} "
            f"leads={info['leads']} sessions={info['sessions']} "
            f"scores={info['scores']} insights={info['insights']}>"
        )


# ── 全局单例 ──

_global_repo: Optional[DataRepository] = None
_repo_lock = threading.Lock()


def get_repository(
    kernel: Optional[DatabaseKernel] = None,
) -> DataRepository:
    """获取全局数据仓库实例（单例）"""
    global _global_repo
    if _global_repo is None:
        with _repo_lock:
            if _global_repo is None:
                _global_repo = DataRepository(kernel)
    return _global_repo
