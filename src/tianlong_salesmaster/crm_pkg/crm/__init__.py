"""SentriKit_salesmaster.crm_pkg.crm — CRM 系统集成

客户关系管理核心模块，包含：

数据模型:
  - Customer   —— 客户（公司/个人）
  - Contact    —— 联系人
  - Deal       —— 商机
  - Contract   —— 合同
  - Activity   —— 活动记录

引擎:
  - CRMManager —— 统一管理所有CRM数据，持久化到存储层
"""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from SentriKit_salesmaster.core.storage.db import get_kernel

# ── 集合名称 ──────────────────────────────────────

_COLL_CUSTOMERS = "crm_customers"
_COLL_CONTACTS = "crm_contacts"
_COLL_DEALS = "crm_deals"
_COLL_CONTRACTS = "crm_contracts"
_COLL_ACTIVITIES = "crm_activities"

_COLL_ALL = [_COLL_CUSTOMERS, _COLL_CONTACTS, _COLL_DEALS,
             _COLL_CONTRACTS, _COLL_ACTIVITIES]


# ═══════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════


@dataclass
class Customer:
    """客户"""
    id: str = ""
    name: str = ""
    company: str = ""
    industry: str = ""
    source: str = ""            # 来源：manual / widget / csv / import
    stage: str = "lead"         # lead / prospect / qualified / customer / churned
    tags: List[str] = field(default_factory=list)
    phone: str = ""
    email: str = ""
    address: str = ""
    website: str = ""
    notes: str = ""
    score: int = 0              # 0-100
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"cust_{uuid.uuid4().hex[:12]}"
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["tags"] = list(self.tags)
        return d

    @staticmethod
    def from_dict(d: Dict) -> Customer:
        return Customer(**{k: v for k, v in d.items()
                           if k in Customer.__dataclass_fields__})

    @property
    def stage_label(self) -> str:
        labels = {
            "lead": "潜在客户", "prospect": "意向客户",
            "qualified": "合格客户", "customer": "成交客户",
            "churned": "流失客户",
        }
        return labels.get(self.stage, self.stage)


@dataclass
class Contact:
    """联系人"""
    id: str = ""
    customer_id: str = ""
    name: str = ""
    role: str = ""              # 职位
    phone: str = ""
    email: str = ""
    wechat: str = ""
    is_primary: bool = False    # 是否主要联系人
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"cont_{uuid.uuid4().hex[:10]}"
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict) -> Contact:
        return Contact(**{k: v for k, v in d.items()
                          if k in Contact.__dataclass_fields__})


@dataclass
class Deal:
    """商机"""
    id: str = ""
    customer_id: str = ""
    title: str = ""
    stage: str = "discovery"    # discovery / proposal / negotiation / closed_won / closed_lost
    amount: float = 0.0
    probability: int = 0        # 0-100
    expected_close: str = ""
    product_info: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"deal_{uuid.uuid4().hex[:10]}"
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict) -> Deal:
        return Deal(**{k: v for k, v in d.items()
                       if k in Deal.__dataclass_fields__})

    @property
    def stage_label(self) -> str:
        labels = {
            "discovery": "初步发现", "proposal": "方案提案",
            "negotiation": "谈判议价", "closed_won": "已成交",
            "closed_lost": "已流失",
        }
        return labels.get(self.stage, self.stage)


@dataclass
class Contract:
    """合同"""
    id: str = ""
    deal_id: str = ""
    customer_id: str = ""
    title: str = ""
    amount: float = 0.0
    status: str = "draft"       # draft / signed / ongoing / completed / terminated
    signed_date: str = ""
    start_date: str = ""
    end_date: str = ""
    content: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"ct_{uuid.uuid4().hex[:10]}"
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict) -> Contract:
        return Contract(**{k: v for k, v in d.items()
                           if k in Contract.__dataclass_fields__})

    @property
    def status_label(self) -> str:
        labels = {
            "draft": "草稿", "signed": "已签署", "ongoing": "执行中",
            "completed": "已完成", "terminated": "已终止",
        }
        return labels.get(self.status, self.status)


@dataclass
class Activity:
    """活动记录"""
    id: str = ""
    customer_id: str = ""
    contact_id: str = ""
    deal_id: str = ""
    type: str = "note"          # call / email / meeting / note / task / system
    title: str = ""
    content: str = ""
    created_by: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"act_{uuid.uuid4().hex[:10]}"
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict) -> Activity:
        return Activity(**{k: v for k, v in d.items()
                           if k in Activity.__dataclass_fields__})


