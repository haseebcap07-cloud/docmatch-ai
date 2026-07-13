from __future__ import annotations
from pathlib import Path
from app.services.docx_structure_extractor import extract_docx_blueprint
from app.services.pdf_layout_extractor import extract_pdf_blueprint
from app.services.layout_blueprint import blueprint_to_profile_source_layout

def route_document_structure(path: str | Path, raw_text: str = "") -> tuple[dict, str, list[str]]:
    path=Path(path); suffix=path.suffix.lower(); warnings=[]
    if suffix==".docx":
        bp,text=extract_docx_blueprint(path); return blueprint_to_profile_source_layout(bp), text, bp.warnings
    if suffix==".pdf":
        bp,text=extract_pdf_blueprint(path); 
        if bp.confidence < 0.55: warnings.append("PDF structure confidence is low. Ask for DOCX upload for exact formatting.")
        return blueprint_to_profile_source_layout(bp), text, bp.warnings+warnings
    lines=[x.strip() for x in (raw_text or "").splitlines() if x.strip()]
    layout={"source_type":suffix.replace(".","") or "text","source_page_count":1 if len(lines)<=55 else 2,"source_line_count":len(lines),"source_section_order":[],"source_employer_bullet_counts":{},"source_preservation_instruction":"Text source detected. Preserve section order and line density where possible.","structure_confidence":0.45,"structure_warnings":["Plain text/markdown source has limited style metadata."]}
    return layout, raw_text, layout["structure_warnings"]
