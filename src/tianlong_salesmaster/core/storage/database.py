"""tianlong_salesmaster.core.storage.database — PostgreSQL 数据库层

支持：
- SQLAlchemy ORM 模型
- JSONB 灵活字段
- RLS 租户隔离
- 分区表（审计日志）
"""

from __future__ import annotations

import os
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Index, Integer,
    Numeric, String, Text, create_engine, event, text
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker
from sqlalchemy.pool import QueuePool

Base = declarative_base()

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://salesadmin:password@localhost:5432/tianlong_sales"
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
    """租户混入 - 自动添加 tenant_id"""

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)


class TimestampMixin:
    """时间戳混入"""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── 租户相关模型 ────────────────────────────────────────


class Tenant(Base, TimestampMixin):
    """租户"""

    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    company = Column(String(255), default="")
    industry = Column(String(100), default="")
    size = Column(String(20), default="small")
    status = Column(String(20), default="active")
    subscription = Column(JSONB, default=dict)
    settings = Column(JSONB, default=dict)
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
    """租户用户"""

    __tablename__ = "tenant_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255), default="")
    phone = Column(String(50), default="")
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="member")
    status = Column(String(20), default="active")
    permissions = Column(JSONB, default=list)
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


# ── CRM 相关模型 ────────────────────────────────────────


class Customer(Base, TenantMixin, TimestampMixin):
    """客户"""

    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    contact = Column(JSONB, default=dict)
    address = Column(String(500), default="")
    custom_fields = Column(JSONB, default=dict)
    owner_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(20), default="active")


class Lead(Base, TenantMixin, TimestampMixin):
    """线索"""

    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    company = Column(String(255), default="")
    contact = Column(JSONB, default=dict)
    source = Column(String(50), default="")
    score = Column(Integer, default=0)
    grade = Column(String(10), default="C")
    owner_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(20), default="new")
    custom_fields = Column(JSONB, default=dict)


class Deal(Base, TenantMixin, TimestampMixin):
    """交易"""

    __tablename__ = "deals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    amount = Column(Numeric(15, 2), default=0)
    stage = Column(String(50), default="prospecting")
    probability = Column(Integer, default=0)
    expected_close = Column(DateTime, nullable=True)
    owner_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(20), default="open")
    custom_fields = Column(JSONB, default=dict)


# ── 报价/合同 ────────────────────────────────────────


class Quote(Base, TenantMixin, TimestampMixin):
    """报价单"""

    __tablename__ = "quotes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_no = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    contact_id = Column(UUID(as_uuid=True), nullable=True)
    items = Column(JSONB, default=list)
    subtotal = Column(Numeric(15, 2), default=0)
    discount = Column(Numeric(15, 2), default=0)
    tax = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), default=0)
    status = Column(String(20), default="draft")
    owner_id = Column(UUID(as_uuid=True), nullable=True)
    valid_until = Column(DateTime, nullable=True)


class Contract(Base, TenantMixin, TimestampMixin):
    """合同"""

    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_no = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True)
    quote_id = Column(UUID(as_uuid=True), ForeignKey("quotes.id"), nullable=True)
    amount = Column(Numeric(15, 2), default=0)
    signers = Column(JSONB, default=list)
    esign_flow_id = Column(String(255), nullable=True)
    status = Column(String(20), default="draft")
    signed_at = Column(DateTime, nullable=True)
    owner_id = Column(UUID(as_uuid=True), nullable=True)


# ── 支付 ────────────────────────────────────────


class Payment(Base, TenantMixin, TimestampMixin):
    """支付记录"""

    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_no = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)
    channel = Column(String(50), default="mock")
    status = Column(String(20), default="pending")
    transaction_id = Column(String(255), nullable=True)
    paid_at = Column(DateTime, nullable=True)
    refund_amount = Column(Numeric(15, 2), default=0)
    refund_at = Column(DateTime, nullable=True)


# ── 审计日志（分区表）───────────────────────────────────────


