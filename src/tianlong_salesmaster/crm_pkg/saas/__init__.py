"""tianlong_salesmaster.crm_pkg.saas — SaaS 多租户系统

提供完整的多租户支持：
- 租户管理：注册、开通、计费
- 用户认证：JWT + 租户绑定
- 订阅管理：套餐、用量、配额
- 租户隔离：数据按租户分离
"""

from __future__ import annotations

import uuid
import secrets
import hashlib
import time
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class PlanType(Enum):
    """订阅套餐类型"""
    FREE = "free"              # 免费版
    STARTER = "starter"        # 入门版
    PROFESSIONAL = "professional"  # 专业版
    ENTERPRISE = "enterprise"  # 企业版


class TenantStatus(Enum):
    """租户状态"""
    PENDING = "pending"        # 待激活
    ACTIVE = "active"          # 正常
    SUSPENDED = "suspended"    # 已停用
    CANCELLED = "cancelled"    # 已注销


class UserStatus(Enum):
    """用户状态"""
    ACTIVE = "active"
    DISABLED = "disabled"
    DELETED = "deleted"


@dataclass
class Subscription:
    """订阅信息"""
    plan: str = "free"
    seats: int = 3
    storage_mb: int = 100
    api_calls_per_month: int = 1000
    started_at: str = ""
    expires_at: str = ""
    auto_renew: bool = True

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def default_free() -> "Subscription":
        return Subscription(
            plan=PlanType.FREE.value,
            seats=3,
            storage_mb=100,
            api_calls_per_month=1000,
            started_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            expires_at="2099-12-31 23:59:59",
            auto_renew=False,
        )


@dataclass
class Tenant:
    """租户"""
    id: str = ""
    name: str = ""
    slug: str = ""                    # 唯一标识符，用于子域名
    company: str = ""
    industry: str = ""
    size: str = ""                    # 公司规模: small/medium/large
    status: str = TenantStatus.ACTIVE.value
    subscription: Subscription = field(default_factory=Subscription)
    settings: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    activated_at: str = ""

    def to_dict(self) -> Dict:
        result = asdict(self)
        return result

    @staticmethod
    def create(name: str, slug: str, company: str = "") -> "Tenant":
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return Tenant(
            id=str(uuid.uuid4()),
            name=name,
            slug=slug.lower(),
            company=company,
            status=TenantStatus.PENDING.value,
            subscription=Subscription.default_free(),
            created_at=now,
            updated_at=now,
        )


@dataclass
class TenantUser:
    """租户用户"""
    id: str = ""
    tenant_id: str = ""
    email: str = ""
    name: str = ""
    phone: str = ""
    password_hash: str = ""
    role: str = "member"           # admin/member/viewer
    status: str = UserStatus.ACTIVE.value
    permissions: List[str] = field(default_factory=list)
    last_login: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self, include_password: bool = False) -> Dict:
        data = asdict(self)
        if not include_password:
            data.pop("password_hash", None)
        return data

    def set_password(self, password: str) -> None:
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def create(tenant_id: str, email: str, name: str, password: str, role: str = "admin") -> "TenantUser":
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user = TenantUser(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            email=email.lower(),
            name=name,
            role=role,
            created_at=now,
            updated_at=now,
        )
        user.set_password(password)
        return user


@dataclass
class UsageRecord:
    """用量记录"""
    tenant_id: str = ""
    month: str = ""                 # YYYY-MM
    api_calls: int = 0
    storage_mb: float = 0.0
    seats_used: int = 0
    updated_at: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


class TenantContext:
    """租户上下文（线程本地存储）"""
    _local = threading.local()

    @classmethod
    def set_tenant(cls, tenant_id: str) -> None:
        cls._local.tenant_id = tenant_id

    @classmethod
    def get_tenant(cls) -> Optional[str]:
        return getattr(cls._local, "tenant_id", None)

    @classmethod
    def clear(cls) -> None:
        cls._local.tenant_id = None

    @classmethod
    def set_user(cls, user_id: str, role: str) -> None:
        cls._local.user_id = user_id
        cls._local.user_role = role

    @classmethod
    def get_user(cls) -> Optional[Dict]:
        uid = getattr(cls._local, "user_id", None)
        role = getattr(cls._local, "user_role", None)
        if uid:
            return {"id": uid, "role": role}
        return None


class JWTToken:
    """JWT Token 生成与验证（简化版）"""

    @staticmethod
    def generate(tenant_id: str, user_id: str, secret: str, expires_in: int = 86400) -> str:
        """生成Token"""
        exp = int(time.time()) + expires_in
        payload = f"{tenant_id}.{user_id}.{exp}"
        signature = hashlib.sha256(f"{payload}.{secret}".encode()).hexdigest()[:32]
        return f"{tenant_id}.{user_id}.{exp}.{signature}"

    @staticmethod
    def verify(token: str, secret: str) -> Optional[Dict[str, str]]:
        """验证Token"""
        try:
            parts = token.split(".")
            if len(parts) != 4:
                return None
            tenant_id, user_id, exp, signature = parts
            if int(exp) < int(time.time()):
                return None
            expected = hashlib.sha256(f"{tenant_id}.{user_id}.{exp}.{secret}".encode()).hexdigest()[:32]
            if signature != expected:
                return None
            return {"tenant_id": tenant_id, "user_id": user_id}
        except Exception:
            return None


class RateLimiter:
    """API限流器"""
    _limits: Dict[str, List[float]] = {}

    @classmethod
    def check(cls, key: str, limit: int, window: int = 60) -> bool:
        """检查是否允许请求"""
        now = time.time()
        if key not in cls._limits:
            cls._limits[key] = []
        cls._limits[key] = [t for t in cls._limits[key] if now - t < window]
        if len(cls._limits[key]) >= limit:
            return False
        cls._limits[key].append(now)
        return True

    @classmethod
    def get_remaining(cls, key: str, limit: int, window: int = 60) -> int:
        """获取剩余请求数"""
        now = time.time()
        if key not in cls._limits:
            return limit
        cls._limits[key] = [t for t in cls._limits[key] if now - t < window]
        return max(0, limit - len(cls._limits[key]))
