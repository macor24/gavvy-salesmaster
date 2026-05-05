"""tianlong_salesmaster.crm_pkg.quotes.db — 报价与合同存储接口

封装对数据库的访问，提供统一的存储接口。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class QuotesStorage:
    """报价与合同存储接口"""

    def __init__(self, kernel):
        self._kernel = kernel

    # ── 产品管理 ──────────────────────────────────

    def get_products(self) -> List[Dict]:
        return self._kernel.get("quotes_products") or []

    def save_products(self, products: List[Dict]) -> None:
        self._kernel.write("quotes_products", products)

    # ── 报价管理 ──────────────────────────────────

    def get_quotes(self) -> List[Dict]:
        return self._kernel.get("quotes_quotes") or []

    def save_quotes(self, quotes: List[Dict]) -> None:
        self._kernel.write("quotes_quotes", quotes)

    # ── 合同管理 ──────────────────────────────────

    def get_contracts(self) -> List[Dict]:
        return self._kernel.get("quotes_contracts") or []

    def save_contracts(self, contracts: List[Dict]) -> None:
        self._kernel.write("quotes_contracts", contracts)

    # ── 模板管理 ──────────────────────────────────

    def get_quote_templates(self) -> List[Dict]:
        return self._kernel.get("quotes_quote_templates") or []

    def save_quote_templates(self, templates: List[Dict]) -> None:
        self._kernel.write("quotes_quote_templates", templates)

    def get_contract_templates(self) -> List[Dict]:
        return self._kernel.get("quotes_contract_templates") or []

    def save_contract_templates(self, templates: List[Dict]) -> None:
        self._kernel.write("quotes_contract_templates", templates)


# ── 获取存储实例 ────────────────────────────────────────

_global_quotes_storage: Optional[QuotesStorage] = None

def get_quotes_kernel(storage_dir: Optional[str] = None) -> QuotesStorage:
    """获取报价与合同存储内核"""
    global _global_quotes_storage
    if _global_quotes_storage is None:
        from tianlong_salesmaster.core.storage.db import get_kernel
        kernel = get_kernel(storage_dir)
        _global_quotes_storage = QuotesStorage(kernel)
    return _global_quotes_storage
