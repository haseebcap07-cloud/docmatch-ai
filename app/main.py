from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routers import resumes


BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "public"

app = FastAPI(
    title=settings.APP_NAME,
    version="3.0.0",
    description="Resume Tailor Pro V3 — ATS 90+ target resume tailoring engine.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(resumes.router, prefix=settings.API_PREFIX)
