"""SentriKit_salesmaster.core.enterprise_client — 企业版 SaaS API 客户端

统一转发到 SentriKit 的 enterprise_client。

所有调用服务端 AI 能力的模块，通过 SentriKit 的统一客户端实现。

社区版（无 API Key）：返回模板/空结果 + 升级提示
企业版（有 API Key）：HTTP 调用服务端 API

API Key 检测链：SENTRIKIT_API_KEY > TIANLONG_API_KEY > 配置文件
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ── 统一引用 SentriKit 的企业版客户端 ─────────────

_HAS_SENTRIKIT_CLIENT = False
try:
    from tianlong.enterprise_client import (
        SentriKitEnterprise,
        is_enterprise as _sk_is_enterprise,
        detect_api_key as _sk_detect_api_key,
    )
    _HAS_SENTRIKIT_CLIENT = True
except ImportError:
    pass


# ── 升级提示（保持自包含） ───────────────────────

UPGRADE_HINT = (
    "\n\n---\n💡 **需要企业版解锁完整 AI 智能能力？**\n"
    "当前为 MIT 社区版演示模式。企业版提供：\n"
    "- ✅ AI 驱动的智能对话（DeepSeek/通义千问 集成）\n"
    "- ✅ 核心 Prompt 工程驱动 Agent 分析\n"
    "- ✅ 无限 Lead 管理与多 Agent 编排\n"
    "- ✅ 学习记忆库与技能进化引擎\n"
    "- ✅ 服务端持续优化，无需升级本地代码\n"
    "获取 API Key：https://sentrikit.com\n"
)


# ── API Key 检测 ────────────────────────────────

def detect_api_key() -> str:
    """检测 API Key：优先用 SentriKit 的检测，否则自己查"""
    if _HAS_SENTRIKIT_CLIENT:
        key = _sk_detect_api_key()
        if key:
            return key
    key = os.environ.get("SENTRIKIT_API_KEY")
    if key:
        return key
    return os.environ.get("TIANLONG_API_KEY", "")


def is_enterprise() -> bool:
    """检查是否为企业版"""
    if _HAS_SENTRIKIT_CLIENT:
        return _sk_is_enterprise()
    return bool(detect_api_key())


# ── 配置 ─────────────────────────────────────────

ENTERPRISE_API_BASE = "https://api.sentrikit.com/v1"


@dataclass
class EnterpriseConfig:
    """企业版 API 配置"""
    api_key: str = ""
    api_base: str = ENTERPRISE_API_BASE
    timeout: float = 30.0

    @property
    def is_enterprise(self) -> bool:
        return bool(self.api_key)

    @classmethod
    def from_env(cls) -> "EnterpriseConfig":
        return cls(
            api_key=detect_api_key(),
            api_base=os.environ.get("SENTRIKIT_API_BASE", ENTERPRISE_API_BASE),
        )

    @classmethod
    def from_config(cls, api_key: str = "", api_base: str = "") -> "EnterpriseConfig":
        return cls(
            api_key=api_key or detect_api_key(),
            api_base=api_base or os.environ.get("SENTRIKIT_API_BASE", ENTERPRISE_API_BASE),
        )


# ── HTTP API 客户端 ─────────────────────────────


class EnterpriseAPIClient:
    """企业版 API 客户端（社区版返回模板降级结果）

    如果 SentriKit 已安装，代理其 SentriKitEnterprise 客户端；
    否则使用本地简化实现。
    """

    def __init__(self, config: Optional[EnterpriseConfig] = None):
        self.config = config or EnterpriseConfig.from_env()
        self._sk_client: Optional[SentriKitEnterprise] = None
        if _HAS_SENTRIKIT_CLIENT and self.config.is_enterprise:
            try:
                self._sk_client = SentriKitEnterprise(
                    api_key=self.config.api_key,
                    api_base=self.config.api_base,
                )
            except Exception:
                pass

    # ── 洞察引擎 ───────────────────────────────

    def analyze_market(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """市场洞察分析"""
        if not self.config.is_enterprise:
            company = lead_data.get("company", "未知公司")
            return {
                "insight": f"市场潜力分析（模板）：{company} 在所属行业中具有{'高' if len(company) > 2 else '中'}等发展潜力。",
                "confidence": 0.3,
                "mode": "template",
                "hint": UPGRADE_HINT,
            }
        return self._call_api("/insight/market-analysis", {"lead_data": lead_data})

    def analyze_performance(self, history: List[Dict]) -> Dict[str, Any]:
        """绩效洞察分析"""
        if not self.config.is_enterprise:
            total = len(history)
            success = len([h for h in history if h.get("status") == "success"])
            return {
                "total_episodes": total,
                "success_rate": round(success / total, 2) if total else 0,
                "insights": [f"成功率 {success}/{total}"],
                "top_insight": f"成功率 {success/total:.0%}" if total else "无数据",
                "performance_trend": "improving" if success > total * 0.7 else "stable",
                "mode": "template",
                "hint": UPGRADE_HINT,
            }
        return self._call_api("/insight/performance", {"history": history})

    # ── 安全守卫 ───────────────────────────────

    def check_safety(self, content: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """安全检查"""
        if not self.config.is_enterprise:
            sensitive = ["违法", "行贿", "欺诈", "贿赂", "走私", "洗钱"]
            for word in sensitive:
                if word in content:
                    return {"safe": False, "reason": f"包含敏感词: {word}", "mode": "basic_filter"}
            return {"safe": True, "mode": "basic_filter", "hint": UPGRADE_HINT}
        return self._call_api("/safety/check", {"content": content, "context": context or {}})

    # ── 线索评分 ───────────────────────────────

    def score_lead(self, lead_info: Dict[str, Any]) -> Dict[str, Any]:
        """智能线索评分"""
        if not self.config.is_enterprise:
            return self._local_score(lead_info)
        return self._call_api("/scorer/lead", {"lead_info": lead_info})

    @staticmethod
    def _local_score(lead_info: Dict) -> Dict:
        score = 0.3
        industry = lead_info.get("industry", "")
        high_value = ["AI Agent", "LLM", "金融科技", "医疗AI", "人工智能", "机器人"]
        for hv in high_value:
            if hv in industry:
                score = 0.5
                break
        return {
            "score": score,
            "confidence": 0.6 + score * 0.3,
            "factors": {"industry_match": score - 0.3 if score > 0.3 else 0},
            "summary": f"综合评分 {score:.0%}（模板）",
            "mode": "template",
            "hint": UPGRADE_HINT,
        }

    # ── 会话记忆 ───────────────────────────────

    def get_session_memory(self, session_id: str) -> Dict[str, Any]:
        if not self.config.is_enterprise:
            return {"data": [], "mode": "template"}
        return self._call_api("/session/memory", {"session_id": session_id})

    def set_session_memory(self, session_id: str, data: dict) -> bool:
        if not self.config.is_enterprise:
            return False
        resp = self._call_api("/session/memory", {"session_id": session_id, "data": data}, method="PUT")
        return resp.get("status") == "ok"

    # ── API 配置 ───────────────────────────────

    def get_api_config(self) -> Dict[str, Any]:
        if not self.config.is_enterprise:
            return {"configured": False, "providers": [], "mode": "template"}
        return self._call_api("/config", {})

    def is_llm_ready(self) -> bool:
        if not self.config.is_enterprise:
            return False
        resp = self._call_api("/health", {})
        return resp.get("llm_ready", False)

    # ── Quickstart ─────────────────────────────

    def get_quickstart_industries(self) -> Dict[str, Any]:
        """获取行业模板（社区版返回内置模板）"""
        if not self.config.is_enterprise:
            return {
                "电商": {"pricing": {"base": 299, "enterprise": 999},
                         "scripts": ["您好，我们是做电商解决方案的..."],
                         "competitors": ["有赞", "微盟"]},
                "SaaS企业服务": {"pricing": {"base": 499, "enterprise": 1999},
                               "scripts": ["了解到贵公司在使用XX系统，我们..."],
                               "competitors": ["钉钉", "飞书"]},
                "AI/科技": {"pricing": {"base": 999, "enterprise": 4999},
                          "scripts": ["我们在AI Agent领域有成熟方案..."],
                          "competitors": ["OpenAI", "LangChain"]},
            }
        return self._call_api("/quickstart/industries", {})

    # ── 内部 API 调用 ─────────────────────────

    def _call_api(self, path: str, data: Dict[str, Any],
                  method: str = "POST") -> Dict[str, Any]:
        """发起 HTTP API 调用（无 httpx 依赖时降级）"""
        try:
            import httpx
        except ImportError:
            return {"error": "请安装 httpx: pip install httpx", "mode": "error"}
        try:
            url = f"{self.config.api_base.rstrip('/')}{path}"
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }
            with httpx.Client(timeout=self.config.timeout) as client:
                if method == "POST":
                    resp = client.post(url, headers=headers, json=data)
                elif method == "PUT":
                    resp = client.put(url, headers=headers, json=data)
                else:
                    resp = client.get(url, headers=headers, params=data)
                resp.raise_for_status()
                result = resp.json()
                result["mode"] = "enterprise_api"
                return result
        except Exception as e:
            return {"error": str(e), "mode": "error"}
