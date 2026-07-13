from __future__ import annotations
import re
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from app.services.layout_blueprint import DocumentBlueprint, SectionBlock, canonical_section_name
from app.services.structure_confidence_scorer import score_blueprint_confidence

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
BULLET_RE = re.compile(r"^\s*[•\-*–—]\s+")
DATE_RE = re.compile(r"\b(19|20)\d{2}\b|\b(Present|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b", re.I)
ROLE_RE = re.compile(r"\b(Engineer|Developer|Analyst|Manager|Lead|Specialist|Coordinator|Consultant|Architect|Administrator)\b", re.I)

def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()

def _paragraph_text(p) -> str:
    return _clean("".join(t.text or "" for t in p.findall(".//w:t", NS)))

def _is_bulleted(p, text: str) -> bool:
    return bool(BULLET_RE.match(text)) or p.find(".//w:numPr", NS) is not None

def _detect_sections(paragraphs: list[tuple[str, bool]]) -> list[SectionBlock]:
    sections=[]; current=None
    for i,(text,is_bullet) in enumerate(paragraphs):
        name=canonical_section_name(text)
        if name:
            if current:
                current.end_index=i-1; sections.append(current)
            current=SectionBlock(name=name,start_index=i,end_index=i)
        elif current:
            current.paragraph_count += 1
            if is_bullet: current.bullet_count += 1
    if current:
        current.end_index=len(paragraphs)-1; sections.append(current)
    return sections

def _detect_employers(paragraphs: list[tuple[str, bool]]) -> list[dict]:
    blocks=[]; current=None; lines=[x[0] for x in paragraphs]
    in_exp=False
    for i,(text,is_bullet) in enumerate(paragraphs):
        section=canonical_section_name(text)
        if section == "PROFESSIONAL EXPERIENCE":
            in_exp=True; continue
        if section and section != "PROFESSIONAL EXPERIENCE" and in_exp:
            if current:
                current["end_index"]=i-1; blocks.append(current); current=None
            in_exp=False
        neighbor=" ".join(lines[max(0,i-1):min(len(lines),i+3)])
        if in_exp and len(text)<100 and ROLE_RE.search(text) and DATE_RE.search(neighbor) and not is_bullet:
            if current:
                current["end_index"]=i-1; blocks.append(current)
            current={"label":text,"start_index":i,"end_index":i,"bullet_count":0,"date_text":neighbor}
            continue
        if current and is_bullet: current["bullet_count"] += 1
    if current:
        current["end_index"]=len(paragraphs)-1; blocks.append(current)
    return blocks

def extract_docx_blueprint(path: str | Path) -> tuple[DocumentBlueprint, str]:
    path=Path(path)
    with ZipFile(path) as z:
        root=ET.fromstring(z.read("word/document.xml"))
    paragraphs=[]; font_names=[]; font_sizes=[]; margins={}
    for p in root.findall(".//w:p", NS):
        text=_paragraph_text(p)
        if not text: continue
        paragraphs.append((text,_is_bulleted(p,text)))
        for rpr in p.findall(".//w:rPr", NS):
            rfonts=rpr.find("w:rFonts", NS)
            if rfonts is not None:
                font=rfonts.attrib.get(f"{{{NS['w']}}}ascii") or rfonts.attrib.get(f"{{{NS['w']}}}hAnsi")
                if font: font_names.append(font)
            sz=rpr.find("w:sz", NS)
            if sz is not None:
                val=sz.attrib.get(f"{{{NS['w']}}}val")
                if val and val.isdigit(): font_sizes.append(int(val)/2)
    sect=root.find(".//w:sectPr", NS)
    if sect is not None:
        mar=sect.find("w:pgMar", NS)
        if mar is not None:
            for key in ["top","right","bottom","left"]:
                val=mar.attrib.get(f"{{{NS['w']}}}{key}")
                if val and val.isdigit(): margins[key]=round(int(val)/1440,3)
    lines=[x[0] for x in paragraphs]
    sections=_detect_sections(paragraphs)
    page_count=3 if len(lines)>95 else 2 if len(lines)>48 else 1
    blueprint=DocumentBlueprint(
        source_type="docx", page_count=page_count, section_order=[s.name for s in sections], sections=sections,
        employer_blocks=_detect_employers(paragraphs), margins=margins, fonts=sorted(set(font_names))[:10],
        dominant_font=max(set(font_names), key=font_names.count) if font_names else "",
        dominant_font_size=max(set(font_sizes), key=font_sizes.count) if font_sizes else 10.0,
        heading_font_size=max(font_sizes) if font_sizes else 11.0,
        has_tables=bool(root.findall(".//w:tbl", NS)), has_images=bool(root.findall(".//w:drawing", NS)),
        has_environment_lines=any(x.lower().startswith("environment:") for x in lines), line_count=len(lines))
    return score_blueprint_confidence(blueprint), "\n".join(lines)
