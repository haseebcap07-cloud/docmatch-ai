from pydantic import BaseModel, EmailStr, Field


class JobDescriptionRequest(BaseModel):
    job_description: str = Field(..., min_length=20)


class JobRequirement(BaseModel):
    category: str
    items: list[str]


class JobDescriptionResponse(BaseModel):
    title_guess: str
    seniority_guess: str
    required_skills: list[str]
    preferred_skills: list[str]
    responsibilities: list[str]
    keywords: list[str]
    ats_focus_areas: list[str]


class RephraseRequest(BaseModel):
    text: str = Field(..., min_length=5)
    tone: str = "professional"


class RephraseResponse(BaseModel):
    original_text: str
    rephrased_text: str
    tone: str


class TailorDocumentRequest(BaseModel):
    job_description: str = Field(..., min_length=20)
    document_text: str = Field(..., min_length=20)
    target_role: str | None = None


class TailorDocumentResponse(BaseModel):
    tailored_summary: str
    tailored_bullets: list[str]
    missing_keywords: list[str]
    ats_recommendations: list[str]
    final_document_text: str


class FormatDocumentRequest(BaseModel):
    document_text: str = Field(..., min_length=20)
    format_style: str = "resume"


class FormatDocumentResponse(BaseModel):
    format_style: str
    formatted_text: str
    recommendations: list[str]


class LeadCreateRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    company: str | None = None
    message: str | None = None


class LeadCreateResponse(BaseModel):
    status: str
    message: str
