@echo off
chcp 65001 >nul
echo.
echo ==============================================
echo        Gavvy 销售宗师 - 启动脚本
echo ==============================================
echo.

REM 设置环境变量
set PYTHONPATH=%cd%\src;%PYTHONPATH%

echo [启动] 正在启动 Gavvy 销售宗师...
echo [信息] 访问地址: http://localhost:8000
echo [提示] 按 Ctrl+C 停止服务
echo.

python -m gavvy_salesmaster.web

pause