class AuditLog(Base, TimestampMixin):
    """审计日志"""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    user_name = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=True)
    resource_id = Column(String(255), nullable=True)
    details = Column(JSONB, default=dict)
    ip_address = Column(String(50), nullable=True)
    level = Column(String(20), default="info")
    status = Column(String(20), default="success")
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, default=0)

    __table_args__ = (
        {"postgresql_partition_by": "RANGE (created_at)"},
        Index("idx_audit_logs_tenant_time", "tenant_id", "created_at"),
        Index("idx_audit_logs_resource", "resource", "resource_id"),
    )


# ── 工作流 ────────────────────────────────────────


class WorkflowInstance(Base, TenantMixin, TimestampMixin):
    """工作流实例"""

    __tablename__ = "workflow_instances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(String(20), default="pending")
    current_step = Column(Integer, default=0)
    context = Column(JSONB, default=dict)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class WorkflowStepLog(Base, TimestampMixin):
    """工作流步骤日志"""

    __tablename__ = "workflow_step_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflow_instances.id", ondelete="CASCADE"), nullable=False)
    step_id = Column(String(100), nullable=False)
    step_name = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)
    status = Column(String(20), default="pending")
    result = Column(JSONB, default=dict)
    error = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


# ── 数据库工具函数 ────────────────────────────────────────


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话（FastAPI依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """上下文管理器获取数据库会话"""
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
    """初始化数据库（创建扩展和表）"""
    from sqlalchemy import text

    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))

        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sales_app') THEN
                    CREATE ROLE sales_app WITH LOGIN PASSWORD 'secure_password';
                END IF;
            END $$;
        """))

        conn.commit()

    Base.metadata.create_all(bind=engine)

    _setup_rls()
    _setup_partition()


def _setup_rls() -> None:
    """设置行级安全策略"""
    from sqlalchemy import text

    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE customers ENABLE ROW LEVEL SECURITY"))
        conn.execute(text("ALTER TABLE leads ENABLE ROW LEVEL SECURITY"))
        conn.execute(text("ALTER TABLE deals ENABLE ROW LEVEL SECURITY"))
        conn.execute(text("ALTER TABLE quotes ENABLE ROW LEVEL SECURITY"))
        conn.execute(text("ALTER TABLE contracts ENABLE ROW LEVEL SECURITY"))
        conn.execute(text("ALTER TABLE payments ENABLE ROW LEVEL SECURITY"))
        conn.execute(text("ALTER TABLE workflow_instances ENABLE ROW LEVEL SECURITY"))

        conn.execute(text("""
            CREATE POLICY tenant_isolation_customers ON customers
                USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """))
        conn.execute(text("""
            CREATE POLICY tenant_isolation_leads ON leads
                USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """))
        conn.execute(text("""
            CREATE POLICY tenant_isolation_deals ON deals
                USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """))
        conn.execute(text("""
            CREATE POLICY tenant_isolation_quotes ON quotes
                USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """))
        conn.execute(text("""
            CREATE POLICY tenant_isolation_contracts ON contracts
                USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """))
        conn.execute(text("""
            CREATE POLICY tenant_isolation_payments ON payments
                USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """))
        conn.execute(text("""
            CREATE POLICY tenant_isolation_workflows ON workflow_instances
                USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """))

        conn.commit()


def _setup_partition() -> None:
    """设置审计日志分区表"""
    from sqlalchemy import text

    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_logs_2024 PARTITION OF audit_logs
            FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_logs_2025 PARTITION OF audit_logs
            FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_logs_2026 PARTITION OF audit_logs
            FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
        """))
        conn.commit()


def set_tenant_context(db: Session, tenant_id: str) -> None:
    """设置当前租户上下文"""
    db.execute(text(f"SET app.tenant_id = '{tenant_id}'"))


def clear_tenant_context(db: Session) -> None:
    """清除租户上下文"""
    db.execute(text("RESET app.tenant_id"))
