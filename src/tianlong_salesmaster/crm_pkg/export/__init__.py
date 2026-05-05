"""SentriKit_salesmaster.crm_pkg.export — 高级导出功能

支持将报价单、合同等导出为 Excel/Word/HTML/PDF 格式。

使用方法：
    from SentriKit_salesmaster.crm_pkg.export import ExportManager

    exporter = ExportManager()

    # 导出报价单
    exporter.export_quote_to_excel(quote, "报价单.xlsx")
    exporter.export_quote_to_pdf(quote, "报价单.pdf")

    # 导出合同
    exporter.export_contract_to_word(contract, "合同.docx")
"""

from __future__ import annotations

import csv
import io
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


# ── 基础导出器 ────────────────────────────────────────

class BaseExporter:
    """导出器基类"""

    @staticmethod
    def format_currency(amount: float) -> str:
        """格式化货币"""
        return f"¥{amount:,.2f}"

    @staticmethod
    def format_date(date_str: str) -> str:
        """格式化日期"""
        if not date_str:
            return ""
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%Y年%m月%d日")
        except Exception:
            return date_str

    @staticmethod
    def format_datetime(dt_str: str) -> str:
        """格式化日期时间"""
        if not dt_str:
            return ""
        try:
            dt = datetime.fromisoformat(dt_str)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return dt_str


# ── Excel 导出器 ────────────────────────────────────────

class ExcelExporter(BaseExporter):
    """Excel 导出器（使用 csv 格式，兼容 Excel）"""

    def export_quote(self, quote, filepath: str) -> str:
        """导出报价单为 Excel 兼容的 CSV 格式"""
        rows = []

        # 标题
        rows.append([f"报价单 - {quote.quote_number}"])
        rows.append([])

        # 基本信息
        rows.append(["报价编号", quote.quote_number])
        rows.append(["报价标题", quote.title])
        rows.append(["客户名称", quote.customer_name])
        rows.append(["销售员", quote.salesperson])
        rows.append(["创建日期", self.format_datetime(quote.created_at)])
        rows.append(["有效期至", self.format_date(quote.valid_until)])
        rows.append(["状态", self._status_text(quote.status)])
        rows.append([])

        # 明细表头
        rows.append(["序号", "产品名称", "数量", "单价", "折扣(%)", "税前金额", "税率(%)", "税额", "合计"])

        # 明细内容
        for i, item in enumerate(quote.items, 1):
            rows.append([
                i,
                item.product_name,
                item.quantity,
                self.format_currency(item.unit_price),
                f"{item.discount_percent:.1f}%",
                self.format_currency(item.total_before_tax),
                f"{item.tax_percent:.1f}%",
                self.format_currency(item.tax_amount),
                self.format_currency(item.total)
            ])

        # 合计
        rows.append([])
        rows.append(["", "", "", "", "", "小计:", "", "", self.format_currency(quote.subtotal)])
        rows.append(["", "", "", "", "", "折扣:", "", "", self.format_currency(quote.total_discount)])
        rows.append(["", "", "", "", "", "税费:", "", "", self.format_currency(quote.total_tax)])
        rows.append(["", "", "", "", "", "总计:", "", "", self.format_currency(quote.total_amount)])
        rows.append([])

        # 备注
        if quote.notes:
            rows.append(["备注:", quote.notes])
        if quote.terms:
            rows.append(["条款:", quote.terms])

        # 写入文件
        self._write_csv(filepath, rows)
        return filepath

    def export_contract(self, contract, filepath: str) -> str:
        """导出合同为 Excel 兼容的 CSV 格式"""
        rows = []

        # 标题
        rows.append([f"合同 - {contract.contract_number}"])
        rows.append([])

        # 基本信息
        rows.append(["合同编号", contract.contract_number])
        rows.append(["合同标题", contract.title])
        rows.append(["客户名称", contract.customer_name])
        rows.append(["销售员", contract.salesperson])
        rows.append(["创建日期", self.format_datetime(contract.created_at)])
        rows.append(["签署日期", self.format_date(contract.signed_at)])
        rows.append(["生效日期", self.format_date(contract.effective_date)])
        rows.append(["结束日期", self.format_date(contract.end_date)])
        rows.append(["状态", self._contract_status_text(contract.status)])
        rows.append([])

        # 合同明细
        rows.append(["序号", "产品名称", "数量", "单价", "金额"])
        for i, item in enumerate(contract.items, 1):
            rows.append([
                i,
                item.product_name,
                item.quantity,
                self.format_currency(item.unit_price),
                self.format_currency(item.quantity * item.unit_price)
            ])

        rows.append([])
        rows.append(["", "", "", "合同总额:", self.format_currency(contract.total_amount)])
        rows.append([])

        # 付款计划
        if contract.payment_plans:
            rows.append(["付款计划"])
            rows.append(["期数", "描述", "金额", "状态", "付款日期"])
            for plan in contract.payment_plans:
                rows.append([
                    f"第{plan.payment_number}期",
                    plan.description,
                    self.format_currency(plan.amount),
                    "已付款" if plan.status == "paid" else "待付款",
                    self.format_date(plan.paid_at) if plan.paid_at else ""
                ])

        # 条款
        if contract.terms:
            rows.append([])
            rows.append(["合同条款:", contract.terms])

        self._write_csv(filepath, rows)
        return filepath

    def export_products(self, products: List, filepath: str) -> str:
        """导出产品目录"""
        rows = [["产品目录"]]
        rows.append([])
        rows.append(["SKU", "产品名称", "描述", "分类", "单价", "成本价", "状态"])

        for p in products:
            rows.append([
                p.sku,
                p.name,
                p.description,
                p.category,
                self.format_currency(p.unit_price),
                self.format_currency(p.cost_price),
                "在售" if p.is_active else "停售"
            ])

        self._write_csv(filepath, rows)
        return filepath

    def _write_csv(self, filepath: str, rows: List[List]) -> None:
        """写入 CSV 文件（UTF-8 with BOM，兼容 Excel）"""
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    def _status_text(self, status: str) -> str:
        status_map = {
            "draft": "草稿",
            "pending_approval": "待审批",
            "approved": "已审批",
            "sent": "已发送",
            "accepted": "已接受",
            "rejected": "已拒绝",
            "expired": "已过期"
        }
        return status_map.get(status, status)

    def _contract_status_text(self, status: str) -> str:
        status_map = {
            "draft": "草稿",
            "pending_approval": "待审批",
            "signed": "已签署",
            "fulfilling": "履行中",
            "completed": "已完成",
            "terminated": "已终止"
        }
        return status_map.get(status, status)


