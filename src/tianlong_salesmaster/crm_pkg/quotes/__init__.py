"""tianlong_salesmaster.crm_pkg.quotes — 报价与合同管理系统

完整的报价管理、合同管理、产品配置功能。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set


# ── 枚举定义 ────────────────────────────────────────

class QuoteStatus(Enum):
    """报价状态"""
    DRAFT = "draft"              # 草稿
    PENDING_APPROVAL = "pending_approval"  # 待审批
    APPROVED = "approved"        # 已审批
    SENT = "sent"                # 已发送
    ACCEPTED = "accepted"        # 已接受
    REJECTED = "rejected"        # 已拒绝
    EXPIRED = "expired"          # 已过期


class ContractStatus(Enum):
    """合同状态"""
    DRAFT = "draft"              # 草稿
    PENDING_APPROVAL = "pending_approval"  # 待审批
    SIGNED = "signed"            # 已签署
    FULFILLING = "fulfilling"    # 履行中
    COMPLETED = "completed"      # 已完成
    TERMINATED = "terminated"    # 已终止


# ── 数据类型定义 ────────────────────────────────────────

@dataclass
class Product:
    """产品"""
    id: str = ""
    name: str = ""
    description: str = ""
    sku: str = ""
    unit_price: float = 0.0
    cost_price: float = 0.0
    category: str = ""
    tags: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:12]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "Product":
        return Product(**data)


@dataclass
class PriceTier:
    """价格层级"""
    id: str = ""
    name: str = ""
    min_quantity: int = 1
    discount_percent: float = 0.0
    unit_price: float = 0.0
    is_active: bool = True

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "PriceTier":
        return PriceTier(**data)


@dataclass
class QuoteItem:
    """报价明细项"""
    id: str = ""
    product_id: str = ""
    product_name: str = ""
    quantity: int = 1
    unit_price: float = 0.0
    discount_percent: float = 0.0
    tax_percent: float = 0.0
    notes: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

    @property
    def subtotal(self) -> float:
        """小计"""
        return self.quantity * self.unit_price

    @property
    def discount_amount(self) -> float:
        """折扣金额"""
        return self.subtotal * (self.discount_percent / 100)

    @property
    def total_before_tax(self) -> float:
        """税前总额"""
        return self.subtotal - self.discount_amount

    @property
    def tax_amount(self) -> float:
        """税额"""
        return self.total_before_tax * (self.tax_percent / 100)

    @property
    def total(self) -> float:
        """总额"""
        return self.total_before_tax + self.tax_amount

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "QuoteItem":
        return QuoteItem(**data)


@dataclass
class Quote:
    """报价单"""
    id: str = ""
    quote_number: str = ""
    title: str = ""
    description: str = ""
    customer_id: str = ""
    customer_name: str = ""
    customer_email: str = ""
    salesperson: str = ""
    items: List[QuoteItem] = field(default_factory=list)
    notes: str = ""
    terms: str = ""
    status: str = "draft"
    created_at: str = ""
    updated_at: str = ""
    valid_until: str = ""
    sent_at: str = ""
    accepted_at: str = ""
    related_lead_id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:12]
        if not self.quote_number:
            self.quote_number = f"Q{datetime.now().strftime('%Y%m%d')}-{self.id[:4].upper()}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    @property
    def subtotal(self) -> float:
        """小计总额"""
        return sum(item.subtotal for item in self.items)

    @property
    def total_discount(self) -> float:
        """折扣总额"""
        return sum(item.discount_amount for item in self.items)

    @property
    def total_tax(self) -> float:
        """税额总额"""
        return sum(item.tax_amount for item in self.items)

    @property
    def total_amount(self) -> float:
        """总价"""
        return sum(item.total for item in self.items)

    @property
    def is_expired(self) -> bool:
        """是否过期"""
        if not self.valid_until:
            return False
        try:
            valid = datetime.fromisoformat(self.valid_until)
            return datetime.now() > valid
        except Exception:
            return False

    def to_dict(self) -> Dict:
        data = asdict(self)
        return data

    @staticmethod
    def from_dict(data: Dict) -> "Quote":
        items_data = data.pop("items", [])
        quote = Quote(**data)
        quote.items = [QuoteItem.from_dict(item) for item in items_data]
        return quote


@dataclass
class PaymentPlan:
    """付款计划"""
    id: str = ""
    payment_number: int = 1
    description: str = ""
    amount: float = 0.0
    due_date: str = ""
    status: str = "pending"  # pending/paid/overdue
    paid_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "PaymentPlan":
        return PaymentPlan(**data)


@dataclass
class ContractItem:
    """合同明细项"""
    id: str = ""
    product_id: str = ""
    product_name: str = ""
    quantity: int = 1
    unit_price: float = 0.0
    description: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "ContractItem":
        return ContractItem(**data)


@dataclass
class Contract:
    """合同"""
    id: str = ""
    contract_number: str = ""
    title: str = ""
    description: str = ""
    customer_id: str = ""
    customer_name: str = ""
    customer_email: str = ""
    salesperson: str = ""
    items: List[ContractItem] = field(default_factory=list)
    payment_plans: List[PaymentPlan] = field(default_factory=list)
    terms: str = ""
    notes: str = ""
    status: str = "draft"
    created_at: str = ""
    updated_at: str = ""
    signed_at: str = ""
    effective_date: str = ""
    end_date: str = ""
    related_quote_id: str = ""
    related_lead_id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:12]
        if not self.contract_number:
            self.contract_number = f"C{datetime.now().strftime('%Y%m%d')}-{self.id[:4].upper()}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    @property
    def total_amount(self) -> float:
        """合同总额"""
        return sum(item.quantity * item.unit_price for item in self.items)

    def to_dict(self) -> Dict:
        data = asdict(self)
        return data

    @staticmethod
    def from_dict(data: Dict) -> "Contract":
        items_data = data.pop("items", [])
        plans_data = data.pop("payment_plans", [])
        contract = Contract(**data)
        contract.items = [ContractItem.from_dict(item) for item in items_data]
        contract.payment_plans = [PaymentPlan.from_dict(plan) for plan in plans_data]
        return contract


@dataclass
class QuoteTemplate:
    """报价模板"""
    id: str = ""
    name: str = ""
    description: str = ""
    terms: str = ""
    notes: str = ""
    default_tax_percent: float = 0.0
    is_default: bool = False
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "QuoteTemplate":
        return QuoteTemplate(**data)


@dataclass
class ContractTemplate:
    """合同模板"""
    id: str = ""
    name: str = ""
    description: str = ""
    terms: str = ""
    default_tax_percent: float = 0.0
    is_default: bool = False
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> "ContractTemplate":
        return ContractTemplate(**data)


# ── 产品管理 ────────────────────────────────────────

class ProductManager:
    """产品管理器"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_quotes_kernel
        self.db = get_quotes_kernel(storage_dir)

    def create_product(self, name: str, description: str = "",
                       sku: str = "", unit_price: float = 0.0,
                       cost_price: float = 0.0, category: str = "",
                       tags: Optional[List[str]] = None) -> Product:
        """创建产品"""
        product = Product(
            name=name,
            description=description,
            sku=sku,
            unit_price=unit_price,
            cost_price=cost_price,
            category=category,
            tags=tags or []
        )
        products = self.db.get_products()
        products.append(product.to_dict())
        self.db.save_products(products)
        return product

    def get_product(self, product_id: str) -> Optional[Product]:
        """获取产品"""
        products = self.db.get_products()
        for data in products:
            if data["id"] == product_id:
                return Product.from_dict(data)
        return None

    def get_products(self, category: Optional[str] = None,
                     is_active: bool = True) -> List[Product]:
        """获取产品列表"""
        products = [Product.from_dict(p) for p in self.db.get_products()]
        if category:
            products = [p for p in products if p.category == category]
        if is_active:
            products = [p for p in products if p.is_active]
        # 按创建时间降序
        products.sort(key=lambda x: x.created_at, reverse=True)
        return products

    def update_product(self, product: Product) -> bool:
        """更新产品"""
        product.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        products = self.db.get_products()
        for i, data in enumerate(products):
            if data["id"] == product.id:
                products[i] = product.to_dict()
                self.db.save_products(products)
                return True
        return False

    def delete_product(self, product_id: str) -> bool:
        """删除产品"""
        products = self.db.get_products()
        for i, data in enumerate(products):
            if data["id"] == product_id:
                products[i]["is_active"] = False
                products[i]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.db.save_products(products)
                return True
        return False


