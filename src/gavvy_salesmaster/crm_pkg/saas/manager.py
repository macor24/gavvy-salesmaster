"""gavvy_salesmaster.crm_pkg.saas.manager — SaaS 管理器

租户管理、用户认证、订阅计费的核心实现。
"""

from __future__ import annotations

import json
import os
import re
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from . import (
    Tenant, TenantUser, Subscription, UsageRecord,
    TenantStatus, UserStatus, PlanType,
    TenantContext, JWTToken, RateLimiter,
)


_TENANT_SECRET = os.environ.get("GAVVY_TENANT_SECRET", "gavvy-secret-key-2024")

DEFAULT_RATE_LIMIT_FREE = 60
DEFAULT_RATE_LIMIT_PAID = 300


class TenantStore:
    """租户存储（文件系统）"""
    _instance = None
    _lock = threading.Lock()

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), "_tenants")
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._tenants_file = self._data_dir / "tenants.json"
        self._users_file = self._data_dir / "users.json"
        self._usage_file = self._data_dir / "usage.json"
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "TenantStore":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _load_tenants(self) -> Dict[str, Dict]:
        if not self._tenants_file.exists():
            return {}
        try:
            with open(self._tenants_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_tenants(self, data: Dict[str, Dict]) -> None:
        with open(self._tenants_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_users(self) -> Dict[str, Dict]:
        if not self._users_file.exists():
            return {}
        try:
            with open(self._users_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_users(self, data: Dict[str, Dict]) -> None:
        with open(self._users_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_usage(self) -> Dict[str, Dict]:
        if not self._usage_file.exists():
            return {}
        try:
            with open(self._usage_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_usage(self, data: Dict[str, Dict]) -> None:
        with open(self._usage_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create_tenant(self, tenant: Tenant) -> bool:
        with self._lock:
            data = self._load_tenants()
            if tenant.slug in data:
                return False
            data[tenant.slug] = tenant.to_dict()
            self._save_tenants(data)
            return True

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        data = self._load_tenants()
        for t in data.values():
            if t.get("id") == tenant_id:
                from . import Subscription
                if isinstance(t.get("subscription"), dict):
                    t["subscription"] = Subscription(**t["subscription"])
                return Tenant(**t)
        return None

    def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        data = self._load_tenants()
        t = data.get(slug.lower())
        if t:
            from . import Subscription
            if isinstance(t.get("subscription"), dict):
                t["subscription"] = Subscription(**t["subscription"])
            return Tenant(**t)
        return None

    def update_tenant(self, tenant: Tenant) -> bool:
        with self._lock:
            data = self._load_tenants()
            if tenant.slug not in data:
                return False
            tenant.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data[tenant.slug] = tenant.to_dict()
            self._save_tenants(data)
            return True

    def list_tenants(self, status: Optional[str] = None) -> List[Tenant]:
        data = self._load_tenants()
        result = []
        for t in data.values():
            if status is None or t.get("status") == status:
                result.append(Tenant(**t))
        return result

    def create_user(self, user: TenantUser) -> bool:
        with self._lock:
            data = self._load_users()
            if user.email in data:
                return False
            data[user.email] = user.to_dict(include_password=True)
            self._save_users(data)
            return True

    def get_user(self, email: str) -> Optional[TenantUser]:
        data = self._load_users()
        u = data.get(email.lower())
        if u:
            return TenantUser(**u)
        return None

    def get_user_by_id(self, user_id: str) -> Optional[TenantUser]:
        data = self._load_users()
        for u in data.values():
            if u.get("id") == user_id:
                return TenantUser(**u)
        return None

    def get_tenant_users(self, tenant_id: str) -> List[TenantUser]:
        data = self._load_users()
        result = []
        for u in data.values():
            if u.get("tenant_id") == tenant_id:
                result.append(TenantUser(**u))
        return result

    def update_user(self, user: TenantUser) -> bool:
        with self._lock:
            data = self._load_users()
            if user.email not in data:
                return False
            user.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data[user.email] = user.to_dict(include_password=True)
            self._save_users(data)
            return True

    def update_usage(self, record: UsageRecord) -> None:
        with self._lock:
            data = self._load_usage()
            key = f"{record.tenant_id}:{record.month}"
            data[key] = record.to_dict()
            self._save_usage(data)

    def get_usage(self, tenant_id: str, month: str) -> UsageRecord:
        data = self._load_usage()
        key = f"{tenant_id}:{month}"
        r = data.get(key)
        if r:
            return UsageRecord(**r)
        return UsageRecord(tenant_id=tenant_id, month=month)


class SaaSManager:
    """SaaS 管理器（租户运营核心）"""

    def __init__(self, store: Optional[TenantStore] = None):
        self._store = store or TenantStore.get_instance()

    def register_tenant(
        self,
        name: str,
        slug: str,
        company: str = "",
        admin_email: str = "",
        admin_name: str = "",
        admin_password: str = "",
    ) -> Dict[str, Any]:
        """注册新租户（包含创建管理员用户）"""
        errors = []
        if not re.match(r"^[a-z0-9][a-z0-9-]{2,19}$", slug.lower()):
            errors.append("slug_invalid")

        existing = self._store.get_tenant_by_slug(slug)
        if existing:
            errors.append("slug_exists")

        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", admin_email):
            errors.append("email_invalid")

        if errors:
            return {"success": False, "errors": errors}

        tenant = Tenant.create(name=name, slug=slug, company=company)
        self._store.create_tenant(tenant)

        if admin_email and admin_password:
            user = TenantUser.create(
                tenant_id=tenant.id,
                email=admin_email,
                name=admin_name or admin_email.split("@")[0],
                password=admin_password,
                role="admin",
            )
            self._store.create_user(user)

            user_data = user.to_dict()
            tenant.activated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tenant.status = TenantStatus.ACTIVE.value
            self._store.update_tenant(tenant)

            token = JWTToken.generate(tenant.id, user.id, _TENANT_SECRET)
            return {
                "success": True,
                "tenant_id": tenant.id,
                "user_id": user.id,
                "token": token,
            }

        return {"success": True, "tenant_id": tenant.id, "pending_activation": True}

    def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """用户登录认证"""
        user = self._store.get_user(email)
        if not user:
            return None
        if not user.check_password(password):
            return None
        if user.status != UserStatus.ACTIVE.value:
            return None

        tenant = self._store.get_tenant(user.tenant_id)
        if not tenant or tenant.status != TenantStatus.ACTIVE.value:
            return None

        user.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._store.update_user(user)

        token = JWTToken.generate(tenant.id, user.id, _TENANT_SECRET)
        return {
            "token": token,
            "user": user.to_dict(),
            "tenant": tenant.to_dict(),
        }

    def verify_token(self, token: str) -> Optional[Dict[str, str]]:
        """验证Token"""
        payload = JWTToken.verify(token, _TENANT_SECRET)
        if not payload:
            return None
        user = self._store.get_user_by_id(payload["user_id"])
        if not user or user.status != UserStatus.ACTIVE.value:
            return None
        return payload

    def get_tenant_context(self, token: str) -> Optional[Tenant]:
        """从Token获取租户上下文"""
        payload = self.verify_token(token)
        if not payload:
            return None
        return self._store.get_tenant(payload["tenant_id"])

    def check_permission(self, token: str, permission: str) -> bool:
        """检查用户权限"""
        payload = self.verify_token(token)
        if not payload:
            return False
        user = self._store.get_user_by_id(payload["user_id"])
        if not user:
            return False
        if user.role == "admin":
            return True
        return permission in user.permissions

    def check_rate_limit(self, token: str) -> bool:
        """检查API限流"""
        payload = self.verify_token(token)
        if not payload:
            return False
        tenant = self._store.get_tenant(payload["tenant_id"])
        if not tenant:
            return False

        limit = DEFAULT_RATE_LIMIT_PAID if tenant.subscription.plan != PlanType.FREE.value else DEFAULT_RATE_LIMIT_FREE
        key = f"api:{payload['tenant_id']}"
        return RateLimiter.check(key, limit)

    def get_rate_limit_remaining(self, token: str) -> int:
        """获取剩余请求数"""
        payload = self.verify_token(token)
        if not payload:
            return 0
        tenant = self._store.get_tenant(payload["tenant_id"])
        if not tenant:
            return 0
        limit = DEFAULT_RATE_LIMIT_PAID if tenant.subscription.plan != PlanType.FREE.value else DEFAULT_RATE_LIMIT_FREE
        key = f"api:{payload['tenant_id']}"
        return RateLimiter.get_remaining(key, limit)

    def update_subscription(self, tenant_id: str, plan: str, seats: Optional[int] = None) -> bool:
        """更新订阅套餐"""
        tenant = self._store.get_tenant(tenant_id)
        if not tenant:
            return False

        tenant.subscription.plan = plan
        if seats:
            tenant.subscription.seats = seats
        tenant.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self._store.update_tenant(tenant)

    def check_quota(self, tenant_id: str) -> Dict[str, Any]:
        """检查租户配额使用情况"""
        tenant = self._store.get_tenant(tenant_id)
        if not tenant:
            return {"error": "tenant_not_found"}

        sub = tenant.subscription
        month = datetime.now().strftime("%Y-%m-%d")[:7]
        usage = self._store.get_usage(tenant_id, month)
        users = self._store.get_tenant_users(tenant_id)
        active_users = len([u for u in users if u.status == UserStatus.ACTIVE.value])

        return {
            "plan": sub.plan,
            "seats": {"limit": sub.seats, "used": active_users, "available": sub.seats - active_users},
            "storage_mb": {"limit": sub.storage_mb, "used": usage.storage_mb, "available": sub.storage_mb - usage.storage_mb},
            "api_calls": {"limit": sub.api_calls_per_month, "used": usage.api_calls, "available": max(0, sub.api_calls_per_month - usage.api_calls)},
            "over_quota": active_users > sub.seats,
        }

    def suspend_tenant(self, tenant_id: str) -> bool:
        """停用租户"""
        tenant = self._store.get_tenant(tenant_id)
        if not tenant:
            return False
        tenant.status = TenantStatus.SUSPENDED.value
        return self._store.update_tenant(tenant)

    def reactivate_tenant(self, tenant_id: str) -> bool:
        """重新激活租户"""
        tenant = self._store.get_tenant(tenant_id)
        if not tenant:
            return False
        tenant.status = TenantStatus.ACTIVE.value
        return self._store.update_tenant(tenant)


_saas_manager: Optional[SaaSManager] = None


def get_saas_manager() -> SaaSManager:
    global _saas_manager
    if _saas_manager is None:
        _saas_manager = SaaSManager()
    return _saas_manager
