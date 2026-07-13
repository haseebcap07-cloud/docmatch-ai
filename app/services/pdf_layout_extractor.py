from __future__ import annotations
import re
from pathlib import Path
from app.services.layout_blueprint import DocumentBlueprint, SectionBlock, canonical_section_name
from app.services.structure_confidence_scorer import score_blueprint_confidence
BULLET_RE=re.compile(r"^\s*[•\-*–—]\s+")
DATE_RE=re.compile(r"\b(19|20)\d{2}\b|\b(Present|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b",re.I)
ROLE_RE=re.compile(r"\b(Engineer|Developer|Analyst|Manager|Lead|Specialist|Coordinator|Consultant|Architect|Administrator)\b",re.I)

def _clean(text:str)->str: return re.sub(r"\s+"," ",text or "").strip()

def _detect_sections(lines:list[str])->list[SectionBlock]:
    sections=[]; cur=None
    for i,line in enumerate(lines):
        name=canonical_section_name(line)
        if name:
            if cur: cur.end_index=i-1; sections.append(cur)
            cur=SectionBlock(name=name,start_index=i,end_index=i)
        elif cur:
            cur.paragraph_count+=1
            if BULLET_RE.match(line): cur.bullet_count+=1
    if cur: cur.end_index=len(lines)-1; sections.append(cur)
    return sections

def _detect_employers(lines:list[str])->list[dict]:
    blocks=[]; cur=None; in_exp=False
    for i,line in enumerate(lines):
        sec=canonical_section_name(line)
        if sec=="PROFESSIONAL EXPERIENCE": in_exp=True; continue
        if sec and sec!="PROFESSIONAL EXPERIENCE" and in_exp:
            if cur: cur["end_index"]=i-1; blocks.append(cur); cur=None
            in_exp=False
        neighbor=" ".join(lines[max(0,i-1):min(len(lines),i+3)])
        if in_exp and len(line)<100 and ROLE_RE.search(line) and DATE_RE.search(neighbor) and not BULLET_RE.match(line):
            if cur: cur["end_index"]=i-1; blocks.append(cur)
            cur={"label":line,"start_index":i,"end_index":i,"bullet_count":0,"date_text":neighbor}
            continue
        if cur and BULLET_RE.match(line): cur["bullet_count"]+=1
    if cur: cur["end_index"]=len(lines)-1; blocks.append(cur)
    return blocks

def extract_pdf_blueprint(path:str|Path)->tuple[DocumentBlueprint,str]:
    path=Path(path); text=""; page_count=1; fonts=[]; sizes=[]; has_images=False
    try:
        import fitz
        doc=fitz.open(str(path)); page_count=max(1,doc.page_count); lines=[]
        for page in doc:
            if page.get_images(): has_images=True
            data=page.get_text("dict")
            for block in data.get("blocks",[]):
                if block.get("type")!=0: continue
                for line in block.get("lines",[]):
                    lt=""
                    for span in line.get("spans",[]):
                        lt += span.get("text","")
                        if span.get("font"): fonts.append(span.get("font"))
                        if span.get("size"): sizes.append(round(float(span.get("size")),1))
                    if _clean(lt): lines.append(_clean(lt))
            text += page.get_text("text") + "\n"
        if not text.strip(): raise RuntimeError("empty")
    except Exception:
        from pypdf import PdfReader
        reader=PdfReader(str(path)); page_count=max(1,len(reader.pages)); text="\n".join(p.extract_text() or "" for p in reader.pages); lines=[_clean(x) for x in text.splitlines() if _clean(x)]
    sections=_detect_sections(lines)
    blueprint=DocumentBlueprint(source_type="pdf",page_count=page_count,section_order=[s.name for s in sections],sections=sections,employer_blocks=_detect_employers(lines),fonts=sorted(set(fonts))[:10],dominant_font=max(set(fonts),key=fonts.count) if fonts else "",dominant_font_size=max(set(sizes),key=sizes.count) if sizes else 10.0,heading_font_size=max(sizes) if sizes else 11.0,has_images=has_images,has_environment_lines=any(x.lower().startswith("environment:") for x in lines),line_count=len(lines))
    return score_blueprint_confidence(blueprint), text
