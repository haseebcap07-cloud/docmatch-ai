from pathlib import Path
import tempfile
import uuid

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings
from app.schemas import TailorTextRequest, TailorResponse
from app.services.extractors import extract_text_from_upload
from app.services.ai_engine import engine
from app.services.docx_builder import create_docx, clean_filename, DOCX_MIME


router = APIRouter(prefix="/resumes", tags=["Resume Tailoring"])


def _output_dir() -> Path:
    folder = Path(tempfile.gettempdir()) / "resume_tailor_pro_v3_outputs"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _package_result(result: dict, filename: str | None = None) -> dict:
    result["status"] = "success"
    result["preview_text"] = result.get("final_resume_text", "")[:3000]

    if filename:
        result["document_id"] = filename
        result["download_url"] = f"/api/v1/resumes/download/{filename}"
        result["filename"] = filename
    else:
        result["document_id"] = None
        result["download_url"] = None
        result["filename"] = None

    return result


@router.post("/tailor-text", response_model=TailorResponse)
def tailor_text(payload: TailorTextRequest):
    result = engine.tailor(
        job_description=payload.job_description,
        resume_text=payload.resume_text,
        target_role=payload.target_role,
    )
    return _package_result(result)


@router.post("/tailor-file", response_model=TailorResponse)
async def tailor_file(
    job_description: str = Form(...),
    target_role: str = Form(""),
    file: UploadFile = File(...),
):
    if len(job_description.strip()) < 40:
        raise HTTPException(status_code=400, detail="Paste a full job description with at least 40 characters.")

    file_bytes = await file.read()

    if len(file_bytes) > settings.max_upload_bytes:
        raise HTTPException(status_code=400, detail=f"File is too large. Max upload size is {settings.MAX_UPLOAD_MB} MB.")

    try:
        resume_text = extract_text_from_upload(file.filename or "resume", file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if len(resume_text.strip()) < 40:
        raise HTTPException(status_code=400, detail="Could not extract enough resume text. Try DOCX or TXT.")

    result = engine.tailor(
        job_description=job_description,
        resume_text=resume_text,
        target_role=target_role or None,
    )

    file_id = str(uuid.uuid4())[:8]
    original_stem = Path(file.filename or "resume").stem
    safe_name = clean_filename(f"tailored_{original_stem}_{file_id}.docx")
    output_path = _output_dir() / safe_name

    create_docx(
        output_path=output_path,
        title="ATS-Targeted Tailored Resume",
        content=result["final_resume_text"],
    )

    return _package_result(result, safe_name)


@router.get("/download/{document_id}")
def download(document_id: str):
    safe_id = clean_filename(document_id)
    path = _output_dir() / safe_id

    if not path.exists():
        raise HTTPException(status_code=404, detail="File expired or not found. Generate it again.")

    return FileResponse(path=path, filename=safe_id, media_type=DOCX_MIME)
