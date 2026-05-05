"""SentriKit_salesmaster.core.storage.pgrepo — PostgreSQL Repository 层

基于 SQLAlchemy 的 Repository 实现，支持：
- 自动 RLS 租户隔离
- JSONB 灵活字段
- 事务管理
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from .database import (
    Base, TenantMixin, TimestampMixin,
    Customer, Lead, Deal, Quote, Contract, Payment,
    Tenant, TenantUser, AuditLog,
    WorkflowInstance, WorkflowStepLog,
    get_db_context, set_tenant_context, clear_tenant_context,
    SessionLocal,
)

T = TypeVar("T", bound=Base)


class PostgresRepository:
    """PostgreSQL Repository 基类"""

    def __init__(self, model: Type[T], tenant_id: Optional[str] = None):
        self.model = model
        self.tenant_id = tenant_id
        self._db: Optional[Session] = None

    def _get_db(self) -> Session:
        """获取数据库会话"""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def _set_context(self) -> None:
        """设置租户上下文"""
        if self.tenant_id:
            set_tenant_context(self._get_db(), self.tenant_id)

    def _clear_context(self) -> None:
        """清除租户上下文"""
        if self._db:
            clear_tenant_context(self._get_db())

    def close(self) -> None:
        """关闭会话"""
        if self._db:
            self._db.close()
            self._db = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


class CustomerRepository(PostgresRepository):
    """客户 Repository"""

    def __init__(self, tenant_id: Optional[str] = None):
        super().__init__(Customer, tenant_id)

    def list(self, status: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Customer]:
        self._set_context()
        try:
            query = self._get_db().query(Customer)
            if status:
                query = query.filter(Customer.status == status)
            return query.order_by(Customer.created_at.desc()).offset(offset).limit(limit).all()
        finally:
            self._clear_context()

    def get(self, customer_id: str) -> Optional[Customer]:
        self._set_context()
        try:
            return self._get_db().query(Customer).filter(Customer.id == uuid.UUID(customer_id)).first()
        finally:
            self._clear_context()

    def create(self, data: Dict[str, Any]) -> Customer:
        self._set_context()
        try:
            customer = Customer(
                id=uuid.uuid4(),
                tenant_id=uuid.UUID(self.tenant_id),
                name=data["name"],
                contact=data.get("contact", {}),
                address=data.get("address", ""),
                custom_fields=data.get("custom_fields", {}),
                owner_id=uuid.UUID(data["owner_id"]) if data.get("owner_id") else None,
            )
            self._get_db().add(customer)
            self._get_db().commit()
            return customer
        finally:
            self._clear_context()

    def update(self, customer_id: str, data: Dict[str, Any]) -> Optional[Customer]:
        self._set_context()
        try:
            customer = self.get(customer_id)
            if not customer:
                return None
            for key, value in data.items():
                if hasattr(customer, key):
                    setattr(customer, key, value)
            customer.updated_at = datetime.utcnow()
            self._get_db().commit()
            return customer
        finally:
            self._clear_context()

    def delete(self, customer_id: str) -> bool:
        self._set_context()
        try:
            customer = self.get(customer_id)
            if not customer:
                return False
            customer.status = "deleted"
            self._get_db().commit()
            return True
        finally:
            self._clear_context()


class LeadRepository(PostgresRepository):
    """线索 Repository"""

    def __init__(self, tenant_id: Optional[str] = None):
        super().__init__(Lead, tenant_id)

    def list(self, status: Optional[str] = None, grade: Optional[str] = None, limit: int = 100) -> List[Lead]:
        self._set_context()
        try:
            query = self._get_db().query(Lead)
            if status:
                query = query.filter(Lead.status == status)
            if grade:
                query = query.filter(Lead.grade == grade)
            return query.order_by(Lead.score.desc()).limit(limit).all()
        finally:
            self._clear_context()

    def get(self, lead_id: str) -> Optional[Lead]:
        self._set_context()
        try:
            return self._get_db().query(Lead).filter(Lead.id == uuid.UUID(lead_id)).first()
        finally:
            self._clear_context()

    def create(self, data: Dict[str, Any]) -> Lead:
        self._set_context()
        try:
            lead = Lead(
                id=uuid.uuid4(),
                tenant_id=uuid.UUID(self.tenant_id),
                name=data["name"],
                company=data.get("company", ""),
                contact=data.get("contact", {}),
                source=data.get("source", ""),
                score=data.get("score", 0),
                grade=data.get("grade", "C"),
                owner_id=uuid.UUID(data["owner_id"]) if data.get("owner_id") else None,
            )
            self._get_db().add(lead)
            self._get_db().commit()
            return lead
        finally:
            self._clear_context()

    def update_score(self, lead_id: str, score: int, grade: str) -> bool:
        self._set_context()
        try:
            lead = self.get(lead_id)
            if not lead:
                return False
            lead.score = score
            lead.grade = grade
            self._get_db().commit()
            return True
        finally:
            self._clear_context()


class DealRepository(PostgresRepository):
    """交易 Repository"""

    def __init__(self, tenant_id: Optional[str] = None):
        super().__init__(Deal, tenant_id)

    def list(self, stage: Optional[str] = None, status: str = "open", limit: int = 100) -> List[Deal]:
        self._set_context()
        try:
            query = self._get_db().query(Deal).filter(Deal.status == status)
            if stage:
                query = query.filter(Deal.stage == stage)
            return query.order_by(Deal.amount.desc()).limit(limit).all()
        finally:
            self._clear_context()

    def get(self, deal_id: str) -> Optional[Deal]:
        self._set_context()
        try:
            return self._get_db().query(Deal).filter(Deal.id == uuid.UUID(deal_id)).first()
        finally:
            self._clear_context()

    def create(self, data: Dict[str, Any]) -> Deal:
        self._set_context()
        try:
            deal = Deal(
                id=uuid.uuid4(),
                tenant_id=uuid.UUID(self.tenant_id),
                title=data["title"],
                customer_id=uuid.UUID(data["customer_id"]) if data.get("customer_id") else None,
                amount=data.get("amount", 0),
                stage=data.get("stage", "prospecting"),
                probability=data.get("probability", 0),
                owner_id=uuid.UUID(data["owner_id"]) if data.get("owner_id") else None,
            )
            self._get_db().add(deal)
            self._get_db().commit()
            return deal
        finally:
            self._clear_context()


class QuoteRepository(PostgresRepository):
    """报价单 Repository"""

    def __init__(self, tenant_id: Optional[str] = None):
        super().__init__(Quote, tenant_id)

    def list(self, status: Optional[str] = None, limit: int = 100) -> List[Quote]:
        self._set_context()
        try:
            query = self._get_db().query(Quote)
            if status:
                query = query.filter(Quote.status == status)
            return query.order_by(Quote.created_at.desc()).limit(limit).all()
        finally:
            self._clear_context()

    def get(self, quote_id: str) -> Optional[Quote]:
        self._set_context()
        try:
            return self._get_db().query(Quote).filter(Quote.id == uuid.UUID(quote_id)).first()
        finally:
            self._clear_context()

    def get_by_no(self, quote_no: str) -> Optional[Quote]:
        self._set_context()
        try:
            return self._get_db().query(Quote).filter(Quote.quote_no == quote_no).first()
        finally:
            self._clear_context()

    def create(self, data: Dict[str, Any]) -> Quote:
        self._set_context()
        try:
            quote = Quote(
                id=uuid.uuid4(),
                tenant_id=uuid.UUID(self.tenant_id),
                quote_no=data["quote_no"],
                title=data["title"],
                customer_id=uuid.UUID(data["customer_id"]) if data.get("customer_id") else None,
                items=data.get("items", []),
                subtotal=data.get("subtotal", 0),
                discount=data.get("discount", 0),
                tax=data.get("tax", 0),
                total=data.get("total", 0),
                status=data.get("status", "draft"),
                owner_id=uuid.UUID(data["owner_id"]) if data.get("owner_id") else None,
            )
            self._get_db().add(quote)
            self._get_db().commit()
            return quote
        finally:
            self._clear_context()


class ContractRepository(PostgresRepository):
    """合同 Repository"""

    def __init__(self, tenant_id: Optional[str] = None):
        super().__init__(Contract, tenant_id)

    def list(self, status: Optional[str] = None, limit: int = 100) -> List[Contract]:
        self._set_context()
        try:
            query = self._get_db().query(Contract)
            if status:
                query = query.filter(Contract.status == status)
            return query.order_by(Contract.created_at.desc()).limit(limit).all()
        finally:
            self._clear_context()

    def get(self, contract_id: str) -> Optional[Contract]:
        self._set_context()
        try:
            return self._get_db().query(Contract).filter(Contract.id == uuid.UUID(contract_id)).first()
        finally:
            self._clear_context()

    def get_by_no(self, contract_no: str) -> Optional[Contract]:
        self._set_context()
        try:
            return self._get_db().query(Contract).filter(Contract.contract_no == contract_no).first()
        finally:
            self._clear_context()


class AuditLogRepository(PostgresRepository):
    """审计日志 Repository"""

    def __init__(self, tenant_id: Optional[str] = None):
        super().__init__(AuditLog, tenant_id)

    def log(
        self,
        action: str,
        user_id: str = "",
        user_name: str = "",
        resource: str = "",
        resource_id: str = "",
        details: Optional[Dict] = None,
        ip_address: str = "",
        level: str = "info",
        status: str = "success",
        error_message: str = "",
        duration_ms: int = 0,
    ) -> AuditLog:
        try:
            log = AuditLog(
                id=uuid.uuid4(),
                tenant_id=uuid.UUID(self.tenant_id) if self.tenant_id else None,
                user_id=uuid.UUID(user_id) if user_id else None,
                user_name=user_name,
                action=action,
                resource=resource,
                resource_id=resource_id,
                details=details or {},
                ip_address=ip_address,
                level=level,
                status=status,
                error_message=error_message,
                duration_ms=duration_ms,
            )
            self._get_db().add(log)
            self._get_db().commit()
            return log
        except Exception:
            self._get_db().rollback()
            raise

    def query(
        self,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        user_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        try:
            query = self._get_db().query(AuditLog)
            if self.tenant_id:
                query = query.filter(AuditLog.tenant_id == uuid.UUID(self.tenant_id))
            if action:
                query = query.filter(AuditLog.action == action)
            if resource:
                query = query.filter(AuditLog.resource == resource)
            if user_id:
                query = query.filter(AuditLog.user_id == uuid.UUID(user_id))
            if start_time:
                query = query.filter(AuditLog.created_at >= datetime.fromisoformat(start_time))
            if end_time:
                query = query.filter(AuditLog.created_at <= datetime.fromisoformat(end_time))
            return query.order_by(AuditLog.created_at.desc()).limit(limit).all()
        finally:
            self._clear_context()


def get_customer_repository(tenant_id: Optional[str] = None) -> CustomerRepository:
    return CustomerRepository(tenant_id)


def get_lead_repository(tenant_id: Optional[str] = None) -> LeadRepository:
    return LeadRepository(tenant_id)


def get_deal_repository(tenant_id: Optional[str] = None) -> DealRepository:
    return DealRepository(tenant_id)


def get_quote_repository(tenant_id: Optional[str] = None) -> QuoteRepository:
    return QuoteRepository(tenant_id)


def get_contract_repository(tenant_id: Optional[str] = None) -> ContractRepository:
    return ContractRepository(tenant_id)


def get_audit_log_repository(tenant_id: Optional[str] = None) -> AuditLogRepository:
    return AuditLogRepository(tenant_id)
