from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routers import profiles, resumes


BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "public"

app = FastAPI(
    title=settings.APP_NAME,
    version="5.0.0",
    description="Resume Tailor Pro V5 — master profile, dashboard, template settings, ATS scoring, and watermark DOCX downloads.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)[:500],
        },
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(PUBLIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=PUBLIC_DIR), name="static")
app.include_router(profiles.router, prefix=settings.API_PREFIX)
app.include_router(resumes.router, prefix=settings.API_PREFIX)
