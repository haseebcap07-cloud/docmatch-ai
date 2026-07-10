from __future__ import annotations
from copy import deepcopy
from app.schemas import ResumeProfile, TemplateSettings
from app.services.ats_engine import compute_breakdown

def score_generated_resume(original_profile:ResumeProfile,generated_summary:str,generated_skills:list[str],generated_bullets:list[str],job_description:str,template:TemplateSettings,generated_experience:list[dict]|None=None)->dict:
    optimized=deepcopy(original_profile); optimized.summary=generated_summary; optimized.technical_skills=generated_skills
    if generated_experience:
        for i,item in enumerate(generated_experience):
            if i < len(optimized.professional_experience): optimized.professional_experience[i].bullets=item.get('bullets',[]) or optimized.professional_experience[i].bullets
    elif optimized.professional_experience: optimized.professional_experience[0].bullets=generated_bullets
    breakdown,match=compute_breakdown(optimized,job_description,template)
    return {'post_score':breakdown.final_ats_estimate,'breakdown':breakdown,'match':match}
