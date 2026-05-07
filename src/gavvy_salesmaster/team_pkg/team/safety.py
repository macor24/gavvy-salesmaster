"""gavvy_salesmaster.team_pkg.team.safety — 安全守卫

社区版：基础本地关键词过滤
企业版：调用服务端 LLM API 智能安全检查（需 SentriKit_API_KEY）
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from gavvy_salesmaster.core.enterprise_client import EnterpriseAPIClient, EnterpriseConfig, UPGRADE_HINT


class SafetyMode(Enum):
    CONSERVATIVE = "conservative"
    OPEN = "open"
    CUSTOM = "custom"


@dataclass
class SafetyLog:
    """安全日志"""
    action: str = ""
    reason: str = ""
    passed: bool = False
    timestamp: str = ""


class SafetyGuard:
    """安全守卫

    社区版：关键词过滤（敏感词、金额阈值）
    企业版：调用服务端 LLM 进行智能安全分析
    """

    SENSITIVE_ACTIONS = {"deal", "quote", "contract", "payment", "price"}
    SENSITIVE_WORDS = ["违法", "行贿", "欺诈", "贿赂", "走私", "洗钱", "毒品", "赌博"]

    def __init__(self, mode: SafetyMode = SafetyMode.CONSERVATIVE,
                 config: Optional[EnterpriseConfig] = None):
        self.mode = mode
        self.logs: List[SafetyLog] = []
        self._client = EnterpriseAPIClient(config)

    @property
    def is_enterprise(self) -> bool:
        return self._client.config.is_enterprise

    def check_action(self, action: str, output_text: str = "",
                     price_ceiling: float = 50000,
                     discount_floor: float = 0.7) -> bool:
        """检查动作是否安全"""
        if self.is_enterprise:
            result = self._client.check_safety(output_text, {
                "action": action,
                "mode": self.mode.value,
                "price_ceiling": price_ceiling,
            })
            passed = result.get("safe", True)
        else:
            passed = self._local_check(action, output_text, price_ceiling)

        self.logs.append(SafetyLog(
            action=action,
            reason=f"mode={self.mode.value}, passed={passed}",
            passed=passed,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ))
        return passed

    def _local_check(self, action: str, output_text: str,
                     price_ceiling: float) -> bool:
        """本地基础安全检查"""
        action_lower = action.lower()
        is_sensitive = any(kw in action_lower for kw in self.SENSITIVE_ACTIONS)

        # 关键词过滤
        for word in self.SENSITIVE_WORDS:
            if word in output_text:
                return False

        if self.mode == SafetyMode.CONSERVATIVE:
            return not is_sensitive
        elif self.mode == SafetyMode.OPEN:
            return True
        else:
            # CUSTOM 模式
            if is_sensitive:
                amount = self._extract_amount(output_text)
                if amount > price_ceiling:
                    return False
            return True

    @staticmethod
    def _extract_amount(text: str) -> float:
        """从文本中提取金额"""
        import re
        amounts = re.findall(r'[¥￥](\d+(?:\.\d+)?)', text)
        if not amounts:
            amounts = re.findall(r'(\d+(?:\.\d+)?)\s*万?元', text)
        return max((float(a) for a in amounts), default=0.0)


__all__ = ["SafetyGuard", "SafetyMode", "SafetyLog"]
