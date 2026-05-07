"""gavvy_salesmaster.crm_pkg.rbac.audit — 审计日志系统

完整的操作审计功能：
- 操作日志记录
- 敏感数据访问审计
- 合规报告生成
- 异常行为检测
"""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class AuditAction(Enum):
    """审计动作类型"""
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    VIEW = "view"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    APPROVE = "approve"
    REJECT = "reject"
    ASSIGN = "assign"
    TRANSFER = "transfer"
    PAY = "pay"
    REFUND = "refund"
    SIGN = "sign"
    SEND = "send"


class AuditLevel(Enum):
    """审计级别"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    SECURITY = "security"


@dataclass
class AuditLog:
    """审计日志"""
    id: str = ""
    timestamp: str = ""
    user_id: str = ""
    username: str = ""
    tenant_id: str = ""
    action: str = ""
    resource: str = ""           # 资源类型
    resource_id: str = ""       # 资源ID
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: str = ""
    user_agent: str = ""
    level: str = AuditLevel.INFO.value
    status: str = "success"     # success / failed
    error_message: str = ""
    duration_ms: int = 0
    correlation_id: str = ""    # 关联ID（如工作流ID）
    session_id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "AuditLog":
        return AuditLog(**data)


@dataclass
class AuditQuery:
    """审计查询条件"""
    user_id: Optional[str] = None
    username: Optional[str] = None
    tenant_id: Optional[str] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    resource_id: Optional[str] = None
    level: Optional[str] = None
    status: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    limit: int = 100
    offset: int = 0


class AuditLogger:
    """审计日志器"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._logs: List[AuditLog] = []
        self._max_logs: int = 10000
        self._lock = threading.Lock()
        self._handlers: Dict[str, List] = {
            "login": [],
            "data_access": [],
            "data_modify": [],
            "sensitive": [],
            "all": [],
        }

    def log(
        self,
        action: str,
        user_id: str = "",
        username: str = "",
        tenant_id: str = "",
        resource: str = "",
        resource_id: str = "",
        details: Optional[Dict[str, Any]] = None,
        ip_address: str = "",
        user_agent: str = "",
        level: str = AuditLevel.INFO.value,
        status: str = "success",
        error_message: str = "",
        duration_ms: int = 0,
        correlation_id: str = "",
        session_id: str = "",
    ) -> AuditLog:
        """记录审计日志"""
        log = AuditLog(
            action=action,
            user_id=user_id,
            username=username,
            tenant_id=tenant_id,
            resource=resource,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            level=level,
            status=status,
            error_message=error_message,
            duration_ms=duration_ms,
            correlation_id=correlation_id,
            session_id=session_id,
        )

        with self._lock:
            self._logs.append(log)
            if len(self._logs) > self._max_logs:
                self._logs = self._logs[-self._max_logs:]

        self._notify_handlers(log)

        return log

    def log_login(self, username: str, success: bool, ip_address: str = "", user_agent: str = "", tenant_id: str = "") -> AuditLog:
        """记录登录"""
        return self.log(
            action=AuditAction.LOGIN.value if success else AuditAction.LOGIN_FAILED.value,
            username=username,
            tenant_id=tenant_id,
            resource="session",
            ip_address=ip_address,
            user_agent=user_agent,
            level=AuditLevel.INFO.value if success else AuditLevel.WARNING.value,
            status="success" if success else "failed",
        )

    def log_logout(self, user_id: str, username: str, tenant_id: str, session_id: str = "") -> AuditLog:
        """记录登出"""
        return self.log(
            action=AuditAction.LOGOUT.value,
            user_id=user_id,
            username=username,
            tenant_id=tenant_id,
            resource="session",
            session_id=session_id,
        )

    def log_data_access(
        self,
        user_id: str,
        username: str,
        tenant_id: str,
        resource: str,
        resource_id: str,
        ip_address: str = "",
    ) -> AuditLog:
        """记录数据访问"""
        return self.log(
            action=AuditAction.VIEW.value,
            user_id=user_id,
            username=username,
            tenant_id=tenant_id,
            resource=resource,
            resource_id=resource_id,
            ip_address=ip_address,
            level=AuditLevel.INFO.value,
        )

    def log_data_modify(
        self,
        action: str,
        user_id: str,
        username: str,
        tenant_id: str,
        resource: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: str = "",
    ) -> AuditLog:
        """记录数据修改"""
        return self.log(
            action=action,
            user_id=user_id,
            username=username,
            tenant_id=tenant_id,
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            level=AuditLevel.INFO.value,
        )

    def log_sensitive(
        self,
        action: str,
        user_id: str,
        username: str,
        tenant_id: str,
        resource: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: str = "",
    ) -> AuditLog:
        """记录敏感操作"""
        return self.log(
            action=action,
            user_id=user_id,
            username=username,
            tenant_id=tenant_id,
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            level=AuditLevel.CRITICAL.value,
        )

    def log_security(
        self,
        action: str,
        user_id: str,
        username: str,
        tenant_id: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        ip_address: str = "",
    ) -> AuditLog:
        """记录安全事件"""
        return self.log(
            action=action,
            user_id=user_id,
            username=username,
            tenant_id=tenant_id,
            resource="security",
            details={"message": message, **(details or {})},
            ip_address=ip_address,
            level=AuditLevel.SECURITY.value,
            status="failed" if "failed" in action.lower() else "success",
        )

    def query(self, query: AuditQuery) -> List[AuditLog]:
        """查询审计日志"""
        with self._lock:
            logs = self._logs.copy()

        if query.user_id:
            logs = [l for l in logs if l.user_id == query.user_id]
        if query.username:
            logs = [l for l in logs if query.username.lower() in l.username.lower()]
        if query.tenant_id:
            logs = [l for l in logs if l.tenant_id == query.tenant_id]
        if query.action:
            logs = [l for l in logs if l.action == query.action]
        if query.resource:
            logs = [l for l in logs if l.resource == query.resource]
        if query.resource_id:
            logs = [l for l in logs if l.resource_id == query.resource_id]
        if query.level:
            logs = [l for l in logs if l.level == query.level]
        if query.status:
            logs = [l for l in logs if l.status == query.status]
        if query.start_time:
            logs = [l for l in logs if l.timestamp >= query.start_time]
        if query.end_time:
            logs = [l for l in logs if l.timestamp <= query.end_time]

        logs.sort(key=lambda x: x.timestamp, reverse=True)

        return logs[query.offset : query.offset + query.limit]

    def get_user_activity(
        self,
        user_id: str,
        days: int = 30,
        limit: int = 100,
    ) -> List[AuditLog]:
        """获取用户活动记录"""
        start_time = (datetime.now() - timedelta(days=days)).isoformat()
        query = AuditQuery(user_id=user_id, start_time=start_time, limit=limit)
        return self.query(query)

    def get_resource_history(
        self,
        resource: str,
        resource_id: str,
        limit: int = 100,
    ) -> List[AuditLog]:
        """获取资源操作历史"""
        query = AuditQuery(resource=resource, resource_id=resource_id, limit=limit)
        return self.query(query)

    def get_failed_logins(
        self,
        tenant_id: Optional[str] = None,
        hours: int = 24,
        limit: int = 100,
    ) -> List[AuditLog]:
        """获取失败登录记录"""
        start_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        query = AuditQuery(
            action=AuditAction.LOGIN_FAILED.value,
            tenant_id=tenant_id,
            start_time=start_time,
            limit=limit,
        )
        return self.query(query)

    def get_sensitive_operations(
        self,
        tenant_id: Optional[str] = None,
        days: int = 30,
        limit: int = 100,
    ) -> List[AuditLog]:
        """获取敏感操作记录"""
        start_time = (datetime.now() - timedelta(days=days)).isoformat()
        query = AuditQuery(
            tenant_id=tenant_id,
            start_time=start_time,
            level=AuditLevel.CRITICAL.value,
            limit=limit,
        )
        return self.query(query)

    def generate_compliance_report(
        self,
        tenant_id: str,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """生成合规报告"""
        query = AuditQuery(
            tenant_id=tenant_id,
            start_time=start_date,
            end_time=end_date,
            limit=10000,
        )
        logs = self.query(query)

        total_operations = len(logs)
        successful_operations = len([l for l in logs if l.status == "success"])
        failed_operations = len([l for l in logs if l.status == "failed"])

        actions_count: Dict[str, int] = {}
        for log in logs:
            actions_count[log.action] = actions_count.get(log.action, 0) + 1

        users_count = len(set(l.user_id for l in logs))

        return {
            "report_period": {"start": start_date, "end": end_date},
            "tenant_id": tenant_id,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_operations": total_operations,
                "successful_operations": successful_operations,
                "failed_operations": failed_operations,
                "unique_users": users_count,
            },
            "actions_breakdown": actions_count,
            "security_events": {
                "failed_logins": len([l for l in logs if l.action == AuditAction.LOGIN_FAILED.value]),
                "sensitive_operations": len([l for l in logs if l.level == AuditLevel.CRITICAL.value]),
                "security_events": len([l for l in logs if l.level == AuditLevel.SECURITY.value]),
            },
        }

    def register_handler(self, category: str, handler) -> None:
        """注册日志处理器"""
        if category in self._handlers:
            self._handlers[category].append(handler)

    def _notify_handlers(self, log: AuditLog) -> None:
        """通知处理器"""
        self._handlers["all"].append(log)

        if log.action in [AuditAction.LOGIN.value, AuditAction.LOGIN_FAILED.value, AuditAction.LOGOUT.value]:
            for handler in self._handlers["login"]:
                try:
                    handler(log)
                except Exception:
                    pass

        if log.level in [AuditLevel.CRITICAL.value, AuditLevel.SECURITY.value]:
            for handler in self._handlers["sensitive"]:
                try:
                    handler(log)
                except Exception:
                    pass


_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
