from pathlib import Path
import tempfile

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from app.schemas import (
    JobDescriptionRequest,
    JobDescriptionResponse,
    RephraseRequest,
    RephraseResponse,
    TailorDocumentRequest,
    TailorDocumentResponse,
    FormatDocumentRequest,
    FormatDocumentResponse,
)
from app.services.ai_provider import ai_provider
from app.services.docx_utils import (
    DOCX_MIME,
    extract_text_from_upload,
    create_docx,
    clean_filename,
)


router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/extract-jd", response_model=JobDescriptionResponse)
def extract_job_description(payload: JobDescriptionRequest):
    return ai_provider.extract_jd(payload.job_description)


@router.post("/rephrase", response_model=RephraseResponse)
def rephrase_text(payload: RephraseRequest):
    rephrased = ai_provider.rephrase(payload.text, payload.tone)
    return {
        "original_text": payload.text,
        "rephrased_text": rephrased,
        "tone": payload.tone,
    }


@router.post("/tailor", response_model=TailorDocumentResponse)
def tailor_document(payload: TailorDocumentRequest):
    return ai_provider.tailor_document(
        job_description=payload.job_description,
        document_text=payload.document_text,
        target_role=payload.target_role,
    )


@router.post("/format", response_model=FormatDocumentResponse)
def format_document(payload: FormatDocumentRequest):
    return ai_provider.format_document(
        document_text=payload.document_text,
        format_style=payload.format_style,
    )


@router.post("/upload-text")
async def upload_text_file(file: UploadFile = File(...)):
    file_bytes = await file.read()

    try:
        text = extract_text_from_upload(file.filename or "upload.txt", file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "text": text,
    }


@router.post("/tailor-file")
async def tailor_uploaded_document(
    job_description: str = Form(...),
    target_role: str = Form(""),
    file: UploadFile = File(...),
):
    if len(job_description.strip()) < 20:
        raise HTTPException(status_code=400, detail="Please paste a complete job description.")

    file_bytes = await file.read()

    try:
        document_text = extract_text_from_upload(file.filename or "uploaded_document", file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if len(document_text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Could not extract enough text from the uploaded document.")

    tailored = ai_provider.tailor_document(
        job_description=job_description,
        document_text=document_text,
        target_role=target_role or None,
    )

    safe_name = clean_filename(f"tailored_{Path(file.filename or 'document').stem}.docx")
    output_dir = Path(tempfile.gettempdir()) / "jd_tailoring_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / safe_name

    create_docx(
        output_path=output_path,
        title="Tailored Document",
        content=tailored["final_document_text"],
    )

    return FileResponse(
        path=output_path,
        filename=safe_name,
        media_type=DOCX_MIME,
    )
