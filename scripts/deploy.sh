#!/bin/bash
# ============================================================
# Gavvy 销售宗师 - 阿里云一键部署脚本
# 用法: bash deploy.sh [你的服务器IP]
# 前提: 服务器已安装 docker + docker-compose
# ============================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SERVER_IP="${1:-}"
PROJECT_DIR="/opt/gavvy-salesmaster"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Gavvy 销售宗师 - 阿里云部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# ---- 检查参数 ----
if [ -z "$SERVER_IP" ]; then
    echo -e "${YELLOW}用法: bash deploy.sh <服务器IP>${NC}"
    echo -e "${YELLOW}示例: bash deploy.sh 123.123.123.123${NC}"
    exit 1
fi

echo -e "${GREEN}[1/5] 本地打包项目...${NC}"
tar czf /tmp/gavvy-deploy.tar.gz \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='.pytest_cache' \
    --exclude='*.pyc' \
    -C "$(dirname "$0")" .

echo -e "${GREEN}[2/5] 上传到服务器 ${SERVER_IP}...${NC}"
ssh -o StrictHostKeyChecking=no "root@${SERVER_IP}" "mkdir -p ${PROJECT_DIR}"
scp -o StrictHostKeyChecking=no /tmp/gavvy-deploy.tar.gz "root@${SERVER_IP}:${PROJECT_DIR}/"

echo -e "${GREEN}[3/5] 服务器解压...${NC}"
ssh -o StrictHostKeyChecking=no "root@${SERVER_IP}" "cd ${PROJECT_DIR} && tar xzf gavvy-deploy.tar.gz && rm gavvy-deploy.tar.gz"

echo -e "${GREEN}[4/5] 构建并启动 Docker 服务...${NC}"
ssh -o StrictHostKeyChecking=no "root@${SERVER_IP}" "cd ${PROJECT_DIR} && \
    export SALES_API_KEY=\$(openssl rand -hex 16) && \
    export SALES_API_HOST=0.0.0.0 && \
    export SALES_API_PORT=8877 && \
    docker compose build gavvy-salesmaster && \
    docker compose up -d gavvy-salesmaster"

echo -e "${GREEN}[5/5] 健康检查...${NC}"
sleep 5
ssh -o StrictHostKeyChecking=no "root@${SERVER_IP}" "curl -s http://127.0.0.1:8877/health" || {
    echo -e "${RED}⚠️ 健康检查失败，请手动检查${NC}"
}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}  访问地址: http://${SERVER_IP}:8877${NC}"
echo -e "${GREEN}  API Key: 在服务器运行: echo \$SALES_API_KEY${NC}"
echo -e "${GREEN}========================================${NC}"
