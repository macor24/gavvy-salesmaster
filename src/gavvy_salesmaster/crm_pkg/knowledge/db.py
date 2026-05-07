"""gavvy_salesmaster.crm_pkg.knowledge.db — 知识库存储接口

封装对数据库的访问，提供统一的存储接口。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ── 知识库存储接口 ──────────────────────────────────────

class KnowledgeStorage:
    """知识库存储接口"""

    def __init__(self, kernel):
        self._kernel = kernel

    def get_items(self) -> List[Dict]:
        """获取所有知识条目"""
        return self._kernel.get("knowledge_items") or []

    def save_items(self, items: List[Dict]) -> None:
        """保存知识条目"""
        self._kernel.write("knowledge_items", items)

    def get_categories(self) -> List[Dict]:
        """获取所有分类"""
        return self._kernel.get("knowledge_categories") or []

    def save_categories(self, categories: List[Dict]) -> None:
        """保存分类"""
        self._kernel.write("knowledge_categories", categories)

    def get_faqs(self) -> List[Dict]:
        """获取所有 FAQ"""
        return self._kernel.get("knowledge_qa") or []

    def save_faqs(self, faqs: List[Dict]) -> None:
        """保存 FAQ"""
        self._kernel.write("knowledge_qa", faqs)


# ── 获取知识库存储实例 ──────────────────────────────────────

_global_storage: Optional[KnowledgeStorage] = None


def get_kb_kernel(storage_dir: Optional[str] = None):
    """获取知识库存储内核"""
    global _global_storage
    if _global_storage is None:
        from gavvy_salesmaster.core.storage.db import get_kernel
        kernel = get_kernel(storage_dir)
        _global_storage = KnowledgeStorage(kernel)
    return _global_storage
