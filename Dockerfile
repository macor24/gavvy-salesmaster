# 使用 Python 3.12 slim 作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装运行时系统依赖（仅 libpq 可选，用于 database 模式）
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY pyproject.toml README.md MANIFEST.in ./

# 复制源码（先复制 src/ 再安装，避免 pip install -e . 找不到文件）
COPY src/ src/

# 安装 Python 依赖（从 PyPI wheel 安装，无需 gcc 编译）
RUN pip install --no-cache-dir .

# 创建数据目录
RUN mkdir -p /app/data /app/logs

# 暴露端口
EXPOSE 8877

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8877/health || exit 1

# 启动命令
CMD ["gavvy-sales-fastapi"]
