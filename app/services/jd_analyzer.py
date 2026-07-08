from __future__ import annotations

import re

from app.services.ats_engine import extract_keywords, extract_requirement_lines


def analyze_job_description(job_description: str, target_role: str = "") -> dict:
    requirement_data = extract_requirement_lines(job_description)
    keywords = extract_keywords(job_description, limit=150)

    title_guess = target_role.strip()
    if not title_guess:
        lines = [x.strip() for x in job_description.splitlines() if x.strip()]
        for line in lines[:8]:
            if len(line) < 90 and any(word in line.lower() for word in ["engineer", "developer", "analyst", "lead", "manager", "administrator", "specialist"]):
                title_guess = line
                break
    if not title_guess:
        title_guess = "Target Role"

    lower = f"{target_role} {job_description}".lower()
    seniority = "mid"
    if any(x in lower for x in ["senior", "sr.", "lead", "manager", "principal", "staff"]):
        seniority = "senior_or_lead"
    elif any(x in lower for x in ["junior", "entry", "associate", "intern"]):
        seniority = "entry_or_junior"

    soft_skills = []
    for term in ["communication", "stakeholder", "collaboration", "leadership", "risk", "governance", "client", "milestone", "scope"]:
        if term in lower:
            soft_skills.append(term)

    certifications = re.findall(r"\b(?:CCNA|CCNP|Security\+|Network\+|PMP|ITIL|AWS|Azure|GCP|CISSP|CISA|CISM)\b", job_description, flags=re.I)

    top_3_priorities = requirement_data["must_haves"][:3]
    if len(top_3_priorities) < 3:
        top_3_priorities.extend(requirement_data["responsibilities"][: 3 - len(top_3_priorities)])

    return {
        "title_guess": title_guess,
        "seniority": seniority,
        "keywords": keywords,
        "must_haves": requirement_data["must_haves"],
        "preferred": requirement_data["preferred"],
        "responsibilities": requirement_data["responsibilities"],
        "soft_skills": sorted(set(soft_skills)),
        "certifications": sorted(set(certifications)),
        "top_3_priorities": top_3_priorities[:3],
    }
