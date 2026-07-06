from pathlib import Path
import tempfile
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.schemas import GenerateResumeRequest, GenerateResumeResponse
from app.core.config import settings
from app.services.ai_engine import engine
from app.services.docx_generator import create_resume_docx, clean_filename, DOCX_MIME


router = APIRouter(prefix="/resumes", tags=["Resume Generation"])


def _output_dir() -> Path:
    folder = Path(tempfile.gettempdir()) / "resume_tailor_pro_v5_outputs"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


@router.post("/generate", response_model=GenerateResumeResponse)
def generate_resume(payload: GenerateResumeRequest):
    profile = payload.profile

    if not profile.summary and not profile.professional_experience and not profile.technical_skills:
        raise HTTPException(status_code=400, detail="Profile is too empty. Add resume details or extract from uploaded resume first.")

    ai = engine.tailor(
        profile=profile,
        job_description=payload.job_description,
        target_role=payload.target_role,
        custom_instructions=payload.custom_instructions,
        template=payload.template_settings,
    )

    file_id = str(uuid.uuid4())[:8]
    name_part = clean_filename(profile.contact.full_name or "resume")
    filename = clean_filename(f"resume_tailor_pro_v5_{name_part}_{file_id}.docx")
    output_path = _output_dir() / filename

    watermark = bool(payload.template_settings.show_watermark and settings.FREE_DOWNLOAD_WATERMARK)
    preview = create_resume_docx(output_path, profile, ai, payload.template_settings, watermark=watermark)

    breakdown = ai["score_breakdown"]

    return GenerateResumeResponse(
        document_id=filename,
        filename=filename,
        download_url=f"/api/v1/resumes/download/{filename}",
        score_breakdown=breakdown,
        score_reason=ai["score_reason"],
        matched_keywords=ai["matched_keywords"],
        missing_keywords=ai["missing_keywords"],
        weak_requirements=ai["weak_requirements"],
        truthful_90_plus_actions=ai["truthful_90_plus_actions"],
        recruiter_warnings=ai["recruiter_warnings"],
        generated_summary=ai["generated_summary"],
        generated_skills=ai["generated_skills"],
        generated_bullets=ai["generated_bullets"],
        preview_text=preview[:5000],
    )


@router.get("/download/{document_id}")
def download(document_id: str):
    safe_id = clean_filename(document_id)
    path = _output_dir() / safe_id

    if not path.exists():
        raise HTTPException(status_code=404, detail="File expired or not found. Generate it again.")

    return FileResponse(path=path, filename=safe_id, media_type=DOCX_MIME)
