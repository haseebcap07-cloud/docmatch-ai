from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Any

@dataclass
class SectionBlock:
    name: str
    start_index: int = 0
    end_index: int = 0
    paragraph_count: int = 0
    bullet_count: int = 0
    style: dict[str, Any] = field(default_factory=dict)

@dataclass
class DocumentBlueprint:
    source_type: str
    page_count: int = 1
    section_order: list[str] = field(default_factory=list)
    sections: list[SectionBlock] = field(default_factory=list)
    employer_blocks: list[dict[str, Any]] = field(default_factory=list)
    margins: dict[str, float] = field(default_factory=dict)
    fonts: list[str] = field(default_factory=list)
    dominant_font: str = ""
    dominant_font_size: float = 10.0
    heading_font_size: float = 11.0
    bullet_style: dict[str, Any] = field(default_factory=dict)
    has_tables: bool = False
    has_columns: bool = False
    has_images: bool = False
    has_environment_lines: bool = False
    line_count: int = 0
    confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["sections"] = [asdict(x) if hasattr(x, "__dataclass_fields__") else x for x in self.sections]
        return data

CANONICAL_SECTIONS = {
    "summary": "SUMMARY", "professional summary": "SUMMARY", "profile": "SUMMARY",
    "skills": "TECHNICAL SKILLS", "technical skills": "TECHNICAL SKILLS", "core skills": "TECHNICAL SKILLS",
    "work experience": "PROFESSIONAL EXPERIENCE", "professional experience": "PROFESSIONAL EXPERIENCE", "experience": "PROFESSIONAL EXPERIENCE",
    "project": "PROJECTS", "projects": "PROJECTS", "projects related": "PROJECTS", "project experience": "PROJECTS",
    "education": "EDUCATION", "certification": "CERTIFICATIONS", "certifications": "CERTIFICATIONS",
    "interests": "INTERESTS",
}

def canonical_section_name(text: str) -> str:
    key = " ".join((text or "").strip().lower().replace(":", "").split())
    return CANONICAL_SECTIONS.get(key, "")

def blueprint_to_profile_source_layout(blueprint: DocumentBlueprint) -> dict[str, Any]:
    return {
        "source_type": blueprint.source_type,
        "source_page_count": blueprint.page_count,
        "source_line_count": blueprint.line_count,
        "source_section_order": blueprint.section_order,
        "source_employer_bullet_counts": {b.get("label", f"Employer {i+1}"): b.get("bullet_count", 0) for i,b in enumerate(blueprint.employer_blocks)},
        "source_project_count": len([s for s in blueprint.sections if s.name == "PROJECTS"]),
        "source_has_environment_lines": blueprint.has_environment_lines,
        "source_margins": blueprint.margins,
        "source_fonts": blueprint.fonts,
        "source_dominant_font": blueprint.dominant_font,
        "source_dominant_font_size": blueprint.dominant_font_size,
        "source_heading_font_size": blueprint.heading_font_size,
        "source_has_tables": blueprint.has_tables,
        "source_has_columns": blueprint.has_columns,
        "source_has_images": blueprint.has_images,
        "structure_confidence": blueprint.confidence,
        "structure_warnings": blueprint.warnings,
        "source_preservation_instruction": (
            f"Preserve uploaded {blueprint.source_type} structure: {blueprint.page_count} page(s), "
            f"{blueprint.line_count} lines, sections {' → '.join(blueprint.section_order) if blueprint.section_order else 'not fully detected'}, "
            f"{len(blueprint.employer_blocks)} employer block(s). Preserve margins, section order, employer order, "
            f"bullet density, certifications, education, and environment lines when present."
        ),
    }
