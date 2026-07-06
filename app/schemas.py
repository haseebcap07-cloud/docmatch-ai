from pydantic import BaseModel, Field


class ResumeProfile(BaseModel):
    source_type: str
    preserve_mode: str
    estimated_page_count: int
    paragraph_count: int
    word_count: int
    detected_sections: list[str]
    detected_fonts: list[str]
    detected_font_sizes: list[str]
    margins: dict[str, str]
    layout_notes: list[str]


class TailorTextRequest(BaseModel):
    job_description: str = Field(..., min_length=40)
    resume_text: str = Field(..., min_length=40)
    target_role: str | None = None


class TailorResponse(BaseModel):
    status: str = "success"
    document_id: str | None = None
    download_url: str | None = None
    filename: str | None = None

    ats_score_before: int
    ats_score_after: int
    target_score: int
    score_gap_to_90: int
    score_reason: str
    job_title_guess: str

    resume_profile: ResumeProfile

    matched_must_haves: list[str]
    matched_keywords: list[str]
    missing_keywords: list[str]
    weak_requirements: list[str]
    truthful_90_plus_actions: list[str]
    recruiter_warnings: list[str]

    optimized_headline: str
    optimized_summary: str
    optimized_skills: list[str]
    optimized_bullets: list[str]
    role_shortlist_words: list[str]
    project_suggestions: list[str]
    interview_pitch: str
    final_resume_text: str
    preview_text: str
