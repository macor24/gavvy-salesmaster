"""SentriKit_salesmaster.trade_pkg.payment — 支付收款模块

支持多种支付渠道：支付宝、微信支付、银行转账等。
"""

from __future__ import annotations

import os
import json
import uuid
import hashlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ── 支付渠道枚举 ────────────────────────────────────────

class PaymentChannel(Enum):
    """支付渠道"""
    ALIPAY = "alipay"              # 支付宝
    WECHAT_PAY = "wechat_pay"      # 微信支付
    BANK_TRANSFER = "bank_transfer"  # 银行转账
    CORPORATE = "corporate"        # 对公汇款
    MOCK = "mock"                 # 模拟模式


class PaymentStatus(Enum):
    """支付状态"""
    PENDING = "pending"            # 待支付
    PROCESSING = "processing"      # 处理中
    PAID = "paid"                 # 已支付
    FAILED = "failed"             # 支付失败
    REFUNDED = "refunded"         # 已退款
    EXPIRED = "expired"           # 已过期
    CANCELLED = "cancelled"       # 已取消


class PaymentType(Enum):
    """支付类型"""
    DIRECT = "direct"             # 直接支付
    ESCROW = "escrow"             # 担保交易
    INSTALLMENT = "installment"   # 分期付款


# ── 数据类型定义 ────────────────────────────────────────

@dataclass
class PaymentItem:
    """支付明细"""
    id: str = ""
    name: str = ""
    description: str = ""
    quantity: int = 1
    unit_price: float = 0.0
    total_price: float = 0.0
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:12]
        if self.total_price == 0:
            self.total_price = self.unit_price * self.quantity


@dataclass
class PaymentOrder:
    """支付订单"""
    id: str = ""
    order_no: str = ""            # 订单号
    title: str = ""               # 订单标题
    description: str = ""         # 订单描述
    items: List[PaymentItem] = field(default_factory=list)
    total_amount: float = 0.0    # 总金额
    paid_amount: float = 0.0      # 已付金额
    currency: str = "CNY"         # 币种
    channel: str = "mock"         # 支付渠道
    payment_type: str = "direct"  # 支付类型
    status: str = "pending"       # 支付状态
    related_contract_id: str = ""  # 关联合同ID
    related_quote_id: str = ""    # 关联报价ID
    payer_id: str = ""             # 付款方ID
    payer_name: str = ""          # 付款方名称
    payer_email: str = ""         # 付款方邮箱
    created_at: str = ""
    paid_at: str = ""             # 支付时间
    expired_at: str = ""          # 过期时间
    paid_channels: List[str] = field(default_factory=list)  # 已支付的渠道
    metadata: Dict = field(default_factory=dict)  # 额外数据

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:12]
        if not self.order_no:
            self.order_no = self._generate_order_no()
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.expired_at:
            exp = datetime.now() + timedelta(hours=24)
            self.expired_at = exp.strftime("%Y-%m-%d %H:%M:%S")
        if self.total_amount == 0:
            self.total_amount = sum(item.total_price for item in self.items)

    def _generate_order_no(self) -> str:
        """生成订单号"""
        prefix = "PAY"
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = str(uuid.uuid4())[:6].upper()
        return f"{prefix}{timestamp}{random_str}"

    @property
    def is_paid(self) -> bool:
        """是否已支付"""
        return self.paid_amount >= self.total_amount

    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        try:
            exp = datetime.fromisoformat(self.expired_at)
            return datetime.now() > exp and not self.is_paid
        except Exception:
            return False

    @property
    def remaining_amount(self) -> float:
        """剩余待付金额"""
        return max(0, self.total_amount - self.paid_amount)


@dataclass
class PaymentRecord:
    """支付记录"""
    id: str = ""
    order_id: str = ""
    order_no: str = ""
    channel: str = ""
    amount: float = 0.0
    status: str = "pending"
    transaction_id: str = ""     # 第三方交易号
    paid_at: str = ""           # 支付时间
    error_code: str = ""
    error_message: str = ""
    raw_response: Dict = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:12]
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class PaymentResult:
    """支付结果"""
    success: bool = False
    order_id: str = ""
    order_no: str = ""
    payment_url: str = ""        # 支付链接/二维码
    qr_code: str = ""            # 二维码（Base64）
    transaction_id: str = ""     # 第三方交易号
    error: Optional[str] = None
    error_code: str = ""
    response: Optional[Dict] = None


@dataclass
class RefundResult:
    """退款结果"""
    success: bool = False
    order_id: str = ""
    refund_id: str = ""
    refund_amount: float = 0.0
    error: Optional[str] = None
    response: Optional[Dict] = None


