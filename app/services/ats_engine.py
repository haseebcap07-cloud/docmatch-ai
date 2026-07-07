from __future__ import annotations

import re
from collections import Counter

from app.schemas import ResumeProfile, ScoreBreakdown, TemplateSettings


COMMON_TERMS = [
    # Software / Data / Cloud
    "python", "sql", "java", "javascript", "typescript", "react", "node", "aws", "azure", "gcp",
    "docker", "kubernetes", "terraform", "jenkins", "git", "ci/cd", "api", "rest api",
    "microservices", "spark", "pyspark", "databricks", "snowflake", "etl", "elt",
    "data pipeline", "airflow", "power bi", "tableau", "looker", "postgresql", "mysql",
    "sql server", "oracle", "mongodb", "analytics", "dashboard", "automation",

    # Network / Infrastructure
    "network", "networking", "infrastructure", "lan", "wan", "sd-wan", "vlan", "vpn",
    "firewall", "cisco", "routing", "switching", "ospf", "bgp", "eigrp", "tcp/ip",
    "dns", "dhcp", "windows server", "linux", "vmware", "active directory",
    "wireshark", "solarwinds", "splunk", "incident response", "production support",

    # Project / Business / Leadership
    "project", "project management", "timeline", "timelines", "milestone", "milestones",
    "deliverables", "stakeholder", "stakeholders", "client", "clients", "communication",
    "governance", "scope", "risk", "risk management", "resource", "resources",
    "quality", "quality benchmarks", "deployment", "change implementation",
    "change management", "incident resolution", "operations", "strategic priorities",
    "project economics", "collaboration", "liaison", "status reporting", "delivery",
]

ACTION_WORDS = [
    "Designed", "Developed", "Implemented", "Automated", "Optimized", "Migrated",
    "Integrated", "Validated", "Analyzed", "Improved", "Reduced", "Increased",
    "Delivered", "Collaborated", "Troubleshot", "Documented", "Monitored",
    "Deployed", "Built", "Maintained", "Led", "Coordinated", "Facilitated",
    "Managed", "Governed", "Prioritized", "Resolved", "Supported", "Streamlined",
    "Enhanced", "Modernized", "Executed", "Planned", "Tracked", "Reviewed",
]

ACTION_VERBS = {word.lower() for word in ACTION_WORDS}

IMPACT_WORDS = {
    "improved", "reduced", "increased", "optimized", "accelerated", "decreased",
    "saved", "minimized", "strengthened", "enhanced", "streamlined", "modernized",
    "standardized", "automated", "resolved", "delivered", "prevented", "improved",
}

LEADERSHIP_TERMS = [
    "lead", "led", "coordinated", "managed", "facilitated", "stakeholder",
    "client", "communication", "timeline", "milestone", "risk", "governance",
    "scope", "resource", "quality", "deliverables", "status", "review",
    "liaison", "collaboration", "priority", "strategic",
]

STOP_WORDS = {
    "with", "that", "this", "from", "will", "have", "your", "role", "team",
    "and", "the", "for", "are", "our", "you", "job", "work", "able", "been",
    "their", "there", "where", "when", "what", "into", "over", "under",
    "responsible", "required", "requirements", "experience", "skills",
}


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _lower(text: str) -> str:
    return _clean_text(text).lower()


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []

    for item in items:
        cleaned = _clean_text(item)
        key = cleaned.lower()

        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)

    return result


def _contains_term(text_lower: str, term: str) -> bool:
    term_lower = term.lower().strip()

    if not term_lower:
        return False

    if " " in term_lower or "/" in term_lower or "-" in term_lower:
        return term_lower in text_lower

    return bool(re.search(rf"\b{re.escape(term_lower)}\b", text_lower))


def _starts_with_action_verb(text: str) -> bool:
    match = re.findall(r"^\s*([A-Za-z]+)", text or "")
    return bool(match and match[0].lower() in ACTION_VERBS)