# ── HTML 导出器 ────────────────────────────────────────

class HTMLExporter(BaseExporter):
    """HTML 导出器"""

    def export_quote(self, quote, filepath: str) -> str:
        """导出报价单为 HTML"""
        html = self._build_quote_html(quote)
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        return filepath

    def export_contract(self, contract, filepath: str) -> str:
        """导出合同为 HTML"""
        html = self._build_contract_html(contract)
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        return filepath

    def _build_quote_html(self, quote) -> str:
        """构建报价单 HTML"""
        items_rows = ""
        for i, item in enumerate(quote.items, 1):
            items_rows += f"""
            <tr>
                <td style="text-align:center">{i}</td>
                <td>{item.product_name}</td>
                <td style="text-align:center">{item.quantity}</td>
                <td style="text-align:right">{self.format_currency(item.unit_price)}</td>
                <td style="text-align:center">{item.discount_percent:.1f}%</td>
                <td style="text-align:right">{self.format_currency(item.total_before_tax)}</td>
                <td style="text-align:center">{item.tax_percent:.1f}%</td>
                <td style="text-align:right">{self.format_currency(item.tax_amount)}</td>
                <td style="text-align:right; font-weight:bold">{self.format_currency(item.total)}</td>
            </tr>
            """

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>报价单 - {quote.quote_number}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; color: #333; }}
        h1 {{ color: #007aff; border-bottom: 2px solid #007aff; padding-bottom: 10px; }}
        .info {{ background: #f5f5f7; padding: 20px; border-radius: 12px; margin: 20px 0; }}
        .info-row {{ display: flex; margin: 8px 0; }}
        .info-label {{ width: 100px; color: #666; }}
        .info-value {{ flex: 1; font-weight: 500; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #007aff; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f9f9f9; }}
        .total-section {{ background: #f5f5f7; padding: 20px; border-radius: 12px; margin-top: 20px; }}
        .total-row {{ display: flex; justify-content: space-between; margin: 8px 0; }}
        .total-final {{ font-size: 1.3em; font-weight: bold; color: #007aff; }}
        .notes {{ margin-top: 30px; padding: 15px; background: #fff3cd; border-radius: 8px; }}
        .footer {{ margin-top: 40px; text-align: center; color: #999; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>报价单</h1>

    <div class="info">
        <div class="info-row">
            <span class="info-label">报价编号:</span>
            <span class="info-value">{quote.quote_number}</span>
        </div>
        <div class="info-row">
            <span class="info-label">报价标题:</span>
            <span class="info-value">{quote.title}</span>
        </div>
        <div class="info-row">
            <span class="info-label">客户名称:</span>
            <span class="info-value">{quote.customer_name}</span>
        </div>
        <div class="info-row">
            <span class="info-label">销售员:</span>
            <span class="info-value">{quote.salesperson}</span>
        </div>
        <div class="info-row">
            <span class="info-label">创建日期:</span>
            <span class="info-value">{self.format_datetime(quote.created_at)}</span>
        </div>
        <div class="info-row">
            <span class="info-label">有效期至:</span>
            <span class="info-value">{self.format_date(quote.valid_until)}</span>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width:40px">序号</th>
                <th>产品名称</th>
                <th style="width:60px">数量</th>
                <th style="width:100px">单价</th>
                <th style="width:70px">折扣</th>
                <th style="width:100px">税前金额</th>
                <th style="width:60px">税率</th>
                <th style="width:100px">税额</th>
                <th style="width:100px">合计</th>
            </tr>
        </thead>
        <tbody>
            {items_rows}
        </tbody>
    </table>

    <div class="total-section">
        <div class="total-row">
            <span>小计:</span>
            <span>{self.format_currency(quote.subtotal)}</span>
        </div>
        <div class="total-row">
            <span>折扣:</span>
            <span>- {self.format_currency(quote.total_discount)}</span>
        </div>
        <div class="total-row">
            <span>税费:</span>
            <span>+ {self.format_currency(quote.total_tax)}</span>
        </div>
        <div class="total-row total-final">
            <span>总计:</span>
            <span>{self.format_currency(quote.total_amount)}</span>
        </div>
    </div>

    {f'<div class="notes"><strong>备注:</strong><br>{quote.notes}</div>' if quote.notes else ''}

    {f'<div class="notes"><strong>条款:</strong><br>{quote.terms}</div>' if quote.terms else ''}

    <div class="footer">
        <p>本报价单由销售宗师（SalesMaster）自动生成</p>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>"""

    def _build_contract_html(self, contract) -> str:
        """构建合同 HTML"""
        items_rows = ""
        for i, item in enumerate(contract.items, 1):
            items_rows += f"""
            <tr>
                <td style="text-align:center">{i}</td>
                <td>{item.product_name}</td>
                <td style="text-align:center">{item.quantity}</td>
                <td style="text-align:right">{self.format_currency(item.unit_price)}</td>
                <td style="text-align:right; font-weight:bold">{self.format_currency(item.quantity * item.unit_price)}</td>
            </tr>
            """

        payment_rows = ""
        if contract.payment_plans:
            for plan in contract.payment_plans:
                status_text = "✅ 已付款" if plan.status == "paid" else "⏳ 待付款"
                payment_rows += f"""
                <tr>
                    <td style="text-align:center">第{plan.payment_number}期</td>
                    <td>{plan.description}</td>
                    <td style="text-align:right">{self.format_currency(plan.amount)}</td>
                    <td style="text-align:center">{status_text}</td>
                    <td>{self.format_date(plan.paid_at) if plan.paid_at else '-'}</td>
                </tr>
                """

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>合同 - {contract.contract_number}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; color: #333; }}
        h1 {{ color: #34c759; border-bottom: 2px solid #34c759; padding-bottom: 10px; }}
        .info {{ background: #f5f5f7; padding: 20px; border-radius: 12px; margin: 20px 0; }}
        .info-row {{ display: flex; margin: 8px 0; }}
        .info-label {{ width: 100px; color: #666; }}
        .info-value {{ flex: 1; font-weight: 500; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #34c759; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f9f9f9; }}
        .total-section {{ background: #f5f5f7; padding: 20px; border-radius: 12px; margin-top: 20px; text-align: right; }}
        .total-amount {{ font-size: 1.5em; font-weight: bold; color: #34c759; }}
        .terms {{ margin-top: 30px; padding: 20px; background: #e8f5e9; border-radius: 8px; }}
        .footer {{ margin-top: 40px; text-align: center; color: #999; font-size: 0.9em; }}
        h2 {{ color: #333; margin-top: 30px; }}
    </style>
</head>
<body>
    <h1>合同</h1>

    <div class="info">
        <div class="info-row">
            <span class="info-label">合同编号:</span>
            <span class="info-value">{contract.contract_number}</span>
        </div>
        <div class="info-row">
            <span class="info-label">合同标题:</span>
            <span class="info-value">{contract.title}</span>
        </div>
        <div class="info-row">
            <span class="info-label">客户名称:</span>
            <span class="info-value">{contract.customer_name}</span>
        </div>
        <div class="info-row">
            <span class="info-label">销售员:</span>
            <span class="info-value">{contract.salesperson}</span>
        </div>
        <div class="info-row">
            <span class="info-label">签署日期:</span>
            <span class="info-value">{self.format_date(contract.signed_at) or '待签署'}</span>
        </div>
        <div class="info-row">
            <span class="info-label">生效日期:</span>
            <span class="info-value">{self.format_date(contract.effective_date) or '待确定'}</span>
        </div>
    </div>

    <h2>合同明细</h2>
    <table>
        <thead>
            <tr>
                <th style="width:40px">序号</th>
                <th>产品名称</th>
                <th style="width:60px">数量</th>
                <th style="width:100px">单价</th>
                <th style="width:100px">金额</th>
            </tr>
        </thead>
        <tbody>
            {items_rows}
        </tbody>
    </table>

    <div class="total-section">
        <span class="total-amount">合同总额: {self.format_currency(contract.total_amount)}</span>
    </div>

    {f'<h2>付款计划</h2><table><thead><tr><th>期数</th><th>描述</th><th>金额</th><th>状态</th><th>付款日期</th></tr></thead><tbody>{payment_rows}</tbody></table>' if contract.payment_plans else ''}

    {f'<div class="terms"><strong>合同条款:</strong><br><br>{contract.terms}</div>' if contract.terms else ''}

    <div class="footer">
        <p>本合同由销售宗师（SalesMaster）自动生成</p>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>"""


# ── PDF 导出器 ────────────────────────────────────────

class PDFExporter(BaseExporter):
    """PDF 导出器（基于 HTML 转 PDF）"""

    def export_quote(self, quote, filepath: str) -> str:
        """导出报价单为 PDF"""
        # 先生成 HTML
        html_exporter = HTMLExporter()
        html_content = html_exporter._build_quote_html(quote)

        # 尝试使用 wkhtmltopdf 或 weasyprint
        pdf_content = self._html_to_pdf(html_content)

        if pdf_content:
            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
            with open(filepath, "wb") as f:
                f.write(pdf_content)
            return filepath
        else:
            # 降级为 HTML
            html_path = filepath.replace(".pdf", ".html")
            html_exporter.export_quote(quote, html_path)
            return html_path

    def export_contract(self, contract, filepath: str) -> str:
        """导出合同为 PDF"""
        html_exporter = HTMLExporter()
        html_content = html_exporter._build_contract_html(contract)

        pdf_content = self._html_to_pdf(html_content)

        if pdf_content:
            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
            with open(filepath, "wb") as f:
                f.write(pdf_content)
            return filepath
        else:
            html_path = filepath.replace(".pdf", ".html")
            html_exporter.export_contract(contract, html_path)
            return html_path

    def _html_to_pdf(self, html_content: str) -> Optional[bytes]:
        """将 HTML 转换为 PDF"""
        # 尝试使用 weasyprint
        try:
            from weasyprint import HTML
            return HTML(string=html_content).write_pdf()
        except ImportError:
            pass

        # 尝试使用 pdfkit (需要 wkhtmltopdf)
        try:
            import pdfkit
            return pdfkit.from_string(html_content, False)
        except ImportError:
            pass

        # 无法生成 PDF，返回 None
        return None


# ── Word 导出器 ────────────────────────────────────────

class WordExporter(BaseExporter):
    """Word 导出器（生成兼容 Word 的 HTML 格式）"""

    def export_quote(self, quote, filepath: str) -> str:
        """导出报价单为 Word 兼容格式"""
        html_exporter = HTMLExporter()
        html_content = html_exporter._build_quote_html(quote)

        # 添加 Word 兼容的 XML 头部
        word_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<?mso-application progid="Word.Document"?>
{html_content}"""

        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(word_content)
        return filepath

    def export_contract(self, contract, filepath: str) -> str:
        """导出合同为 Word 兼容格式"""
        html_exporter = HTMLExporter()
        html_content = html_exporter._build_contract_html(contract)

        word_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<?mso-application progid="Word.Document"?>
{html_content}"""

        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(word_content)
        return filepath


# ── 统一导出管理器 ────────────────────────────────────────

class ExportManager:
    """统一导出管理器"""

    def __init__(self):
        self.excel = ExcelExporter()
        self.html = HTMLExporter()
        self.pdf = PDFExporter()
        self.word = WordExporter()

    # ── 报价单导出 ──────────────────────────────────

    def export_quote_to_excel(self, quote, filepath: str) -> str:
        """导出报价单为 Excel"""
        return self.excel.export_quote(quote, filepath)

    def export_quote_to_html(self, quote, filepath: str) -> str:
        """导出报价单为 HTML"""
        return self.html.export_quote(quote, filepath)

    def export_quote_to_pdf(self, quote, filepath: str) -> str:
        """导出报价单为 PDF"""
        return self.pdf.export_quote(quote, filepath)

    def export_quote_to_word(self, quote, filepath: str) -> str:
        """导出报价单为 Word"""
        return self.word.export_quote(quote, filepath)

    def export_quote(self, quote, filepath: str, format: str = "auto") -> str:
        """自动根据文件扩展名导出报价单"""
        if format == "auto":
            format = self._detect_format(filepath)

        format = format.lower()
        if format in ("xlsx", "xls", "csv", "excel"):
            return self.export_quote_to_excel(quote, filepath)
        elif format == "html":
            return self.export_quote_to_html(quote, filepath)
        elif format == "pdf":
            return self.export_quote_to_pdf(quote, filepath)
        elif format in ("doc", "docx", "word"):
            return self.export_quote_to_word(quote, filepath)
        else:
            return self.export_quote_to_html(quote, filepath)

    # ── 合同导出 ──────────────────────────────────

    def export_contract_to_excel(self, contract, filepath: str) -> str:
        """导出合同为 Excel"""
        return self.excel.export_contract(contract, filepath)

    def export_contract_to_html(self, contract, filepath: str) -> str:
        """导出合同为 HTML"""
        return self.html.export_contract(contract, filepath)

    def export_contract_to_pdf(self, contract, filepath: str) -> str:
        """导出合同为 PDF"""
        return self.pdf.export_contract(contract, filepath)

    def export_contract_to_word(self, contract, filepath: str) -> str:
        """导出合同为 Word"""
        return self.word.export_contract(contract, filepath)

    def export_contract(self, contract, filepath: str, format: str = "auto") -> str:
        """自动根据文件扩展名导出合同"""
        if format == "auto":
            format = self._detect_format(filepath)

        format = format.lower()
        if format in ("xlsx", "xls", "csv", "excel"):
            return self.export_contract_to_excel(contract, filepath)
        elif format == "html":
            return self.export_contract_to_html(contract, filepath)
        elif format == "pdf":
            return self.export_contract_to_pdf(contract, filepath)
        elif format in ("doc", "docx", "word"):
            return self.export_contract_to_word(contract, filepath)
        else:
            return self.export_contract_to_html(contract, filepath)

    # ── 产品导出 ──────────────────────────────────

    def export_products_to_excel(self, products: List, filepath: str) -> str:
        """导出产品目录为 Excel"""
        return self.excel.export_products(products, filepath)

    # ── 辅助方法 ──────────────────────────────────

    def _detect_format(self, filepath: str) -> str:
        """根据文件扩展名检测格式"""
        ext = os.path.splitext(filepath)[1].lower().lstrip(".")
        return ext if ext else "html"


# ── 工厂函数 ────────────────────────────────────────

def get_export_manager() -> ExportManager:
    """获取导出管理器实例"""
    return ExportManager()
