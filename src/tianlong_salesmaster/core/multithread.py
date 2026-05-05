"""SentriKit.sales.multithread — 拆分自 master.py"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional




class CustomerRole(Enum):
    """客户角色类型（多角色决策链）"""
    GATEKEEPER = "gatekeeper"
    USER = "user"
    INFLUENCER = "influencer"
    DECISION_MAKER = "decision_maker"
    UNKNOWN = "unknown"


@dataclass
class CustomerContact:
    """客户联系人信息"""
    name: str = ""
    role: CustomerRole = CustomerRole.UNKNOWN
    department: str = ""
    concerns: list = None
    decision_power: float = 0.0
    relationship: float = 0.3
    last_touch: str = ""


class MultiThreadManager:
    """多角色决策链管理与跨会话记忆（§4-5）

    能力：
    4. 多角色决策链渗透与联盟构建
    5. 跨渠道跨会话无缝记忆
    """

    def __init__(self):
        self._contacts: Dict[str, CustomerContact] = {}

    def identify_role(self, title: str, department: str) -> CustomerRole:
        """自动识别客户角色。"""
        title_lower = title.lower()
        dept_lower = department.lower()

        if any(k in title_lower for k in ["总裁", "ceo", "总经理", "vp", "director"]):
            return CustomerRole.DECISION_MAKER
        if any(k in dept_lower for k in ["采购", "procurement", "purchasing"]):
            return CustomerRole.GATEKEEPER
        if any(k in title_lower for k in ["经理", "主管", "manager", "lead", "head"]):
            return CustomerRole.INFLUENCER
        if any(k in dept_lower for k in ["技术", "研发", "工程", "产品", "tech", "eng"]):
            return CustomerRole.USER
        return CustomerRole.UNKNOWN

    def add_contact(self, name: str, title: str, department: str) -> CustomerContact:
        """添加联系人。"""
        contact = CustomerContact(
            name=name,
            role=self.identify_role(title, department),
            department=department,
            last_touch=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )
        self._contacts[name] = contact
        return contact

    def suggest_alliance_strategy(self, contact_name: str) -> str:
        """为特定联系人生成联盟构建策略。"""
        contact = self._contacts.get(contact_name)
        if not contact:
            return ""

        if contact.role == CustomerRole.USER:
            return (
                f"建议主动为{contact.name}准备一份ROI测算报告，"
                f"方便他向决策层汇报时使用。这样既能帮助他内部推销，"
                f"也能加深联盟关系。"
            )
        elif contact.role == CustomerRole.GATEKEEPER:
            return (
                f"对{contact.name}保持透明和尊重。"
                f"提前提供所需的所有资质材料，降低他的筛选成本。"
            )
        elif contact.role == CustomerRole.INFLUENCER:
            return (
                f"与{contact.name}进行技术细节的深入交流，"
                f"获取他的认可和支持，让他成为内部推荐人。"
            )
        elif contact.role == CustomerRole.DECISION_MAKER:
            return (
                f"为{contact.name}准备高层视角的商业价值分析，"
                f"聚焦ROI、竞争差异化和战略价值。"
            )
        return ""

    def find_internal_champion(self) -> Optional[str]:
        """寻找内部支持者（最有潜力成为联盟对象的联系人）。"""
        best = None
        best_score = 0
        for name, c in self._contacts.items():
            score = c.relationship * 0.6 + c.decision_power * 0.4
            if score > best_score:
                best_score = score
                best = name
        return best