# ── 配置类 ────────────────────────────────────────

@dataclass
class PaymentConfig:
    """支付配置基类"""
    channel: str = "mock"
    app_id: str = ""
    merchant_id: str = ""
    callback_url: str = ""       # 回调地址
    return_url: str = ""         # 支付完成跳转地址


@dataclass
class AlipayConfig(PaymentConfig):
    """支付宝配置"""
    channel: str = "alipay"
    app_id: str = ""
    private_key: str = ""        # 应用私钥
    alipay_public_key: str = "" # 支付宝公钥
    sign_type: str = "RSA2"     # 签名类型


@dataclass
class WeChatPayConfig(PaymentConfig):
    """微信支付配置"""
    channel: str = "wechat_pay"
    mch_id: str = ""             # 商户号
    api_key: str = ""            # API密钥
    cert_path: str = ""          # 证书路径


@dataclass
class BankTransferConfig(PaymentConfig):
    """银行转账配置"""
    channel: str = "bank_transfer"
    bank_name: str = ""
    bank_account: str = ""
    bank_account_name: str = ""
    bank_branch: str = ""


# ── 支付渠道基类 ────────────────────────────────────────

class BasePayment(ABC):
    """支付渠道基类"""

    def __init__(self, config: PaymentConfig):
        self.config = config

    @abstractmethod
    def create_order(self, order: PaymentOrder) -> PaymentResult:
        """创建支付订单"""
        pass

    @abstractmethod
    def get_order_status(self, order_id: str) -> PaymentStatus:
        """查询订单状态"""
        pass

    @abstractmethod
    def refund(self, order_id: str, amount: float, reason: str = "") -> RefundResult:
        """申请退款"""
        pass

    @abstractmethod
    def verify_notification(self, notification: Dict) -> bool:
        """验证回调通知"""
        pass

    def generate_qr_code(self, content: str) -> str:
        """生成二维码（Base64）"""
        try:
            import qrcode
            import io
            import base64

            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(content)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode()
        except ImportError:
            return ""


# ── Mock 支付 ────────────────────────────────────────

class MockPayment(BasePayment):
    """模拟支付（用于测试）"""

    def __init__(self, config: PaymentConfig):
        super().__init__(config)
        self._orders: Dict[str, PaymentOrder] = {}
        self._records: Dict[str, List[PaymentRecord]] = {}

    def create_order(self, order: PaymentOrder) -> PaymentResult:
        """创建支付订单"""
        try:
            self._orders[order.id] = order
            self._records[order.id] = []

            # 生成模拟支付链接
            payment_url = f"https://mock-payment.example.com/pay?order={order.order_no}"

            return PaymentResult(
                success=True,
                order_id=order.id,
                order_no=order.order_no,
                payment_url=payment_url,
                qr_code=self.generate_qr_code(payment_url),
                transaction_id=f"MOCK_{order.order_no}",
                response={"mock": True}
            )

        except Exception as e:
            return PaymentResult(
                success=False,
                order_id=order.id,
                error=str(e)
            )

    def get_order_status(self, order_id: str) -> PaymentStatus:
        """查询订单状态"""
        order = self._orders.get(order_id)
        if not order:
            return PaymentStatus.FAILED

        if order.is_paid:
            return PaymentStatus.PAID
        elif order.is_expired:
            return PaymentStatus.EXPIRED
        else:
            return PaymentStatus.PENDING

    def refund(self, order_id: str, amount: float, reason: str = "") -> RefundResult:
        """申请退款"""
        order = self._orders.get(order_id)
        if not order:
            return RefundResult(success=False, error="订单不存在")

        if not order.is_paid:
            return RefundResult(success=False, error="订单未支付")

        refund_id = f"REFUND_{order_id[:12]}_{int(time.time())}"

        return RefundResult(
            success=True,
            order_id=order_id,
            refund_id=refund_id,
            refund_amount=amount,
            response={"mock": True}
        )

    def verify_notification(self, notification: Dict) -> bool:
        """验证回调通知"""
        return True

    def simulate_pay(self, order_id: str) -> PaymentResult:
        """模拟支付（用于测试）"""
        order = self._orders.get(order_id)
        if not order:
            return PaymentResult(success=False, error="订单不存在")

        # 更新订单状态
        order.status = "paid"
        order.paid_amount = order.total_amount
        order.paid_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 创建支付记录
        record = PaymentRecord(
            order_id=order.id,
            order_no=order.order_no,
            channel="mock",
            amount=order.total_amount,
            status="paid",
            transaction_id=f"MOCK_{order.order_no}",
            paid_at=order.paid_at
        )
        self._records[order_id].append(record)

        return PaymentResult(
            success=True,
            order_id=order.id,
            order_no=order.order_no,
            transaction_id=record.transaction_id
        )


