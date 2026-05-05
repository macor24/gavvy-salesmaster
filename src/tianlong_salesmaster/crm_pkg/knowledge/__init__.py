"""SentriKit_salesmaster.crm_pkg.knowledge — 产品知识库系统

完整的产品知识库系统，包含：
- 知识条目管理（新增、编辑、删除）
- FAQ 问答管理
- 智能搜索（关键词匹配 + 语义检索）
- 分类与标签体系
- Agent 训练与知识注入
- 版本历史记录

使用方法：
    from SentriKit_salesmaster.crm_pkg.knowledge import KnowledgeBase

    kb = KnowledgeBase()

    # 添加知识条目
    kb.add_item(
        title="产品价格政策",
        content="我们的产品支持 7 天无理由退换...",
        category="产品政策",
        tags=["价格", "退换货", "售后"]
    )

    # 搜索知识
    results = kb.search("价格政策")

    # 获取 Agent 训练素材
    training_data = kb.get_training_for_agent("presales_agent")
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union


# ── 数据类型定义 ────────────────────────────────────────

@dataclass
class KnowledgeItem:
    """知识条目"""
    id: str = ""
    title: str = ""
    content: str = ""
    category: str = ""
    tags: List[str] = field(default_factory=list)
    priority: int = 1  # 优先级，1-5，数字越大越优先
    status: str = "published"  # published / draft / archived
    version: int = 1
    created_at: str = ""
    updated_at: str = ""
    views: int = 0
    useful_count: int = 0
    extra: Dict = field(default_factory=dict)

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
    def from_dict(data: Dict) -> KnowledgeItem:
        return KnowledgeItem(**data)


@dataclass
class FAQItem:
    """常见问答对"""
    id: str = ""
    question: str = ""
    answer: str = ""
    category: str = ""
    tags: List[str] = field(default_factory=list)
    use_count: int = 0
    positive_rating: int = 0
    created_at: str = ""
    updated_at: str = ""
    extra: Dict = field(default_factory=dict)

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
    def from_dict(data: Dict) -> FAQItem:
        return FAQItem(**data)


@dataclass
class Category:
    """知识分类"""
    id: str = ""
    name: str = ""
    parent_id: str = ""
    description: str = ""
    sort_order: int = 0
    item_count: int = 0
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> Category:
        return Category(**data)


@dataclass
class SearchResult:
    """搜索结果"""
    item: Union[KnowledgeItem, FAQItem]
    score: float
    match_type: str  # "keyword" / "semantic" / "tag"
    highlights: List[str] = field(default_factory=list)


# ── 知识库主类 ──────────────────────────────────────────

class KnowledgeBase:
    """产品知识库核心类"""

    def __init__(self, storage_dir: Optional[str] = None):
        from .db import get_kb_kernel
        self.db = get_kb_kernel(storage_dir)
        self._init_default_categories()

    # ── 分类管理 ──────────────────────────────────────

    def _init_default_categories(self) -> None:
        """初始化默认分类"""
        categories = self.get_categories()
        if not categories:
            default_cats = [
                {"name": "产品政策", "description": "价格、折扣、促销活动等"},
                {"name": "售后服务", "description": "退换货、保修、客服政策等"},
                {"name": "技术规格", "description": "产品参数、技术要求、兼容性等"},
                {"name": "常见问题", "description": "用户常见疑问解答"},
                {"name": "竞争对手", "description": "竞品对比、优劣势分析"},
                {"name": "销售话术", "description": "销售沟通技巧与话术"},
            ]
            for cat_data in default_cats:
                self.add_category(cat_data["name"], cat_data["description"])

    def add_category(self, name: str, description: str = "",
                     parent_id: str = "", sort_order: int = 0) -> Category:
        """添加分类"""
        cat = Category(
            name=name,
            description=description,
            parent_id=parent_id,
            sort_order=sort_order
        )
        cats = self.db.get_categories()
        cats.append(cat.to_dict())
        self.db.save_categories(cats)
        return cat

    def get_categories(self) -> List[Category]:
        """获取所有分类"""
        data = self.db.get_categories()
        return [Category.from_dict(d) for d in data]

    def get_category_by_name(self, name: str) -> Optional[Category]:
        """按名称获取分类"""
        for cat in self.get_categories():
            if cat.name == name:
                return cat
        return None

    # ── 知识条目管理 ──────────────────────────────────────

    def add_item(self, title: str, content: str,
                 category: str = "", tags: Optional[List[str]] = None,
                 priority: int = 1) -> KnowledgeItem:
        """添加知识条目"""
        item = KnowledgeItem(
            title=title,
            content=content,
            category=category,
            tags=tags or [],
            priority=priority
        )
        items = self.db.get_items()
        items.append(item.to_dict())
        self.db.save_items(items)
        # 更新分类计数
        self._update_category_counts()
        return item

    def get_items(self, category: Optional[str] = None,
                  status: str = "published") -> List[KnowledgeItem]:
        """获取知识条目列表"""
        data = self.db.get_items()
        items = [KnowledgeItem.from_dict(d) for d in data]
        # 过滤
        if category:
            items = [i for i in items if i.category == category]
        if status:
            items = [i for i in items if i.status == status]
        # 排序：优先级降序 + 更新时间降序
        items.sort(key=lambda x: (-x.priority, x.updated_at), reverse=True)
        return items

    def get_item(self, item_id: str) -> Optional[KnowledgeItem]:
        """获取单个知识条目"""
        items = self.db.get_items()
        for data in items:
            if data["id"] == item_id:
                item = KnowledgeItem.from_dict(data)
                item.views += 1
                self.update_item(item)
                return item
        return None

    def update_item(self, item: KnowledgeItem) -> bool:
        """更新知识条目"""
        item.version += 1
        item.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        items = self.db.get_items()
        for i, data in enumerate(items):
            if data["id"] == item.id:
                items[i] = item.to_dict()
                self.db.save_items(items)
                self._update_category_counts()
                return True
        return False

    def delete_item(self, item_id: str) -> bool:
        """删除知识条目"""
        items = self.db.get_items()
        for i, data in enumerate(items):
            if data["id"] == item_id:
                del items[i]
                self.db.save_items(items)
                self._update_category_counts()
                return True
        return False

    def mark_useful(self, item_id: str) -> bool:
        """标记为有用（点赞）"""
        item = self.get_item(item_id)
        if item:
            item.useful_count += 1
            self.update_item(item)
            return True
        return False

    def _update_category_counts(self) -> None:
        """更新分类下的条目数量"""
        items = self.db.get_items()
        category_counts: Dict[str, int] = {}
        for item in items:
            cat = item.get("category", "")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        cats = self.get_categories()
        for cat in cats:
            cat.item_count = category_counts.get(cat.name, 0)
        self.db.save_categories([c.to_dict() for c in cats])

    # ── FAQ 管理 ──────────────────────────────────────

    def add_faq(self, question: str, answer: str,
                category: str = "常见问题",
                tags: Optional[List[str]] = None) -> FAQItem:
        """添加 FAQ"""
        faq = FAQItem(
            question=question,
            answer=answer,
            category=category,
            tags=tags or []
        )
        faqs = self.db.get_faqs()
        faqs.append(faq.to_dict())
        self.db.save_faqs(faqs)
        return faq

    def get_faqs(self, category: Optional[str] = None) -> List[FAQItem]:
        """获取 FAQ 列表"""
        data = self.db.get_faqs()
        faqs = [FAQItem.from_dict(d) for d in data]
        if category:
            faqs = [f for f in faqs if f.category == category]
        return faqs

    def get_faq(self, faq_id: str) -> Optional[FAQItem]:
        """获取单个 FAQ"""
        faqs = self.db.get_faqs()
        for data in faqs:
            if data["id"] == faq_id:
                faq = FAQItem.from_dict(data)
                faq.use_count += 1
                self.update_faq(faq)
                return faq
        return None

    def update_faq(self, faq: FAQItem) -> bool:
        """更新 FAQ"""
        faq.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        faqs = self.db.get_faqs()
        for i, data in enumerate(faqs):
            if data["id"] == faq.id:
                faqs[i] = faq.to_dict()
                self.db.save_faqs(faqs)
                return True
        return False

    def rate_faq(self, faq_id: str, positive: bool = True) -> bool:
        """评价 FAQ（有用/没用）"""
        faq = self.get_faq(faq_id)
        if faq:
            if positive:
                faq.positive_rating += 1
            else:
                faq.positive_rating = max(0, faq.positive_rating - 1)
            self.update_faq(faq)
            return True
        return False

    # ── 搜索功能 ──────────────────────────────────────

    def search(self, query: str, limit: int = 20,
               search_faqs: bool = True) -> List[SearchResult]:
        """搜索知识条目和 FAQ"""
        results: List[SearchResult] = []
        query = query.lower().strip()

        if not query:
            return results

        # 搜索知识条目
        items = self.get_items()
        for item in items:
            score, match_type, highlights = self._calculate_match(item, query)
            if score > 0:
                results.append(SearchResult(
                    item=item,
                    score=score,
                    match_type=match_type,
                    highlights=highlights
                ))

        # 搜索 FAQ
        if search_faqs:
            faqs = self.get_faqs()
            for faq in faqs:
                score, match_type, highlights = self._calculate_match_faq(faq, query)
                if score > 0:
                    results.append(SearchResult(
                        item=faq,
                        score=score,
                        match_type=match_type,
                        highlights=highlights
                    ))

        # 排序：分数降序
        results.sort(key=lambda x: -x.score)
        return results[:limit]

    def _calculate_match(self, item: KnowledgeItem, query: str) -> tuple:
        """计算匹配度"""
        score = 0.0
        match_type = ""
        highlights: List[str] = []

        # 标题匹配
        if query in item.title.lower():
            score += 3.0
            match_type = "keyword"
            highlights.append(self._highlight(item.title, query))

        # 内容匹配
        if query in item.content.lower():
            score += 1.0
            if not match_type:
                match_type = "keyword"
            highlights.append(self._highlight_excerpt(item.content, query))

        # 标签匹配
        for tag in item.tags:
            if query in tag.lower():
                score += 0.5
                match_type = "tag"
                highlights.append(f"标签: {tag}")

        # 分类匹配
        if query in item.category.lower():
            score += 0.3

        # 优先级加成
        score *= (0.8 + item.priority * 0.08)
        return score, match_type, highlights

    def _calculate_match_faq(self, faq: FAQItem, query: str) -> tuple:
        """计算 FAQ 匹配度"""
        score = 0.0
        match_type = ""
        highlights: List[str] = []

        # 问题匹配
        if query in faq.question.lower():
            score += 3.0
            match_type = "keyword"
            highlights.append(self._highlight(faq.question, query))

        # 答案匹配
        if query in faq.answer.lower():
            score += 1.0
            if not match_type:
                match_type = "keyword"
            highlights.append(self._highlight_excerpt(faq.answer, query))

        # 标签匹配
        for tag in faq.tags:
            if query in tag.lower():
                score += 0.5
                match_type = "tag"

        return score, match_type, highlights

    @staticmethod
    def _highlight(text: str, query: str) -> str:
        """高亮匹配词"""
        # 简单高亮
        regex = re.compile(re.escape(query), re.IGNORECASE)
        return regex.sub(f"[{query}]", text)

    @staticmethod
    def _highlight_excerpt(text: str, query: str) -> str:
        """高亮摘要"""
        idx = text.lower().find(query.lower())
        if idx >= 0:
            start = max(0, idx - 30)
            end = min(len(text), idx + len(query) + 50)
            excerpt = text[start:end]
            if start > 0:
                excerpt = "..." + excerpt
            if end < len(text):
                excerpt += "..."
            return excerpt
        return text[:100] + "..." if len(text) > 100 else text

    # ── Agent 训练功能 ──────────────────────────────────────

    def get_training_for_agent(self, agent_role: str) -> List[Dict]:
        """获取 Agent 训练素材"""
        training_data: List[Dict] = []

        # 根据不同 Agent 角色获取不同知识
        items = self.get_items()
        faqs = self.get_faqs()

        # 基础训练素材（所有 Agent）
        for item in items:
            training_data.append({
                "type": "knowledge",
                "title": item.title,
                "content": item.content,
                "category": item.category,
                "priority": item.priority,
            })

        for faq in faqs:
            training_data.append({
                "type": "faq",
                "question": faq.question,
                "answer": faq.answer,
                "category": faq.category,
            })

        # 根据 Agent 角色过滤
        if agent_role == "presales_agent":
            training_data = [d for d in training_data
                            if d["category"] in ["产品政策", "销售话术", "常见问题"]]
        elif agent_role == "aftersales_agent":
            training_data = [d for d in training_data
                            if d["category"] in ["售后服务", "常见问题"]]
        elif agent_role == "competitor_intel":
            training_data = [d for d in training_data
                            if d["category"] in ["竞争对手"]]

        return training_data

    def train_agent_with_knowledge(self, agent_role: str) -> str:
        """生成 Agent 训练提示词"""
        training_data = self.get_training_for_agent(agent_role)
        if not training_data:
            return ""

        prompt = f"""你是专业的 {agent_role} 销售助手。

