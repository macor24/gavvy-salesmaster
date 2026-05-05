# 📄 导出功能使用文档

## 简介

导出功能模块提供了将报价单、合同等业务数据导出为多种格式的能力，支持 Excel、HTML、Word 和 PDF 格式。

## 功能架构

```
导出系统
├── Excel 导出器
│   ├── 报价单导出（CSV 格式，兼容 Excel）
│   ├── 合同导出
│   └── 产品目录导出
├── HTML 导出器
│   ├── 报价单网页（精美样式）
│   └── 合同网页
├── Word 导出器
│   ├── 报价单文档（Word 兼容格式）
│   └── 合同文档
└── PDF 导出器
    ├── 报价单 PDF（需要额外依赖）
    └── 合同 PDF
```

## 快速开始

### 基础使用

```python
from SentriKit_salesmaster.export import ExportManager
from SentriKit_salesmaster.quotes import QuoteManager

# 创建导出管理器
exporter = ExportManager()

# 获取报价单
qm = QuoteManager()
quote = qm.get_quote("quote-id")

# 导出为不同格式
exporter.export_quote_to_excel(quote, "报价单.csv")
exporter.export_quote_to_html(quote, "报价单.html")
exporter.export_quote_to_word(quote, "报价单.doc")
exporter.export_quote_to_pdf(quote, "报价单.pdf")
```

## Excel 导出

### 导出报价单

```python
# 导出为 CSV 格式（Excel 兼容）
exporter.export_quote_to_excel(quote, "报价单.csv")
```

**输出内容：**
- 报价编号、标题、客户信息
- 明细表（序号、产品、数量、单价、折扣、税费、合计）
- 汇总（小计、折扣、税费、总计）
- 备注和条款

### 导出合同

```python
exporter.export_contract_to_excel(contract, "合同.csv")
```

**输出内容：**
- 合同编号、标题、客户信息
- 合同明细
- 付款计划
- 合同条款

### 导出产品目录

```python
from SentriKit_salesmaster.quotes import ProductManager

pm = ProductManager()
products = pm.get_products()

exporter.export_products_to_excel(products, "产品目录.csv")
```

## HTML 导出

### 导出报价单

```python
exporter.export_quote_to_html(quote, "报价单.html")
```

**特点：**
- 精美的苹果风格样式
- 响应式布局
- 清晰的表格展示
- 自动计算和汇总

### 导出合同

```python
exporter.export_contract_to_html(contract, "合同.html")
```

**特点：**
- 专业的合同样式
- 付款计划展示
- 合同条款展示

## Word 导出

### 导出报价单

```python
exporter.export_quote_to_word(quote, "报价单.doc")
```

**特点：**
- Word 兼容的 HTML 格式
- 可在 Microsoft Word 中打开编辑
- 保留样式和格式

### 导出合同

```python
exporter.export_contract_to_word(contract, "合同.doc")
```

## PDF 导出

### 导出报价单

```python
result = exporter.export_quote_to_pdf(quote, "报价单.pdf")
```

**注意事项：**
- PDF 导出需要额外依赖（weasyprint 或 pdfkit）
- 如果没有安装依赖，会自动降级为 HTML 格式
- 建议安装 weasyprint：`pip install weasyprint`

### 导出合同

```python
result = exporter.export_contract_to_pdf(contract, "合同.pdf")
```

## 自动格式检测

```python
# 根据文件扩展名自动选择导出格式
exporter.export_quote(quote, "报价单.xlsx")    # Excel
exporter.export_quote(quote, "报价单.html")    # HTML
exporter.export_quote(quote, "报价单.doc")     # Word
exporter.export_quote(quote, "报价单.pdf")     # PDF

# 也可以显式指定格式
exporter.export_quote(quote, "output", format="html")
```

## 完整示例

```python
from SentriKit_salesmaster.quotes import (
    ProductManager,
    QuoteManager,
    ContractManager,
)
from SentriKit_salesmaster.export import ExportManager

# 创建管理器
pm = ProductManager()
qm = QuoteManager()
cm = ContractManager()
exporter = ExportManager()

# 创建产品
product = pm.create_product(
    name="企业版套餐",
    unit_price=50000.0,
    category="软件产品"
)

# 创建报价单
quote = qm.create_quote(
    title="客户A方案",
    customer_name="客户A有限公司",
    salesperson="销售员A"
)

# 添加报价明细
qm.add_quote_item(
    quote_id=quote.id,
    product_id=product.id,
    product_name=product.name,
    quantity=2,
    unit_price=product.unit_price,
    discount_percent=10.0,
    tax_percent=13.0
)

# 导出报价单
exporter.export_quote_to_excel(quote, f"报价单_{quote.quote_number}.csv")
exporter.export_quote_to_html(quote, f"报价单_{quote.quote_number}.html")

# 创建合同
qm.update_quote_status(quote.id, "accepted")
contract = cm.create_contract_from_quote(quote.id, title="正式合同")

# 导出合同
exporter.export_contract_to_excel(contract, f"合同_{contract.contract_number}.csv")
exporter.export_contract_to_html(contract, f"合同_{contract.contract_number}.html")
```

## 格式说明

### Excel（CSV）
- **优点**：无需额外依赖，兼容性好
- **缺点**：不支持复杂格式
- **适用场景**：数据导入导出、批量处理

### HTML
- **优点**：精美样式，可直接在浏览器查看
- **缺点**：需要浏览器打开
- **适用场景**：在线展示、邮件发送

### Word
- **优点**：可编辑，专业文档
- **缺点**：需要 Word 软件打开
- **适用场景**：正式文档、客户发送

### PDF
- **优点**：格式固定，不可修改
- **缺点**：需要额外依赖
- **适用场景**：正式合同、存档

## 依赖说明

### 基础功能（无需额外依赖）
- ✅ Excel（CSV）导出
- ✅ HTML 导出
- ✅ Word 导出

### PDF 导出（需要额外依赖）

**选项 1：weasyprint（推荐）**
```bash
pip install weasyprint
```

**选项 2：pdfkit**
```bash
pip install pdfkit
# 还需要安装 wkhtmltopdf
```

## 最佳实践

1. **选择合适的格式**
   - 内部使用：Excel（便于数据分析）
   - 客户发送：HTML 或 PDF（专业美观）
   - 正式合同：PDF（不可修改）

2. **文件命名规范**
   ```python
   filename = f"报价单_{quote.quote_number}_{datetime.now().strftime('%Y%m%d')}.pdf"
   ```

3. **批量导出**
   ```python
   quotes = qm.get_quotes(status="accepted")
   for quote in quotes:
       exporter.export_quote_to_pdf(
           quote,
           f"exports/报价单_{quote.quote_number}.pdf"
       )
   ```

## 下一步

- 查看完整测试：`tests/test_export.py`
- 学习报价与合同管理：`docs/QUOTES_AND_CONTRACTS.md`

---

**祝您使用愉快！🎉**
