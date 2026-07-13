from __future__ import annotations
from app.schemas import ResumeProfile

def validate_section_preservation(profile: ResumeProfile, ai: dict) -> list[str]:
    warnings=[]; layout=profile.source_layout or {}; sections=layout.get("source_section_order",[])
    if sections and "CERTIFICATIONS" in sections and profile.certifications and not profile.certifications:
        warnings.append("Source had certifications, but profile certifications are empty.")
    generated_exp=ai.get("generated_experience") or []
    if profile.professional_experience and len(generated_exp)!=len(profile.professional_experience):
        warnings.append("Generated experience count does not match source experience count.")
    source_counts=layout.get("source_employer_bullet_counts",{})
    if source_counts and generated_exp:
        for sc,gc in zip(source_counts.values(), [len(x.get("bullets",[]) or []) for x in generated_exp]):
            if sc and abs(sc-gc)>4: warnings.append(f"Bullet density changed too much: source {sc}, generated {gc}.")
    return warnings
