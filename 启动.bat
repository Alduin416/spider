@echo off
chcp 65001 >nul
echo ========================================
echo   侘寂 - 百度热搜爬虫快速启动
echo ========================================
echo.

:menu
echo 请选择运行模式：
echo 1. 爬虫模式 - 命令行显示热搜
echo 2. Web 模式 - 启动网页展示
echo 3. 退出
echo.
set /p choice="请输入选项 (1/2/3): "

if "%choice%"=="1" (
    python main.py --scraper
    echo.
    pause
    goto menu
) else if "%choice%"=="2" (
    python main.py --web
) else if "%choice%"=="3" (
    exit /b
) else (
    echo 无效选项，请重新输入！
    echo.
    goto menu
)
