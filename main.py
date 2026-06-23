from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR, STATIC_DIR
from app.database.init_db import init_db
from app.routers.auth import router as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.menu import router as menu_router
from app.routers.public import router as public_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Menu Maker API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

frontend_dir = BASE_DIR / "frontend"
if frontend_dir.exists():
    app.mount(
        "/frontend", StaticFiles(directory=frontend_dir, html=True), name="frontend"
    )

app.include_router(auth_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(menu_router, prefix="/api")
app.include_router(public_router, prefix="/api")


def frontend_file(name: str) -> Path:
    return BASE_DIR / "frontend" / name


@app.get("/")
async def root():
    index_file = frontend_file("index.html")
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Menu Maker API is running. Frontend not found."}


@app.get("/m/{slug}", name="public_page")
async def public_page(slug: str):
    public_file = frontend_file("public_menu.html")
    if public_file.exists():
        return FileResponse(public_file)
    raise HTTPException(status_code=404, detail="Public menu page not found")


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not Found")

    requested_file = frontend_file(full_path)
    if requested_file.exists() and requested_file.is_file():
        return FileResponse(requested_file)

    index_file = frontend_file("index.html")
    if index_file.exists():
        return FileResponse(index_file)

    raise HTTPException(status_code=404, detail="Frontend not found")
