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


def normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


def detect_sections(text: str) -> list[str]:
    known = {
        "summary": "Summary",
        "professional summary": "Summary",
        "profile": "Summary",
        "technical skills": "Technical Skills",
        "skills": "Technical Skills",
        "professional experience": "Professional Experience",
        "work experience": "Professional Experience",
        "experience": "Professional Experience",
        "project experience": "Projects",
        "projects": "Projects",
        "projects related": "Projects",
        "education": "Education",
        "certifications": "Certifications",
        "certification": "Certifications",
        "interests": "Interests",
        "languages": "Languages",
        "achievements": "Achievements",
    }

    found = []
    for raw in text.splitlines():
        cleaned = re.sub(r"[^a-zA-Z ]", " ", raw).lower()
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if cleaned in known and known[cleaned] not in found:
            found.append(known[cleaned])
    return found