def _has_metric(text: str) -> bool:
    if not text:
        return False

    lower = text.lower()

    patterns = [
        r"\d+%",
        r"\$\s?\d+",
        r"\b\d+\s?(users|customers|clients|sites|servers|devices|tickets|incidents|projects|hours|days|weeks|months|years|teams|applications|systems|reports)\b",
        r"\b\d+x\b",
        r"\b\d+\+\b",
    ]

    return any(re.search(pattern, lower) for pattern in patterns)


def _all_bullets(profile: ResumeProfile) -> list[str]:
    bullets: list[str] = []

    for exp in profile.professional_experience:
        bullets.extend(exp.bullets or [])

    for project in profile.projects:
        bullets.extend(project.bullets or [])

    return [_clean_text(b) for b in bullets if _clean_text(b)]


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
        chunks.extend(
            [
                exp.title,
                exp.company,
                exp.location,
                exp.start_date,
                exp.end_date,
                " ".join(exp.bullets),
            ]
        )

    for project in profile.projects:
        chunks.extend(
            [
                project.name,
                project.description,
                ", ".join(project.technologies),
                " ".join(project.bullets),
            ]
        )

    for edu in profile.education:
        chunks.extend([edu.degree, edu.school, edu.location, edu.graduation])

    return "\n".join([x for x in chunks if x])


def extract_requirement_lines(job_description: str) -> dict:
    lines = [_clean_text(line) for line in job_description.splitlines() if _clean_text(line)]

    must_indicators = [
        "required", "requirement", "must", "need", "responsible", "responsibilities",
        "develop", "support", "monitor", "manage", "ensure", "act as", "liaison",
        "proactively", "deliver", "project", "timeline", "stakeholder",
    ]

    preferred_indicators = [
        "preferred", "nice to have", "plus", "desired", "bonus",
    ]

    must_haves = []
    preferred = []
    responsibilities = []

    for line in lines:
        low = line.lower()

        if any(indicator in low for indicator in preferred_indicators):
            preferred.append(line)

        if any(indicator in low for indicator in must_indicators):
            must_haves.append(line)

        if any(word in low for word in ["develop", "support", "monitor", "act as", "ensure", "facilitate", "manage"]):
            responsibilities.append(line)

    return {
        "must_haves": _dedupe(must_haves)[:20],
        "preferred": _dedupe(preferred)[:12],
        "responsibilities": _dedupe(responsibilities)[:20],
    }


def extract_keywords(text: str, limit: int = 140) -> list[str]:
    lowered = _lower(text)
    found: list[str] = []

    for term in COMMON_TERMS:
        if _contains_term(lowered, term):
            found.append(term)

    # Capture technical acronyms/tools like BGP, OSPF, AWS, SQL, REST, ITIL.
    caps = re.findall(r"\b[A-Z][A-Za-z0-9+#./-]{2,}\b", text or "")
    for token in caps:
        if token.lower() not in STOP_WORDS:
            found.append(token)

    # Capture important single words and short phrases from requirement-style lines.
    requirement_data = extract_requirement_lines(text)
    important_lines = (
        requirement_data["must_haves"]
        + requirement_data["preferred"]
        + requirement_data["responsibilities"]
    )

    for line in important_lines:
        words = [
            w for w in re.findall(r"[A-Za-z][A-Za-z0-9+#./-]{3,}", line)
            if w.lower() not in STOP_WORDS
        ]

        for word in words:
            found.append(word)

        # Useful two-word phrases, such as "project timelines", "resource discrepancies".
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i + 1]}"
            if len(phrase) <= 45:
                found.append(phrase)

    return _dedupe(found)[:limit]


