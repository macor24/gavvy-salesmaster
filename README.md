# gavvy 销售引擎

> 开源销售引擎 — CRM + AI 虚拟销售团队 + 自动化 Pipeline  
> `pip install gavvy-salesmaster` 即用，零外部依赖跑通全流程

---

## 快速启动

```bash
# 1. 安装
pip install gavvy-salesmaster

# 2. 启动 Web 管理后台（带 API）
gavvy-sales-fastapi

# 3. 浏览器打开
open http://localhost:8877
```

就这么简单。不需要数据库，不需要配置，不需要 API Key。

---

## 功能架构

```
┌──────────────────────────────────────────────────────┐
│                  gavvy 销售引擎                  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ CRM 客户  │  │ 报价系统  │  │ 电子签    │           │
│  │ 管理      │  │ Quotes   │  │ ESign    │  开源     │
│  └──────────┘  └──────────┘  └──────────┘  (MIT)    │
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
│  │  AI 销售引擎（企业版）                        │ ← 闭源 │
│  │  SalesOrchestrator + 7 Agent + MemoryStore │        │
│  └────────────────────────────────────────────┘      │
│                                                      │
│  ┌────────────────────────────────────────────┐      │
│  │  Web 管理后台（14页面 SPA）                   │      │
│  │  REST API（160 路由）                       │      │
│  │  嵌入式获客 widget                          │      │
│  └────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────┘
```

---

## CLI 命令

| 命令 | 说明 |
|------|------|
| `gavvy-sales-fastapi` | **推荐** 统一 API + Web 服务（8877端口） |
| `gavvy-sales-api` | 纯 API 服务（已弃用，建议用 FastAPI） |

### 安装可选依赖

```bash
# 激活 AI 销售引擎（企业版闭源）
pip install gavvy-salesmaster[enterprise]

# 激活 SentriKit 进化闭环集成
pip install gavvy-salesmaster[SentriKit]

# 使用 FastAPI（推荐）
pip install gavvy-salesmaster[fastapi]

# 全部装齐
pip install gavvy-salesmaster[all]
```

---

## 功能模块

### 开源版（MIT，pip install 即得）

| 模块 | 功能 | 行数 |
|------|------|------|
| `crm` | 客户管理：Customer/Deal/Contract/Activity CRUD | 484 |
| `payment` | 支付系统：多渠道支付/退款/对账 | 1,326 |
| `channels` | 消息渠道：企业微信/钉钉/飞书/邮件/SMS | 2,109 |
| `rbac` | 权限体系：User/Role/Permission 完整 RBAC | 2,114 |
| `quotes` | 报价系统：自动报价/合同/多级价格 | 922 |
| `esign` | 电子签章：字节跳动签 + 腾讯签双引擎 | 1,206 |
| `workflow` | 工作流引擎：Step/Event/Template | 1,165 |
| `saas` | SaaS 多租户：Tenant/Subscription/Plan | 1,161 |
| `knowledge` | 知识库：条目/FAQ/分类/搜索 | 738 |
| `scripts` | 话术训练：场景/评分/模拟对话 | 613 |
| `analytics` | 分析报表：KPI/漏斗/趋势/预测 | 637 |
| `export` | 导出引擎：Excel/PDF/HTML/Word | 676 |
| `tasks` | 任务管理：调度/队列/定时 | 902 |
| `webhook` | Webhook：Stripe/支付宝/微信支付集成 | 565 |
| `storage` | 文件数据库内核（线程安全 JSON 存储） | 3,392 |
| `llm` | 多模型 LLM 接入：DeepSeek/OpenAI/Claude | 946 |
| `calls` | 通话系统：记录/录音/分析 | 763 |

### 企业版（闭源，需商业授权）

| 模块 | 功能 | 行数 |
|------|------|------|
| `team` | AI 销售团队：SalesOrchestrator + 7Agent + LeadScorer + SafetyGuard | 4,661 |
| `memory` | 学习记忆库：MemoryStore + Learner + SkillEvolver | 624 |

---

## API 文档

启动服务后访问：

- **Swagger UI**: http://localhost:8877/docs
- **ReDoc**: http://localhost:8877/redoc
- **健康检查**: http://localhost:8877/health

### 核心 API（部分）

```http
POST /api/orchestrator/lead    # 添加销售线索
GET  /api/orchestrator/leads   # 线索列表
POST /api/orchestrator/dispatch # 派发到AI Agent
POST /api/pipeline/run         # 触发销售管道
GET  /api/analytics/summary    # 分析摘要
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
# 一键启动
docker compose up -d

# 访问 http://localhost:8877
```

---

## 与 SentriKit 集成

销售宗师可与 SentriKit（SentriKit-toolkit）集成，获得完整的自进化闭环能力：

1. 启动 SentriKit API：`SentriKit-api --port 8899`
2. 设置环境变量：`export SentriKit_API_URL=http://127.0.0.1:8899`
3. 销售宗师自动检测并激活进化闭环

可调用：退化检测 → 提案评分 → 完整进化闭环（学习→分析→判断→进化→验证→反射→清理）

---

## 项目结构

```
gavvy-salesmaster/
├── src/SentriKit_salesmaster/
│   ├── app.py              # FastAPI 统一服务（2485行，160路由）
│   ├── master.py           # SalesMaster 六维引擎
│   ├── SentriKit_client.py  # SentriKit API 客户端
│   ├── team/               # (shim) AI 销售团队 ← 指向企业版
│   ├── memory/             # (shim) 学习记忆库 ← 指向企业版
│   ├── web/                # 前端 SPA（index.html+script.js+styles.css）
│   ├── crm/ payment/ rbac/ quotes/ ...  # 20+业务模块
│   └── storage/            # 文件数据库内核
├── tests/                  # 5,236 行测试
└── pyproject.toml          # pip install 即用
```

---

## 许可

- **开源模块**: MIT License
- **AI 销售引擎**: 企业版闭源（`gavvy-sales-enterprise`）
- **联系方式**: [GitHub Issues](https://github.com/)
