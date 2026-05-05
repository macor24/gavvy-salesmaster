FROM python:3.11-slim

WORKDIR /app

# 从本地 wheel 安装（发布到 PyPI 后改回 pip install SentriKit-salesmaster[fastapi]）
COPY dist/SentriKit_salesmaster-2.5.0-py3-none-any.whl /tmp/
RUN pip install /tmp/SentriKit_salesmaster-2.5.0-py3-none-any.whl[fastapi] --no-cache-dir

# 默认端口
EXPOSE 8877

# 启动
CMD ["SentriKit-sales-fastapi", "--host", "0.0.0.0", "--port", "8877"]
