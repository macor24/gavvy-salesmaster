# 📦 Gavvy 销售宗师 - 安装包说明

## 📥 下载安装包

### 方式 1：直接下载（推荐）

**最新稳定版下载：**
- 🔗 [GavvySalesMaster_v1.0.0.zip](https://github.com/your-repo/gavvy-salesmaster/releases/download/v1.0.0/GavvySalesMaster_v1.0.0.zip)
- 📦 文件大小：约 200MB（包含 Python 运行时）
- ✅ 无需安装 Python，开箱即用

### 方式 2：源码安装

```bash
# 克隆仓库
git clone https://github.com/your-repo/gavvy-salesmaster.git

# 进入目录
cd gavvy-salesmaster
```

---

## 🖱️ 一键安装（Windows）

### 步骤 1：解压安装包
1. 下载 `GavvySalesMaster_v1.0.0.zip`
2. 右键解压到任意文件夹（如 `D:\GavvySalesMaster`）

### 步骤 2：运行安装
1. 打开解压后的文件夹
2. **右键点击 `install.bat`** → **以管理员身份运行**
3. 等待安装完成（约 5-10 分钟）

### 步骤 3：启动服务
1. 双击 `start.bat`
2. 打开浏览器访问 → **http://localhost:8000**

---

## 🐳 Docker 一键部署（跨平台）

### 前提条件
- 安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### 启动命令
```bash
# 下载并启动
docker run -d -p 8000:8000 gavvy/salesmaster:latest

# 或使用 Docker Compose
docker-compose up -d
```

### 访问服务
- 浏览器打开：**http://localhost:8000**

---

## 📁 安装包结构

```
GavvySalesMaster/
├── install.bat          # 一键安装脚本
├── start.bat            # 启动脚本
├── stop.bat             # 停止脚本
├── src/                 # 源代码目录
├── data/                # 数据库数据目录
├── logs/                # 日志目录
└── README.md            # 使用说明
```

---

## ⚠️ 注意事项

### 安装前准备
1. **关闭杀毒软件**：部分杀毒软件可能会拦截安装脚本
2. **管理员权限**：必须以管理员身份运行安装脚本
3. **网络连接**：首次安装需要下载依赖包

### 常见问题

**Q: 安装失败提示权限不足？**
- 右键 `install.bat` → 以管理员身份运行

**Q: 端口 8000 被占用？**
- 修改 `start.bat` 中的端口号
- 或关闭占用 8000 端口的程序

**Q: 服务启动后无法访问？**
- 检查防火墙是否允许 8000 端口
- 尝试访问：http://127.0.0.1:8000

---

## 📞 技术支持

| 方式 | 联系方式 |
|------|----------|
| 📧 邮箱 | support@gavvy.io |
| 💬 微信 | Gavvy_Support |
| 📖 文档 | https://docs.gavvy.io |
| 🐛 反馈 | https://github.com/your-repo/issues |

---

**🎉 祝您使用愉快！**

Gavvy 销售宗师 - 让 AI 帮您自动找客户、谈订单！
