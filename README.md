# gavvy 销售引擎

> 开源销售引擎 — CRM + AI 虚拟销售团队 + 自动化 Pipeline  
> `pip install gavvy-salesmaster` 即用，1分钟启动全流程

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

启动后控制台会输出访问地址和默认密码。

---

## 功能架构

```
┌──────────────────────────────────────────────────────┐
│                  gavvy 销售引擎                       │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ CRM 客户  │  │ 报价系统  │  │ 电子签    │  开源   │
│  │ 管理      │  │ Quotes   │  │ ESign    │  (MIT)   │
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
│  │  AI 销售引擎                                │      │
│  │  SalesOrchestrator + 7 Agent + MemoryStore │      │
│  │  + HuntEngine(自动寻客) + AutoScheduler    │      │
│  └────────────────────────────────────────────┘      │
│                                                      │
│  ┌────────────────────────────────────────────┐      │
│  │  Web 管理后台（14页面 SPA）                  │      │
│  │  REST API（187 路由）                       │      │
│  │  嵌入式获客 widget                          │      │
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

## Docker 部署

```bash
docker build -t gavvy-salesmaster .
docker run -d -p 8877:8877 --name gavvy gavvy-salesmaster
# 访问 http://localhost:8877，默认账号 admin / admin123
```

---

## 首次使用

1. 浏览器打开 `http://localhost:8877`
2. 用 `admin` / `admin123` 登录
3. 系统会弹出快速配置向导，引导你完成行业和产品设置
4. 配置完成后即可开始使用

### 主要功能入口

| 页面 | 功能 |
|------|------|
| 📊 仪表盘 | 销售总览、管道状态、Agent 运行状态 |
| 💬 工作台 | 客户对话、消息管理、AI 调度 |
| 👥 客户 | CRM 客户/商机/合同管理 |
| 📈 分析 | 销售漏斗、Agent 效能、KPI 看板 |
| 🤖 团队 | 7 个 AI Agent 管理和状态监控 |
| 🧠 记忆库 | 销售数据学习、技能进化、模式识别 |
| ⚙️ 设置 | 安全模式、渠道配置、SentriKit 集成 |

---

## API 文档

启动服务后访问：

- **Swagger UI**: http://localhost:8877/docs
- **ReDoc**: http://localhost:8877/redoc
- **健康检查**: http://localhost:8877/health

### 示例 API

```http
POST /api/hunt/run          # 触发自动寻客
GET  /api/hunt/leads        # 查看寻客线索
POST /api/scheduler/submit  # 提交消息到 AI Agent 处理
GET  /api/orchestrator/summary  # 销售总览
POST /api/flywheel/cycle    # 触发数据飞轮学习
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
│   ├── core/              # FastAPI 服务、API 路由、Web SPA
│   ├── team_pkg/          # AI 销售团队（7Agent + Orchestrator + 记忆库）
│   ├── crm_pkg/           # CRM、寻客引擎、调度器、RBAC
│   ├── trade_pkg/         # 支付、电子签章
│   ├── channels_pkg/      # 消息渠道（企微/钉钉/飞书/邮件）
│   └── data/              # JSON 文件存储
├── tests/                 # 测试
└── pyproject.toml
```

---

## 许可

- **社区版**: MIT License（pip install 即得）
- **企业版**: 闭源（核心 Prompt 和 AI 策略在服务端）