def extract_shortlist_words(job_description: str, profile_text: str) -> list[str]:
    jd_lower = _lower(job_description)
    profile_lower = _lower(profile_text)

    shortlist = []

    for word in ACTION_WORDS:
        if word.lower() in jd_lower or word.lower() in profile_lower:
            shortlist.append(word)

    role_specific = [
        "Delivered", "Coordinated", "Facilitated", "Tracked", "Monitored",
        "Resolved", "Managed", "Governed", "Reviewed", "Implemented",
        "Supported", "Improved", "Aligned", "Communicated", "Prioritized",
    ]

    shortlist.extend(role_specific)
    return _dedupe(shortlist)[:24]


def keyword_match(job_description: str, profile_text: str) -> dict:
    jd_terms = extract_keywords(job_description)
    profile_lower = _lower(profile_text)

    matched = [term for term in jd_terms if _contains_term(profile_lower, term)]
    missing = [term for term in jd_terms if not _contains_term(profile_lower, term)]

    keyword_score = round((len(matched) / max(1, len(jd_terms))) * 100)

    requirement_data = extract_requirement_lines(job_description)
    must_have_terms = extract_keywords("\n".join(requirement_data["must_haves"]), limit=80)

    matched_must = [term for term in must_have_terms if _contains_term(profile_lower, term)]
    missing_must = [term for term in must_have_terms if not _contains_term(profile_lower, term)]

    must_have_score = round((len(matched_must) / max(1, len(must_have_terms))) * 100)

    shortlist_words = extract_shortlist_words(job_description, profile_text)

    rewrite_focus = build_rewrite_focus(
        missing=missing,
        missing_must=missing_must,
        must_haves=requirement_data["must_haves"],
    )

    return {
        "jd_terms": jd_terms,
        "matched": matched,
        "missing": missing,
        "score": max(0, min(100, keyword_score)),
        "must_haves": requirement_data["must_haves"],
        "preferred": requirement_data["preferred"],
        "responsibilities": requirement_data["responsibilities"],
        "matched_must_have_terms": matched_must,
        "missing_must_have_terms": missing_must,
        "must_have_score": max(0, min(100, must_have_score)),
        "shortlist_words": shortlist_words,
        "rewrite_focus": rewrite_focus,
        "ats_change_plan": build_ats_change_plan(missing, missing_must, shortlist_words),
    }


def build_rewrite_focus(missing: list[str], missing_must: list[str], must_haves: list[str]) -> list[str]:
    focus = []

    if missing_must:
        focus.append(
            "Strengthen must-have alignment using truthful evidence for: "
            + ", ".join(missing_must[:8])
        )

    if missing:
        focus.append(
            "Add supported JD keywords naturally where the resume already has matching experience: "
            + ", ".join(missing[:10])
        )

    for line in must_haves[:5]:
        focus.append(f"Address JD responsibility: {line}")

    return focus[:10]


def build_ats_change_plan(
    missing: list[str],
    missing_must: list[str],
    shortlist_words: list[str],
) -> list[str]:
    plan = []

    if missing_must:
        plan.append(
            "Prioritize missing must-have terms first: "
            + ", ".join(missing_must[:8])
        )

    if missing:
        plan.append(
            "Use missing keywords only if supported by the candidate profile: "
            + ", ".join(missing[:10])
        )

    if shortlist_words:
        plan.append(
            "Rewrite bullets with strong recruiter verbs such as: "
            + ", ".join(shortlist_words[:10])
        )

    plan.append("Convert generic duties into Challenge-Action-Result bullets.")
    plan.append("Add measurable impact where truthful: percentages, incidents resolved, users supported, timelines, cost, or downtime reduction.")
    plan.append("Keep formatting ATS-readable: clean headings, simple bullets, no complex tables, no images for critical text.")

    return plan