# ── 报价管理 ────────────────────────────────────────

class QuoteManager:
    """报价管理器"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_quotes_kernel
        self.db = get_quotes_kernel(storage_dir)

    def create_quote(self, title: str, customer_id: str = "",
                     customer_name: str = "", salesperson: str = "",
                     related_lead_id: str = "", valid_days: int = 30) -> Quote:
        """创建报价单"""
        from datetime import timedelta
        valid_until = datetime.now() + timedelta(days=valid_days)

        quote = Quote(
            title=title,
            customer_id=customer_id,
            customer_name=customer_name,
            salesperson=salesperson,
            related_lead_id=related_lead_id,
            valid_until=valid_until.strftime("%Y-%m-%d")
        )

        quotes = self.db.get_quotes()
        quotes.append(quote.to_dict())
        self.db.save_quotes(quotes)
        return quote

    def add_quote_item(self, quote_id: str, product_id: str = "",
                      product_name: str = "", quantity: int = 1,
                      unit_price: float = 0.0, discount_percent: float = 0.0,
                      tax_percent: float = 0.0) -> Optional[QuoteItem]:
        """添加报价明细项"""
        quote = self.get_quote(quote_id)
        if not quote:
            return None

        item = QuoteItem(
            product_id=product_id,
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            discount_percent=discount_percent,
            tax_percent=tax_percent
        )
        quote.items.append(item)

        # 更新报价
        quotes = self.db.get_quotes()
        for i, data in enumerate(quotes):
            if data["id"] == quote_id:
                quotes[i] = quote.to_dict()
                self.db.save_quotes(quotes)
                break

        return item

    def get_quote(self, quote_id: str) -> Optional[Quote]:
        """获取报价单"""
        quotes = self.db.get_quotes()
        for data in quotes:
            if data["id"] == quote_id:
                return Quote.from_dict(data)
        return None

    def get_quotes(self, status: Optional[str] = None,
                  customer_id: Optional[str] = None,
                  salesperson: Optional[str] = None) -> List[Quote]:
        """获取报价单列表"""
        quotes = [Quote.from_dict(q) for q in self.db.get_quotes()]

        # 更新过期状态
        for q in quotes:
            if q.is_expired and q.status not in ["accepted", "rejected", "completed"]:
                q.status = "expired"

        if status:
            quotes = [q for q in quotes if q.status == status]

        if customer_id:
            quotes = [q for q in quotes if q.customer_id == customer_id]

        if salesperson:
            quotes = [q for q in quotes if q.salesperson == salesperson]

        # 按更新时间降序
        quotes.sort(key=lambda x: x.updated_at, reverse=True)
        return quotes

    def update_quote(self, quote: Quote) -> bool:
        """更新报价单"""
        quote.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        quotes = self.db.get_quotes()
        for i, data in enumerate(quotes):
            if data["id"] == quote.id:
                quotes[i] = quote.to_dict()
                self.db.save_quotes(quotes)
                return True
        return False

    def update_quote_status(self, quote_id: str, new_status: str) -> bool:
        """更新报价状态"""
        quote = self.get_quote(quote_id)
        if not quote:
            return False

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        quote.status = new_status
        quote.updated_at = now

        if new_status == "sent" and not quote.sent_at:
            quote.sent_at = now
        if new_status == "accepted" and not quote.accepted_at:
            quote.accepted_at = now

        return self.update_quote(quote)

    def delete_quote(self, quote_id: str) -> bool:
        """删除报价单（标记为已取消）"""
        return self.update_quote_status(quote_id, "cancelled")

    def get_stats(self) -> Dict:
        """获取报价统计"""
        quotes = self.get_quotes()

        total = len(quotes)
        by_status = {}
        total_amount = 0.0

        for q in quotes:
            by_status[q.status] = by_status.get(q.status, 0) + 1
            if q.status in ["accepted", "completed"]:
                total_amount += q.total_amount

        return {
            "total": total,
            "by_status": by_status,
            "total_amount": total_amount
        }


# ── 合同管理 ────────────────────────────────────────

class ContractManager:
    """合同管理器"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_quotes_kernel
        self.db = get_quotes_kernel(storage_dir)

    def create_contract_from_quote(self, quote_id: str,
                                     title: str = "",
                                     salesperson: str = "") -> Optional[Contract]:
        """从报价单创建合同"""
        quote = QuoteManager().get_quote(quote_id)
        if not quote:
            return None

        # 创建合同
        contract = Contract(
            title=title or quote.title,
            customer_id=quote.customer_id,
            customer_name=quote.customer_name,
            customer_email=quote.customer_email,
            salesperson=salesperson or quote.salesperson,
            related_quote_id=quote.id,
            related_lead_id=quote.related_lead_id
        )

        # 复制报价明细到合同
        for item in quote.items:
            contract.items.append(ContractItem(
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price
            ))

        # 创建默认付款计划（3-3-3-1）
        total = contract.total_amount
        if total > 0:
            contract.payment_plans = [
                PaymentPlan(
                    payment_number=1,
                    description="首期付款",
                    amount=total * 0.3
                ),
                PaymentPlan(
                    payment_number=2,
                    description="中期付款",
                    amount=total * 0.3
                ),
                PaymentPlan(
                    payment_number=3,
                    description="后期货款",
                    amount=total * 0.3
                ),
                PaymentPlan(
                    payment_number=4,
                    description="质保金",
                    amount=total * 0.1
                )
            ]

        contracts = self.db.get_contracts()
        contracts.append(contract.to_dict())
        self.db.save_contracts(contracts)
        return contract

    def create_contract(self, title: str, customer_id: str = "",
                       customer_name: str = "", salesperson: str = "") -> Contract:
        """创建合同"""
        contract = Contract(
            title=title,
            customer_id=customer_id,
            customer_name=customer_name,
            salesperson=salesperson
        )
        contracts = self.db.get_contracts()
        contracts.append(contract.to_dict())
        self.db.save_contracts(contracts)
        return contract

    def get_contract(self, contract_id: str) -> Optional[Contract]:
        """获取合同"""
        contracts = self.db.get_contracts()
        for data in contracts:
            if data["id"] == contract_id:
                return Contract.from_dict(data)
        return None

    def get_contracts(self, status: Optional[str] = None,
                    customer_id: Optional[str] = None,
                    salesperson: Optional[str] = None) -> List[Contract]:
        """获取合同列表"""
        contracts = [Contract.from_dict(c) for c in self.db.get_contracts()]

        if status:
            contracts = [c for c in contracts if c.status == status]

        if customer_id:
            contracts = [c for c in contracts if c.customer_id == customer_id]

        if salesperson:
            contracts = [c for c in contracts if c.salesperson == salesperson]

        # 按更新时间降序
        contracts.sort(key=lambda x: x.updated_at, reverse=True)
        return contracts

    def update_contract(self, contract: Contract) -> bool:
        """更新合同"""
        contract.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        contracts = self.db.get_contracts()
        for i, data in enumerate(contracts):
            if data["id"] == contract.id:
                contracts[i] = contract.to_dict()
                self.db.save_contracts(contracts)
                return True
        return False

    def update_contract_status(self, contract_id: str, new_status: str) -> bool:
        """更新合同状态"""
        contract = self.get_contract(contract_id)
        if not contract:
            return False

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        contract.status = new_status
        contract.updated_at = now

        if new_status == "signed" and not contract.signed_at:
            contract.signed_at = now
        if new_status == "fulfilling" and not contract.effective_date:
            contract.effective_date = datetime.now().strftime("%Y-%m-%d")

        return self.update_contract(contract)

    def add_payment_plan(self, contract_id: str,
                         description: str = "", amount: float = 0.0,
                         due_date: str = "") -> Optional[PaymentPlan]:
        """添加付款计划"""
        contract = self.get_contract(contract_id)
        if not contract:
            return None

        # 下一期数
        next_num = len(contract.payment_plans) + 1

        plan = PaymentPlan(
            payment_number=next_num,
            description=description,
            amount=amount,
            due_date=due_date
        )

        contract.payment_plans.append(plan)
        return self.update_contract(contract)

    def mark_payment_paid(self, contract_id: str, plan_id: str) -> bool:
        """标记付款完成"""
        contract = self.get_contract(contract_id)
        if not contract:
            return False

        for plan in contract.payment_plans:
            if plan.id == plan_id:
                plan.status = "paid"
                plan.paid_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return self.update_contract(contract)
        return False

    def get_stats(self) -> Dict:
        """获取合同统计"""
        contracts = self.get_contracts()

        total = len(contracts)
        by_status = {}
        total_amount = 0.0

        for c in contracts:
            by_status[c.status] = by_status.get(c.status, 0) + 1
            if c.status in ["signed", "fulfilling", "completed"]:
                total_amount += c.total_amount

        return {
            "total": total,
            "by_status": by_status,
            "total_amount": total_amount
        }