# ═══════════════════════════════════════════════════════
# CRM 引擎
# ═══════════════════════════════════════════════════════


class CRMManager:
    """CRM 管理器 — 统一操作所有CRM数据"""

    def __init__(self):
        self._kernel = get_kernel()

    # ── 内部方法 ──

    def _get_all(self, collection: str) -> List[Dict]:
        data = self._kernel.get(collection)
        if not isinstance(data, list):
            return []
        return data

    def _save_all(self, collection: str, data: List[Dict]) -> None:
        self._kernel.write(collection, data)

    def _find_index(self, collection: str, item_id: str) -> int:
        items = self._get_all(collection)
        for i, item in enumerate(items):
            if item.get("id") == item_id:
                return i
        return -1

    # ── 客户 CRUD ──

    def list_customers(self, stage: str = "", limit: int = 100) -> List[Dict]:
        items = self._get_all(_COLL_CUSTOMERS)
        if stage:
            items = [c for c in items if c.get("stage") == stage]
        return items[-limit:][::-1]

    def get_customer(self, customer_id: str) -> Optional[Dict]:
        idx = self._find_index(_COLL_CUSTOMERS, customer_id)
        if idx < 0:
            return None
        items = self._get_all(_COLL_CUSTOMERS)
        return items[idx]

    def add_customer(self, customer: Customer) -> Dict:
        items = self._get_all(_COLL_CUSTOMERS)
        items.append(customer.to_dict())
        self._save_all(_COLL_CUSTOMERS, items)
        return customer.to_dict()

    def update_customer(self, customer_id: str, updates: Dict) -> Optional[Dict]:
        idx = self._find_index(_COLL_CUSTOMERS, customer_id)
        if idx < 0:
            return None
        items = self._get_all(_COLL_CUSTOMERS)
        item = items[idx]
        for k, v in updates.items():
            if k in Customer.__dataclass_fields__ and v is not None:
                item[k] = v
        item["updated_at"] = datetime.now().isoformat()
        items[idx] = item
        self._save_all(_COLL_CUSTOMERS, items)
        return item

    def delete_customer(self, customer_id: str) -> bool:
        idx = self._find_index(_COLL_CUSTOMERS, customer_id)
        if idx < 0:
            return False
        items = self._get_all(_COLL_CUSTOMERS)
        items.pop(idx)
        self._save_all(_COLL_CUSTOMERS, items)
        # 级联删除相关数据
        for coll in [_COLL_CONTACTS, _COLL_DEALS, _COLL_CONTRACTS, _COLL_ACTIVITIES]:
            related = [x for x in self._get_all(coll)
                       if x.get("customer_id") != customer_id]
            self._save_all(coll, related)
        return True

    def search_customers(self, query: str) -> List[Dict]:
        q = query.lower().strip()
        if not q:
            return self.list_customers()
        items = self._get_all(_COLL_CUSTOMERS)
        return [c for c in items
                if q in c.get("name", "").lower()
                or q in c.get("company", "").lower()
                or q in c.get("phone", "")
                or q in c.get("email", "").lower()][:30]

    def get_customer_stats(self) -> Dict:
        items = self._get_all(_COLL_CUSTOMERS)
        stages = {}
        for c in items:
            s = c.get("stage", "lead")
            stages[s] = stages.get(s, 0) + 1
        total = len(items)
        return {
            "total": total,
            "stages": stages,
            "leads": stages.get("lead", 0),
            "prospects": stages.get("prospect", 0),
            "qualified": stages.get("qualified", 0),
            "customers": stages.get("customer", 0),
            "churned": stages.get("churned", 0),
        }

    # ── 联系人 CRUD ──

    def list_contacts(self, customer_id: str = "") -> List[Dict]:
        items = self._get_all(_COLL_CONTACTS)
        if customer_id:
            items = [c for c in items if c.get("customer_id") == customer_id]
        return items

    def add_contact(self, contact: Contact) -> Dict:
        items = self._get_all(_COLL_CONTACTS)
        items.append(contact.to_dict())
        self._save_all(_COLL_CONTACTS, items)
        return contact.to_dict()

    def delete_contact(self, contact_id: str) -> bool:
        idx = self._find_index(_COLL_CONTACTS, contact_id)
        if idx < 0:
            return False
        items = self._get_all(_COLL_CONTACTS)
        items.pop(idx)
        self._save_all(_COLL_CONTACTS, items)
        return True

    # ── 商机 CRUD ──

    def list_deals(self, customer_id: str = "") -> List[Dict]:
        items = self._get_all(_COLL_DEALS)
        if customer_id:
            items = [d for d in items if d.get("customer_id") == customer_id]
        return items[::-1]

    def add_deal(self, deal: Deal) -> Dict:
        items = self._get_all(_COLL_DEALS)
        items.append(deal.to_dict())
        self._save_all(_COLL_DEALS, items)
        return deal.to_dict()

    def update_deal(self, deal_id: str, updates: Dict) -> Optional[Dict]:
        idx = self._find_index(_COLL_DEALS, deal_id)
        if idx < 0:
            return None
        items = self._get_all(_COLL_DEALS)
        item = items[idx]
        for k, v in updates.items():
            if k in Deal.__dataclass_fields__ and v is not None:
                item[k] = v
        item["updated_at"] = datetime.now().isoformat()
        items[idx] = item
        self._save_all(_COLL_DEALS, items)
        return item

    def get_deal_summary(self) -> Dict:
        items = self._get_all(_COLL_DEALS)
        total_amount = sum(d.get("amount", 0) for d in items
                           if d.get("stage") != "closed_lost")
        won = sum(1 for d in items if d.get("stage") == "closed_won")
        lost = sum(1 for d in items if d.get("stage") == "closed_lost")
        stages = {}
        for d in items:
            s = d.get("stage", "discovery")
            stages[s] = stages.get(s, 0) + 1
        return {
            "total": len(items),
            "total_pipeline": total_amount,
            "won": won,
            "lost": lost,
            "stages": stages,
        }

    # ── 合同 CRUD ──

    def list_contracts(self, customer_id: str = "") -> List[Dict]:
        items = self._get_all(_COLL_CONTRACTS)
        if customer_id:
            items = [c for c in items if c.get("customer_id") == customer_id]
        return items[::-1]

    def add_contract(self, contract: Contract) -> Dict:
        items = self._get_all(_COLL_CONTRACTS)
        items.append(contract.to_dict())
        self._save_all(_COLL_CONTRACTS, items)
        return contract.to_dict()

    def update_contract(self, contract_id: str, updates: Dict) -> Optional[Dict]:
        idx = self._find_index(_COLL_CONTRACTS, contract_id)
        if idx < 0:
            return None
        items = self._get_all(_COLL_CONTRACTS)
        item = items[idx]
        for k, v in updates.items():
            if k in Contract.__dataclass_fields__ and v is not None:
                item[k] = v
        items[idx] = item
        self._save_all(_COLL_CONTRACTS, items)
        return item

    def get_contract_summary(self) -> Dict:
        items = self._get_all(_COLL_CONTRACTS)
        total_amount = sum(c.get("amount", 0) for c in items
                           if c.get("status") in ("signed", "ongoing"))
        statuses = {}
        for c in items:
            s = c.get("status", "draft")
            statuses[s] = statuses.get(s, 0) + 1
        return {
            "total": len(items),
            "total_signed": total_amount,
            "statuses": statuses,
        }

    # ── 活动记录 ──

    def list_activities(self, customer_id: str = "", limit: int = 100) -> List[Dict]:
        items = self._get_all(_COLL_ACTIVITIES)
        if customer_id:
            items = [a for a in items if a.get("customer_id") == customer_id]
        return items[-limit:][::-1]

    def add_activity(self, activity: Activity) -> Dict:
        items = self._get_all(_COLL_ACTIVITIES)
        items.append(activity.to_dict())
        self._save_all(_COLL_ACTIVITIES, items)
        # 清理旧数据
        if len(items) > 2000:
            self._save_all(_COLL_ACTIVITIES, items[-1500:])
        return activity.to_dict()

    # ── 仪表盘摘要 ──

    def get_dashboard(self) -> Dict:
        return {
            "customers": self.get_customer_stats(),
            "deals": self.get_deal_summary(),
            "contracts": self.get_contract_summary(),
        }


# ── 全局函数 ──────────────────────────────────────

def get_crm() -> CRMManager:
    """获取 CRM 管理器实例"""
    return CRMManager()
