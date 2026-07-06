from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}


def extract_text_from_txt(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="ignore")


def extract_text_from_docx(file_bytes: bytes) -> str:
    with ZipFile(io.BytesIO(file_bytes)) as docx:
        try:
            xml_bytes = docx.read("word/document.xml")
        except KeyError:
            return ""

    root = ET.fromstring(xml_bytes)
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", NS):
        line = "".join(t.text or "" for t in paragraph.findall(".//w:t", NS)).strip()
        if line:
            paragraphs.append(line)
    return "\n".join(paragraphs)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text.strip())
    return "\n\n".join(pages)


def extract_text_from_upload(filename: str, file_bytes: bytes) -> tuple[str, str]:
    lower = filename.lower()

    if lower.endswith(".docx"):
        return extract_text_from_docx(file_bytes), "docx"

    if lower.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes), "pdf"

    if lower.endswith(".txt") or lower.endswith(".md"):
        return extract_text_from_txt(file_bytes), "text"

    raise ValueError("Unsupported file type. Upload DOCX, PDF, TXT, or MD.")


def normalize_section_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z ]", " ", value).lower()
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    mapping = {
        "summary": "Professional Summary",
        "professional summary": "Professional Summary",
        "profile": "Professional Summary",
        "career summary": "Professional Summary",
        "objective": "Professional Summary",
        "skills": "Skills",
        "technical skills": "Skills",
        "core skills": "Skills",
        "technologies": "Skills",
        "professional experience": "Experience",
        "work experience": "Experience",
        "experience": "Experience",
        "employment history": "Experience",
        "projects": "Projects",
        "project experience": "Projects",
        "education": "Education",
        "certifications": "Certifications",
        "certification": "Certifications",
    }

    return mapping.get(cleaned, value.strip())


def detect_sections_from_text(text: str) -> list[str]:
    found = []
    known = {
        "summary", "professional summary", "profile", "career summary", "objective",
        "skills", "technical skills", "core skills", "technologies",
        "professional experience", "work experience", "experience", "employment history",
        "projects", "education", "certifications", "certification"
    }

    for line in text.splitlines():
        clean = re.sub(r"[^a-zA-Z ]", " ", line).lower()
        clean = re.sub(r"\s+", " ", clean).strip()
        if clean in known:
            normalized = normalize_section_name(clean)
            if normalized not in found:
                found.append(normalized)

    return found
