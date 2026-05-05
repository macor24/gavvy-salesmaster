"""SentriKit_salesmaster.core.storage.db — 文件数据库内核

提供线程安全的 JSON 文件存储，支持 CRUD 和索引。

特点:
    - 每个集合（collection）存储为独立 JSON 文件
    - 读写锁保护，线程安全
    - 支持按索引快速查询
    - 自动迁移旧路径数据
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# 存储根目录（用户可配置）
_STORAGE_DIR: Optional[str] = None
_STORAGE_LOCK = threading.Lock()

_STORAGE_DEFAULT = os.path.join(os.path.dirname(__file__), "_data")


def get_storage_dir() -> str:
    """获取存储根目录"""
    global _STORAGE_DIR
    if _STORAGE_DIR is None:
        with _STORAGE_LOCK:
            if _STORAGE_DIR is None:
                _STORAGE_DIR = _STORAGE_DEFAULT
    return _STORAGE_DIR


def set_storage_dir(path: str) -> None:
    """设置存储根目录"""
    global _STORAGE_DIR
    with _STORAGE_LOCK:
        _STORAGE_DIR = path


# ── 旧路径映射（用于数据迁移） ────

_LEGACY_PATHS: Dict[str, str] = {
    "leads": os.path.join(
        os.path.dirname(__file__), "..", "team", "_leads.json"
    ),
    "product_config": os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "product", "config.json"
    ),
    "product_pricing": os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "product", "pricing.json"
    ),
}


# ═══════════════════════════════════════════════════════
# 集合定义
# ═══════════════════════════════════════════════════════

# 每个集合：文件名、默认值
_COLLECTIONS: Dict[str, Dict] = {
    "leads": {
        "file": "leads.json",
        "default": {},
        "legacy_key": "leads",  # 对应 _LEGACY_PATHS
    },
    "sessions": {
        "file": "sessions.json",
        "default": {},
        "legacy_key": None,
    },
    "scores": {
        "file": "scores.json",
        "default": [],
        "legacy_key": None,
    },
    "insights": {
        "file": "insights.json",
        "default": [],
        "legacy_key": None,
    },
    "safety_logs": {
        "file": "safety_logs.json",
        "default": [],
        "legacy_key": None,
    },
    "product_config": {
        "file": "product_config.json",
        "default": {},
        "legacy_key": "product_config",
    },
    "product_pricing": {
        "file": "product_pricing.json",
        "default": {},
        "legacy_key": "product_pricing",
    },
    "stats_cache": {
        "file": "stats_cache.json",
        "default": {},
        "legacy_key": None,
    },
    "knowledge_items": {
        "file": "knowledge_items.json",
        "default": [],
        "legacy_key": None,
    },
    "knowledge_categories": {
        "file": "knowledge_categories.json",
        "default": [],
        "legacy_key": None,
    },
    "knowledge_qa": {
        "file": "knowledge_qa.json",
        "default": [],
        "legacy_key": None,
    },
    "tasks_items": {
        "file": "tasks_items.json",
        "default": [],
        "legacy_key": None,
    },
    "tasks_subtasks": {
        "file": "tasks_subtasks.json",
        "default": [],
        "legacy_key": None,
    },
    "approvals_items": {
        "file": "approvals_items.json",
        "default": [],
        "legacy_key": None,
    },
    "approval_rules": {
        "file": "approval_rules.json",
        "default": [],
        "legacy_key": None,
    },
    "notifications_items": {
        "file": "notifications_items.json",
        "default": [],
        "legacy_key": None,
    },
    # ── CRM 集合 ──
    "crm_customers": {
        "file": "crm_customers.json",
        "default": [],
        "legacy_key": None,
    },
    "crm_contacts": {
        "file": "crm_contacts.json",
        "default": [],
        "legacy_key": None,
    },
    "crm_deals": {
        "file": "crm_deals.json",
        "default": [],
        "legacy_key": None,
    },
    "crm_contracts": {
        "file": "crm_contracts.json",
        "default": [],
        "legacy_key": None,
    },
    "crm_activities": {
        "file": "crm_activities.json",
        "default": [],
        "legacy_key": None,
    },
    "quotes_products": {
        "file": "quotes_products.json",
        "default": [],
        "legacy_key": None,
    },
    "quotes_quotes": {
        "file": "quotes_quotes.json",
        "default": [],
        "legacy_key": None,
    },
    "quotes_contracts": {
        "file": "quotes_contracts.json",
        "default": [],
        "legacy_key": None,
    },
    "quotes_quote_templates": {
        "file": "quotes_quote_templates.json",
        "default": [],
        "legacy_key": None,
    },
    "quotes_contract_templates": {
        "file": "quotes_contract_templates.json",
        "default": [],
        "legacy_key": None,
    },
    "calls_records": {
        "file": "calls_records.json",
        "default": [],
        "legacy_key": None,
    },
    "calls_recordings": {
        "file": "calls_recordings.json",
        "default": [],
        "legacy_key": None,
    },
    "calls_scripts": {
        "file": "calls_scripts.json",
        "default": [],
        "legacy_key": None,
    },
    "calls_analyses": {
        "file": "calls_analyses.json",
        "default": [],
        "legacy_key": None,
    },
    # ── 话术训练集合 ──
    "scripts_items": {
        "file": "scripts_items.json",
        "default": [],
        "legacy_key": None,
    },
    "scripts_training": {
        "file": "scripts_training.json",
        "default": [],
        "legacy_key": None,
    },
    "scripts_ratings": {
        "file": "scripts_ratings.json",
        "default": [],
        "legacy_key": None,
    },
    # ── RBAC 权限集合 ──
    "rbac_roles": {
        "file": "rbac_roles.json",
        "default": [],
        "legacy_key": None,
    },
    "rbac_users": {
        "file": "rbac_users.json",
        "default": [],
        "legacy_key": None,
    },
    "rbac_sessions": {
        "file": "rbac_sessions.json",
        "default": [],
        "legacy_key": None,
    },
    # ── 配置存储集合 ──
    "agent_toggles": {
        "file": "agent_toggles.json",
        "default": {},
        "legacy_key": None,
    },
    "flow_toggles": {
        "file": "flow_toggles.json",
        "default": {},
        "legacy_key": None,
    },
    "channel_configs": {
        "file": "channel_configs.json",
        "default": {},
        "legacy_key": None,
    },
}


# ═══════════════════════════════════════════════════════
# 文件数据库内核
# ═══════════════════════════════════════════════════════

class DatabaseKernel:
    """线程安全的 JSON 文件数据库内核。

    每个集合（collection）是一个独立的 JSON 文件。
    所有读写操作带锁保护。
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self._dir = storage_dir or get_storage_dir()
        self._collections: Dict[str, Dict] = {}
        self._locks: Dict[str, threading.Lock] = {}
        self._init_locks()

        # 创建存储目录
        os.makedirs(self._dir, exist_ok=True)

        # 从旧路径迁移数据
        self._migrate_legacy()

        # 加载所有已存在的集合
        self._load_all()

    def _init_locks(self) -> None:
        """为每个集合初始化锁"""
        for name in _COLLECTIONS:
            self._locks[name] = threading.Lock()
            self._collections[name] = None  # 懒加载标记

    def _collection_path(self, name: str) -> str:
        """获取集合文件路径"""
        info = _COLLECTIONS.get(name)
        if info is None:
            raise ValueError(f"未知集合: {name}")
        return os.path.join(self._dir, info["file"])

    def _migrate_legacy(self) -> None:
        """从旧路径迁移数据（一次性操作）"""
        for name, info in _COLLECTIONS.items():
            legacy_key = info.get("legacy_key")
            if legacy_key is None:
                continue
            legacy_path = _LEGACY_PATHS.get(legacy_key)
            if legacy_path is None:
                continue
            new_path = self._collection_path(name)
            # 仅在目标文件不存在且旧文件存在时迁移
            if not os.path.exists(new_path) and os.path.exists(legacy_path):
                try:
                    import shutil
                    os.makedirs(self._dir, exist_ok=True)
                    shutil.copy2(legacy_path, new_path)
                    print(f"[storage] 迁移数据: {legacy_path} → {new_path}")
                except (IOError, OSError):
                    pass

    def _load_all(self) -> None:
        """加载所有已存在的集合文件到内存"""
        for name in _COLLECTIONS:
            self._load(name)

    def _load(self, name: str) -> None:
        """加载单个集合"""
        path = self._collection_path(name)
        info = _COLLECTIONS[name]
        default = info["default"]
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._collections[name] = data
            except (json.JSONDecodeError, IOError):
                self._collections[name] = self._deep_copy(default)
        else:
            self._collections[name] = self._deep_copy(default)

    def _save(self, name: str) -> None:
        """保存单个集合到文件"""
        path = self._collection_path(name)
        data = self._collections.get(name)
        if data is None:
            return
        try:
            os.makedirs(self._dir, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except (IOError, OSError):
            pass

    @staticmethod
    def _deep_copy(obj: Any) -> Any:
        """深拷贝一个简单对象（只适用于 dict/list/基本类型）"""
        return json.loads(json.dumps(obj))

    # ── 公共 API ──

    def get(self, name: str) -> Any:
        """获取整个集合数据"""
        with self._locks[name]:
            data = self._collections.get(name)
            if data is None:
                self._load(name)
                data = self._collections.get(name)
            # 只对写操作返回副本，读操作直接返回引用
            # 调用方不应修改返回的数据
            return data if data is not None else []

    def write(self, name: str, data: Any) -> None:
        """覆写整个集合数据并持久化"""
        with self._locks[name]:
            self._collections[name] = data
            self._save(name)

    def update(self, name: str, key: str, value: Any) -> None:
        """更新集合中的单个 key-value（仅对 dict 类型有效）"""
        with self._locks[name]:
            data = self._collections.get(name)
            if data is None:
                self._load(name)
                data = self._collections.get(name) or {}
            if isinstance(data, dict):
                data[key] = self._deep_copy(value)
                self._save(name)

    def append(self, name: str, item: Any) -> None:
        """向集合追加一项（仅对 list 类型有效）"""
        with self._locks[name]:
            data = self._collections.get(name)
            if data is None:
                self._load(name)
                data = self._collections.get(name) or []
            if isinstance(data, list):
                data.append(self._deep_copy(item))
                self._save(name)

    def delete(self, name: str, key: str) -> None:
        """从 dict 集合中删除一个 key"""
        with self._locks[name]:
            data = self._collections.get(name)
            if isinstance(data, dict) and key in data:
                del data[key]
                self._save(name)

    def clear(self, name: str) -> None:
        """清空一个集合"""
        info = _COLLECTIONS.get(name)
        if info is None:
            return
        with self._locks[name]:
            self._collections[name] = self._deep_copy(info["default"])
            self._save(name)

    def exists(self, name: str) -> bool:
        """检查集合文件是否存在"""
        return os.path.exists(self._collection_path(name))

    def get_collection_files(self) -> List[str]:
        """获取所有集合文件的绝对路径"""
        files = []
        for name in _COLLECTIONS:
            path = self._collection_path(name)
            if os.path.exists(path):
                files.append(path)
        return files

    @property
    def storage_dir(self) -> str:
        return self._dir

    def __repr__(self) -> str:
        return f"<DatabaseKernel dir={self._dir} collections={len(_COLLECTIONS)}>"


# ── 全局单例 ──

_global_kernel: Optional[DatabaseKernel] = None
_kernel_lock = threading.Lock()


def get_kernel(storage_dir: Optional[str] = None) -> DatabaseKernel:
    """获取全局数据库内核实例（单例）"""
    global _global_kernel
    if _global_kernel is None:
        with _kernel_lock:
            if _global_kernel is None:
                _global_kernel = DatabaseKernel(storage_dir)
    return _global_kernel
