# 📚 产品知识库系统使用文档

## 简介

产品知识库系统（Knowledge Base）是销售宗师（SalesMaster）的重要功能模块，提供了完整的知识管理、智能搜索、Agent 训练等功能。

## 功能特点

### 核心功能
- ✅ **知识条目管理** - 添加、编辑、删除知识
- ✅ **FAQ 问答管理** - 管理常见问题和答案
- ✅ **分类与标签** - 灵活的分类体系和标签
- ✅ **智能搜索** - 支持关键词搜索、标签匹配
- ✅ **Agent 训练素材** - 自动生成训练提示词
- ✅ **统计与分析** - 查看知识库使用情况
- ✅ **导入/导出** - 数据备份与迁移
- ✅ **数据持久化** - JSON 文件存储

### 架构特点
- 🚀 **轻量级设计** - 无需数据库，纯文件存储
- 🔒 **线程安全** - 使用读写锁保证并发安全
- 🔗 **无缝集成** - 与现有系统完美融合
- 📦 **零依赖** - 纯标准库实现

## 快速开始

### 安装

确保已安装销售宗师：

```bash
pip install tianlong-salesmaster
```

### 基础使用

```python
from tianlong_salesmaster.knowledge import KnowledgeBase

# 创建知识库实例
kb = KnowledgeBase()

# 添加知识条目
kb.add_item(
    title="产品价格政策",
    content="我们的产品支持7天无理由退换...",
    category="产品政策",
    tags=["价格", "退换货"],
    priority=3
)

# 添加 FAQ
kb.add_faq(
    question="产品可以退换吗？",
    answer="是的，支持 7 天无理由退换...",
    category="常见问题"
)

# 搜索知识
results = kb.search("退换货")

# 查看统计
stats = kb.get_stats()
```

### 运行示例

```bash
# 测试知识库功能
python tests/test_knowledge.py

# 运行完整示例
python examples/knowledge_example.py
```

## 详细功能

### 1. 知识条目管理

#### 添加知识
```python
item = kb.add_item(
    title="标题",
    content="详细内容",
    category="分类",
    tags=["标签1", "标签2"],
    priority=2  # 优先级1-5，数字越大越重要
)
```

#### 获取知识列表
```python
# 获取所有已发布的知识
items = kb.get_items(status="published")

# 获取特定分类的知识
items = kb.get_items(category="产品政策")

# 获取单个知识
item = kb.get_item("item_id")
```

#### 更新和删除
```python
# 更新知识
kb.update_item(item)

# 删除知识
kb.delete_item("item_id")

# 标记为有用
kb.mark_useful("item_id")
```

### 2. FAQ 管理

#### 添加 FAQ
```python
faq = kb.add_faq(
    question="常见问题",
    answer="答案",
    category="常见问题",
    tags=["标签"]
)

# 快速添加（自动分类）
kb.quick_add_faq("怎么退款？", "退款流程...")
```

#### 获取 FAQ
```python
# 获取所有 FAQ
faqs = kb.get_faqs()

# 按分类获取
faqs = kb.get_faqs(category="常见问题")
```

#### 评价 FAQ
```python
kb.rate_faq("faq_id", positive=True)  # 好评
kb.rate_faq("faq_id", positive=False)  # 差评
```

### 3. 分类管理

#### 查看分类
```python
categories = kb.get_categories()
for cat in categories:
    print(f"{cat.name} (数量: {cat.item_count})")
```

#### 添加自定义分类
```python
kb.add_category(
    name="新分类",
    description="分类说明",
    parent_id="",  # 父分类ID，支持层级
    sort_order=1
)
```

### 4. 智能搜索

```python
# 简单搜索
results = kb.search("关键词")

# 限制结果数量
results = kb.search("价格", limit=10)

# 只搜索知识（不搜索 FAQ）
results = kb.search("技术", search_faqs=False)

# 查看搜索结果
for r in results:
    print(f"匹配类型: {r.match_type}")
    print(f"得分: {r.score}")
    if hasattr(r.item, "title"):
        print(f"标题: {r.item.title}")
    else:
        print(f"问题: {r.item.question}")
```

### 5. Agent 训练

#### 获取训练素材
```python
# 根据 Agent 角色获取
training_data = kb.get_training_for_agent("presales_agent")

# 生成完整训练提示词
prompt = kb.train_agent_with_knowledge("presales_agent")
print(prompt)
```

#### 支持的 Agent 角色
- `presales_agent` - 售前谈判官
- `aftersales_agent` - 售后维系官
- `market_research_agent` - 市场调研官
- `competitor_intel_agent` - 竞品分析官

### 6. 统计功能

```python
stats = kb.get_stats()
print(f"总知识: {stats['total_items']}")
print(f"总FAQ: {stats['total_faqs']}")
print(f"总分类: {stats['total_categories']}")
print(f"总浏览: {stats['total_views']}")
print(f"有用标记: {stats['total_useful']}")
print(f"热门知识: {stats['top_items']}")
print(f"热门FAQ: {stats['top_faqs']}")
```

