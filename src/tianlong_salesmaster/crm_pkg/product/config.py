"""tianlong_salesmaster.crm_pkg.product.config — 商品资料与定价配置

用户通过 Web 后台输入，存储在 JSON 文件中。
所有信息仅内部使用，不展示给客户。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional


DEFAULT_PRICING = {
    "trial": {"days": 7, "daily_limit": 30, "price": 0, "price_label": "免费"},
    "personal": {"price": 999, "period": "year", "price_label": "¥999/年"},
    "team": {"price": 4999, "period": "year", "price_label": "¥4,999/年"},
    "enterprise": {"price": 19999, "period": "year", "price_label": "¥19,999/年"},
}


@dataclass
class ProductConfig:
    """商品资料（私密，不展示给客户）"""

    # 基本信息
    name: str = ""
    description: str = ""
    tagline: str = ""

    # 价格
    price_min: float = 0.0
    price_max: float = 0.0
    pricing: Dict = field(default_factory=lambda: dict(DEFAULT_PRICING))

    # 销售策略
    core_strength: str = ""          # 核心竞争力
    target_industries: List[str] = field(default_factory=list)   # 目标行业
    keywords: List[str] = field(default_factory=list)            # 目标关键词

    # FAQ
    faq: List[Dict] = field(default_factory=list)  # [{"q": "...", "a": "..."}]

    # 安全模式默认值
    safe_price_ceiling: float = 0.0    # 价格天花板，0=不限制
    safe_discount_floor: float = 0.0   # 折扣底线（百分比），0=不限制
    safe_daily_limit: int = 0          # 日成交上限，0=不限制
    safe_sensitive_words: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)

    @property
    def is_configured(self) -> bool:
        """是否已完成基本配置"""
        return bool(self.name) and self.price_max > 0


def get_config_path(project_dir: str = ".") -> Path:
    """获取配置文件路径"""
    return Path(project_dir) / "product" / "config.json"


def load_product(project_dir: str = ".") -> ProductConfig:
    """从文件加载商品配置"""
    fp = get_config_path(project_dir)
    if fp.exists():
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            return ProductConfig(**data)
        except Exception:
            pass
    return ProductConfig()


def save_product(config: ProductConfig, project_dir: str = ".") -> None:
    """保存商品配置到文件"""
    fp = get_config_path(project_dir)
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(json.dumps(config.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def get_pricing_path(project_dir: str = ".") -> Path:
    """获取定价文件路径"""
    return Path(project_dir) / "product" / "pricing.json"


def load_pricing(project_dir: str = ".") -> Dict:
    """加载定价配置"""
    fp = get_pricing_path(project_dir)
    if fp.exists():
        try:
            return json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            pass
    return dict(DEFAULT_PRICING)


def save_pricing(pricing: Dict, project_dir: str = ".") -> None:
    """保存定价配置"""
    fp = get_pricing_path(project_dir)
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(json.dumps(pricing, ensure_ascii=False, indent=2), encoding="utf-8")