# ── 支付宝 ────────────────────────────────────────

class AlipayPayment(BasePayment):
    """支付宝支付"""

    def create_order(self, order: PaymentOrder) -> PaymentResult:
        """创建支付订单"""
        try:
            # 实际实现需要使用 alipay-sdk-python
            # 这里使用模拟实现
            mock_config = PaymentConfig(channel="mock")
            mock = MockPayment(mock_config)
            self._orders = mock._orders
            self._records = mock._records
            return mock.create_order(order)
        except Exception as e:
            return PaymentResult(success=False, error=str(e))

    def get_order_status(self, order_id: str) -> PaymentStatus:
        """查询订单状态"""
        mock = MockPayment(PaymentConfig(channel="mock"))
        return mock.get_order_status(order_id)

    def refund(self, order_id: str, amount: float, reason: str = "") -> RefundResult:
        """申请退款"""
        mock = MockPayment(PaymentConfig(channel="mock"))
        mock._orders = self._orders if hasattr(self, "_orders") else {}
        return mock.refund(order_id, amount, reason)

    def verify_notification(self, notification: Dict) -> bool:
        """验证回调通知"""
        # 实际实现需要验证签名
        return True


# ── 微信支付 ────────────────────────────────────────

class WeChatPayPayment(BasePayment):
    """微信支付"""

    def create_order(self, order: PaymentOrder) -> PaymentResult:
        """创建支付订单"""
        try:
            mock = MockPayment(PaymentConfig(channel="mock"))
            self._orders = mock._orders
            self._records = mock._records
            return mock.create_order(order)
        except Exception as e:
            return PaymentResult(success=False, error=str(e))

    def get_order_status(self, order_id: str) -> PaymentStatus:
        """查询订单状态"""
        mock = MockPayment(PaymentConfig(channel="mock"))
        return mock.get_order_status(order_id)

    def refund(self, order_id: str, amount: float, reason: str = "") -> RefundResult:
        """申请退款"""
        mock = MockPayment(PaymentConfig(channel="mock"))
        mock._orders = self._orders if hasattr(self, "_orders") else {}
        return mock.refund(order_id, amount, reason)

    def verify_notification(self, notification: Dict) -> bool:
        """验证回调通知"""
        # 实际实现需要验证签名
        return True


# ── 银行转账 ────────────────────────────────────────

class BankTransferPayment(BasePayment):
    """银行转账"""

    def __init__(self, config: BankTransferConfig):
        super().__init__(config)
        self._orders: Dict[str, PaymentOrder] = {}

    def create_order(self, order: PaymentOrder) -> PaymentResult:
        """创建转账信息"""
        try:
            self._orders[order.id] = order

            bank_config: BankTransferConfig = self.config

            # 生成银行转账信息
            transfer_info = f"""
银行名称: {bank_config.bank_name}
银行账号: {bank_config.bank_account}
账户名称: {bank_config.bank_account_name}
开户行: {bank_config.bank_branch}

付款时请备注: {order.order_no}
"""
            payment_url = f"bank://transfer?order={order.order_no}"

            return PaymentResult(
                success=True,
                order_id=order.id,
                order_no=order.order_no,
                payment_url=payment_url,
                qr_code=self.generate_qr_code(transfer_info),
                response={
                    "transfer_info": transfer_info,
                    "mock": True
                }
            )

        except Exception as e:
            return PaymentResult(success=False, error=str(e))

    def get_order_status(self, order_id: str) -> PaymentStatus:
        """查询订单状态（银行转账需要人工确认）"""
        order = self._orders.get(order_id)
        if not order:
            return PaymentStatus.FAILED

        if order.is_paid:
            return PaymentStatus.PAID
        elif order.is_expired:
            return PaymentStatus.EXPIRED
        else:
            return PaymentStatus.PENDING

    def refund(self, order_id: str, amount: float, reason: str = "") -> RefundResult:
        """申请退款（银行转账退款需要人工处理）"""
        return RefundResult(
            success=True,
            order_id=order_id,
            refund_id=f"BANK_REFUND_{order_id[:12]}",
            refund_amount=amount,
            response={"note": "银行转账退款需要人工处理"}
        )

    def verify_notification(self, notification: Dict) -> bool:
        """验证回调通知（银行转账通常不需要）"""
        return True


# ── 支付管理器 ────────────────────────────────────────

