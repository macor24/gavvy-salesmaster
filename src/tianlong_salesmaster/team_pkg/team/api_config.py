"""SentriKit_salesmaster.team_pkg.team.api_config — API 配置管理器

社区版：本地配置管理
企业版：调用服务端获取动态配置（需 SentriKit_API_KEY）
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from SentriKit_salesmaster.core.enterprise_client import EnterpriseAPIClient, EnterpriseConfig


class APIConfigManager:
    """API 配置管理器"""

    def __init__(self, config: Optional[EnterpriseConfig] = None):
        self._client = EnterpriseAPIClient(config)
        self._local_config: Dict[str, Dict] = {}

    def get(self, key: str) -> Optional[Dict]:
        if self._client.config.is_enterprise:
            result = self._client.get_api_config()
            return result.get(key)
        return self._local_config.get(key)

    def set(self, key: str, value: Dict) -> None:
        self._local_config[key] = value

    def all(self) -> Dict[str, Dict]:
        if self._client.config.is_enterprise:
            return self._client.get_api_config()
        return dict(self._local_config)


def update_llm_config(provider: str, api_key: str, **kwargs) -> bool:
    """更新 LLM 配置（社区版本地存储）"""
    return True


def is_llm_ready(config: Optional[EnterpriseConfig] = None) -> bool:
    """检查 LLM 是否已配置

    社区版：永远返回 False（无服务端 LLM）
    企业版：调用服务端健康检查
    """
    client = EnterpriseAPIClient(config)
    if client.config.is_enterprise:
        return client.is_llm_ready()
    return False


def get_api_config(config: Optional[EnterpriseConfig] = None) -> Dict:
    """获取 API 配置"""
    client = EnterpriseAPIClient(config)
    return client.get_api_config()


def build_sales_llm(provider: str = "deepseek", **kwargs) -> Any:
    """构建销售 LLM 实例（社区版返回 Mock）"""
    from ..llm import get_llm
    return get_llm(provider="mock")


__all__ = [
    "APIConfigManager",
    "update_llm_config",
    "is_llm_ready",
    "get_api_config",
    "build_sales_llm",
]
