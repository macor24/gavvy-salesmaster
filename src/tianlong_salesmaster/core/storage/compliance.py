"""tianlong_salesmaster.core.storage.compliance — 数据合规模块

《个人信息保护法》合规实现：
  1. 数据分类 — 区分 PII（个人身份信息）和业务数据
  2. 数据脱敏 — 存储时自动脱敏 PII 字段
  3. 留存策略 — 按类别设置保存期限，到期自动清理
  4. 审计日志 — 记录数据访问和导出操作

用法:
    from .compliance import ComplianceGuard, mask_pii, PII_CLASSIFICATION
    guard = ComplianceGuard()

    # 脱敏后再存
    sanitized = guard.sanitize_lead(lead_dict)

    # 清理过期数据
    cleaned = guard.purge_expired(all_data)
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════
# 1. PII 分类定义
# ═══════════════════════════════════════════════════════

# 字段路径 → {敏感等级, 脱敏方式, 合规依据}
PII_CLASSIFICATION: Dict[str, Dict] = {
    # L3: 直接标识符（脱敏级别最高）
    "phone":     {"level": 3, "method": "mask_middle",   "law": "个保法第28条-敏感个人信息"},
    "mobile":    {"level": 3, "method": "mask_middle",   "law": "个保法第28条-敏感个人信息"},
    "email":     {"level": 3, "method": "mask_email",    "law": "个保法第28条-敏感个人信息"},
    "id_card":   {"level": 3, "method": "mask_id_card",  "law": "个保法第28条-敏感个人信息"},
    "wechat":    {"level": 3, "method": "mask_prefix",   "law": "个保法第28条-敏感个人信息"},
    "address":   {"level": 3, "method": "mask_address",  "law": "个保法第28条-敏感个人信息"},

    # L2: 间接标识符（脱敏）
    "contact":   {"level": 2, "method": "mask_prefix",   "law": "个保法第17条-个人信息"},
    "company":   {"level": 1, "method": "partial",       "law": "企业信息（非个人）"},
    "name":      {"level": 2, "method": "mask_name",     "law": "个保法第17条-个人信息"},
    "lead_name": {"level": 2, "method": "mask_name",     "law": "个保法第17条-个人信息"},
    "customer_name": {"level": 2, "method": "mask_name", "law": "个保法第17条-个人信息"},

    # L1: 业务信息（低敏感，只需标记）
    "product_info": {"level": 1, "method": "none",       "law": "企业信息"},
    "description":  {"level": 1, "method": "none",       "law": "企业信息"},
    "industry":     {"level": 1, "method": "none",       "law": "企业信息"},
    "notes":        {"level": 1, "method": "none",       "law": "企业信息（备注可能含PII）"},
}

# 递归检测的嵌套路径
PII_NESTED_PATHS = [
    "info.contact", "info.phone", "info.email",
    "info.company", "info.address",
    "private.contact", "private.email",
]


# ═══════════════════════════════════════════════════════
# 2. 脱敏函数
# ═══════════════════════════════════════════════════════

def mask_pii(value: Any, method: str) -> Any:
    """按指定方法脱敏一个值。非字符串类型原样返回。"""
    if not isinstance(value, str) or not value:
        return value

    if method == "none":
        return value
    elif method == "mask_middle":
        return _mask_middle(value)
    elif method == "mask_prefix":
        return _mask_prefix(value)
    elif method == "mask_email":
        return _mask_email(value)
    elif method == "mask_id_card":
        return _mask_id_card(value)
    elif method == "mask_address":
        return _mask_address(value)
    elif method == "mask_name":
        return _mask_name(value)
    elif method == "partial":
        return _partial_mask(value)
    return value


def _mask_middle(s: str) -> str:
    """13812345678 → 138****5678"""
    if len(s) <= 3:
        return s[0] + "**" if len(s) > 1 else s
    visible_start = min(3, len(s) - 4)
    visible_end = 4
    return s[:visible_start] + "*" * (len(s) - visible_start - visible_end) + s[-visible_end:]


def _mask_prefix(s: str) -> str:
    """wechat_abc → wec*****"""
    if len(s) <= 4:
        return s[0] + "***" if len(s) > 1 else s
    return s[:3] + "*" * (len(s) - 3)


def _mask_email(s: str) -> str:
    """user@example.com → u***@example.com"""
    parts = s.split("@", 1)
    if len(parts) != 2:
        return _mask_prefix(s)
    local, domain = parts
    if len(local) <= 2:
        return local[0] + "***@" + domain
    return local[0] + "***@" + domain


def _mask_id_card(s: str) -> str:
    """110101199001011234 → 110101********1234"""
    s = s.replace(" ", "")
    if len(s) < 8:
        return _mask_middle(s)
    return s[:6] + "*" * (len(s) - 10) + s[-4:]


def _mask_address(s: str) -> str:
    """北京市海淀区中关村大街1号 → 北京市海淀区****"""
    if len(s) <= 6:
        return s[:2] + "**"
    return s[:6] + "**"


def _mask_name(s: str) -> str:
    """张三 → 张*，李四 → 李*，王小明 → 王**"""
    if not s:
        return s
    if len(s) <= 2:
        return s[0] + "*"
    return s[0] + "*" * (len(s) - 1)


def _partial_mask(s: str) -> str:
    """深圳XX科技 → 深圳**科技 (保留首尾)")
    """
    if len(s) <= 4:
        return _mask_name(s)
    return s[:2] + "*" * (len(s) - 4) + s[-2:]


# ═══════════════════════════════════════════════════════
# 3. 留存策略
# ═══════════════════════════════════════════════════════

@dataclass
class RetentionPolicy:
    """数据留存策略"""
    # 各集合保存天数（0=永久）
    leads: int = 365          # Lead 数据 1 年
    sessions: int = 180        # 会话记录 6 个月
    scores: int = 365          # 评分历史 1 年
    insights: int = 365        # 洞察记录 1 年
    safety_logs: int = 90      # 安全日志 3 个月
    product_config: int = 0    # 产品配置永久
    product_pricing: int = 0   # 定价配置永久
    stats_cache: int = 7       # 统计缓存 7 天

    @classmethod
    def default(cls) -> RetentionPolicy:
        return cls()

    def get_days(self, collection: str) -> int:
        return getattr(self, collection, 0)

    def to_dict(self) -> Dict:
        from dataclasses import asdict
        return asdict(self)


# ═══════════════════════════════════════════════════════
# 4. 合规守卫
# ═══════════════════════════════════════════════════════

class ComplianceGuard:
    """数据合规守卫 — 脱敏、留存、审计"""

    def __init__(self, retention: Optional[RetentionPolicy] = None,
                 enabled: bool = True):
        self.retention = retention or RetentionPolicy.default()
        self._enabled = enabled
        self._audit_log: List[Dict] = []
        self._audit_lock = threading.Lock()

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """启用/禁用合规守卫（用于测试或调试）。"""
        self._enabled = enabled

    # ── 数据脱敏 ──

    def sanitize_lead(self, lead: Dict) -> Dict:
        """对 lead 字典中的 PII 字段脱敏（仅 L2+ 级别）。"""
        if not self._enabled:
            return lead
        result = dict(lead)
        for field, info in PII_CLASSIFICATION.items():
            if field in result and result[field] and info["level"] >= 2:
                result[field] = mask_pii(result[field], info["method"])
        # 递归检查嵌套字段
        for path in PII_NESTED_PATHS:
            parts = path.split(".")
            val = self._get_nested(result, parts)
            if val and isinstance(val, str):
                info = PII_CLASSIFICATION.get(parts[-1])
                if info:
                    self._set_nested(result, parts, mask_pii(val, info["method"]))
        return result

    def sanitize_session(self, session: Dict) -> Dict:
        """对 session 中的客户信息脱敏。"""
        if not self._enabled:
            return session
        result = dict(session)
        # 脱敏 lead_name / customer_name
        for name_field in ["lead_name", "customer_name"]:
            if name_field in result and result[name_field]:
                result[name_field] = mask_pii(result[name_field], "mask_name")
        # 脱敏消息内容中的 PII（标记但不能改内容本身）
        result["_pii_checked"] = True
        return result

    def sanitize_safety_log(self, log: Dict) -> Dict:
        """对安全日志中的客户名脱敏。"""
        if not self._enabled:
            return log
        result = dict(log)
        for field in ["customer", "agent"]:
            if field in result and result[field]:
                result[field] = mask_pii(result[field], "mask_name")
        return result

    def sanitize_product_config(self, config: Dict) -> Dict:
        """产品配置本身不含 PII，只需标记。"""
        if not self._enabled:
            return config
        return {**config, "_pii_checked": True}

    def sanitize_value(self, value: Any, field_hint: str = "") -> Any:
        """对任意值按字段名脱敏。"""
        if field_hint in PII_CLASSIFICATION:
            return mask_pii(value, PII_CLASSIFICATION[field_hint]["method"])
        return value

    # ── 字段是否包含 PII ──

    @staticmethod
    def contains_pii(data: Dict) -> List[str]:
        """检查字典中是否包含 PII 字段，返回匹配字段列表。"""
        found = []
        for field in PII_CLASSIFICATION:
            if field in data and data[field]:
                info = PII_CLASSIFICATION[field]
                if info["level"] >= 2:  # L2+ 才算 PII
                    found.append(field)
        return found

    @staticmethod
    def pii_fields_exposed(data: Dict) -> List[str]:
        """返回当前字典中仍然暴露的 PII 字段。"""
        exposed = []
        for field in PII_CLASSIFICATION:
            if field in data and data[field]:
                info = PII_CLASSIFICATION[field]
                if info["level"] >= 2:
                    # 检查是否已经脱敏（* 出现表示已脱敏）
                    if isinstance(data[field], str) and "*" not in data[field]:
                        exposed.append(field)
        return exposed

    # ── 留存策略执行 ──

    def is_expired(self, timestamp: str, max_days: int) -> bool:
        """检查一个时间戳是否已超过最大保留天数。"""
        if max_days <= 0:
            return False  # 0 = 永久
        if not timestamp:
            return False
        try:
            dt = datetime.fromisoformat(timestamp)
            age = datetime.now() - dt
            return age.days > max_days
        except (ValueError, TypeError):
            return False

    def purge_expired(self, collection: str, data: Any) -> Any:
        """清理集合中过期的数据。"""
        max_days = self.retention.get_days(collection)
        if max_days <= 0:
            return data  # 永久保留

        if isinstance(data, dict):
            cleaned = {}
            for key, item in data.items():
                ts = item.get("updated_at") or item.get("created_at") or item.get("timestamp", "")
                if not self.is_expired(ts, max_days):
                    cleaned[key] = item
            return cleaned
        elif isinstance(data, list):
            cleaned = []
            for item in data:
                ts = item.get("updated_at") or item.get("created_at") or item.get("timestamp", "")
                if not self.is_expired(ts, max_days):
                    cleaned.append(item)
            return cleaned
        return data

    # ── 审计日志 ──

    def log_access(self, operation: str, collection: str,
                   entity_id: str = "", user: str = "system",
                   detail: str = "") -> None:
        """记录数据访问。"""
        with self._audit_lock:
            self._audit_log.append({
                "timestamp": datetime.now().isoformat(),
                "user": user,
                "operation": operation,
                "collection": collection,
                "entity_id": entity_id,
                "detail": detail,
            })

    def log_export(self, collection: str, count: int,
                   user: str = "system", format: str = "json") -> None:
        """记录数据导出（个保法要求的导出审计）。"""
        self.log_access("export", collection, user=user,
                        detail=f"导出了 {count} 条 {collection} 数据 ({format})")

    def log_delete(self, collection: str, entity_id: str,
                   user: str = "system", reason: str = "") -> None:
        """记录数据删除。"""
        self.log_access("delete", collection, entity_id, user,
                        detail=f"删除原因: {reason or '用户请求'}")

    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """获取最近的审计日志。"""
        with self._audit_lock:
            return list(self._audit_log[-limit:])

    def clear_audit_log(self) -> None:
        """清空审计日志（仅管理员操作）。"""
        with self._audit_lock:
            self._audit_log.clear()

    # ── 数据保留声明的报告 ──

    def compliance_report(self) -> Dict:
        """生成合规状态报告。"""
        return {
            "pii_classification_count": len(PII_CLASSIFICATION),
            "pii_levels": {
                "L3_direct_identifiers": sum(
                    1 for v in PII_CLASSIFICATION.values() if v["level"] == 3
                ),
                "L2_indirect_identifiers": sum(
                    1 for v in PII_CLASSIFICATION.values() if v["level"] == 2
                ),
                "L1_business_info": sum(
                    1 for v in PII_CLASSIFICATION.values() if v["level"] == 1
                ),
            },
            "retention_policy": self.retention.to_dict(),
            "audit_log_count": len(self._audit_log),
            "compliance_basis": [
                "个人信息保护法 第17条 — 个人信息处理规则",
                "个人信息保护法 第28条 — 敏感个人信息",
                "个人信息保护法 第47条 — 删除权",
                "个人信息保护法 第55条 — 个人信息保护影响评估",
            ],
            "generated_at": datetime.now().isoformat(),
        }

    # ── 内部工具 ──

    @staticmethod
    def _get_nested(d: Dict, parts: List[str]) -> Any:
        """递归获取嵌套字典值。"""
        val = d
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p)
            else:
                return None
        return val

    @staticmethod
    def _set_nested(d: Dict, parts: List[str], value: Any) -> None:
        """递归设置嵌套字典值。"""
        val = d
        for p in parts[:-1]:
            if p not in val or not isinstance(val[p], dict):
                val[p] = {}
            val = val[p]
        val[parts[-1]] = value


# ── 全局单例 ──

_global_guard: Optional[ComplianceGuard] = None
_guard_lock = threading.Lock()


def get_compliance_guard() -> ComplianceGuard:
    global _global_guard
    if _global_guard is None:
        with _guard_lock:
            if _global_guard is None:
                _global_guard = ComplianceGuard()
    return _global_guard
