"""gavvy_salesmaster.crm_pkg.rbac.db — RBAC 存储接口"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class RBACStorage:
    """RBAC 存储接口"""

    def __init__(self, kernel):
        self._kernel = kernel

    # ── 角色 ──────────────────────────────────

    def get_roles(self) -> List[Dict]:
        return self._kernel.get("rbac_roles") or []

    def save_roles(self, roles: List[Dict]) -> None:
        self._kernel.write("rbac_roles", roles)

    # ── 用户 ──────────────────────────────────

    def get_users(self) -> List[Dict]:
        return self._kernel.get("rbac_users") or []

    def save_users(self, users: List[Dict]) -> None:
        self._kernel.write("rbac_users", users)

    # ── 会话 ──────────────────────────────────

    def get_sessions(self) -> List[Dict]:
        return self._kernel.get("rbac_sessions") or []

    def save_sessions(self, sessions: List[Dict]) -> None:
        self._kernel.write("rbac_sessions", sessions)


# ── 获取存储实例 ────────────────────────────────────────

_global_rbac_storage: Optional[RBACStorage] = None

def get_rbac_kernel(storage_dir: Optional[str] = None) -> RBACStorage:
    """获取 RBAC 存储内核"""
    global _global_rbac_storage
    if _global_rbac_storage is None:
        from gavvy_salesmaster.core.storage.db import get_kernel
        kernel = get_kernel(storage_dir)
        _global_rbac_storage = RBACStorage(kernel)
    return _global_rbac_storage
