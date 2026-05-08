# gavvy 销售引擎

> AI 驱动的销售对话引擎 — 六维心理博弈 + 7×24 AI 销售团队
> `pip install gavvy-salesmaster` 即用，零外部依赖跑通全流程

---

## 核心能力：第一屏就看这个

gavvy 不是普通的 CRM，是**会思考的销售 AI**。每个销售对话背后，都有六维引擎在驱动：

```
┌──────────────────────────────────────────────────────────────┐
│                   gavvy 六维销售引擎                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  §1  心理博弈      能量感知 → 情绪解码 → 决策节奏分析           │
│                                                              │
│  §2  多线程谈判    联系人图谱 → 组织博弈 → 决策链追踪           │
│                                                              │
│  §3  价值量化      痛点映射 → ROI 计算 → 价值等式构建           │
│                                                              │
│  §4  风险管控      合规检查 → 敏感词检测 → 信任建设             │
│                                                              │
│  §5  话术进化      A/B 测试 → 策略迭代 → 成交率优化             │
│                                                              │
│  §6  销售团队     7 Agent 并行 → 智能分流 → 全天候跟进         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

> 六维引擎代码 100% 开源（MIT），本地完整运行。
> AI 团队（7 Agent 并行 + 自动寻客）由企业版服务端驱动，设置 API Key 激活。

---

## 快速启动

```bash
# 1. 安装
pip install gavvy-salesmaster

# 2. 启动 Web 管理后台
gavvy-sales-fastapi

# 3. 浏览器打开 http://localhost:8877
#    默认账号: admin / admin123
```

不需要数据库，不需要配置，不需要 API Key。

---

## 功能架构

```
┌──────────────────────────────────────────────────────┐
│                    gavvy 销售引擎                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────┐      │
│  │  六维销售引擎（MIT 开源，本地运行）           │  ⭐  │
│  │  心理博弈 · 多线程谈判 · 价值量化              │      │
│  │  风险管控 · 话术进化 · 销售团队               │      │
│  └────────────────────────────────────────────┘      │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ CRM 客户  │  │ 报价系统  │  │ 电子签    │           │
│  │ 管理      │  │ Quotes   │  │ ESign    │  MIT 开源  │
│  └──────────┘  └──────────┘  └──────────┘           │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ 支付系统  │  │ 权限管理  │  │ 消息渠道  │           │
│  │ Payment  │  │ RBAC     │  │ Channels │           │
│  └──────────┘  └──────────┘  └──────────┘           │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ 知识库   │  │ 话术训练  │  │ 工作流   │           │
│  │ Knowledge│  │ Scripts  │  │ Workflow │           │
│  └──────────┘  └──────────┘  └──────────┘           │
│                                                      │
│  ┌────────────────────────────────────────────┐      │
│  │  AI 销售引擎（企业版，服务端 API）            │ ← 付费  │
│  │  7 Agent + HuntEngine + AutoScheduler       │        │
│  └────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────┘
```

---

## CLI 命令

| 命令 | 说明 |
|------|------|
| `gavvy-sales-fastapi` | **推荐** 统一 API + Web 服务（8877端口） |

### 可选增强

```bash
# 激活 SentriKit 进化闭环集成（需安装 sentrikit）
pip install gavvy-salesmaster[gavvy]

# 使用 PostgreSQL 数据库（默认使用 JSON 文件存储）
pip install gavvy-salesmaster[database]

