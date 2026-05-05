@echo off
REM Gavvy 销售宗师 - PostgreSQL 启动脚本 (Windows)
REM 使用方法: 双击运行此脚本

echo ============================================================
echo Gavvy 销售宗师 - PostgreSQL 数据库设置
echo ============================================================
echo.

REM 检查 Docker 是否安装
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Docker 未安装或未运行
    echo.
    echo 请先安装 Docker Desktop:
    echo   https://docs.docker.com/desktop/install/windows-install/
    echo.
    pause
    exit /b 1
)

REM 检查 Docker 是否运行
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] Docker 未运行，正在启动...
    echo 请手动启动 Docker Desktop 后重试
    pause
    exit /b 1
)

REM 检查 SentriKit-postgres 容器
docker ps -a --format "{{.Names}}" | findstr /C:"SentriKit-postgres" >nul 2>&1
if %errorlevel% equ 0 (
    echo [提示] 容器 SentriKit-postgres 已存在
    docker start SentriKit-postgres >nul 2>&1
    echo [完成] 容器已启动
) else (
    echo [创建] 启动 PostgreSQL 容器...
    docker run -d --name SentriKit-postgres ^
        -e POSTGRES_DB=SentriKit_sales ^
        -e POSTGRES_USER=salesadmin ^
        -e POSTGRES_PASSWORD=sales123 ^
        -p 5432:5432 ^
        postgres:15-alpine >nul 2>&1
    echo [完成] PostgreSQL 容器已创建并启动
)

echo.
echo 等待 PostgreSQL 就绪...
timeout /t 5 /nobreak >nul

REM 测试连接
docker exec SentriKit-postgres psql -U salesadmin -d SentriKit_sales -c "SELECT 1" >nul 2>&1
if %errorlevel% equ 0 (
    echo [完成] PostgreSQL 连接成功
) else (
    echo [错误] PostgreSQL 连接失败
    echo 请检查容器状态: docker ps -a
    pause
    exit /b 1
)

echo.
echo ============================================================
echo 安装 Python 依赖
echo ============================================================

pip install sqlalchemy psycopg2-binary -q

if %errorlevel% equ 0 (
    echo [完成] Python 依赖已安装
) else (
    echo [错误] Python 依赖安装失败
    pause
    exit /b 1
)

echo.
echo ============================================================
echo 初始化数据库
echo ============================================================

python scripts/setup_postgresql.py init

echo.
echo ============================================================
echo 迁移数据
echo ============================================================

python scripts/setup_postgresql.py migrate

echo.
echo ============================================================
echo 验证数据库
echo ============================================================

python scripts/setup_postgresql.py verify

echo.
echo ============================================================
echo 设置完成!
echo ============================================================
echo.
echo 下一步:
echo   1. 配置 .env 文件中的 API 密钥
echo   2. 启动服务: SentriKit-sales-fastapi
echo   3. 访问文档: http://localhost:8877/docs
echo.
pause
