from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.config import settings
from app.schemas import ExtractProfileResponse
from app.services.extractors import extract_text_from_upload, detect_sections
from app.services.profile_parser import build_profile_from_text
from app.services.ats_engine import resume_only_score


router = APIRouter(prefix="/profiles", tags=["Master Profile"])


@router.post("/extract", response_model=ExtractProfileResponse)
async def extract_profile(file: UploadFile = File(...)):
    file_bytes = await file.read()

    if len(file_bytes) > settings.max_upload_bytes:
        raise HTTPException(status_code=400, detail=f"File is too large. Max upload size is {settings.MAX_UPLOAD_MB} MB.")

    try:
        text, source_type = extract_text_from_upload(file.filename or "resume", file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if len(text.strip()) < 40:
        raise HTTPException(status_code=400, detail="Could not extract enough resume text. Try DOCX or TXT.")

    profile, notes = build_profile_from_text(text)
    detected = detect_sections(text)

    formatting = 80
    if source_type == "pdf":
        formatting -= 8
    if len(detected) >= 5:
        formatting += 10

    return ExtractProfileResponse(
        profile=profile,
        extraction_notes=notes,
        resume_only_score=resume_only_score(profile),
        formatting_score=max(40, min(100, formatting)),
        detected_sections=detected,
    )
