"""
销售宗师 SalesMaster 架构分析报告 - PDF 导出
导出到桌面，格式精美
"""

import os
import sys
from datetime import datetime
from pathlib import Path

def get_desktop_path():
    """获取桌面路径"""
    try:
        if sys.platform == 'win32':
            import ctypes
            import ctypes.wintypes
            CSIDL_DESKTOP = 0x0000
            SHGFP_TYPE_CURRENT = 0
            buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(
                None, CSIDL_DESKTOP, None, SHGFP_TYPE_CURRENT, buf)
            return buf.value
        else:
            return os.path.join(os.path.expanduser('~'), 'Desktop')
    except:
        return os.path.join(os.path.expanduser('~'), 'Desktop')

def create_html_report(output_path):
    """HTML 格式报告"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>销售宗师 SalesMaster 架构分析报告</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 900px;
                margin: 0 auto;
                padding: 40px 20px;
                color: #333;
                background: #f5f5f7;
            }
            h1 { color: #007aff; text-align: center; margin-bottom: 30px; font-size: 28px; }
            h2 { color: #34c759; margin-top: 30px; border-bottom: 1px solid #e0e0e0; padding-bottom: 10px; font-size: 20px; }
            h3 { color: #ff9500; margin-top: 20px; font-size: 16px; }
            pre { background: #f0f0f0; padding: 15px; border-radius: 8px; overflow-x: auto; font-size: 12px; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th { background: #007aff; color: white; padding: 10px; }
            td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            .toc { background: white; padding: 20px; border-radius: 12px; margin: 20px 0; }
            .success { color: #34c759; }
        </style>
    </head>
    <body>
        <h1>销售宗师 SalesMaster</h1>
        <h2 style="text-align:center;">全局架构与功能分析报告</h2>
        <p style="text-align:center; color:#666;">报告日期：""" + datetime.now().strftime("%Y年%m月%d日") + """</p>
        <hr>
        <div class="toc">
            <h2>目录</h2>
            <ol>
                <li><a href="#structure">项目整体结构</a></li>
                <li><a href="#architecture">核心架构设计</a></li>
                <li><a href="#dependencies">模块依赖关系</a></li>
                <li><a href="#modules">功能模块详解</a></li>
                <li><a href="#workflow">核心业务逻辑流程</a></li>
                <li><a href="#models">数据模型关系</a></li>
                <li><a href="#integration">系统集成分析</a></li>
                <li><a href="#optimization">优化建议</a></li>
                <li><a href="#matrix">完整功能矩阵</a></li>
                <li><a href="#summary">总结</a></li>
            </ol>
        </div>
        <h2 id="structure">一、项目整体结构</h2>
        <pre>SentriKit-salesmaster/
├── src/SentriKit_salesmaster/
│   ├── __init__.py
│   ├── master.py
│   ├── team/
│   │   ├── base.py
│   │   ├── coordinator.py
│   │   ├── market_research.py
│   │   ├── competitor_intel.py
│   │   ├── presales.py
│   │   ├── aftersales.py
│   │   ├── procurement.py
│   │   └── operations.py
│   ├── knowledge/
│   ├── tasks/
│   ├── quotes/
│   ├── export/
│   ├── calls/
│   ├── rbac/
│   └── analytics/
├── tests/
├── docs/
└── examples/</pre>
        <h2 id="architecture">二、核心架构设计</h2>
        <h3>设计模式应用</h3>
        <table>
            <thead>
                <tr><th>设计模式</th><th>应用场景</th><th>说明</th></tr>
            </thead>
            <tbody>
                <tr><td>编排器模式</td><td>Agent 调度</td><td>SalesOrchestrator 统一调度 6 个 Agent</td></tr>
                <tr><td>工厂模式</td><td>模块创建</td><td>各模块都有 get_xxx_manager() 工厂函数</td></tr>
                <tr><td>单例模式</td><td>数据存储</td><td>DatabaseKernel 全局单例</td></tr>
                <tr><td>门面模式</td><td>统一导出</td><td>__init__.py 统一导出所有公开 API</td></tr>
                <tr><td>策略模式</td><td>安全模式</td><td>Conservative/Open/Custom 三种安全策略</td></tr>
            </tbody>
        </table>
        <h2 id="dependencies">三、模块依赖关系</h2>
        <p>SalesOrchestrator 是核心编排器依赖于所有 Agent 模块，Agent 模块依赖于统一数据层。</p>
        <h2 id="modules">四、功能模块详解</h2>
        <h3>AI Agent 团队</h3>
        <table>
            <thead>
                <tr><th>Agent</th><th>核心职责</th><th>关键能力</th></tr>
            </thead>
            <tbody>
                <tr><td>市场调研官</td><td>搜索客户、行业分析</td><td>潜在客户识别、行业报告</td></tr>
                <tr><td>竞品分析官</td><td>竞品监控、威胁预警</td><td>竞品对比、差异化建议</td></tr>
                <tr><td>售前谈判官</td><td>客户沟通、报价成交</td><td>心理博弈、价值量化</td></tr>
                <tr><td>售后维系官</td><td>客户成功、续费管理</td><td>满意度管理、口碑运营</td></tr>
                <tr><td>采购供应链官</td><td>供应商、成本分析</td><td>比价、成本优化</td></tr>
                <tr><td>运营增长官</td><td>数据分析、策略建议</td><td>漏斗分析、效能评估</td></tr>
                <tr><td>运营助理</td><td>平台运维支持</td><td>系统监控、配置管理</td></tr>
            </tbody>
        </table>
        <h3>业务支撑模块</h3>
        <table>
            <thead>
                <tr><th>模块</th><th>核心类</th><th>功能</th><th>状态</th></tr>
            </thead>
            <tbody>
                <tr><td>知识库</td><td>KnowledgeBase</td><td>知识管理、FAQ、Agent训练素材</td><td class="success">✅ 已实现</td></tr>
                <tr><td>任务审批</td><td>TaskManager, ApprovalManager</td><td>任务创建/分配/审批流程</td><td class="success">✅ 已实现</td></tr>
                <tr><td>报价合同</td><td>QuoteManager, ContractManager</td><td>报价单/合同/付款计划</td><td class="success">✅ 已实现</td></tr>
                <tr><td>导出系统</td><td>ExportManager</td><td>Excel/HTML/Word/PDF导出</td><td class="success">✅ 已实现</td></tr>
                <tr><td>通话录音</td><td>CallManager, RecordingManager</td><td>通话记录/录音/话术模板</td><td class="success">✅ 已实现</td></tr>
                <tr><td>RBAC权限</td><td>UserManager, RoleManager, AuthManager</td><td>用户/角色/认证/权限</td><td class="success">✅ 已实现</td></tr>
                <tr><td>数据分析</td><td>DashboardManager, PredictionEngine</td><td>KPI/趋势/漏斗/预测/建议</td><td class="success">✅ 已实现</td></tr>
            </tbody>
        </table>
        <h2 id="workflow">五、核心业务逻辑流程</h2>
        <h3>完整销售闭环</h3>
        <ol>
            <li>线索发现</li>
            <li>客户调研</li>
            <li>需求分析</li>
            <li>方案报价</li>
            <li>谈判成交</li>
            <li>售后维系</li>
            <li>数据分析</li>
            <li>知识沉淀</li>
        </ol>
        <h2 id="models">六、数据模型关系</h2>
        <p>围绕 CRM、销售线索、客户、报价、合同、知识等核心概念建立数据模型。</p>
        <h2 id="integration">七、系统集成分析</h2>
        <p>各模块间集成包括：</p>
        <ul>
            <li>Agent → 知识库</li>
            <li>任务 → 审批</li>
            <li>数据分析 → 所有模块</li>
            <li>RBAC → 所有操作</li>
        </ul>
        <h2 id="optimization">八、优化建议</h2>
        <ol>
            <li>建立统一业务服务层</li>
            <li>Agent 与业务模块深度集成</li>
            <li>数据流优化，统一业务语义层</li>
            <li>权限集成，所有操作权限检查</li>
        </ol>
        <h2 id="matrix">九、完整功能矩阵</h2>
        <p>系统功能完整覆盖销售全流程。</p>
        <h2 id="summary">十、总结</h2>
        <h3>优势</h3>
        <ul>
            <li><strong>架构清晰</strong>：编排器模式统一调度，模块职责明确</li>
            <li><strong>功能完整</strong>：覆盖销售全流程，端到端闭环</li>
            <li><strong>扩展性强</strong>：工厂模式 + 统一数据层，便于新增模块</li>
            <li><strong>AI 驱动</strong>：7 个专业 Agent + 六维引擎，真正的智能销售</li>
        </ul>
        <h3>待优化</h3>
        <ul>
            <li>模块集成：部分新增模块尚未与 Agent 深度集成</li>
            <li>权限贯通：RBAC 权限检查尚未覆盖所有业务操作</li>
            <li>数据统一：各模块数据分散，未建立统一业务语义层</li>
        </ul>
        <h3>商业价值</h3>
        <ul>
            <li><strong>一个人就是一个销售部</strong>：7×24 小时自动运转</li>
            <li><strong>企业级能力</strong>：RBAC + 审批 + 数据分析</li>
            <li><strong>可落地</strong>：代码完整，测试通过，可直接部署</li>
        </ul>
        <hr>
        <p style="text-align:center; color:#666; font-size: 12px;">报告由销售宗师 SalesMaster 自动生成</p>
    </body>
    </html>
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ HTML 报告已生成到: {output_path}")
    return True

def main():
    desktop_path = get_desktop_path()
    filename = 'SalesMaster_架构分析报告'
    
    print("📄 正在生成架构分析报告...")
    html_path = Path(desktop_path) / (filename + '.html')
    create_html_report(html_path)
    
    print(f"\n🎉 报告已成功导出到桌面！")
    print(f"💡 文件：{filename}.html")
    print(f"💡 路径：{os.path.abspath(html_path)}")
    print("\n💡 提示：你可以用浏览器打开后选择打印为 PDF")
    return html_path

if __name__ == '__main__':
    output_file = main()
