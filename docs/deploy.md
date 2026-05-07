# 部署指南

## pip 安装

```bash
pip install SentriKit-salesmaster[fastapi]
gavvy-sales-fastapi --host 0.0.0.0 --port 8877
```

## Docker

```bash
docker compose up -d
```

## Docker Compose（生产推荐）

```yaml
services:
  salesmaster:
    image: SentriKit-salesmaster:latest
    ports:
      - "8877:8877"
    environment:
      - SALES_API_KEY=your-api-key
    volumes:
      - sales_data:/app/src/SentriKit_salesmaster/storage/_data
    restart: unless-stopped
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SALES_API_KEY` | API Key 认证 | 无认证 |
| `SALES_ENTERPRISE` | 企业版激活 | 社区版 |
| `SALES_ENTERPRISE_KEY` | License Key | - |
| `SentriKit_API_URL` | SentriKit API 地址 | - |
