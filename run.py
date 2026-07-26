"""一键启动脚本"""
import os
import sys
import subprocess
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def main():
    print("=" * 50)
    print("  FM2024 战术顾问 — 启动中...")
    print("=" * 50)

    # 检查依赖
    try:
        import fastapi
        import uvicorn
        import anthropic
    except ImportError as e:
        print(f"\n缺少依赖: {e}")
        print("正在安装依赖...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(BASE_DIR / "requirements.txt")])
        print("依赖安装完成，请重新运行 run.py")
        return

    # 启动后端
    print("\n启动后端服务 (http://localhost:8000)...")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
        cwd=str(BASE_DIR),
    )

    # 检查前端是否已构建
    frontend_dist = BASE_DIR / "frontend" / "dist"
    if not frontend_dist.exists():
        print("\n前端尚未构建。请在另一个终端运行：")
        print("  cd frontend && npm install && npm run dev")
        print("\n或构建后直接访问后端：")
        print("  cd frontend && npm run build")

    # 打开浏览器
    webbrowser.open("http://localhost:8000/docs")

    print("\n后端已启动！")
    print("API 文档: http://localhost:8000/docs")
    print("前端开发: cd frontend && npm run dev")
    print("\n按 Ctrl+C 停止...")

    try:
        backend.wait()
    except KeyboardInterrupt:
        print("\n正在停止...")
        backend.terminate()
        backend.wait()


if __name__ == "__main__":
    main()
