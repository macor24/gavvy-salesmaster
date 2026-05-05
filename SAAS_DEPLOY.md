# Gavvy 销售宗师 SaaS 部署指南

## 🚀 快速部署

### 方式一：Docker 一键部署

```bash
# 克隆项目
git clone https://github.com/your-repo/SentriKit-salesmaster.git
cd SentriKit-salesmaster

# 启动服务
docker-compose up -d

# 访问
# 落地页: http://localhost:8877/landing
# 管理后台: http://localhost:8877/
# API文档: http://localhost:8877/docs
```

### 方式二：手动部署

```bash
# 安装依赖
pip install fastapi uvicorn python-dotenv

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的配置

# 启动服务
SentriKit-sales-fastapi
```

---

## 📋 环境变量配置

### 必需配置

```bash
# API 认证
SALES_API_KEY=your-secure-api-key

# SaaS 模式（设为 true 启用多租户）
SALES_USE_SAAS=true

# 租户密钥
SALES_TENANT_SECRET=your-tenant-secret
```

### 可选配置

```bash
# CORS 跨域（生产环境建议配置）
SALES_CORS_ORIGINS=https://your-domain.com

# API 限流（每分钟请求数）
SALES_RATE_LIMIT=100

# 数据库
DB_TYPE=sqlite  # 或 mysql / postgres
DATABASE_URL=your-database-url
```

---

## 🌐 SaaS 功能

### 落地页
- 访问 `/landing` 或 `/demo` 查看产品展示
- 包含功能介绍、定价、试用申请

### 管理后台
- 访问 `/` 进入管理后台
- 支持多租户数据隔离

### API 接口
- 访问 `/docs` 查看完整 API 文档
- 支持租户注册、订阅管理

---

## 📦 目录结构

```
├── data/               # 数据存储
├── backups/            # 自动备份
├── src/
│   └── SentriKit_salesmaster/
│       ├── saas/      # SaaS 多租户模块
│       └── web/       # 前端页面
├── scripts/
│   └── backup_data.py # 备份脚本
└── docker-compose.yml # Docker 配置
```

---

## 🔒 安全建议

1. **生产环境务必配置**
   - `SALES_API_KEY` 设置强密钥
   - `SALES_CORS_ORIGINS` 限制来源
   - 使用 HTTPS

2. **定期备份**
   ```bash
   python scripts/backup_data.py --keep-days 30
   ```

3. **监控健康状态**
   - `/api/health` - 简单检查
   - `/api/health/detailed` - 详细状态

---

## 🆘 技术支持

- 文档: `/docs`
- 问题反馈: GitHub Issues
- 邮箱: support@example.com