class PaymentManager:
    """支付管理器"""

    def __init__(self, config: Optional[PaymentConfig] = None):
        self.config = config or PaymentConfig(channel="mock")
        self._payment: Optional[BasePayment] = None
        self._orders: Dict[str, PaymentOrder] = {}

    @property
    def payment(self) -> BasePayment:
        """获取支付实例"""
        if self._payment is None:
            self._payment = self._create_payment()
        return self._payment

    def _create_payment(self) -> BasePayment:
        """创建支付实例"""
        if self.config.channel == "alipay":
            return AlipayPayment(self.config)
        elif self.config.channel == "wechat_pay":
            return WeChatPayPayment(self.config)
        elif self.config.channel == "bank_transfer":
            return BankTransferPayment(self.config)
        else:
            return MockPayment(self.config)

    def create_order(self, title: str, amount: float,
                    items: Optional[List[PaymentItem]] = None,
                    channel: str = "mock",
                    **kwargs) -> PaymentOrder:
        """创建支付订单"""
        order_items = items or [
            PaymentItem(
                name=title,
                description=title,
                unit_price=amount,
                quantity=1,
                total_price=amount
            )
        ]

        order = PaymentOrder(
            title=title,
            items=order_items,
            total_amount=amount,
            channel=channel,
            **kwargs
        )

        self._orders[order.id] = order
        return order

    def initiate_payment(self, order: PaymentOrder) -> PaymentResult:
        """发起支付"""
        return self.payment.create_order(order)

    def get_order(self, order_id: str) -> Optional[PaymentOrder]:
        """获取订单"""
        return self._orders.get(order_id)

    def query_status(self, order_id: str) -> PaymentStatus:
        """查询状态"""
        return self.payment.get_order_status(order_id)

    def refund(self, order_id: str, amount: float, reason: str = "") -> RefundResult:
        """申请退款"""
        return self.payment.refund(order_id, amount, reason)

    def verify_notification(self, notification: Dict) -> bool:
        """验证回调"""
        return self.payment.verify_notification(notification)

    def handle_notification(self, notification: Dict) -> Tuple[bool, str]:
        """处理支付回调"""
        if not self.verify_notification(notification):
            return False, "验证失败"

        # 解析回调数据并更新订单状态
        # 具体实现根据不同渠道而异

        return True, "处理成功"


# ── 合同收款集成 ────────────────────────────────────────

class ContractPayment:
    """合同收款集成"""

    def __init__(self, payment_manager: Optional[PaymentManager] = None):
        self.payment_manager = payment_manager or PaymentManager()

    def create_payment_for_contract(self, contract, payment_plan=None) -> Tuple[PaymentOrder, PaymentResult]:
        """为合同创建支付订单"""
        # 确定金额
        if payment_plan:
            amount = payment_plan.amount
            title = f"合同付款 - {contract.title} (第{payment_plan.payment_number}期)"
        else:
            amount = contract.total_amount
            title = f"合同付款 - {contract.title}"

        # 创建订单
        order = self.payment_manager.create_order(
            title=title,
            amount=amount,
            related_contract_id=contract.id,
            channel="mock",
            payer_name=getattr(contract, "customer_name", ""),
            payer_email=getattr(contract, "customer_email", "")
        )

        # 发起支付
        result = self.payment_manager.initiate_payment(order)

        return order, result

    def create_payment_link(self, order_id: str) -> str:
        """创建支付链接"""
        order = self.payment_manager.get_order(order_id)
        if not order:
            return ""

        result = self.payment_manager.initiate_payment(order)
        return result.payment_url


# ── 工厂函数 ────────────────────────────────────────

def create_payment_manager(config: PaymentConfig) -> PaymentManager:
    """创建支付管理器"""
    return PaymentManager(config)


def get_mock_payment() -> PaymentManager:
    """获取模拟支付管理器"""
    config = PaymentConfig(channel="mock")
    return PaymentManager(config)


def create_alipay_payment(app_id: str, private_key: str,
                         alipay_public_key: str) -> PaymentManager:
    """创建支付宝支付管理器"""
    config = AlipayConfig(
        app_id=app_id,
        private_key=private_key,
        alipay_public_key=alipay_public_key
    )
    return PaymentManager(config)


def create_wechat_payment(mch_id: str, api_key: str) -> PaymentManager:
    """创建微信支付管理器"""
    config = WeChatPayConfig(
        mch_id=mch_id,
        api_key=api_key
    )
    return PaymentManager(config)


def create_bank_transfer_payment(bank_name: str, bank_account: str,
                               bank_account_name: str) -> PaymentManager:
    """创建银行转账管理器"""
    config = BankTransferConfig(
        bank_name=bank_name,
        bank_account=bank_account,
        bank_account_name=bank_account_name
    )
    return PaymentManager(config)
