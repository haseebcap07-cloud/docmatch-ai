from __future__ import annotations

import re

from app.schemas import ResumeProfile
from app.services.ats_engine import profile_to_text, extract_keywords


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _contains(text: str, term: str) -> bool:
    lower = text.lower()
    term = term.lower().strip()
    if not term:
        return False
    if " " in term or "-" in term or "/" in term:
        return term in lower
    return bool(re.search(rf"\b{re.escape(term)}\b", lower))


def _profile_evidence_sources(profile: ResumeProfile) -> list[dict]:
    sources = []
    if profile.summary:
        sources.append({"section": "summary", "text": profile.summary})
    if profile.technical_skills:
        sources.append({"section": "technical_skills", "text": ", ".join(profile.technical_skills)})
    for exp in profile.professional_experience:
        header = " | ".join([x for x in [exp.title, exp.company, exp.start_date, exp.end_date] if x])
        if header:
            sources.append({"section": "experience_header", "text": header})
        for bullet in exp.bullets:
            sources.append({"section": "experience_bullet", "text": bullet})
    for project in profile.projects:
        if project.name:
            sources.append({"section": "project_name", "text": project.name})
        if project.description:
            sources.append({"section": "project_description", "text": project.description})
        if project.technologies:
            sources.append({"section": "project_technologies", "text": ", ".join(project.technologies)})
        for bullet in project.bullets:
            sources.append({"section": "project_bullet", "text": bullet})
    for cert in profile.certifications:
        sources.append({"section": "certification", "text": cert})
    for edu in profile.education:
        sources.append({"section": "education", "text": " | ".join([edu.degree, edu.school, edu.graduation])})
    return [{"section": s["section"], "text": _clean(s["text"])} for s in sources if _clean(s["text"])]


def map_evidence(profile: ResumeProfile, jd_analysis: dict, match: dict) -> dict:
    sources = _profile_evidence_sources(profile)
    profile_text = profile_to_text(profile)
    keywords = jd_analysis.get("keywords", [])[:80]

    supported = []
    partial = []
    unsupported = []
    evidence_items = []

    for requirement in jd_analysis.get("must_haves", [])[:24]:
        req_keywords = extract_keywords(requirement, limit=20)
        exact_sources = []
        partial_sources = []
        for source in sources:
            hits = [kw for kw in req_keywords if _contains(source["text"], kw)]
            if len(hits) >= max(1, min(3, len(req_keywords) // 2)):
                exact_sources.append({"source": source["section"], "text": source["text"], "matched_terms": hits[:6]})
            elif hits:
                partial_sources.append({"source": source["section"], "text": source["text"], "matched_terms": hits[:4]})
        if exact_sources:
            supported.append(requirement)
            status = "supported"
            used_sources = exact_sources[:3]
        elif partial_sources:
            partial.append(requirement)
            status = "partial"
            used_sources = partial_sources[:3]
        else:
            unsupported.append(requirement)
            status = "unsupported"
            used_sources = []
        evidence_items.append({"requirement": requirement, "status": status, "evidence": used_sources, "requirement_keywords": req_keywords[:10]})

    unsupported_terms = [term for term in keywords if not _contains(profile_text, term)][:30]

    return {
        "supported_requirements": supported,
        "partially_supported_requirements": partial,
        "unsupported_requirements": unsupported,
        "evidence_items": evidence_items,
        "unsupported_terms": unsupported_terms,
    }