以下是你需要掌握的产品知识：

"""
        for data in training_data:
            if data["type"] == "knowledge":
                prompt += f"\n【{data['title']}】\n{data['content']}\n"
            elif data["type"] == "faq":
                prompt += f"\n问：{data['question']}\n答：{data['answer']}\n"

        prompt += """

请根据以上知识回答客户问题，确保回答准确一致。
如果问题超出知识库范围，请告知客户并建议咨询人工客服。

回答要求：
- 友好专业
- 简洁清晰
- 基于知识库，不编造信息
- 不确定时建议人工确认

"""
        return prompt

    # ── 统计功能 ──────────────────────────────────────

    def get_stats(self) -> Dict:
        """获取知识库统计"""
        items = self.get_items()
        faqs = self.get_faqs()
        categories = self.get_categories()

        total_views = sum(i.get("views", 0) for i in self.db.get_items())
        total_useful = sum(i.get("useful_count", 0) for i in self.db.get_items())

        return {
            "total_items": len(items),
            "total_faqs": len(faqs),
            "total_categories": len(categories),
            "total_views": total_views,
            "total_useful": total_useful,
            "top_items": self._get_top_items(items, limit=5),
            "top_faqs": self._get_top_faqs(faqs, limit=5),
        }

    def _get_top_items(self, items: List[KnowledgeItem], limit: int) -> List[Dict]:
        sorted_items = sorted(items, key=lambda x: (-x.useful_count, -x.views))[:limit]
        return [{"id": i.id, "title": i.title, "views": i.views, "useful": i.useful_count}
                for i in sorted_items]

    def _get_top_faqs(self, faqs: List[FAQItem], limit: int) -> List[Dict]:
        sorted_faqs = sorted(faqs, key=lambda x: (-x.positive_rating, -x.use_count))[:limit]
        return [{"id": f.id, "question": f.question, "use_count": f.use_count,
                 "positive": f.positive_rating} for f in sorted_faqs]

    # ── 导入/导出功能 ──────────────────────────────────────

    def export_all(self) -> Dict:
        """导出所有知识数据"""
        return {
            "items": self.db.get_items(),
            "faqs": self.db.get_faqs(),
            "categories": self.db.get_categories(),
            "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def import_all(self, data: Dict, overwrite: bool = False) -> tuple:
        """导入知识数据"""
        imported_count = 0
        error_count = 0

        try:
            if "categories" in data:
                if overwrite:
                    self.db.save_categories(data["categories"])
                else:
                    for cat_data in data["categories"]:
                        exists = any(c["name"] == cat_data["name"]
                                     for c in self.db.get_categories())
                        if not exists:
                            cats = self.db.get_categories()
                            cats.append(cat_data)
                            self.db.save_categories(cats)

            if "items" in data:
                for item_data in data["items"]:
                    items = self.db.get_items()
                    exists = any(i["id"] == item_data["id"] for i in items)
                    if not exists or overwrite:
                        if exists and overwrite:
                            items = [i for i in items if i["id"] != item_data["id"]]
                        items.append(item_data)
                        self.db.save_items(items)
                        imported_count += 1

            if "faqs" in data:
                for faq_data in data["faqs"]:
                    faqs = self.db.get_faqs()
                    exists = any(f["id"] == faq_data["id"] for f in faqs)
                    if not exists or overwrite:
                        if exists and overwrite:
                            faqs = [f for f in faqs if f["id"] != faq_data["id"]]
                        faqs.append(faq_data)
                        self.db.save_faqs(faqs)
                        imported_count += 1

            self._update_category_counts()

        except Exception as e:
            error_count += 1
            print(f"[KnowledgeBase] 导入错误: {e}")

        return imported_count, error_count

    # ── 快捷操作 ──────────────────────────────────────

    def quick_add_faq(self, question: str, answer: str) -> FAQItem:
        """快速添加 FAQ（自动分类）"""
        category = "常见问题"
        for keyword in ["价格", "费用", "折扣"]:
            if keyword in question:
                category = "产品政策"
                break
        for keyword in ["退换", "退款", "售后", "保修"]:
            if keyword in question:
                category = "售后服务"
                break

        return self.add_faq(question, answer, category=category)

    def batch_add_items(self, item_list: List[Dict]) -> int:
        """批量添加知识条目"""
        count = 0
        for data in item_list:
            try:
                self.add_item(
                    title=data.get("title", ""),
                    content=data.get("content", ""),
                    category=data.get("category", ""),
                    tags=data.get("tags", []),
                    priority=data.get("priority", 1)
                )
                count += 1
            except Exception:
                pass
        return count

    def __repr__(self) -> str:
        stats = self.get_stats()
        return f"<KnowledgeBase items={stats['total_items']} faqs={stats['total_faqs']}>"


# ── 全局单例 ──────────────────────────────────────

_global_kb: Optional[KnowledgeBase] = None


def get_knowledge_base(storage_dir: Optional[str] = None) -> KnowledgeBase:
    """获取全局知识库单例"""
    global _global_kb
    if _global_kb is None:
        _global_kb = KnowledgeBase(storage_dir)
    return _global_kb