def resume_only_score_breakdown(profile: ResumeProfile, raw_text: str = "") -> dict:
    score = 0
    bullets = _all_bullets(profile)
    total_bullets = len(bullets)
    breakdown: dict[str, dict] = {}

    # Contact quality — 10
    contact_score = 0
    if profile.contact.full_name:
        contact_score += 3
    if profile.contact.email:
        contact_score += 3
    if profile.contact.phone:
        contact_score += 2
    if profile.contact.location:
        contact_score += 1
    if profile.contact.linkedin or profile.contact.github or profile.contact.portfolio:
        contact_score += 1

    breakdown["contact_quality"] = {
        "score": min(contact_score, 10),
        "max": 10,
        "notes": "Checks name, email, phone, location, and professional links.",
    }
    score += min(contact_score, 10)

    # Section structure — 15
    structure_score = 0
    if profile.summary:
        structure_score += 3
    if profile.technical_skills:
        structure_score += 3
    if profile.professional_experience:
        structure_score += 4
    if profile.projects:
        structure_score += 2
    if profile.education:
        structure_score += 2
    if profile.certifications:
        structure_score += 1

    breakdown["section_structure"] = {
        "score": min(structure_score, 15),
        "max": 15,
        "notes": "Checks summary, skills, experience, projects, education, and certifications.",
    }
    score += min(structure_score, 15)

    # Summary quality — 10
    summary_score = 0
    summary_words = _word_count(profile.summary)

    if summary_words >= 20:
        summary_score += 3
    if 35 <= summary_words <= 95:
        summary_score += 3
    if any(skill.lower() in profile.summary.lower() for skill in profile.technical_skills[:20]):
        summary_score += 2
    if not re.search(r"\b(I|me|my)\b", profile.summary or "", re.IGNORECASE):
        summary_score += 1
    if any(word in profile.summary.lower() for word in ["experience", "skilled", "proven", "delivered", "supported", "led"]):
        summary_score += 1

    breakdown["summary_quality"] = {
        "score": min(summary_score, 10),
        "max": 10,
        "notes": "Checks summary length, keyword relevance, and professional tone.",
    }
    score += min(summary_score, 10)

    # Technical skills quality — 15
    skills_score = 0
    skill_count = len(profile.technical_skills)
    skills_text = " ".join(profile.technical_skills).lower()

    if skill_count >= 8:
        skills_score += 4
    if 12 <= skill_count <= 45:
        skills_score += 5
    elif skill_count > 45:
        skills_score += 2

    useful_hits = sum(1 for word in COMMON_TERMS if word in skills_text)
    if useful_hits >= 4:
        skills_score += 4
    if useful_hits >= 8:
        skills_score += 2

    breakdown["technical_skills_quality"] = {
        "score": min(skills_score, 15),
        "max": 15,
        "notes": "Checks useful skill count, role relevance, and avoids keyword stuffing.",
    }
    score += min(skills_score, 15)

    # Experience quality — 25
    experience_score = 0

    if profile.professional_experience:
        experience_score += 5

    role_headers = 0
    for exp in profile.professional_experience:
        if exp.title:
            role_headers += 1
        if exp.company:
            role_headers += 1
        if exp.start_date or exp.end_date:
            role_headers += 1

    if role_headers >= 2:
        experience_score += 4
    if total_bullets >= 4:
        experience_score += 4
    if total_bullets >= 8:
        experience_score += 4

    action_bullets = sum(1 for bullet in bullets if _starts_with_action_verb(bullet))
    if action_bullets >= 4:
        experience_score += 4
    if action_bullets >= 8:
        experience_score += 2

    good_length_bullets = sum(1 for bullet in bullets if 8 <= _word_count(bullet) <= 32)
    if total_bullets and good_length_bullets / total_bullets >= 0.60:
        experience_score += 2

    breakdown["experience_quality"] = {
        "score": min(experience_score, 25),
        "max": 25,
        "notes": "Checks job titles, companies, dates, bullets, action verbs, and bullet readability.",
    }
    score += min(experience_score, 25)

    # Impact / metrics — 15
    impact_score = 0

    metric_bullets = sum(1 for bullet in bullets if _has_metric(bullet))
    if metric_bullets >= 1:
        impact_score += 5
    if metric_bullets >= 3:
        impact_score += 5
    if metric_bullets >= 6:
        impact_score += 3

    impact_hits = sum(
        1 for bullet in bullets
        if any(word in bullet.lower() for word in IMPACT_WORDS)
    )
    if impact_hits >= 3:
        impact_score += 2

    breakdown["impact_metrics"] = {
        "score": min(impact_score, 15),
        "max": 15,
        "notes": "Checks measurable achievements, numbers, percentages, and impact words.",
    }
    score += min(impact_score, 15)

    # Proof sections — 10
    proof_score = 0
    if profile.education:
        proof_score += 4
    if profile.certifications:
        proof_score += 3
    if profile.projects:
        proof_score += 3

    breakdown["education_certifications_projects"] = {
        "score": min(proof_score, 10),
        "max": 10,
        "notes": "Checks education, certifications, and project proof.",
    }
    score += min(proof_score, 10)

    # ATS readability — 10
    readability_score = 10

    very_long_bullets = sum(1 for bullet in bullets if _word_count(bullet) > 38)
    if very_long_bullets >= 5:
        readability_score -= 3

    if len(profile.technical_skills) > 65:
        readability_score -= 2

    if raw_text:
        if len(raw_text.splitlines()) < 8:
            readability_score -= 2

        if "│" in raw_text or "┌" in raw_text or "└" in raw_text:
            readability_score -= 3

        if len(re.findall(r"[^\x00-\x7F]", raw_text)) > 50:
            readability_score -= 2

    readability_score = max(0, min(10, readability_score))

    breakdown["ats_readability"] = {
        "score": readability_score,
        "max": 10,
        "notes": "Checks ATS-readable formatting, bullet length, symbols, and keyword stuffing risk.",
    }
    score += readability_score

    final_score = max(20, min(100, round(score)))

    return {
        "final_score": final_score,
        "breakdown": breakdown,
        "recommendations": build_resume_score_recommendations(profile, breakdown),
    }


