@echo off
echo ================================================
echo   FM2024 AI 战术顾问 - 启动中...
echo ================================================
echo.

cd /d "%~dp0"

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

REM 安装 Python 依赖
echo [1/3] 检查 Python 依赖...
pip install -r requirements.txt -q 2>nul

REM 检查 Node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 未找到 Node.js，前端将无法启动
    echo        请安装 Node.js 18+ 后重试
)

REM 安装前端依赖
if exist "frontend\node_modules" (
    echo [2/3] 前端依赖已安装
) else (
    echo [2/3] 安装前端依赖...
    cd frontend
    call npm install
    cd ..
)

echo [3/3] 启动服务...
echo.
echo 后端启动在: http://127.0.0.1:8000
echo 前端启动在: http://localhost:5173
echo API 文档:    http://127.0.0.1:8000/docs
echo.
echo 按 Ctrl+C 停止所有服务
echo ================================================
echo.

REM 启动后端
start "FM-Advisor-Backend" cmd /c "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

REM 启动前端
start "FM-Advisor-Frontend" cmd /c "cd frontend && npm run dev"

REM 等待一下让服务启动
timeout /t 3 >nul

REM 打开浏览器
start http://localhost:5173

echo 已在浏览器中打开前端界面。
echo 如果前端未启动，请手动运行: cd frontend ^&^& npm run dev
pause
