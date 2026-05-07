@echo off
chcp 65001 >nul
echo.
echo ==============================================
echo        Gavvy 销售宗师 - 一键安装脚本
echo ==============================================
echo.

REM 检查是否以管理员身份运行
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [✓] 已获取管理员权限
) else (
    echo [⚠] 请以管理员身份运行此脚本
    pause
    exit /b 1
)

REM 检查 Python 是否已安装
python --version >nul 2>&1
if %errorLevel% == 0 (
    echo [✓] Python 已安装
) else (
    echo [安装] 正在安装 Python 3.10...
    start /wait "" "https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe" /quiet InstallAllUsers=1 PrependPath=1
    if %errorLevel% == 0 (
        echo [✓] Python 安装成功
    ) else (
        echo [✗] Python 安装失败，请手动安装 Python 3.10+
        pause
        exit /b 1
    )
)

REM 设置环境变量
echo [配置] 设置环境变量...
set PYTHONPATH=%cd%\src;%PYTHONPATH%
set PATH=%cd%;%PATH%

REM 安装依赖
echo [安装] 安装项目依赖...
pip install -e . --quiet

if %errorLevel% == 0 (
    echo [✓] 依赖安装成功
) else (
    echo [✗] 依赖安装失败
    pause
    exit /b 1
)

REM 初始化数据库
echo [配置] 初始化数据库...
python -c "from gavvy_salesmaster.core.app import init_app; init_app()"

if %errorLevel% == 0 (
    echo [✓] 数据库初始化成功
) else (
    echo [✗] 数据库初始化失败
    pause
    exit /b 1
)

echo.
echo ==============================================
echo         安装完成！
echo ==============================================
echo.
echo 启动命令：
echo   方式1：双击 start.bat
echo   方式2：python -m gavvy_salesmaster.web
echo.
echo 访问地址：http://localhost:8000
echo.
pause