### 7. 导入/导出

#### 导出数据
```python
data = kb.export_all()
# data 包含:
#   - items: 知识列表
#   - faqs: FAQ列表
#   - categories: 分类列表
#   - exported_at: 导出时间

# 保存到文件
import json
with open("kb_backup.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

#### 导入数据
```python
import json
with open("kb_backup.json", "r", encoding="utf-8") as f:
    data = json.load(f)

count, errors = kb.import_all(data, overwrite=False)
print(f"导入: {count}条, 错误: {errors}")
```

### 8. 批量操作

```python
# 批量添加知识
kb.batch_add_items([
    {
        "title": "标题1",
        "content": "内容1",
        "category": "分类",
        "tags": ["标签"],
        "priority": 1
    },
    {
        "title": "标题2",
        "content": "内容2",
        ...
    }
])
```

## 数据存储

### 存储位置
知识库数据默认存储在：
- `tianlong_salesmaster/storage/knowledge_items.json` - 知识条目
- `tianlong_salesmaster/storage/knowledge_faqs.json` - FAQ
- `tianlong_salesmaster/storage/knowledge_categories.json` - 分类

### 自定义存储路径

```python
kb = KnowledgeBase(storage_dir="/path/to/custom/dir")
```

## 最佳实践

### 1. 知识组织建议
- 使用清晰的分类结构
- 合理设置标签
- 按重要程度设置优先级

### 2. 知识质量建议
- 内容简洁准确
- 定期更新维护
- 及时标记过时内容

### 3. 安全建议
- 定期备份知识库
- 敏感信息谨慎存储
- 注意数据权限管理

## API 参考

### KnowledgeBase 类
主要类，提供所有知识库功能。

#### 主要方法
| 方法名 | 说明 |
|--------|------|
| `add_item(...)` | 添加知识条目 |
| `get_items(...)` | 获取知识列表 |
| `get_item(id)` | 获取单个知识 |
| `update_item(item)` | 更新知识 |
| `delete_item(id)` | 删除知识 |
| `mark_useful(id)` | 标记为有用 |
| `add_faq(...)` | 添加FAQ |
| `get_faqs(...)` | 获取FAQ列表 |
| `rate_faq(id, positive)` | 评价FAQ |
| `search(query, limit)` | 搜索知识 |
| `get_training_for_agent(role)` | 获取训练素材 |
| `train_agent_with_knowledge(role)` | 生成训练提示词 |
| `get_stats()` | 获取统计信息 |
| `export_all()` | 导出所有数据 |
| `import_all(data, overwrite)` | 导入数据 |
| `get_categories()` | 获取所有分类 |
| `add_category(...)` | 添加分类 |

#### 数据类
- `KnowledgeItem` - 知识条目
- `FAQItem` - FAQ问答
- `Category` - 分类
- `SearchResult` - 搜索结果

## 示例

### 示例 1: 销售知识库初始化
```python
def init_sales_kb():
    """初始化销售知识库"""
    kb = KnowledgeBase()

    # 添加产品介绍
    kb.add_item(
        title="产品简介",
        content="我们的产品是一套完整的...",
        category="产品介绍",
        tags=["介绍", "销售"],
        priority=5
    )

    # 添加常见问题
    faq_list = [
        ("价格多少？", "根据套餐不同，价格..."),
        ("怎么安装？", "下载安装包，一键安装..."),
    ]
    for q, a in faq_list:
        kb.quick_add_faq(q, a)
```

### 示例 2: 在 Agent 中使用知识库
```python
def agent_with_kb():
    """Agent 集成知识库示例"""
    from tianlong_salesmaster.knowledge import get_knowledge_base

    kb = get_knowledge_base()

    # 获取训练素材
    training = kb.get_training_for_agent("presales_agent")

    # 在对话中搜索知识
    def answer_query(query):
        results = kb.search(query)
        if results:
            best = results[0]
            return best.item.content if hasattr(best.item, "content") else best.item.answer
        return "抱歉，我需要人工客服帮您。"
```

## 常见问题

### Q: 知识库数据存在哪里？
A: 默认存储在 `tianlong_salesmaster/storage/` 目录下，可通过 `storage_dir` 参数自定义。

### Q: 如何迁移知识库数据？
A: 使用 `kb.export_all()` 和 `kb.import_all()` 导出和导入数据。

### Q: 支持多少条知识？
A: 理论上没有限制，取决于可用内存和文件存储空间。

### Q: 搜索速度如何？
A: 采用索引优化，一般查询在毫秒级完成。

## 下一步

- 阅读 `examples/knowledge_example.py` 查看完整示例
- 运行测试 `python tests/test_knowledge.py`
- 集成到您的销售系统中

---

**祝您使用愉快！** 🎉
