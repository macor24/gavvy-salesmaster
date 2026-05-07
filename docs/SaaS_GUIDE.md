# SaaS 多租户快速入门

## 启用 SaaS 模式

```bash
# Windows PowerShell
$env:SALES_USE_SAAS="true"

# Windows CMD
set SALES_USE_SAAS=true

# Linux/Mac
export SALES_USE_SAAS=true
```

## 启动服务

```bash
# 使用命令行工具
gavvy-sales-fastapi

# 或直接运行模块
python -m SentriKit_salesmaster.app
```

启动时会看到：
```
🚀 Chat Sales FastAPI 启动: http://0.0.0.0:8877
   🌐 SaaS模式: 已启用
   📋 SaaS API: /api/saas/*
   ...
```

## API 使用

### 1. 注册租户

```bash
curl -X POST http://localhost:8877/api/saas/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的公司",
    "slug": "my-company",
    "company": "某某科技有限公司",
    "admin_email": "admin@company.com",
    "admin_name": "管理员",
    "admin_password": "your-password"
  }'
```

响应：
```json
{
  "success": true,
  "tenant_id": "uuid",
  "user_id": "uuid",
  "token": "JWT token"
}
```

### 2. 用户登录

```bash
curl -X POST http://localhost:8877/api/saas/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@company.com",
    "password": "your-password"
  }'
```

响应：
```json
{
  "token": "JWT token",
  "user": {...},
  "tenant": {...}
}
```

### 3. 访问需要认证的 API

使用 `Authorization: Bearer <token>` 头：

```bash
curl http://localhost:8877/api/saas/tenant \
  -H "Authorization: Bearer your-token"
```

## SaaS API 路由

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/saas/auth/register` | POST | 注册租户和管理员 |
| `/api/saas/auth/login` | POST | 用户登录 |
| `/api/saas/auth/me` | GET | 获取当前用户信息 |
| `/api/saas/tenant` | GET | 获取租户信息 |
| `/api/saas/tenant` | PUT | 更新租户设置 |
| `/api/saas/subscription` | GET | 获取订阅信息 |
| `/api/saas/subscription` | PUT | 更新订阅套餐 |
| `/api/saas/quota` | GET | 获取配额使用情况 |
| `/api/saas/users` | GET | 列出租户用户 |
| `/api/saas/users` | POST | 创建新用户 |
| `/api/saas/users/{id}` | PUT | 更新用户 |
| `/api/saas/users/{id}` | DELETE | 删除用户 |
| `/api/saas/plans` | GET | 列出可用套餐 |

## 套餐对比

| 套餐 | 价格 | 用户数 | 存储 | API调用/月 |
|------|------|--------|------|-----------|
| Free | 免费 | 3 | 100MB | 1,000 |
| Starter | ¥99 | 10 | 1GB | 10,000 |
| Professional | ¥399 | 50 | 10GB | 100,000 |
| Enterprise | ¥999 | 无限 | 100GB | 无限 |

## 目录结构

```
SentriKit_salesmaster/
├── saas/
│   ├── __init__.py          # 数据模型：Tenant, TenantUser, JWT, RateLimiter
│   ├── manager.py           # SaaS管理器
│   ├── middleware.py        # FastAPI中间件
│   └── routes.py            # API路由
└── storage/_tenants/
    ├── tenants.json         # 租户数据
    ├── users.json           # 用户数据
    └── usage.json           # 用量统计
```

## 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `SALES_USE_SAAS` | `false` | 启用SaaS模式 |
| `SALES_TENANT_SECRET` | 随机密钥 | JWT签名密钥 |
| `SALES_API_HOST` | `0.0.0.0` | 监听地址 |
| `SALES_API_PORT` | `8877` | 监听端口 |

## JWT Token

Token格式：`tenant_id.user_id.expires.signature`

```python
from SentriKit_salesmaster.saas import JWTToken
token = JWTToken.generate(tenant_id, user_id, secret, expires_in=86400)
payload = JWTToken.verify(token, secret)
```

## 配额检查

```python
from SentriKit_salesmaster.saas.manager import get_saas_manager
saas = get_saas_manager()
quota = saas.check_quota(tenant_id)
# {
#   "plan": "free",
#   "seats": {"limit": 3, "used": 1, "available": 2},
#   "storage_mb": {"limit": 100, "used": 0, "available": 100},
#   "api_calls": {"limit": 1000, "used": 0, "available": 1000},
#   "over_quota": false
# }
```

## API限流

- Free版：60次/分钟
- Paid版：300次/分钟

响应头包含 `X-RateLimit-Remaining` 显示剩余请求数。

## 测试SaaS功能

```bash
# 运行所有SaaS测试
python -m pytest tests/test_saas.py -v

# 运行集成测试
python -m pytest tests/test_saas_integration.py -v
```
