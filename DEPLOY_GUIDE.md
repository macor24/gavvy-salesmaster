# 🚀 Gavvy 销售宗师 - 一键部署指南

> 本指南提供多种部署方式，从简单到复杂，适合不同技术水平的用户。

---

## 一、快速开始（Windows 用户）

### 方式 1：一键安装（最简单）

1. **下载安装包**
   - 下载最新版本的 Gavvy 销售宗师安装包
   - 解压到任意文件夹（如 `D:\GavvySalesMaster`）

2. **双击安装**
   - 找到 `install.bat` 文件
   - **右键以管理员身份运行**
   - 等待安装完成（约5-10分钟）

3. **启动服务**
   - 双击 `start.bat`
   - 打开浏览器访问: **http://localhost:8000**

### 方式 2：使用 Docker（推荐）

> 需要先安装 Docker Desktop

1. **安装 Docker**
   - 下载并安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - 启动 Docker Desktop

2. **启动服务**
   ```bash
   # 进入项目目录
   cd GavvySalesMaster
   
   # 一键启动
   docker-compose up -d
   ```

3. **访问服务**
   - 浏览器打开: **http://localhost:8000**

---

## 二、部署方式对比

| 方式 | 难度 | 适用场景 | 优点 | 缺点 |
|------|------|----------|------|------|
| 🖱️ 一键安装 | 🌟 最简单 | Windows 用户、非技术人员 | 双击即可，无需配置 | 仅限 Windows |
| 🐳 Docker | ⭐ 简单 | 跨平台、生产环境 | 隔离性好、一键启动 | 需要安装 Docker |
| 📦 源码安装 | 🛠️ 中等 | 开发人员、自定义需求 | 灵活定制、调试方便 | 需要 Python 环境 |
| ☁️ 云服务器 | 🔧 复杂 | 企业级部署 | 高可用、可扩展 | 需要服务器知识 |

---

## 三、Docker 部署详细指南

### 3.1 前提条件

- Docker Desktop (Windows/macOS) 或 Docker Engine (Linux)
- 至少 2GB 内存
- 至少 10GB 磁盘空间

### 3.2 启动命令

```bash
# 进入项目目录
cd GavvySalesMaster

# 构建并启动（首次运行）
docker-compose up -d --build

# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 3.3 停止服务

```bash
# 停止服务（保留数据）
docker-compose stop

# 停止并删除容器（保留数据）
docker-compose down

# 完全清理（删除数据）
docker-compose down -v
```

### 3.4 数据持久化

数据会自动保存到 `./data` 目录，删除容器不会丢失数据。

---

## 四、源码部署指南（开发人员）

### 4.1 环境要求

- Python 3.10+
- pip 包管理器
- Git（可选）

### 4.2 安装步骤

```bash
# 1. 克隆仓库或解压源码
git clone https://github.com/your-repo/gavvy-salesmaster.git
cd gavvy-salesmaster

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -e .

# 4. 初始化数据库
python -c "from gavvy_salesmaster.core.app import init_app; init_app()"

# 5. 启动服务
python -m gavvy_salesmaster.web
```

### 4.3 开发模式

```bash
# 开发模式（自动重载）
python -m uvicorn gavvy_salesmaster.core.web:app --reload --host 0.0.0.0 --port 8000
```

---

## 五、云服务器部署（企业级）

### 5.1 服务器要求

| 配置 | 推荐配置 |
|------|----------|
| CPU | 2核以上 |
| 内存 | 4GB以上 |
| 存储 | 20GB以上 |
| 系统 | Ubuntu 22.04 LTS |

### 5.2 部署步骤

```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo systemctl enable docker
sudo systemctl start docker

# 3. 安装 Docker Compose
sudo apt install docker-compose-plugin -y

# 4. 下载项目
git clone https://github.com/your-repo/gavvy-salesmaster.git
cd gavvy-salesmaster

# 5. 启动服务
docker-compose up -d

# 6. 设置开机自启
sudo systemctl enable docker
```

### 5.3 配置域名（可选）

1. 购买域名并解析到服务器 IP
2. 配置 Nginx SSL（参考 nginx/conf.d/gavvy.conf）
3. 申请 SSL 证书（推荐 Let's Encrypt）

---

## 六、配置说明

### 6.1 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | sqlite:///data/tianlong_sales.db | 数据库连接地址 |
| `LOG_LEVEL` | INFO | 日志级别 |
| `PORT` | 8000 | 服务端口 |
| `HOST` | 0.0.0.0 | 绑定地址 |
| `DEEPSEEK_API_KEY` | - | DeepSeek API 密钥（可选） |

### 6.2 修改配置

创建 `.env` 文件：

```env
# .env 文件示例
DATABASE_URL=sqlite:///data/tianlong_sales.db
LOG_LEVEL=INFO
PORT=8000
```

---

## 七、常见问题

### Q1: 服务启动失败？

**可能原因**:
- 端口 8000 被占用
- 缺少依赖
- 权限不足

**解决方法**:
```bash
# 检查端口占用
netstat -ano | findstr :8000  # Windows
lsof -i :8000               # Linux/Mac

# 更换端口
set PORT=8080  # Windows
export PORT=8080  # Linux/Mac
```

### Q2: 数据库连接失败？

**解决方法**:
- 确保 `./data` 目录有写入权限
- 检查 `DATABASE_URL` 配置是否正确

### Q3: Docker 构建失败？

**解决方法**:
```bash
# 清理缓存后重新构建
docker-compose build --no-cache
```

---

## 八、升级指南

### 升级步骤

```bash
# 1. 停止服务
docker-compose stop

# 2. 备份数据
cp -r data data_backup

# 3. 更新代码
git pull

# 4. 重新构建
docker-compose up -d --build
```

---

## 九、支持与反馈

- 📧 邮箱: support@gavvy.io
- 📖 文档: https://docs.gavvy.io
- 🐛 问题反馈: https://github.com/your-repo/issues

---

**🎉 恭喜！你已成功部署 Gavvy 销售宗师！**

访问地址: **http://localhost:8000**

---

## 附录：命令速查表

| 操作 | 命令 |
|------|------|
| 启动服务 | `docker-compose up -d` |
| 停止服务 | `docker-compose stop` |
| 查看日志 | `docker-compose logs -f` |
| 重启服务 | `docker-compose restart` |
| 查看状态 | `docker-compose ps` |
| 清理容器 | `docker-compose down` |
