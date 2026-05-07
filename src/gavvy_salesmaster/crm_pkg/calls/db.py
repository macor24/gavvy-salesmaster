"""gavvy_salesmaster.crm_pkg.crm_pkg.calls.db — 通话与录音存储接口"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class CallsStorage:
    """通话与录音存储接口"""

    def __init__(self, kernel):
        self._kernel = kernel

    # ── 通话记录 ──────────────────────────────────

    def get_calls(self) -> List[Dict]:
        return self._kernel.get("calls_records") or []

    def save_calls(self, calls: List[Dict]) -> None:
        self._kernel.write("calls_records", calls)

    # ── 录音 ──────────────────────────────────

    def get_recordings(self) -> List[Dict]:
        return self._kernel.get("calls_recordings") or []

    def save_recordings(self, recordings: List[Dict]) -> None:
        self._kernel.write("calls_recordings", recordings)

    # ── 话术模板 ──────────────────────────────────

    def get_scripts(self) -> List[Dict]:
        return self._kernel.get("calls_scripts") or []

    def save_scripts(self, scripts: List[Dict]) -> None:
        self._kernel.write("calls_scripts", scripts)

    # ── 通话分析 ──────────────────────────────────

    def get_analyses(self) -> List[Dict]:
        return self._kernel.get("calls_analyses") or []

    def save_analyses(self, analyses: List[Dict]) -> None:
        self._kernel.write("calls_analyses", analyses)


# ── 获取存储实例 ────────────────────────────────────────

_global_calls_storage: Optional[CallsStorage] = None

def get_calls_kernel(storage_dir: Optional[str] = None) -> CallsStorage:
    """获取通话与录音存储内核"""
    global _global_calls_storage
    if _global_calls_storage is None:
        from gavvy_salesmaster.core.storage.db import get_kernel
        kernel = get_kernel(storage_dir)
        _global_calls_storage = CallsStorage(kernel)
    return _global_calls_storage