# ── 模板管理 ────────────────────────────────────────

class TemplateManager:
    """模板管理器"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_quotes_kernel
        self.db = get_quotes_kernel(storage_dir)
        self._init_default_templates()

    def _init_default_templates(self):
        """初始化默认模板"""
        # 检查是否已有模板
        quote_templates = self.db.get_quote_templates()
        if not quote_templates:
            # 创建默认报价模板
            default_quote = QuoteTemplate(
                name="标准报价单模板",
                description="适用于大多数场景的报价模板",
                terms="本报价单有效期30天，具体条款以最终合同为准",
                default_tax_percent=13.0,
                is_default=True
            )
            self.create_quote_template(default_quote)

        contract_templates = self.db.get_contract_templates()
        if not contract_templates:
            # 创建默认合同模板
            default_contract = ContractTemplate(
                name="标准合同模板",
                description="适用于大多数场景的合同模板",
                terms="具体条款以双方协商一致为准",
                default_tax_percent=13.0,
                is_default=True
            )
            self.create_contract_template(default_contract)

    def create_quote_template(self, template: QuoteTemplate) -> QuoteTemplate:
        """创建报价模板"""
        templates = self.db.get_quote_templates()
        templates.append(template.to_dict())
        self.db.save_quote_templates(templates)
        return template

    def create_contract_template(self, template: ContractTemplate) -> ContractTemplate:
        """创建合同模板"""
        templates = self.db.get_contract_templates()
        templates.append(template.to_dict())
        self.db.save_contract_templates(templates)
        return template

    def get_quote_templates(self) -> List[QuoteTemplate]:
        """获取报价模板列表"""
        templates = self.db.get_quote_templates()
        return [QuoteTemplate.from_dict(t) for t in templates]

    def get_contract_templates(self) -> List[ContractTemplate]:
        """获取合同模板列表"""
        templates = self.db.get_contract_templates()
        return [ContractTemplate.from_dict(t) for t in templates]

    def get_default_quote_template(self) -> Optional[QuoteTemplate]:
        """获取默认报价模板"""
        for t in self.get_quote_templates():
            if t.is_default:
                return t
        return self.get_quote_templates()[0] if self.get_quote_templates() else None


# ── 工厂函数 ────────────────────────────────────────

def get_product_manager(storage_dir: Optional[str] = None) -> ProductManager:
    return ProductManager(storage_dir)

def get_quote_manager(storage_dir: Optional[str] = None) -> QuoteManager:
    return QuoteManager(storage_dir)

def get_contract_manager(storage_dir: Optional[str] = None) -> ContractManager:
    return ContractManager(storage_dir)

def get_template_manager(storage_dir: Optional[str] = None) -> TemplateManager:
    return TemplateManager(storage_dir)
