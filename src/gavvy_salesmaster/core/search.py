"""gavvy_salesmaster.core.search — 模糊搜索与高级筛选引擎

提供：
- 模糊字符串匹配
- 多条件高级筛选
- 排序与分页
- 全文搜索
- 标签筛选
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# ── 模糊匹配算法 ──────────────────────────────────────


def levenshtein_distance(s1: str, s2: str) -> int:
    """计算两个字符串的编辑距离"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def fuzzy_match(query: str, text: str, threshold: float = 0.6) -> float:
    """
    模糊匹配，返回相似度分数 (0-1)
    
    :param query: 搜索词
    :param text: 目标文本
    :param threshold: 匹配阈值
    :return: 相似度分数，如果低于阈值返回0
    """
    query = query.lower().strip()
    text = text.lower().strip()
    
    if not query or not text:
        return 0.0
    
    # 完全匹配
    if query == text:
        return 1.0
    
    # 包含匹配
    if query in text:
        return 0.9 + (len(query) / len(text)) * 0.1
    
    # 编辑距离匹配
    max_len = max(len(query), len(text))
    if max_len == 0:
        return 0.0
    
    distance = levenshtein_distance(query, text)
    similarity = 1 - (distance / max_len)
    
    if similarity >= threshold:
        return similarity
    
    return 0.0


def multi_field_match(query: str, fields: List[str], weights: Optional[List[float]] = None) -> float:
    """
    多字段模糊匹配，返回综合相似度分数
    
    :param query: 搜索词
    :param fields: 字段值列表
    :param weights: 字段权重列表
    :return: 综合相似度分数
    """
    if weights is None:
        weights = [1.0] * len(fields)
    
    total_weight = sum(weights)
    if total_weight == 0:
        return 0.0
    
    score = 0.0
    for field, weight in zip(fields, weights):
        score += fuzzy_match(query, str(field)) * weight
    
    return score / total_weight


# ── 高级筛选器 ──────────────────────────────────────


class FilterOperator:
    """筛选操作符"""
    EQ = "eq"          # 等于
    NEQ = "neq"        # 不等于
    CONTAINS = "contains"  # 包含
    NOT_CONTAINS = "not_contains"  # 不包含
    STARTS_WITH = "starts_with"    # 以...开头
    ENDS_WITH = "ends_with"        # 以...结尾
    GT = "gt"          # 大于
    LT = "lt"          # 小于
    GTE = "gte"        # 大于等于
    LTE = "lte"        # 小于等于
    IN = "in"          # 在列表中
    NOT_IN = "not_in"  # 不在列表中
    BETWEEN = "between"  # 在范围内
    IS_EMPTY = "is_empty"  # 为空
    NOT_EMPTY = "not_empty"  # 不为空
    LIKE = "like"      # 模糊匹配


class FilterCondition:
    """筛选条件"""
    
    def __init__(self, field: str, operator: str, value: Any):
        self.field = field
        self.operator = operator.lower()
        self.value = value
    
    def matches(self, item: Dict) -> bool:
        """检查项目是否满足条件"""
        field_value = item.get(self.field)
        
        try:
            return self._evaluate(field_value)
        except Exception:
            return False
    
    def _evaluate(self, field_value: Any) -> bool:
        """执行条件判断"""
        op = self.operator
        
        if op == FilterOperator.EQ:
            return field_value == self.value
        
        elif op == FilterOperator.NEQ:
            return field_value != self.value
        
        elif op == FilterOperator.CONTAINS:
            return str(self.value).lower() in str(field_value).lower()
        
        elif op == FilterOperator.NOT_CONTAINS:
            return str(self.value).lower() not in str(field_value).lower()
        
        elif op == FilterOperator.STARTS_WITH:
            return str(field_value).lower().startswith(str(self.value).lower())
        
        elif op == FilterOperator.ENDS_WITH:
            return str(field_value).lower().endswith(str(self.value).lower())
        
        elif op == FilterOperator.GT:
            return float(field_value) > float(self.value)
        
        elif op == FilterOperator.LT:
            return float(field_value) < float(self.value)
        
        elif op == FilterOperator.GTE:
            return float(field_value) >= float(self.value)
        
        elif op == FilterOperator.LTE:
            return float(field_value) <= float(self.value)
        
        elif op == FilterOperator.IN:
            values = self.value if isinstance(self.value, list) else [self.value]
            return field_value in values
        
        elif op == FilterOperator.NOT_IN:
            values = self.value if isinstance(self.value, list) else [self.value]
            return field_value not in values
        
        elif op == FilterOperator.BETWEEN:
            if not isinstance(self.value, list) or len(self.value) != 2:
                return False
            return float(self.value[0]) <= float(field_value) <= float(self.value[1])
        
        elif op == FilterOperator.IS_EMPTY:
            return field_value is None or field_value == "" or field_value == []
        
        elif op == FilterOperator.NOT_EMPTY:
            return not (field_value is None or field_value == "" or field_value == [])
        
        elif op == FilterOperator.LIKE:
            pattern = str(self.value).replace("%", ".*")
            return bool(re.match(f".*{pattern}.*", str(field_value), re.IGNORECASE))
        
        return False


