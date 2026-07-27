"""FastAPI 应用入口

启动命令：uvicorn backend.main:app --reload
打开浏览器访问 http://127.0.0.1:8000
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.api.routes import router

app = FastAPI(
    title="AI 商品增长运营助手",
    description="一款面向电商运营的 AI 辅助工具 Demo，支持商品分析、标题优化、营销内容生成和运营策略建议。",
    version="1.0.0",
)

# CORS 配置（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(router, prefix="/api")

# 托管前端静态文件
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """提供前端静态文件"""
    # 先检查 API 路径前缀，避免干扰 API 路由
    if (
        full_path.startswith("api/")
        or full_path.startswith("docs")
        or full_path.startswith("openapi")
        or full_path.startswith("redoc")
    ):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=404, content={"detail": "Not Found"})

    file_path = FRONTEND_DIR / full_path if full_path else FRONTEND_DIR / "index.html"

    # 如果路径是目录或不存在，返回 index.html（SPA 支持）
    if not file_path.exists() or file_path.is_dir():
        file_path = FRONTEND_DIR / "index.html"

    if file_path.exists():
        suffix = file_path.suffix.lower()
        media_type = MIME_TYPES.get(suffix, "application/octet-stream")
        return FileResponse(str(file_path), media_type=media_type)

    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=404, content={"detail": "Not Found"})
