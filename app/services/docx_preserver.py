from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from app.services.docx_builder import create_generated_docx


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}

ET.register_namespace("w", W_NS)
ET.register_namespace("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")
ET.register_namespace("mc", "http://schemas.openxmlformats.org/markup-compatibility/2006")


SECTION_ALIASES = {
    "summary": "summary",
    "professional summary": "summary",
    "profile": "summary",
    "career summary": "summary",
    "objective": "summary",
    "skills": "skills",
    "technical skills": "skills",
    "core skills": "skills",
    "technologies": "skills",
    "professional experience": "experience",
    "work experience": "experience",
    "experience": "experience",
    "employment history": "experience",
    "projects": "projects",
    "project experience": "projects",
}


def _qn(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def _paragraph_text(p: ET.Element) -> str:
    return "".join(t.text or "" for t in p.findall(".//w:t", NS)).strip()


def _norm(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z ]", " ", value).lower()
    return re.sub(r"\s+", " ", cleaned).strip()


def _is_numbered(p: ET.Element) -> bool:
    return p.find(".//w:numPr", NS) is not None


def _style_name(p: ET.Element) -> str:
    style = p.find(".//w:pStyle", NS)
    if style is None:
        return ""
    return style.attrib.get(_qn("val"), "")


def _is_heading(p: ET.Element) -> bool:
    text = _paragraph_text(p)
    norm = _norm(text)
    style = _style_name(p).lower()
    if norm in SECTION_ALIASES:
        return True
    if style.startswith("heading"):
        return True
    if 2 <= len(text) <= 38 and text.isupper() and any(c.isalpha() for c in text):
        return True
    return False


def _replace_paragraph_text(p: ET.Element, new_text: str) -> None:
    texts = p.findall(".//w:t", NS)

    if not texts:
        r = ET.SubElement(p, _qn("r"))
        t = ET.SubElement(r, _qn("t"))
        t.text = new_text
        return

    texts[0].text = new_text
    for t in texts[1:]:
        t.text = ""


def _append_paragraph(body: ET.Element, template: ET.Element, text: str) -> None:
    new_p = deepcopy(template)
    _replace_paragraph_text(new_p, text)
    body.append(new_p)


def _find_sections(paragraphs: list[ET.Element]) -> dict[str, tuple[int, int]]:
    headings = []
    for i, p in enumerate(paragraphs):
        text = _paragraph_text(p)
        section = SECTION_ALIASES.get(_norm(text))
        if section:
            headings.append((section, i))
        elif _is_heading(p):
            maybe = SECTION_ALIASES.get(_norm(text))
            if maybe:
                headings.append((maybe, i))

    sections: dict[str, tuple[int, int]] = {}
    for idx, (name, start) in enumerate(headings):
        end = headings[idx + 1][1] if idx + 1 < len(headings) else len(paragraphs)
        if name not in sections:
            sections[name] = (start, end)
    return sections


def _first_content_index(paragraphs: list[ET.Element], start: int, end: int) -> int | None:
    for i in range(start + 1, end):
        text = _paragraph_text(paragraphs[i])
        if text and not _is_heading(paragraphs[i]):
            return i
    return None


def _replace_section_first_paragraph(paragraphs: list[ET.Element], section: tuple[int, int] | None, value: str) -> bool:
    if not section or not value.strip():
        return False
    idx = _first_content_index(paragraphs, section[0], section[1])
    if idx is None:
        return False
    _replace_paragraph_text(paragraphs[idx], value.strip())
    return True


def preserve_docx_layout(
    original_bytes: bytes,
    output_path: Path,
    tailoring: dict,
) -> dict:
    """Copy original DOCX and replace targeted text in word/document.xml.

    This preserves the package, styles, margins, borders, images, headers, and most paragraph formatting.
    It does not guarantee perfect pagination because Word layout depends on fonts and renderer.
    """
    try:
        zin = ZipFile(io.BytesIO(original_bytes), "r")
        document_xml = zin.read("word/document.xml")
        root = ET.fromstring(document_xml)
    except Exception:
        create_generated_docx(output_path, "ATS-Targeted Tailored Resume", tailoring["final_resume_text"])
        return {
            "mode": "generated_fallback",
            "changed_sections": [],
            "notes": ["Could not safely edit the DOCX package; generated a clean fallback DOCX."],
        }

    body = root.find("w:body", NS)
    paragraphs = root.findall(".//w:p", NS)
    sections = _find_sections(paragraphs)

    changed = []
    notes = []

    if _replace_section_first_paragraph(paragraphs, sections.get("summary"), tailoring.get("optimized_summary", "")):
        changed.append("Professional Summary")
    else:
        notes.append("Summary section not found; final report appended to the document.")

    skills_text = ", ".join(tailoring.get("optimized_skills", []))
    if _replace_section_first_paragraph(paragraphs, sections.get("skills"), skills_text):
        changed.append("Skills")
    else:
        notes.append("Skills section not found or not safely editable.")

    experience = sections.get("experience")
    bullets = tailoring.get("optimized_bullets", [])
    if experience and bullets:
        start, end = experience
        bullet_indices = [i for i in range(start + 1, end) if _is_numbered(paragraphs[i]) and len(_paragraph_text(paragraphs[i])) > 10]
        if not bullet_indices:
            bullet_indices = [i for i in range(start + 1, end) if len(_paragraph_text(paragraphs[i])) > 35 and not _is_heading(paragraphs[i])]

        for idx, bullet in zip(bullet_indices[:len(bullets)], bullets):
            _replace_paragraph_text(paragraphs[idx], bullet)
        if bullet_indices:
            changed.append("Experience Bullets")
        else:
            notes.append("Experience section found but bullet paragraphs were not safely detected.")

    if body is not None and paragraphs:
        template = paragraphs[-1]
        _append_paragraph(body, template, "")
        _append_paragraph(body, template, "ATS SCORE REPORT")
        _append_paragraph(body, template, f"Before: {tailoring.get('ats_score_before', 0)}/100 | After: {tailoring.get('ats_score_after', 0)}/100 | Target: {tailoring.get('target_score', 90)}+")
        _append_paragraph(body, template, "GAPS TO FIX FOR 90+")
        for gap in tailoring.get("truthful_90_plus_actions", [])[:8]:
            _append_paragraph(body, template, f"- {gap}")
        changed.append("ATS Report Appendix")

    updated_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    with ZipFile(output_path, "w", ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "word/document.xml":
                zout.writestr(item, updated_xml)
            else:
                zout.writestr(item, zin.read(item.filename))

    zin.close()

    return {
        "mode": "docx_in_place_preservation",
        "changed_sections": changed,
        "notes": notes or ["Edited the original DOCX package while preserving styles and layout metadata."],
    }
