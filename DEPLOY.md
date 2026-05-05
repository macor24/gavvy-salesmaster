# 灯塔水母 · 销售宗师 部署说明
# ───────────────────────────────────────
# 服务已运行在 http://localhost:8877
# API: http://localhost:8877/api/health
# Web: http://localhost:8877/
# Widget: http://localhost:8877/widget.js
# Demo: http://localhost:8877/widget-demo.html

# ── 公网暴露方式（按可用性排序）──

# 方式1: 已有公网 IP + 已配置端口转发
# 访问: http://113.101.213.55:8877/
# 注意: 运营商可能封锁端口，可尝试更换端口
# Windows 防火墙规则已添加（若需删除）:
#   netsh advfirewall firewall delete rule name="SalesMaster 8877"
# 端口转发（若需删除）:
#   netsh interface portproxy delete v4tov4 listenport=8877

# 方式2: 使用 frp（推荐）
# 服务端: frps -c frps.ini（需一台有公网IP的服务器）
# 客户端（本机）:
#   [common]
#   server_addr = your-server-ip
#   server_port = 7000
#   [salesmaster]
#   type = tcp
#   local_ip = 127.0.0.1
#   local_port = 8877
#   remote_port = 8877

# 方式3: cloudflare tunnel
# cloudflared tunnel --url http://localhost:8877

# 方式4: 用 Python 快速启动一个本地可访问的 HTTP 服务
# （如果只是局域网使用）
# python3 -m http.server 8877

# ── 真实 API Key 配置 ──
# 方式A: 在 API 配置页面 DeepSeek 卡片中填写
# 方式B: 环境变量
#   export LLM_API_KEY=sk-your-real-key
#   export OPENAI_API_KEY=sk-your-real-key
# 方式C: API 调用
#   curl -X POST http://localhost:8877/api/llm/config \
#     -H "Content-Type: application/json" \
#     -d '{"api_key":"sk-your-real-key"}'

# ── 验证全链路 ──
# 1. 配置 API Key
# 2. 测试: curl http://localhost:8877/api/llm/status
# 3. 发送消息: 
#    curl -X POST http://localhost:8877/api/chat/send \
#      -H "Content-Type: application/json" \
#      -d '{"message":"你好，我想了解产品","customer":"测试客户"}'
# 4. 检查 Dashboard: http://localhost:8877/
# 5. 嵌入 Widget: 在任意网页的 <body> 末尾加入
#    <script src="http://你的地址:8877/widget.js"
#        data-api-url="http://你的地址:8877"
#        data-site-name="你的网站"></script>
