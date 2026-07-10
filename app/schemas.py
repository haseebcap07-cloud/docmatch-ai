from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""


class ExperienceItem(BaseModel):
    title: str = ""
    company: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    bullets: list[str] = []


class ProjectItem(BaseModel):
    name: str = ""
    description: str = ""
    technologies: list[str] = []
    bullets: list[str] = []


class EducationItem(BaseModel):
    degree: str = ""
    school: str = ""
    location: str = ""
    graduation: str = ""


class ResumeProfile(BaseModel):
    contact: ContactInfo = ContactInfo()
    target_titles: list[str] = []
    summary: str = ""
    technical_skills: list[str] = []
    professional_experience: list[ExperienceItem] = []
    projects: list[ProjectItem] = []
    education: list[EducationItem] = []
    certifications: list[str] = []
    interests: list[str] = []
    languages: list[str] = []
    achievements: list[str] = []
    work_authorization: str = ""
    source_layout: dict = {}
    source_text_snapshot: str = ""


class TemplateSettings(BaseModel):
    template_name: str = "ATS Modern"
    font_family: str = "Aptos"
    body_font_size: float = 10.0
    heading_font_size: float = 11.0
    name_font_size: float = 18.0
    margin_inches: float = 0.55
    line_spacing: float = 1.0
    page_limit: int = 2
    show_projects: bool = True
    show_certifications: bool = True
    show_interests: bool = False
    show_watermark: bool = True
    preserve_source_structure: bool = True
    strict_length_match: bool = True


class ExtractProfileResponse(BaseModel):
    status: str = "success"
    profile: ResumeProfile
    extraction_notes: list[str] = []
    resume_only_score: int
    formatting_score: int
    detected_sections: list[str] = []


class GenerateResumeRequest(BaseModel):
    profile: ResumeProfile
    job_description: str = Field(..., min_length=40)
    target_role: str = ""
    custom_instructions: str = ""
    user_requested_additions: list[str] = []
    user_requested_replacements: list[str] = []
    template_settings: TemplateSettings = TemplateSettings()


class ScoreBreakdown(BaseModel):
    resume_only_score: int
    jd_match_score: int
    keyword_score: int
    experience_relevance_score: int
    leadership_soft_skill_score: int
    formatting_score: int
    recruiter_readability_score: int
    final_ats_estimate: int


class AdaptiveAnalysis(BaseModel):
    resume_role_family: str = "general"
    jd_role_family: str = "general"
    role_alignment: str = "unknown"
    selected_playbook: str = "general"
    top_3_jd_priorities: list[str] = []
    supported_requirements: list[str] = []
    partially_supported_requirements: list[str] = []
    unsupported_requirements: list[str] = []
    rewrite_focus: list[str] = []
    validator_warnings: list[str] = []


class InitialAnalysis(BaseModel):
    baseline_ats_score: int = 0
    resume_role_family: str = "general"
    jd_role_family: str = "general"
    role_alignment: str = "unknown"
    summary: str = ""


class GapAnalysis(BaseModel):
    missing_hard_skills_not_added: list[str] = []
    semantic_gaps: list[str] = []
    likely_possessed_rephrasing: list[str] = []
    unsupported_requirements: list[str] = []


class ChangeLog(BaseModel):
    semantic_mappings_applied: list[str] = []
    keyword_rephrasing: list[str] = []
    user_requested_additions_replacements: list[str] = []
    unsupported_jd_skills_not_added: list[str] = []
    title_or_structure_adjustments: list[str] = []


class FinalResult(BaseModel):
    post_optimization_ats_score: int = 0
    score_improvement: str = ""
    score_improvement_points: int = 0


class GeneratedExperienceItem(BaseModel):
    title: str = ""
    company: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    bullets: list[str] = []
    environment: str = ""


class GenerateResumeResponse(BaseModel):
    status: str = "success"
    document_id: str
    filename: str
    download_url: str
    score_breakdown: ScoreBreakdown
    score_reason: str
    matched_keywords: list[str]
    missing_keywords: list[str]
    weak_requirements: list[str]
    truthful_90_plus_actions: list[str]
    recruiter_warnings: list[str]
    adaptive_analysis: AdaptiveAnalysis
    initial_analysis: InitialAnalysis
    gap_analysis: GapAnalysis
    change_log: ChangeLog
    final_result: FinalResult
    generated_summary: str
    generated_skills: list[str]
    generated_bullets: list[str]
    generated_experience: list[GeneratedExperienceItem] = []
    preview_text: str
