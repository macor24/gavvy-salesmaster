"""tianlong_salesmaster.team_pkg.team.quickstart — 快速启动引导

社区版：内置基础行业模板
企业版：调用服务端获取定制化模板（需 TIANLONG_API_KEY）
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from tianlong_salesmaster.core.enterprise_client import EnterpriseAPIClient, EnterpriseConfig


QUICKSTART_INDUSTRIES = {
    "电商": {
        "pricing": {"base": 299, "enterprise": 999},
        "scripts": ["您好，我们是做电商解决方案的..."],
        "faq": [{"q": "价格多少", "a": "基础版299/月"}],
        "competitors": ["有赞", "微盟"],
    },
    "SaaS企业服务": {
        "pricing": {"base": 499, "enterprise": 1999},
        "scripts": ["了解到贵公司在使用XX系统，我们..."],
        "faq": [{"q": "支持私有部署吗", "a": "支持"}],
        "competitors": ["钉钉", "飞书"],
    },
    "AI/科技": {
        "pricing": {"base": 999, "enterprise": 4999},
        "scripts": ["我们在AI Agent领域有成熟方案..."],
        "faq": [{"q": "API接入复杂吗", "a": "3行代码接入"}],
        "competitors": ["OpenAI", "LangChain"],
    },
}


class QuickstartGuide:
    """快速启动引导

    社区版：返回内置基础模板
    企业版：调用服务端获取定制化模板
    """

    def __init__(self, config: Optional[EnterpriseConfig] = None):
        self._client = EnterpriseAPIClient(config)

    def get_industries(self) -> Dict:
        """获取行业模板列表"""
        return self._client.get_quickstart_industries()

    def apply_template(self, industry: str, product_name: str) -> Dict:
        """应用行业模板"""
        if self._client.config.is_enterprise:
            result = self._client._call_api("/quickstart/apply", {
                "industry": industry,
                "product_name": product_name,
            })
            return result

        tmpl = QUICKSTART_INDUSTRIES.get(industry, {})
        return {
            "product_name": product_name,
            "industry": industry,
            "pricing": tmpl.get("pricing", {}),
            "competitors": tmpl.get("competitors", []),
        }

    @staticmethod
    def generate_demo_data() -> List[Dict]:
        """生成演示数据"""
        return [
            {"id": "demo_1", "name": "演示客户A", "intent": "了解产品", "stage": "contact",
             "last_msg": "请介绍下方案", "last_time": "2026-05-03 10:00"},
            {"id": "demo_2", "name": "演示客户B", "intent": "咨询价格", "stage": "negotiation",
             "last_msg": "价格能再优惠吗", "last_time": "2026-05-03 10:30"},
        ]


__all__ = ["QuickstartGuide", "QUICKSTART_INDUSTRIES"]
