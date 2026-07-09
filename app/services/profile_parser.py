from __future__ import annotations

import re
from app.schemas import ResumeProfile, ContactInfo, ExperienceItem, ProjectItem, EducationItem
from app.services.extractors import detect_sections, normalize_line
from app.services.layout_analyzer import analyze_source_layout


SECTION_KEYS = {
    "summary": ["summary", "professional summary", "profile", "career summary", "objective"],
    "skills": ["technical skills", "skills", "core skills", "technologies"],
    "experience": ["professional experience", "work experience", "experience", "employment history"],
    "projects": ["projects", "project experience", "projects related"],
    "education": ["education", "academic background"],
    "certifications": ["certifications", "certification", "licenses"],
    "interests": ["interests", "hobbies"],
    "languages": ["languages"],
    "achievements": ["achievements", "awards"],
}


def _norm(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z ]", " ", value).lower()
    return re.sub(r"\s+", " ", cleaned).strip()


def _split_sections(text: str) -> dict[str, list[str]]:
    lines = [normalize_line(x) for x in text.splitlines() if normalize_line(x)]
    sections: dict[str, list[str]] = {"top": []}
    current = "top"

    for line in lines:
        key = None
        n = _norm(line)
        for canonical, aliases in SECTION_KEYS.items():
            if n in aliases:
                key = canonical
                break

        if key:
            current = key
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)

    return sections


def _extract_contact(top_lines: list[str]) -> ContactInfo:
    joined = " | ".join(top_lines[:5])
    email = ""
    phone = ""
    location = ""

    email_match = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", joined)
    if email_match:
        email = email_match.group(0)

    phone_match = re.search(r"(\+?\d[\d\s().-]{8,}\d)", joined)
    if phone_match:
        phone = phone_match.group(0).strip()

    first_line = top_lines[0] if top_lines else ""
    name = first_line.strip()
    if "@" in name or re.search(r"\d", name):
        name = ""

    parts = [p.strip() for p in re.split(r"\||•", joined) if p.strip()]
    for p in parts:
        if p != email and p != phone and re.search(r"\b[A-Z]{2}\b", p):
            location = p
            break

    linkedin = ""
    github = ""
    for token in parts:
        low = token.lower()
        if "linkedin" in low:
            linkedin = token
        if "github" in low:
            github = token

    return ContactInfo(full_name=name, email=email, phone=phone, location=location, linkedin=linkedin, github=github)


def _split_skills(lines: list[str]) -> list[str]:
    raw = "\n".join(lines)
    parts = re.split(r",|;|\||•|\n", raw)
    skills = []
    for p in parts:
        item = normalize_line(p)
        item = re.sub(r"^[A-Za-z /&]+:\s*", "", item).strip()
        if 2 <= len(item) <= 70 and item.lower() not in {"and", "or", "tools"}:
            if item not in skills:
                skills.append(item)
    return skills[:90]


def _extract_bullets(lines: list[str]) -> list[str]:
    bullets = []
    for line in lines:
        cleaned = re.sub(r"^[•*–—-]\s*", "", line).strip()
        if len(cleaned) > 20:
            bullets.append(cleaned)
    return bullets


def _parse_experience(lines: list[str]) -> list[ExperienceItem]:
    bullets = _extract_bullets(lines)
    titles = []
    for line in lines[:15]:
        if len(line) < 90 and not re.search(r"^[•*–—-]", line):
            if any(word in line.lower() for word in ["engineer", "developer", "analyst", "manager", "lead", "administrator", "specialist", "consultant"]):
                titles.append(line)

    title = titles[0] if titles else "Professional Experience"
    return [ExperienceItem(title=title, company="", bullets=bullets[:22])] if bullets else []


def _parse_projects(lines: list[str]) -> list[ProjectItem]:
    projects: list[ProjectItem] = []
    current_name = ""
    current_bullets = []

    for line in lines:
        is_bullet = re.match(r"^[•*–—-]", line) or len(line) > 90
        if not is_bullet and len(line) <= 90:
            if current_name:
                projects.append(ProjectItem(name=current_name, bullets=current_bullets[:5]))
                current_bullets = []
            current_name = line
        else:
            current_bullets.append(re.sub(r"^[•*–—-]\s*", "", line))

    if current_name:
        projects.append(ProjectItem(name=current_name, bullets=current_bullets[:5]))

    if not projects and lines:
        projects.append(ProjectItem(name="Relevant Project Experience", bullets=_extract_bullets(lines)[:6]))

    return projects[:6]


def _parse_education(lines: list[str]) -> list[EducationItem]:
    education = []
    for line in lines[:10]:
        if any(x in line.lower() for x in ["bachelor", "master", "degree", "university", "college", "school", "science"]):
            education.append(EducationItem(degree=line))
    return education[:5]


def _simple_list(lines: list[str]) -> list[str]:
    items = []
    for line in lines:
        for part in re.split(r",|;|•|\n", line):
            item = normalize_line(part)
            if len(item) >= 2 and item not in items:
                items.append(item)
    return items[:30]


def build_profile_from_text(text: str) -> tuple[ResumeProfile, list[str]]:
    sections = _split_sections(text)
    profile = ResumeProfile()

    profile.contact = _extract_contact(sections.get("top", []))
    profile.summary = " ".join(sections.get("summary", []))[:1400]
    profile.technical_skills = _split_skills(sections.get("skills", []))
    profile.professional_experience = _parse_experience(sections.get("experience", []))
    profile.projects = _parse_projects(sections.get("projects", []))
    profile.education = _parse_education(sections.get("education", []))
    profile.certifications = _simple_list(sections.get("certifications", []))
    profile.interests = _simple_list(sections.get("interests", []))
    profile.languages = _simple_list(sections.get("languages", []))
    profile.achievements = _simple_list(sections.get("achievements", []))
    profile.source_layout = analyze_source_layout(text)
    profile.source_text_snapshot = text[:25000]

    notes = []
    detected = detect_sections(text)
    if not profile.summary:
        notes.append("Summary was not clearly detected. User can enter or edit it manually.")
    if not profile.technical_skills:
        notes.append("Technical skills were not clearly detected. User can enter or edit them manually.")
    if not profile.professional_experience:
        notes.append("Professional experience was not clearly detected as structured bullets.")
    if not profile.education:
        notes.append("Education was not clearly detected.")
    if detected:
        notes.append("Detected sections: " + ", ".join(detected))

    return profile, notes