def build_resume_score_recommendations(profile: ResumeProfile, breakdown: dict) -> list[str]:
    recommendations = []

    if breakdown["summary_quality"]["score"] < 7:
        recommendations.append("Improve the summary with a clear target role, stronger keywords, and 35–95 words.")

    if breakdown["technical_skills_quality"]["score"] < 10:
        recommendations.append("Improve skills with 12–35 relevant role-specific tools and categories.")

    if breakdown["experience_quality"]["score"] < 18:
        recommendations.append("Rewrite experience bullets using action verbs, tools, responsibilities, and outcomes.")

    if breakdown["impact_metrics"]["score"] < 8:
        recommendations.append("Add measurable impact such as percentages, users supported, tickets resolved, timelines, cost savings, or downtime reduction.")

    if breakdown["ats_readability"]["score"] < 8:
        recommendations.append("Simplify formatting and avoid complex symbols, tables, or very long bullets.")

    if not profile.certifications:
        recommendations.append("Add relevant certifications only if the candidate truly has them.")

    return recommendations


def resume_only_score(profile: ResumeProfile, raw_text: str = "") -> int:
    return resume_only_score_breakdown(profile, raw_text)["final_score"]


def formatting_score(template: TemplateSettings, section_count: int) -> int:
    score = 70

    if 9 <= template.body_font_size <= 11:
        score += 8

    if 0.35 <= template.margin_inches <= 0.75:
        score += 8

    if section_count >= 5:
        score += 8

    if template.page_limit in {1, 2}:
        score += 4

    if template.show_watermark:
        score -= 2

    return max(40, min(100, score))


def experience_relevance_score(profile: ResumeProfile, matched_terms: list[str]) -> int:
    exp_text = " ".join(
        [" ".join(exp.bullets) for exp in profile.professional_experience]
    ).lower()

    if not exp_text:
        return 35

    hits = sum(1 for term in matched_terms if _contains_term(exp_text, term))
    score = 45 + hits * 5

    action_bullets = sum(
        1 for bullet in _all_bullets(profile)
        if _starts_with_action_verb(bullet)
    )

    if action_bullets >= 5:
        score += 8

    return max(35, min(100, score))


