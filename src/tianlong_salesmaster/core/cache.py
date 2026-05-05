"""tianlong_salesmaster.core.cache — 销售宗师缓存工具

基于 LRU 的内存缓存，用于加速频繁的读操作。
纯标准库，零外部依赖。
"""

from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any, Callable, Dict, Optional, Tuple


class _CacheEntry:
    __slots__ = ("value", "expires")

    def __init__(self, value: Any, expires: Optional[float]):
        self.value = value
        self.expires = expires


class SalesCache:
    """LRU 缓存（最近最少使用淘汰）

    用法:
        cache = SalesCache(maxsize=256, default_ttl=30)
        cache.set("key", value)
        val = cache.get("key")
    """

    def __init__(self, maxsize: int = 256, default_ttl: Optional[float] = 30.0):
        self._maxsize = maxsize
        self._default_ttl = default_ttl
        self._data: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._hits = 0
        self._misses = 0

    @property
    def hits(self) -> int:
        return self._hits

    @property
    def misses(self) -> int:
        return self._misses

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return round(self._hits / max(total, 1) * 100, 1)

    @property
    def size(self) -> int:
        return len(self._data)

    def get(self, key: str) -> Any:
        if key not in self._data:
            self._misses += 1
            return None
        entry = self._data[key]
        if entry.expires is not None and time.time() > entry.expires:
            del self._data[key]
            self._misses += 1
            return None
        self._data.move_to_end(key)
        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        if key in self._data:
            self._data.move_to_end(key)
        expires = None
        effective_ttl = self._default_ttl if ttl is None else ttl
        if effective_ttl is not None:
            expires = time.time() + effective_ttl
        self._data[key] = _CacheEntry(value, expires)
        if len(self._data) > self._maxsize:
            self._data.popitem(last=False)

    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            return True
        return False

    def clear(self) -> None:
        self._data.clear()
        self._hits = 0
        self._misses = 0

    def stats(self) -> Dict:
        return {
            "size": self.size,
            "maxsize": self._maxsize,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.hit_rate,
            "ttl": self._default_ttl,
        }


# ── 全局缓存实例（按用途命名） ──────────────────

_caches: Dict[str, SalesCache] = {
    # RBAC 查询缓存（用户、角色、权限 — 变化不频繁）
    "rbac": SalesCache(maxsize=128, default_ttl=60),
    # CRM 仪表盘缓存（每30秒刷新一次）
    "crm": SalesCache(maxsize=32, default_ttl=30),
    # 分析摘要缓存（每60秒刷新一次）
    "analytics": SalesCache(maxsize=16, default_ttl=60),
    # 话术推荐缓存（每120秒刷新一次）
    "scripts": SalesCache(maxsize=64, default_ttl=120),
    # 渠道配置缓存（变化极少，300秒刷新）
    "channels": SalesCache(maxsize=16, default_ttl=300),
}


def get_cache(name: str = "rbac") -> SalesCache:
    """获取指定名称的缓存实例"""
    if name not in _caches:
        _caches[name] = SalesCache(maxsize=64, default_ttl=60)
    return _caches[name]


def invalidate(name: str) -> None:
    """清空指定缓存"""
    c = _caches.get(name)
    if c:
        c.clear()


def invalidate_all() -> None:
    """清空所有缓存"""
    for c in _caches.values():
        c.clear()


def all_stats() -> Dict[str, Dict]:
    """获取所有缓存统计"""
    return {name: c.stats() for name, c in _caches.items()}
