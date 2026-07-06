from pathlib import Path
import tempfile
import uuid

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings
from app.schemas import TailorTextRequest, TailorResponse
from app.services.extractors import extract_text_from_upload
from app.services.layout_analyzer import analyze_resume_layout, analyze_plain_layout
from app.services.ai_engine import engine
from app.services.docx_builder import create_generated_docx, clean_filename, DOCX_MIME
from app.services.docx_preserver import preserve_docx_layout


router = APIRouter(prefix="/resumes", tags=["Resume Intelligence"])


def _output_dir() -> Path:
    folder = Path(tempfile.gettempdir()) / "resume_tailor_pro_v4_outputs"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _package_result(result: dict, filename: str | None = None) -> dict:
    result["status"] = "success"
    result["preview_text"] = result.get("final_resume_text", "")[:3500]

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
    profile = analyze_plain_layout("text", payload.resume_text)
    result = engine.tailor(
        job_description=payload.job_description,
        resume_text=payload.resume_text,
        target_role=payload.target_role,
        profile=profile,
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
        resume_text, source_type = extract_text_from_upload(file.filename or "resume", file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if len(resume_text.strip()) < 40:
        raise HTTPException(status_code=400, detail="Could not extract enough resume text. Try DOCX or TXT.")

    profile = analyze_resume_layout(file_bytes, source_type, resume_text)

    result = engine.tailor(
        job_description=job_description,
        resume_text=resume_text,
        target_role=target_role or None,
        profile=profile,
    )

    file_id = str(uuid.uuid4())[:8]
    original_stem = Path(file.filename or "resume").stem
    safe_name = clean_filename(f"tailored_v4_{original_stem}_{file_id}.docx")
    output_path = _output_dir() / safe_name

    if source_type == "docx" and settings.PRESERVE_DOCX_LAYOUT:
        preservation = preserve_docx_layout(file_bytes, output_path, result)
        result["resume_profile"]["layout_notes"].extend(preservation.get("notes", []))
        result["resume_profile"]["preserve_mode"] = preservation.get("mode", result["resume_profile"]["preserve_mode"])
    else:
        create_generated_docx(
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
