from __future__ import annotations

import io
import xml.etree.ElementTree as ET
from zipfile import ZipFile


def extract_text_from_txt(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="ignore")


def extract_text_from_docx(file_bytes: bytes) -> str:
    with ZipFile(io.BytesIO(file_bytes)) as docx:
        try:
            xml_bytes = docx.read("word/document.xml")
        except KeyError:
            return ""

    root = ET.fromstring(xml_bytes)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", ns):
        text_parts = []
        for node in paragraph.findall(".//w:t", ns):
            if node.text:
                text_parts.append(node.text)
        line = "".join(text_parts).strip()
        if line:
            paragraphs.append(line)

    return "\n".join(paragraphs)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(file_bytes))
    pages: list[str] = []

    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text.strip())

    return "\n\n".join(pages)


def extract_text_from_upload(filename: str, file_bytes: bytes) -> str:
    lower = filename.lower()

    if lower.endswith(".docx"):
        return extract_text_from_docx(file_bytes)

    if lower.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)

    if lower.endswith(".txt") or lower.endswith(".md"):
        return extract_text_from_txt(file_bytes)

    raise ValueError("Unsupported file type. Upload DOCX, PDF, TXT, or MD.")