def leadership_soft_skill_score(profile_text: str, job_description: str) -> int:
    profile_lower = _lower(profile_text)
    jd_lower = _lower(job_description)

    hits = sum(
        1 for term in LEADERSHIP_TERMS
        if _contains_term(profile_lower, term) and _contains_term(jd_lower, term)
    )

    score = 45 + hits * 8
    return max(35, min(100, score))


def recruiter_readability_score(profile: ResumeProfile) -> int:
    bullets = _all_bullets(profile)
    score = 85

    if not bullets:
        return 45

    long_bullets = sum(1 for bullet in bullets if _word_count(bullet) > 34)
    weak_bullets = sum(1 for bullet in bullets if not _starts_with_action_verb(bullet))

    if long_bullets > 4:
        score -= 10

    if weak_bullets > len(bullets) * 0.50:
        score -= 10

    if len(profile.technical_skills) > 60:
        score -= 8

    return max(40, min(100, score))


def compute_breakdown(
    profile: ResumeProfile,
    job_description: str,
    template: TemplateSettings,
) -> tuple[ScoreBreakdown, dict]:
    profile_text = profile_to_text(profile)
    match = keyword_match(job_description, profile_text)

    section_count = sum(
        [
            bool(profile.summary),
            bool(profile.technical_skills),
            bool(profile.professional_experience),
            bool(profile.projects),
            bool(profile.education),
            bool(profile.certifications),
            bool(profile.interests),
            bool(profile.languages),
        ]
    )

    resume_score = resume_only_score(profile, profile_text)
    format_score = formatting_score(template, section_count)
    keyword_score = match["score"]
    must_have_score = match["must_have_score"]

    exp_relevance = experience_relevance_score(profile, match["matched"])
    leadership_score = leadership_soft_skill_score(profile_text, job_description)
    readability = recruiter_readability_score(profile)

    jd_match = round(
        (keyword_score * 0.30)
        + (must_have_score * 0.25)
        + (exp_relevance * 0.25)
        + (leadership_score * 0.20)
    )

    final = round(
        (jd_match * 0.55)
        + (resume_score * 0.20)
        + (format_score * 0.10)
        + (readability * 0.15)
    )

    coverage_ratio = len(match["matched"]) / max(1, len(match["jd_terms"]))
    must_have_ratio = len(match["matched_must_have_terms"]) / max(1, len(match["matched_must_have_terms"]) + len(match["missing_must_have_terms"]))

    # Truth caps: do not display fake 90+ if the profile does not support the JD.
    if must_have_ratio < 0.45:
        final = min(final, 72)
    elif must_have_ratio < 0.60:
        final = min(final, 82)
    elif must_have_ratio < 0.75:
        final = min(final, 89)

    if coverage_ratio < 0.55:
        final = min(final, 74)
    elif coverage_ratio < 0.70:
        final = min(final, 84)
    elif coverage_ratio < 0.82:
        final = min(final, 89)

    if resume_score < 65:
        final = min(final, 78)

    final = max(0, min(100, final))

    match["score_explanation"] = {
        "resume_only_score": resume_score,
        "keyword_score": keyword_score,
        "must_have_score": must_have_score,
        "experience_relevance_score": exp_relevance,
        "leadership_soft_skill_score": leadership_score,
        "formatting_score": format_score,
        "recruiter_readability_score": readability,
        "final_ats_estimate": final,
    }

    return (
        ScoreBreakdown(
            resume_only_score=resume_score,
            jd_match_score=jd_match,
            keyword_score=keyword_score,
            experience_relevance_score=exp_relevance,
            leadership_soft_skill_score=leadership_score,
            formatting_score=format_score,
            recruiter_readability_score=readability,
            final_ats_estimate=final,
        ),
        match,
    )