"""tianlong_salesmaster.core.storage.db_mysql — MySQL 数据库层

支持 MySQL 作为生产数据库，保持与 PostgreSQL 层相同的接口。

使用方法:
    from tianlong_salesmaster.core.storage.db_mysql import init_database, get_db_context
"""

from __future__ import annotations

import os
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Index, Integer,
    Numeric, String, Text, create_engine, event, text, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker
from sqlalchemy.pool import QueuePool

Base = declarative_base()

DATABASE_URL = os.environ.get(
    "MYSQL_URL",
    "mysql+pymysql://salesadmin:sales123@localhost:3306/tianlong_sales"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    poolclass=QueuePool,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TenantMixin:
    tenant_id = Column(String(36), nullable=False, index=True)


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    company = Column(String(255), default="")
    industry = Column(String(100), default="")
    size = Column(String(20), default="small")
    status = Column(String(20), default="active")
    subscription = Column(JSON, default=dict)
    settings = Column(JSON, default=dict)
    activated_at = Column(DateTime, nullable=True)

    users = relationship("TenantUser", back_populates="tenant", cascade="all, delete-orphan")

    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "company": self.company,
            "status": self.status,
            "subscription": self.subscription,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TenantUser(Base, TimestampMixin):
    __tablename__ = "tenant_users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255), default="")
    phone = Column(String(50), default="")
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="member")
    status = Column(String(20), default="active")
    permissions = Column(JSON, default=list)
    last_login = Column(DateTime, nullable=True)

    tenant = relationship("Tenant", back_populates="users")

    def to_dict(self, include_password: bool = False) -> Dict:
        data = {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "status": self.status,
        }
        if include_password:
            data["password_hash"] = self.password_hash
        return data


class Customer(Base, TenantMixin, TimestampMixin):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    contact = Column(JSON, default=dict)
    address = Column(String(500), default="")
    custom_fields = Column(JSON, default=dict)
    owner_id = Column(String(36), nullable=True)
    status = Column(String(20), default="active")


class Lead(Base, TenantMixin, TimestampMixin):
    __tablename__ = "leads"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    company = Column(String(255), default="")
    contact = Column(JSON, default=dict)
    source = Column(String(50), default="")
    score = Column(Integer, default=0)
    grade = Column(String(10), default="C")
    owner_id = Column(String(36), nullable=True)
    status = Column(String(20), default="new")
    custom_fields = Column(JSON, default=dict)


class Deal(Base, TenantMixin, TimestampMixin):
    __tablename__ = "deals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=True)
    amount = Column(Numeric(15, 2), default=0)
    stage = Column(String(50), default="prospecting")
    probability = Column(Integer, default=0)
    expected_close = Column(DateTime, nullable=True)
    owner_id = Column(String(36), nullable=True)
    status = Column(String(20), default="open")
    custom_fields = Column(JSON, default=dict)


class Quote(Base, TenantMixin, TimestampMixin):
    __tablename__ = "quotes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_no = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=True)
    contact_id = Column(String(36), nullable=True)
    items = Column(JSON, default=list)
    subtotal = Column(Numeric(15, 2), default=0)
    discount = Column(Numeric(15, 2), default=0)
    tax = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), default=0)
    status = Column(String(20), default="draft")
    owner_id = Column(String(36), nullable=True)
    valid_until = Column(DateTime, nullable=True)


class Contract(Base, TenantMixin, TimestampMixin):
    __tablename__ = "contracts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_no = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=True)
    quote_id = Column(String(36), ForeignKey("quotes.id"), nullable=True)
    amount = Column(Numeric(15, 2), default=0)
    signers = Column(JSON, default=list)
    esign_flow_id = Column(String(255), nullable=True)
    status = Column(String(20), default="draft")
    signed_at = Column(DateTime, nullable=True)
    owner_id = Column(String(36), nullable=True)


class Payment(Base, TenantMixin, TimestampMixin):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_no = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    contract_id = Column(String(36), ForeignKey("contracts.id"), nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)
    channel = Column(String(50), default="mock")
    status = Column(String(20), default="pending")
    transaction_id = Column(String(255), nullable=True)
    paid_at = Column(DateTime, nullable=True)
    refund_amount = Column(Numeric(15, 2), default=0)
    refund_at = Column(DateTime, nullable=True)


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=True, index=True)
    user_id = Column(String(36), nullable=True)
    user_name = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=True)
    resource_id = Column(String(255), nullable=True)
    details = Column(JSON, default=dict)
    ip_address = Column(String(50), nullable=True)
    level = Column(String(20), default="info")
    status = Column(String(20), default="success")
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, default=0)

    __table_args__ = (
        Index("idx_audit_logs_tenant_time", "tenant_id", "created_at"),
        Index("idx_audit_logs_resource", "resource", "resource_id"),
    )


class WorkflowInstance(Base, TenantMixin, TimestampMixin):
    __tablename__ = "workflow_instances"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(String(20), default="pending")
    current_step = Column(Integer, default=0)
    context = Column(JSON, default=dict)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class WorkflowStepLog(Base, TimestampMixin):
    __tablename__ = "workflow_step_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String(36), ForeignKey("workflow_instances.id", ondelete="CASCADE"), nullable=False)
    step_id = Column(String(100), nullable=False)
    step_name = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)
    status = Column(String(20), default="pending")
    result = Column(JSON, default=dict)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_database() -> None:
    Base.metadata.create_all(bind=engine)
