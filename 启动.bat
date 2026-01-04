@echo off
chcp 65001 >nul
title 收入记账助手

echo ============================================
echo         💰 收入记账助手 启动中...
echo ============================================
echo.

cd /d "%~dp0"

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查依赖是否安装
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装依赖项...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
    echo [完成] 依赖安装成功！
    echo.
)

echo [启动] 正在启动收入记账助手...
echo.

REM 启动应用
python main.py

if errorlevel 1 (
    echo.
    echo [错误] 程序异常退出
    pause
)
