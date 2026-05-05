"""SentriKit_salesmaster.team_pkg.team.session — 会话记忆

社区版：本地内存存储
企业版：调用服务端 API（需 SentriKit_API_KEY）
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from SentriKit_salesmaster.core.enterprise_client import EnterpriseAPIClient, EnterpriseConfig


# ── 社区版本地内存存储 ──────────────────────────

_SESSION_MEMORY: Dict[str, List[Dict]] = {}


def get_session_memory(config: Optional[EnterpriseConfig] = None) -> Any:
    """获取会话记忆

    社区版：本地内存
    企业版：服务端持久化
    """
    client = EnterpriseAPIClient(config)
    if client.config.is_enterprise:
        return EnterpriseSessionMemory(client)
    return LocalSessionMemory()


class LocalSessionMemory:
    """社区版本地会话记忆"""

    def get(self, session_id: str) -> List[Dict]:
        return _SESSION_MEMORY.get(session_id, [])

    def set(self, session_id: str, data: List[Dict]) -> None:
        _SESSION_MEMORY[session_id] = data

    def clear(self, session_id: str = "") -> None:
        if session_id:
            _SESSION_MEMORY.pop(session_id, None)
        else:
            _SESSION_MEMORY.clear()


class EnterpriseSessionMemory:
    """企业版服务端会话记忆"""

    def __init__(self, client: EnterpriseAPIClient):
        self._client = client

    def get(self, session_id: str) -> List[Dict]:
        result = self._client.get_session_memory(session_id)
        return result.get("data", [])

    def set(self, session_id: str, data: List[Dict]) -> None:
        self._client.set_session_memory(session_id, {"data": data})

    def clear(self, session_id: str = "") -> None:
        pass


__all__ = ["get_session_memory", "LocalSessionMemory", "EnterpriseSessionMemory"]
