from __future__ import annotations

import re
from app.schemas import ResumeProfile, ScoreBreakdown, TemplateSettings

COMMON_TERMS = [
    "python", "sql", "java", "javascript", "typescript", "react", "node", "aws", "azure", "gcp",
    "docker", "kubernetes", "terraform", "jenkins", "git", "ci/cd", "api", "microservices",
    "spark", "pyspark", "databricks", "snowflake", "etl", "elt", "data pipeline", "airflow",
    "power bi", "tableau", "looker", "postgresql", "mysql", "sql server", "oracle", "mongodb",
    "network", "infrastructure", "lan", "wan", "vlan", "vpn", "firewall", "cisco", "routing",
    "switching", "ospf", "bgp", "eigrp", "incident", "deployment", "change", "stakeholder",
    "project", "timeline", "milestone", "risk", "governance", "quality", "resource",
    "client", "communication", "production support", "operations", "scope", "strategic",
]

ACTION_WORDS = [
    "Designed", "Developed", "Implemented", "Automated", "Optimized", "Migrated", "Integrated",
    "Validated", "Analyzed", "Improved", "Reduced", "Increased", "Delivered", "Collaborated",
    "Troubleshot", "Documented", "Monitored", "Deployed", "Built", "Maintained", "Led",
    "Coordinated", "Facilitated", "Managed", "Governed", "Prioritized",
]


def profile_to_text(profile: ResumeProfile) -> str:
    chunks = [
        profile.contact.full_name,
        " ".join(profile.target_titles),
        profile.summary,
        ", ".join(profile.technical_skills),
        ", ".join(profile.certifications),
        ", ".join(profile.interests),
        ", ".join(profile.languages),
        ", ".join(profile.achievements),
        profile.work_authorization,
    ]

    for exp in profile.professional_experience:
        chunks.extend([exp.title, exp.company, " ".join(exp.bullets)])

    for project in profile.projects:
        chunks.extend([project.name, project.description, ", ".join(project.technologies), " ".join(project.bullets)])

    for edu in profile.education:
        chunks.extend([edu.degree, edu.school, edu.location, edu.graduation])

    return "\n".join([x for x in chunks if x])


def extract_keywords(text: str, limit: int = 120) -> list[str]:
    lowered = text.lower()
    found = []

    for term in COMMON_TERMS:
        if term in lowered:
            found.append(term)

    caps = re.findall(r"\b[A-Z][A-Za-z0-9+#./-]{2,}\b", text)
    for token in caps:
        if token.lower() not in [x.lower() for x in found]:
            found.append(token)

    for line in text.splitlines():
        low = line.lower()
        if any(x in low for x in ["required", "responsible", "ability", "experience", "support", "manage", "develop", "monitor", "deliver", "role"]):
            for word in re.findall(r"[A-Za-z][A-Za-z0-9+#./-]{3,}", line):
                if word.lower() not in {"with", "that", "this", "from", "will", "have", "your", "role", "team"}:
                    if word.lower() not in [x.lower() for x in found]:
                        found.append(word)

    return found[:limit]


def keyword_match(job_description: str, profile_text: str) -> dict:
    jd_terms = extract_keywords(job_description)
    lower = profile_text.lower()
    matched = [x for x in jd_terms if x.lower() in lower]
    missing = [x for x in jd_terms if x.lower() not in lower]
    score = round((len(matched) / max(1, len(jd_terms))) * 100)
    return {"jd_terms": jd_terms, "matched": matched, "missing": missing, "score": max(0, min(100, score))}


def resume_only_score(profile: ResumeProfile) -> int:
    score = 0
    if profile.contact.full_name: score += 8
    if profile.contact.email or profile.contact.phone: score += 8
    if profile.summary and len(profile.summary.split()) >= 25: score += 14
    if len(profile.technical_skills) >= 10: score += 16
    if profile.professional_experience: score += 20
    if sum(len(e.bullets) for e in profile.professional_experience) >= 6: score += 14
    if profile.projects: score += 8
    if profile.education: score += 8
    if profile.certifications: score += 4
    return max(20, min(100, score))


def formatting_score(template: TemplateSettings, section_count: int) -> int:
    score = 70
    if 9 <= template.body_font_size <= 11: score += 8
    if 0.35 <= template.margin_inches <= 0.75: score += 8
    if section_count >= 5: score += 8
    if template.page_limit in {1, 2}: score += 4
    return min(100, score)


def compute_breakdown(profile: ResumeProfile, job_description: str, template: TemplateSettings) -> tuple[ScoreBreakdown, dict]:
    ptext = profile_to_text(profile)
    match = keyword_match(job_description, ptext)

    section_count = sum([
        bool(profile.summary),
        bool(profile.technical_skills),
        bool(profile.professional_experience),
        bool(profile.projects),
        bool(profile.education),
        bool(profile.certifications),
        bool(profile.interests),
        bool(profile.languages),
    ])

    resume_score = resume_only_score(profile)
    format_score = formatting_score(template, section_count)
    keyword_score = match["score"]

    exp_text = " ".join([" ".join(e.bullets) for e in profile.professional_experience]).lower()
    jd_lower = job_description.lower()

    leadership_terms = ["lead", "stakeholder", "client", "communication", "risk", "governance", "timeline", "milestone", "resource", "scope"]
    leadership_hits = sum(1 for t in leadership_terms if t in ptext.lower() and t in jd_lower)
    leadership_score = min(100, 45 + leadership_hits * 8)

    exp_hits = sum(1 for t in match["matched"] if t.lower() in exp_text)
    exp_relevance = min(100, 45 + exp_hits * 4)

    readability = 82
    long_bullets = sum(1 for e in profile.professional_experience for b in e.bullets if len(b.split()) > 32)
    if long_bullets > 6:
        readability -= 10
    if len(profile.technical_skills) > 60:
        readability -= 8
    readability = max(45, readability)

    jd_match = round((keyword_score * 0.45) + (exp_relevance * 0.30) + (leadership_score * 0.25))
    final = round((jd_match * 0.55) + (resume_score * 0.20) + (format_score * 0.15) + (readability * 0.10))

    ratio = len(match["matched"]) / max(1, len(match["jd_terms"]))
    if ratio < 0.55:
        final = min(final, 74)
    elif ratio < 0.70:
        final = min(final, 84)
    elif ratio < 0.82:
        final = min(final, 89)

    return ScoreBreakdown(
        resume_only_score=resume_score,
        jd_match_score=jd_match,
        keyword_score=keyword_score,
        experience_relevance_score=exp_relevance,
        leadership_soft_skill_score=leadership_score,
        formatting_score=format_score,
        recruiter_readability_score=readability,
        final_ats_estimate=max(0, min(100, final)),
    ), match
