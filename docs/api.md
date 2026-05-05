# API 文档

启动服务后访问 Swagger UI 获取完整 API 文档：

- **Swagger UI**: http://localhost:8877/docs
- **ReDoc**: http://localhost:8877/redoc

## 核心 API

### AI 销售团队

```http
POST /api/orchestrator/lead       # 添加销售线索
GET  /api/orchestrator/leads      # 线索列表
POST /api/orchestrator/dispatch   # 派发到AI Agent
GET  /api/orchestrator/agents     # Agent 列表
```

### 销售管道

```http
POST /api/pipeline/run            # 触发销售管道
POST /api/pipeline/lead           # 添加线索到管道
GET  /api/pipeline/leads          # 管道内线索
```

### 分析

```http
GET /api/analytics/summary        # 分析摘要
```

### 进化闭环

```http
POST /api/evolve/run              # 触发进化
GET  /api/evolve/status           # 进化状态
POST /api/evolve/auto-check       # 自动检查+触发
```

### 认证

所有 API 请求需要携带 `X-API-Key` 请求头。

```bash
curl -H "X-API-Key: your-key" http://localhost:8877/api/health
```