# 全部装齐
pip install gavvy-salesmaster[all]
```

---

## 功能模块

### 六维销售引擎（⭐ 核心差异化，MIT 开源）

| 模块 | 功能 |
|------|------|
| `psychology` | 心理博弈：能量感知、情绪解码、服从性阶梯、合规检查 |
| `multithread` | 多线程谈判：联系人图谱、组织博弈、决策链追踪 |
| `value` | 价值量化：痛点映射、ROI 计算、价值等式构建 |
| `risk` | 风险管控：敏感词检测、承诺管控、合同风险 |
| `language` | 销售语言：话术生成、语体适配、副语言解码 |
| `evolver` | 策略进化：A/B 测试、策略迭代、成交率优化 |

### 基础设施（MIT 开源，pip install 即得）

| 模块 | 功能 |
|------|------|
| `crm` | 客户管理：Customer/Deal/Contract/Activity CRUD |
| `payment` | 支付系统：多渠道支付/退款/对账 |
| `channels` | 消息渠道：企业微信/钉钉/飞书/邮件/SMS |
| `rbac` | 权限体系：User/Role/Permission 完整 RBAC |
| `quotes` | 报价系统：自动报价/合同/多级价格 |
| `esign` | 电子签章：字节跳动签 + 腾讯签双引擎 |
| `workflow` | 工作流引擎：Step/Event/Template |
| `saas` | SaaS 多租户：Tenant/Subscription/Plan |
| `knowledge` | 知识库：条目/FAQ/分类/搜索 |
| `scripts` | 话术训练：场景/评分、模拟对话 |
| `analytics` | 分析报表：KPI/漏斗/趋势/预测 |
| `export` | 导出引擎：Excel/PDF/HTML/Word |
| `tasks` | 任务管理：调度/队列/定时 |
| `webhook` | Webhook：Stripe/支付宝/微信支付集成 |
| `storage` | 文件数据库内核（线程安全 JSON 存储） |
| `llm` | 多模型 LLM 接入：DeepSeek/OpenAI/Claude |
| `calls` | 通话系统：记录/录音/分析 |

### 企业版（服务端 API，需商业授权）

| 模块 | 功能 |
|------|------|
| `team` | AI 销售团队：SalesOrchestrator + 7 Agent + 智能线索评分 |
| `memory` | 学习记忆库：MemoryStore + Learner + 技能进化引擎 |
| `hunt` | 自动寻客引擎：多渠道线索挖掘 + 智能评分 |
| `scheduler` | 自动调度：消息队列 + 定时跟进 |

---

## API 文档

启动服务后访问：

- **Swagger UI**: http://localhost:8877/docs
- **ReDoc**: http://localhost:8877/redoc
- **健康检查**: http://localhost:8877/health

### 核心 API

```http
POST /api/orchestrator/lead     # 添加销售线索
GET  /api/orchestrator/leads    # 线索列表
POST /api/orchestrator/dispatch # 派发到 AI Agent
POST /api/pipeline/run          # 触发销售管道
POST /api/hunt/run              # 触发自动寻客
GET  /api/hunt/leads            # 查看寻客线索
GET  /api/analytics/summary     # 分析摘要
POST /api/flywheel/cycle        # 触发数据飞轮学习
```

---

## 嵌入式获客

在任意网页嵌入一行 script 即可收集销售线索：

```html
<script src="http://你的域名/widget.js" 
  data-api-url="http://你的域名"
  data-welcome="您好！有什么可以帮您？">
</script>
```

---

## Docker 部署

```bash
docker build -t gavvy-salesmaster .
docker run -d -p 8877:8877 --name gavvy gavvy-salesmaster
# 访问 http://localhost:8877，默认账号 admin / admin123
```

---

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SALES_API_KEY` | API 认证密钥 | 自动生成 |
| `LLM_API_KEY` | DeepSeek/OpenAI API Key | 空（社区版用模板回复） |
| `SENTRIKIT_API_KEY` | SentriKit 企业版 API Key | 空 |

---

## 项目结构

```
gavvy-salesmaster/
├── src/gavvy_salesmaster/
│   ├── core/
│   │   ├── app.py             # FastAPI 服务（187路由）
│   │   ├── psychology.py      # §1 心理博弈
│   │   ├── multithread.py    # §2 多线程谈判
│   │   ├── value.py           # §3 价值量化
│   │   ├── risk.py            # §4 风险管控
│   │   ├── language.py        # §5 销售语言
│   │   ├── evolver.py         # §5 话术进化
│   │   └── llm_engine.py      # LLM 引擎框架
│   ├── team_pkg/             # AI 销售团队（企业版 API）
│   ├── crm_pkg/              # CRM、寻客引擎、调度器、RBAC
│   ├── trade_pkg/            # 支付、电子签章
│   ├── channels_pkg/         # 消息渠道（企微/钉钉/飞书/邮件）
│   └── data/                 # JSON 文件存储
├── tests/
└── pyproject.toml
```

---

## 许可

- **六维销售引擎 + 基础设施模块**: MIT License
- **AI 销售团队 + 自动寻客 + 学习记忆库**: 企业版（`SENTRIKIT_API_KEY` 激活）
- **联系方式**: [GitHub Issues](https://github.com/macor24/gavvy-salesmaster/issues)
