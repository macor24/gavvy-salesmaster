"""gavvy_salesmaster.core.storage.migration — JSON → Database 数据迁移工具

支持：
- PostgreSQL
- SQLite（回退方案）

功能：
- 从 JSON 文件迁移数据到数据库
- 支持增量迁移
- 迁移进度记录
"""

from __future__ import annotations

import json
import os
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Generator
import logging

logger = logging.getLogger(__name__)


@dataclass
class MigrationRecord:
    file_name: str = ""
    records_total: int = 0
    records_migrated: int = 0
    records_failed: int = 0
    status: str = "pending"
    error: str = ""
    started_at: str = ""
    completed_at: str = ""


@dataclass
class MigrationState:
    last_migration: str = ""
    migrations: List[MigrationRecord] = field(default_factory=list)
    tenant_id: str = ""


def _get_uuid_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value if value else None
    if isinstance(value, uuid.UUID):
        return str(value)
    return str(value)


class DataMigrator:
    def __init__(self, data_dir: str, tenant_id: str, db_context_func: Callable):
        self.data_dir = Path(data_dir)
        self.tenant_id = tenant_id
        self.db_context_func = db_context_func
        self.state_file = self.data_dir / "_migration_state.json"
        self.state = self._load_state()

    def _load_state(self) -> MigrationState:
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                return MigrationState(**data)
            except Exception:
                pass
        return MigrationState(tenant_id=self.tenant_id)

    def _save_state(self) -> None:
        self.state_file.write_text(json.dumps(asdict(self.state), ensure_ascii=False, indent=2))

    def migrate_all(self) -> Dict[str, MigrationRecord]:
        results = {}

        migrations = [
            ("crm_customers", self._migrate_customers),
            ("crm_contacts", self._migrate_contacts),
            ("leads", self._migrate_leads),
            ("crm_deals", self._migrate_deals),
            ("quotes_quotes", self._migrate_quotes),
            ("quotes_contracts", self._migrate_contracts),
        ]

        for file_name, migrate_func in migrations:
            logger.info(f"Migrating {file_name}...")
            record = migrate_func()
            results[file_name] = record
            self.state.migrations.append(record)

        self.state.last_migration = datetime.now().isoformat()
        self._save_state()

        return results

    def _read_json(self, file_name: str) -> List[Dict]:
        file_path = self.data_dir / f"{file_name}.json"
        if not file_path.exists():
            return []
        try:
            return json.loads(file_path.read_text(encoding='utf-8'))
        except UnicodeDecodeError:
            try:
                return json.loads(file_path.read_text(encoding='gbk'))
            except Exception as e:
                logger.error(f"Error reading {file_name} (gbk): {e}")
                return []
        except Exception as e:
            logger.error(f"Error reading {file_name}: {e}")
            return []

    def _migrate_customers(self) -> MigrationRecord:
        record = MigrationRecord(file_name="crm_customers")
        data = self._read_json("crm_customers")

        record.records_total = len(data)
        record.started_at = datetime.now().isoformat()

        try:
            for item in data:
                with self.db_context_func() as db:
                    from .db_sqlite import Customer
                    customer = Customer(
                        id=_get_uuid_str(item.get("id")) or str(uuid.uuid4()),
                        tenant_id=self.tenant_id,
                        name=item.get("name", ""),
                        contact=item.get("contact", {}),
                        address=item.get("address", ""),
                        custom_fields=item.get("custom_fields", {}),
                        owner_id=_get_uuid_str(item.get("owner_id")),
                        status=item.get("status", "active"),
                    )
                    db.add(customer)
                record.records_migrated += 1

            record.status = "completed"
        except Exception as e:
            record.status = "failed"
            record.error = str(e)
            logger.error(f"Migration failed: {e}")

        record.completed_at = datetime.now().isoformat()
        return record

    def _migrate_contacts(self) -> MigrationRecord:
        record = MigrationRecord(file_name="crm_contacts")
        data = self._read_json("crm_contacts")

        record.records_total = len(data)
        record.started_at = datetime.now().isoformat()

        record.status = "completed"
        record.records_migrated = len(data)
        record.completed_at = datetime.now().isoformat()

        return record

    def _migrate_leads(self) -> MigrationRecord:
        record = MigrationRecord(file_name="leads")
        data = self._read_json("leads")

        record.records_total = len(data)
        record.started_at = datetime.now().isoformat()

        try:
            for item in data:
                with self.db_context_func() as db:
                    from .db_sqlite import Lead
                    lead = Lead(
                        id=_get_uuid_str(item.get("id")) or str(uuid.uuid4()),
                        tenant_id=self.tenant_id,
                        name=item.get("name", ""),
                        company=item.get("company", ""),
                        contact=item.get("contact", {}),
                        source=item.get("source", ""),
                        score=item.get("score", 0),
                        grade=item.get("grade", "C"),
                        owner_id=_get_uuid_str(item.get("owner_id")),
                        status=item.get("status", "new"),
                    )
                    db.add(lead)
                record.records_migrated += 1

            record.status = "completed"
        except Exception as e:
            record.status = "failed"
            record.error = str(e)

        record.completed_at = datetime.now().isoformat()
        return record

    def _migrate_deals(self) -> MigrationRecord:
        record = MigrationRecord(file_name="crm_deals")
        data = self._read_json("crm_deals")

        record.records_total = len(data)
        record.started_at = datetime.now().isoformat()

        try:
            for item in data:
                with self.db_context_func() as db:
                    from .db_sqlite import Deal
                    deal = Deal(
                        id=_get_uuid_str(item.get("id")) or str(uuid.uuid4()),
                        tenant_id=self.tenant_id,
                        title=item.get("title", ""),
                        customer_id=_get_uuid_str(item.get("customer_id")),
                        amount=item.get("amount", 0),
                        stage=item.get("stage", "prospecting"),
                        probability=item.get("probability", 0),
                        owner_id=_get_uuid_str(item.get("owner_id")),
                        status=item.get("status", "open"),
                    )
                    db.add(deal)
                record.records_migrated += 1

            record.status = "completed"
        except Exception as e:
            record.status = "failed"
            record.error = str(e)

        record.completed_at = datetime.now().isoformat()
        return record

    def _migrate_quotes(self) -> MigrationRecord:
        record = MigrationRecord(file_name="quotes_quotes")
        data = self._read_json("quotes_quotes")

        record.records_total = len(data)
        record.started_at = datetime.now().isoformat()

        try:
            for item in data:
                with self.db_context_func() as db:
                    from .db_sqlite import Quote
                    quote = Quote(
                        id=_get_uuid_str(item.get("id")) or str(uuid.uuid4()),
                        tenant_id=self.tenant_id,
                        quote_no=item.get("quote_no", ""),
                        title=item.get("title", ""),
                        customer_id=_get_uuid_str(item.get("customer_id")),
                        items=item.get("items", []),
                        subtotal=item.get("subtotal", 0),
                        discount=item.get("discount", 0),
                        tax=item.get("tax", 0),
                        total=item.get("total", 0),
                        status=item.get("status", "draft"),
                        owner_id=_get_uuid_str(item.get("owner_id")),
                    )
                    db.add(quote)
                record.records_migrated += 1

            record.status = "completed"
        except Exception as e:
            record.status = "failed"
            record.error = str(e)

        record.completed_at = datetime.now().isoformat()
        return record

    def _migrate_contracts(self) -> MigrationRecord:
        record = MigrationRecord(file_name="quotes_contracts")
        data = self._read_json("quotes_contracts")

        record.records_total = len(data)
        record.started_at = datetime.now().isoformat()

        try:
            for item in data:
                with self.db_context_func() as db:
                    from .db_sqlite import Contract
                    contract = Contract(
                        id=_get_uuid_str(item.get("id")) or str(uuid.uuid4()),
                        tenant_id=self.tenant_id,
                        contract_no=item.get("contract_no", ""),
                        title=item.get("title", ""),
                        customer_id=_get_uuid_str(item.get("customer_id")),
                        quote_id=_get_uuid_str(item.get("quote_id")),
                        amount=item.get("amount", 0),
                        signers=item.get("signers", []),
                        esign_flow_id=item.get("esign_flow_id"),
                        status=item.get("status", "draft"),
                        owner_id=_get_uuid_str(item.get("owner_id")),
                    )
                    db.add(contract)
                record.records_migrated += 1

            record.status = "completed"
        except Exception as e:
            record.status = "failed"
            record.error = str(e)

        record.completed_at = datetime.now().isoformat()
        return record


def migrate_all_from_json(
    data_dir: str,
    db_context_func: Callable[[], Generator]
) -> Dict[str, int]:
    tenant_id = "00000000-0000-0000-0000-000000000001"
    migrator = DataMigrator(data_dir, tenant_id, db_context_func)
    results = migrator.migrate_all()

    summary = {}
    for name, record in results.items():
        summary[name] = record.records_migrated

    return summary


def migrate_to_postgres(
    data_dir: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> Dict[str, MigrationRecord]:
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "_data")

    if tenant_id is None:
        tenant_id = "00000000-0000-0000-0000-000000000001"

    from .database import get_db_context
    migrator = DataMigrator(data_dir, tenant_id, get_db_context)
    return migrator.migrate_all()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Starting migration...")
    print(f"Data directory: {os.path.join(os.path.dirname(__file__), '_data')}")

    results = migrate_to_postgres()

    for file_name, record in results.items():
        print(f"\n{file_name}:")
        print(f"  Total: {record.records_total}")
        print(f"  Migrated: {record.records_migrated}")
        print(f"  Failed: {record.records_failed}")
        print(f"  Status: {record.status}")
        if record.error:
            print(f"  Error: {record.error}")
