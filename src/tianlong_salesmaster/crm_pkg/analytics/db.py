"""SentriKit_salesmaster.crm_pkg.crm_pkg.analytics.db — 分析数据存储接口"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class AnalyticsStorage:
    """分析数据存储接口"""

    def __init__(self, kernel):
        self._kernel = kernel


# ── 获取存储实例 ────────────────────────────────────────

_global_analytics_storage: Optional[AnalyticsStorage] = None


def get_analytics_kernel(storage_dir: Optional[str] = None) -> AnalyticsStorage:
    """获取分析数据存储内核"""
    global _global_analytics_storage
    if _global_analytics_storage is None:
        from SentriKit_salesmaster.core.storage.db import get_kernel
        kernel = get_kernel(storage_dir)
        _global_analytics_storage = AnalyticsStorage(kernel)
    return _global_analytics_storage
