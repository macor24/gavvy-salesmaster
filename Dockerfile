# 使用 Python 3.10 作为基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY pyproject.toml .
COPY setup.cfg .
COPY MANIFEST.in .

# 安装 Python 依赖
RUN pip install --no-cache-dir -e .

# 复制源代码
COPY src/ src/
COPY docs/ docs/

# 创建数据目录
RUN mkdir -p /app/data /app/logs

# 暴露端口
EXPOSE 8877

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8877/health || exit 1

# 启动命令
CMD ["python3", "-c", "import sys; sys.path.insert(0, '/app/src'); from gavvy_salesmaster.core.app import start_app; start_app()"]
