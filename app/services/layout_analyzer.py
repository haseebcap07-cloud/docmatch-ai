from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from app.services.extractors import detect_sections_from_text


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}


def _qn(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def _paragraph_text(p: ET.Element) -> str:
    return "".join(t.text or "" for t in p.findall(".//w:t", NS)).strip()


def _twips_to_inches(value: str | None) -> str:
    if not value:
        return ""
    try:
        return f"{int(value) / 1440:.2f} in"
    except Exception:
        return value


def analyze_docx_layout(file_bytes: bytes, resume_text: str) -> dict:
    profile = {
        "source_type": "docx",
        "preserve_mode": "original_docx_layout_preservation",
        "estimated_page_count": 1,
        "paragraph_count": 0,
        "word_count": len(resume_text.split()),
        "detected_sections": detect_sections_from_text(resume_text),
        "detected_fonts": [],
        "detected_font_sizes": [],
        "margins": {},
        "layout_notes": [],
    }

    try:
        with ZipFile(io.BytesIO(file_bytes)) as docx:
            document_xml = docx.read("word/document.xml")
    except Exception:
        profile["layout_notes"].append("Could not read DOCX layout metadata.")
        return profile

    root = ET.fromstring(document_xml)
    paragraphs = root.findall(".//w:p", NS)
    profile["paragraph_count"] = len(paragraphs)

    fonts = []
    sizes = []

    for p in paragraphs:
        for r_fonts in p.findall(".//w:rFonts", NS):
            val = r_fonts.attrib.get(_qn("ascii")) or r_fonts.attrib.get(_qn("hAnsi"))
            if val and val not in fonts:
                fonts.append(val)

        for sz in p.findall(".//w:sz", NS):
            val = sz.attrib.get(_qn("val"))
            if val:
                try:
                    display = f"{int(val) / 2:.0f} pt"
                except Exception:
                    display = val
                if display not in sizes:
                    sizes.append(display)

    profile["detected_fonts"] = fonts[:8]
    profile["detected_font_sizes"] = sizes[:8]

    sect = root.find(".//w:sectPr", NS)
    if sect is not None:
        margins = sect.find("w:pgMar", NS)
        if margins is not None:
            profile["margins"] = {
                "top": _twips_to_inches(margins.attrib.get(_qn("top"))),
                "right": _twips_to_inches(margins.attrib.get(_qn("right"))),
                "bottom": _twips_to_inches(margins.attrib.get(_qn("bottom"))),
                "left": _twips_to_inches(margins.attrib.get(_qn("left"))),
            }

    # A rough but useful page estimate when direct Word pagination is unavailable.
    words = max(1, len(resume_text.split()))
    profile["estimated_page_count"] = max(1, round(words / 475))

    if profile["detected_fonts"]:
        profile["layout_notes"].append("Detected font information from DOCX runs.")
    else:
        profile["layout_notes"].append("Font may be inherited from Word styles rather than direct runs.")

    profile["layout_notes"].append("DOCX mode preserves the original package and replaces targeted text in-place when possible.")
    profile["layout_notes"].append("Exact Word page count can vary by installed fonts and rendering engine.")

    return profile


def analyze_plain_layout(source_type: str, resume_text: str) -> dict:
    words = len(resume_text.split())
    return {
        "source_type": source_type,
        "preserve_mode": "generated_docx_fallback",
        "estimated_page_count": max(1, round(max(1, words) / 475)),
        "paragraph_count": len([x for x in resume_text.splitlines() if x.strip()]),
        "word_count": words,
        "detected_sections": detect_sections_from_text(resume_text),
        "detected_fonts": [],
        "detected_font_sizes": [],
        "margins": {},
        "layout_notes": [
            "PDF/TXT/MD uploads use generated DOCX fallback.",
            "For strongest layout preservation, upload DOCX.",
        ],
    }


def analyze_resume_layout(file_bytes: bytes, source_type: str, resume_text: str) -> dict:
    if source_type == "docx":
        return analyze_docx_layout(file_bytes, resume_text)
    return analyze_plain_layout(source_type, resume_text)
