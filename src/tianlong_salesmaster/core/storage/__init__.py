"""SentriKit_salesmaster.core.storage — 统一数据库抽象层

支持多种数据库后端：
- SQLite (默认，开发/测试用)
- PostgreSQL
- MySQL

使用方法:
    from SentriKit_salesmaster.core.storage import get_db, get_db_context, init_database
    # 自动选择可用的数据库
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

_DEFAULT_DATABASE = "sqlite"

def _get_database_type() -> str:
    db_type = os.environ.get("DB_TYPE", _DEFAULT_DATABASE)
    return db_type.lower()

def _is_postgres_available() -> bool:
    try:
        from .database import Base
        return True
    except Exception:
        return False

def _is_mysql_available() -> bool:
    try:
        from .db_mysql import Base
        return True
    except Exception:
        return False

def _auto_detect_db() -> str:
    db_type = _get_database_type()
    if db_type == "postgres" and _is_postgres_available():
        return "postgres"
    if db_type == "mysql" and _is_mysql_available():
        return "mysql"
    return "sqlite"

_current_db = None

def set_database(db_type: str) -> None:
    """设置使用的数据库类型"""
    global _current_db
    valid = ["sqlite", "postgres", "mysql"]
    if db_type not in valid:
        raise ValueError(f"Invalid database type: {db_type}. Valid options: {valid}")
    _current_db = db_type

def get_current_database() -> str:
    """获取当前使用的数据库类型"""
    global _current_db
    if _current_db is None:
        _current_db = _auto_detect_db()
    return _current_db

def get_db() -> Generator[Any, None, None]:
    """获取数据库会话（FastAPI依赖注入）"""
    db_type = get_current_database()
    if db_type == "sqlite":
        from .db_sqlite import get_db as sqlite_get_db
        return sqlite_get_db()
    elif db_type == "postgres":
        from .database import get_db as pg_get_db
        return pg_get_db()
    elif db_type == "mysql":
        from .db_mysql import get_db as mysql_get_db
        return mysql_get_db()
    raise ValueError(f"Unknown database type: {db_type}")

@contextmanager
def get_db_context() -> Generator[Any, None, None]:
    """上下文管理器获取数据库会话"""
    db_type = get_current_database()
    if db_type == "sqlite":
        from .db_sqlite import get_db_context as sqlite_ctx
        with sqlite_ctx() as db:
            yield db
    elif db_type == "postgres":
        from .database import get_db_context as pg_ctx
        with pg_ctx() as db:
            yield db
    elif db_type == "mysql":
        from .db_mysql import get_db_context as mysql_ctx
        with mysql_ctx() as db:
            yield db
    else:
        raise ValueError(f"Unknown database type: {db_type}")

def init_database() -> None:
    """初始化数据库（创建表）"""
    db_type = get_current_database()
    if db_type == "sqlite":
        from .db_sqlite import init_database as sqlite_init
        sqlite_init()
    elif db_type == "postgres":
        from .database import init_database as pg_init
        pg_init()
    elif db_type == "mysql":
        from .db_mysql import init_database as mysql_init
        mysql_init()

def migrate_from_json(data_dir: Optional[str] = None) -> Dict[str, int]:
    """从 JSON 文件迁移数据到当前数据库"""
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "_data")

    db_type = get_current_database()
    from .migration import migrate_all_from_json
    from .db_sqlite import get_db_context as sqlite_ctx

    if db_type == "sqlite":
        return migrate_all_from_json(data_dir, sqlite_ctx)
    elif db_type == "postgres":
        from .database import get_db_context as pg_ctx
        from .migration import migrate_to_postgres
        migrate_to_postgres(data_dir)
        return {}
    elif db_type == "mysql":
        from .db_mysql import get_db_context as mysql_ctx
        return migrate_all_from_json(data_dir, mysql_ctx)
    else:
        raise ValueError(f"Unknown database type: {db_type}")

__all__ = [
    "get_db",
    "get_db_context",
    "init_database",
    "migrate_from_json",
    "set_database",
    "get_current_database",
    "DatabaseKernel",
    "get_kernel",
    "DataRepository",
    "get_repository",
    "StatsEngine",
    "get_storage_dir",
    "set_storage_dir",
]

from .db import DatabaseKernel, get_kernel
from .repository import DataRepository, get_repository
from .stats import StatsEngine
from .db import get_storage_dir, set_storage_dir