class FilterGroup:
    """筛选条件组"""
    
    def __init__(self, conditions: List[Union[FilterCondition, 'FilterGroup']], operator: str = "and"):
        self.conditions = conditions
        self.operator = operator.lower()
    
    def matches(self, item: Dict) -> bool:
        """检查项目是否满足条件组"""
        if self.operator == "and":
            return all(c.matches(item) for c in self.conditions)
        else:  # or
            return any(c.matches(item) for c in self.conditions)
    
    @staticmethod
    def from_dict(data: Dict) -> 'FilterGroup':
        """从字典创建筛选条件组"""
        operator = data.get("operator", "and")
        conditions = []
        
        for cond in data.get("conditions", []):
            if "conditions" in cond:
                # 嵌套条件组
                conditions.append(FilterGroup.from_dict(cond))
            else:
                # 简单条件
                conditions.append(FilterCondition(
                    field=cond.get("field", ""),
                    operator=cond.get("operator", "eq"),
                    value=cond.get("value")
                ))
        
        return FilterGroup(conditions, operator)


# ── 排序器 ──────────────────────────────────────────


class SortField:
    """排序字段"""
    
    def __init__(self, field: str, direction: str = "asc"):
        self.field = field
        self.direction = direction.lower()
    
    def get_key(self, item: Dict) -> Any:
        """获取排序键"""
        value = item.get(self.field)
        if value is None:
            return ""
        return value
    
    def is_ascending(self) -> bool:
        """是否升序"""
        return self.direction == "asc"


# ── 搜索结果 ────────────────────────────────────────


@dataclass
class SearchResult:
    """搜索结果"""
    items: List[Dict] = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    has_more: bool = False
    query: str = ""
    filters: Optional[Dict] = None


# ── 搜索管理器 ──────────────────────────────────────


class SearchManager:
    """搜索管理器"""
    
    def __init__(self):
        self._index_cache = {}
    
    def search(
        self,
        items: List[Dict],
        query: str = "",
        filters: Optional[Dict] = None,
        sort_by: Optional[List[Dict]] = None,
        page: int = 1,
        page_size: int = 20,
        search_fields: Optional[List[str]] = None,
        field_weights: Optional[List[float]] = None
    ) -> SearchResult:
        """
        执行搜索
        
        :param items: 数据源列表
        :param query: 搜索关键词（模糊匹配）
        :param filters: 高级筛选条件
        :param sort_by: 排序字段
        :param page: 页码
        :param page_size: 每页数量
        :param search_fields: 指定搜索字段
        :param field_weights: 字段权重
        :return: 搜索结果
        """
        # 1. 应用筛选条件
        if filters:
            filter_group = FilterGroup.from_dict(filters)
            items = [item for item in items if filter_group.matches(item)]
        
        # 2. 执行模糊搜索
        if query:
            if search_fields:
                scored_items = []
                for item in items:
                    fields = [item.get(f, "") for f in search_fields]
                    score = multi_field_match(query, fields, field_weights)
                    if score > 0:
