# 快速开始

## 安装

```bash
pip install tianlong-salesmaster
```

启动 Web 管理后台：

```bash
tianlong-sales-fastapi
```

浏览器打开 http://localhost:8877。

## 激活 AI 销售团队（企业版）

```bash
pip install tianlong-salesmaster[enterprise]
export SALES_ENTERPRISE=1
tianlong-sales-fastapi
```

## Docker 部署

```bash
docker compose up -d
# 访问 http://localhost:8877
```

## 嵌入式获客

```html
<script src="http://你的域名/widget.js"
  data-api-url="http://你的域名"
  data-welcome="您好！有什么可以帮您？">
</script>
```
