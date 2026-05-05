# 销售宗师 v2.0 开发计划

> **界面设计:** `/mnt/c/XSZS/`（9 个功能页面）
> **代码目录:** `tianlong-salesmaster/src/tianlong_salesmaster/`
> **技术栈:** 纯标准库 Python（后端）+ HTML/CSS/JS（前端）

---

## 阶段一：项目骨架（P0）

| # | 任务 | 文件 |
|---|------|------|
| 1 | 创建目录结构 | `team/` `llm/` `channels/` `product/` `web/` |
| 2 | 商品管理模块 | `product/__init__.py` `product/config.py` `product/pricing.json` |
| 3 | LLM 引擎 | `llm/__init__.py` `llm/deepseek.py` `llm/fallback.py` |
| 4 | 平台通信基类 | `channels/__init__.py` `channels/base.py` `channels/email.py` |
| 5 | Agent 基类 | `team/__init__.py` `team/base.py` |

## 阶段二：SalesOrchestrator 编排器（P0）

| # | 任务 | 文件 |
|---|------|------|
| 6 | 编排器核心 | `team/coordinator.py`（任务调度+状态管理+数据总线）|
| 7 | 安全模式门控 | 内置在编排器中 |
| 8 | 冷启动引导 | `web/pages/quickstart.html` |

## 阶段三：6 个 Agent（P1）

| # | 任务 | 文件 |
|---|------|------|
| 9 | 市场调研 Agent | `team/market_research.py` |
| 10 | 竞品分析 Agent | `team/competitor_intel.py` |
| 11 | 售前 Agent | `team/presales.py` |
| 12 | 售后 Agent | `team/aftersales.py` |
| 13 | 成本优化 Agent | `team/procurement.py` |
| 14 | 运营 Agent | `team/operations.py` |

## 阶段四：Web 管理后台（P2）

| # | 任务 | 文件 |
|---|------|------|
| 15 | Web 服务启动 | `web/server.py`（纯标准库 http.server）|
| 16 | 9 个页面路由 | 集成 `/mnt/c/XSZS/` 界面 |
| 17 | API 端点 | 对接编排器和各 Agent |

## 阶段五：集成与测试（P2）

| # | 任务 | 文件 |
|---|------|------|
| 18 | API 平台集成测试 | 邮件/微信等 |
| 19 | 安全模式工作流测试 | 保守/开放/自定义 |
| 20 | 冷启动流程测试 | 行业模板 → 5 步启动 |
