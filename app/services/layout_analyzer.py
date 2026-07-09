from __future__ import annotations

import re
from collections import OrderedDict

SECTION_ALIASES = {
    "SUMMARY": ["SUMMARY", "PROFESSIONAL SUMMARY", "PROFILE"],
    "TECHNICAL SKILLS": ["TECHNICAL SKILLS", "SKILLS", "CORE SKILLS"],
    "PROFESSIONAL EXPERIENCE": ["PROFESSIONAL EXPERIENCE", "WORK EXPERIENCE", "EXPERIENCE"],
    "PROJECTS": ["PROJECTS", "PROJECTS RELATED", "PROJECT EXPERIENCE"],
    "EDUCATION": ["EDUCATION"],
    "CERTIFICATIONS": ["CERTIFICATIONS", "CERTIFICATION"],
    "INTERESTS": ["INTERESTS", "HOBBIES"],
}

ROLE_WORDS = ["Engineer", "Developer", "Analyst", "Manager", "Lead", "Administrator", "Specialist", "Consultant", "Architect", "Coordinator"]


def clean_line(line: str) -> str:
    return re.sub(r"\s+", " ", line or "").strip()


def lines_from_text(text: str) -> list[str]:
    return [clean_line(x) for x in (text or "").splitlines() if clean_line(x)]


def is_section(line: str) -> bool:
    upper = re.sub(r"[^A-Z ]", "", line.upper()).strip()
    return any(upper in aliases for aliases in SECTION_ALIASES.values())


def detect_section_order(text: str) -> list[str]:
    found = []
    for line in lines_from_text(text):
        upper = re.sub(r"[^A-Z ]", "", line.upper()).strip()
        for canonical, aliases in SECTION_ALIASES.items():
            if upper in aliases and canonical not in found:
                found.append(canonical)
    return found


def detect_page_count(text: str) -> int:
    if "\f" in text:
        return max(1, len([p for p in text.split("\f") if p.strip()]))
    line_count = len(lines_from_text(text))
    if line_count <= 55:
        return 1
    if line_count <= 105:
        return 2
    return 3


def looks_like_role_header(line: str) -> bool:
    if len(line) > 100 or is_section(line):
        return False
    return any(word.lower() in line.lower() for word in ROLE_WORDS)


def detect_employer_bullet_counts(text: str) -> dict[str, int]:
    lines = lines_from_text(text)
    counts: OrderedDict[str, int] = OrderedDict()
    current = ""

    for i, line in enumerate(lines):
        if is_section(line):
            current = ""
            continue

        neighbor = " ".join(lines[max(0, i - 1): i + 3])
        has_date_nearby = bool(re.search(r"\b(20\d{2}|Present|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b", neighbor))

        if looks_like_role_header(line) and ("—" in line or has_date_nearby):
            current = line
            counts.setdefault(current, 0)
            continue

        if current and re.match(r"^\s*[•\-*–—]\s+", line):
            counts[current] = counts.get(current, 0) + 1

    if not counts:
        total_bullets = len([x for x in lines if re.match(r"^\s*[•\-*–—]\s+", x)])
        if total_bullets:
            counts["Professional Experience"] = total_bullets

    return dict(counts)


def estimate_project_count(text: str) -> int:
    lines = lines_from_text(text)
    in_projects = False
    count = 0

    for line in lines:
        upper = re.sub(r"[^A-Z ]", "", line.upper()).strip()
        if upper in SECTION_ALIASES["PROJECTS"]:
            in_projects = True
            continue
        if in_projects and is_section(line):
            break
        if in_projects and len(line) <= 95 and not line.startswith(("•", "-", "*")):
            if not re.search(r"\b(Designed|Developed|Built|Modernized|Improved|Supported)\b", line):
                count += 1

    return max(0, min(count, 12))


def analyze_source_layout(text: str, uploaded_name: str = "") -> dict:
    lines = lines_from_text(text)
    section_order = detect_section_order(text)
    employer_counts = detect_employer_bullet_counts(text)
    page_count = detect_page_count(text)

    instruction_parts = [
        f"Preserve approximate uploaded length: {page_count} page(s), about {len(lines)} extracted lines.",
        "Do not replace the uploaded resume with a generic format.",
    ]

    if section_order:
        instruction_parts.append("Preserve section order exactly: " + " → ".join(section_order) + ".")

    if employer_counts:
        instruction_parts.append("Preserve employer/client bullet counts where possible: " + "; ".join(f"{k}: {v} bullets" for k, v in employer_counts.items()) + ".")

    if any(line.lower().startswith("environment:") for line in lines):
        instruction_parts.append("Keep Environment lines in the same employer sections.")

    return {
        "uploaded_name": uploaded_name,
        "source_page_count": page_count,
        "source_line_count": len(lines),
        "source_section_order": section_order,
        "source_employer_bullet_counts": employer_counts,
        "source_project_count": estimate_project_count(text),
        "source_has_environment_lines": any(line.lower().startswith("environment:") for line in lines),
        "source_preservation_instruction": " ".join(instruction_parts),
    }
