# CLI 命令

| 命令 | 说明 | 依赖 |
|------|------|------|
| `tianlong-sales-fastapi` | 统一 API + Web 服务（端口 8877） | 无 |
| `tianlong-sales-api` | 纯 API 服务（已弃用） | 无 |

## 常用选项

```bash
# 指定端口
tianlong-sales-fastapi --port 8877

# 指定监听地址
tianlong-sales-fastapi --host 0.0.0.0

# 设置 API Key
SALES_API_KEY=my-key tianlong-sales-fastapi
```

## API 文档

启动服务后访问：

- Swagger UI: http://localhost:8877/docs
- ReDoc: http://localhost:8877/redoc
