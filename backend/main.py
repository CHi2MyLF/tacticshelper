"""FM2024 战术顾问 — FastAPI 主入口"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .api import import_api, squad_api, chat_api, tactic_api
from .database import init_db

app = FastAPI(
    title="FM2024 Tactical Advisor",
    description="AI 驱动的 Football Manager 2024 战术顾问",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由
app.include_router(import_api.router)
app.include_router(squad_api.router)
app.include_router(chat_api.router)
app.include_router(tactic_api.router)


@app.on_event("startup")
async def startup():
    init_db()
    # 初始化 RAG 知识库（后台加载，不阻塞启动）
    from .api.chat_api import init_rag
    init_rag()


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# 生产模式：挂载前端构建产物
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
