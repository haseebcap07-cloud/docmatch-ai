from __future__ import annotations
from app.services.layout_blueprint import DocumentBlueprint

def score_blueprint_confidence(blueprint: DocumentBlueprint) -> DocumentBlueprint:
    score = 0.0
    warnings: list[str] = []
    if blueprint.page_count >= 1: score += 0.10
    else: warnings.append("Could not estimate page count.")
    if blueprint.section_order: score += min(0.25, len(blueprint.section_order) * 0.05)
    else: warnings.append("No standard resume sections detected.")
    if blueprint.employer_blocks: score += min(0.25, len(blueprint.employer_blocks) * 0.10)
    else: warnings.append("No employer blocks detected; generated experience may require parser fallback.")
    if blueprint.dominant_font or blueprint.dominant_font_size: score += 0.15
    else: warnings.append("Could not detect font signature.")
    if blueprint.margins: score += 0.10
    else: warnings.append("Could not detect margins.")
    if blueprint.line_count > 0: score += 0.10
    if blueprint.has_columns: warnings.append("Possible multi-column layout detected; exact DOCX recreation may need manual review.")
    if blueprint.has_tables: warnings.append("Tables detected; preserve-mode output may approximate table layout.")
    blueprint.confidence = round(min(1.0, score), 2)
    blueprint.warnings = list(dict.fromkeys(blueprint.warnings + warnings))
    return blueprint
