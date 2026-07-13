from __future__ import annotations
from app.schemas import ResumeProfile, TemplateSettings

def apply_blueprint_to_template_settings(profile: ResumeProfile, template: TemplateSettings) -> TemplateSettings:
    layout=profile.source_layout or {}
    if not getattr(template,"preserve_source_structure",True): return template
    margins=layout.get("source_margins") or {}; left=margins.get("left") or margins.get("right")
    if left: template.margin_inches=float(left)
    if layout.get("source_dominant_font"): template.font_family=str(layout["source_dominant_font"]).split("+")[-1]
    if layout.get("source_dominant_font_size"):
        size=float(layout["source_dominant_font_size"])
        if 7<=size<=12: template.body_font_size=size
    if layout.get("source_heading_font_size"):
        heading=float(layout["source_heading_font_size"])
        if 8<=heading<=18: template.heading_font_size=heading
    if layout.get("source_page_count"): template.page_limit=int(layout["source_page_count"])
    return template
