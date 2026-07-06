from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import html
import re

from app.schemas import ResumeProfile, TemplateSettings


DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def clean_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_")
    return cleaned or "resume_tailor_pro_v5.docx"


def _x(value: str) -> str:
    return html.escape(value or "", quote=False)


def _sz(points: float) -> int:
    return max(12, int(float(points) * 2))


def _twips(inches: float) -> int:
    return int(float(inches) * 1440)


def _p(text: str, style: str = "Normal") -> str:
    safe = _x(text)
    return f'''
<w:p>
  <w:pPr><w:pStyle w:val="{style}"/></w:pPr>
  <w:r><w:t xml:space="preserve">{safe}</w:t></w:r>
</w:p>'''


def _bullet(text: str) -> str:
    safe = _x(text)
    return f'''
<w:p>
  <w:pPr><w:pStyle w:val="Bullet"/></w:pPr>
  <w:r><w:t xml:space="preserve">• {safe}</w:t></w:r>
</w:p>'''


def _heading(text: str) -> str:
    return _p(text.upper(), "Heading")


def build_resume_text(profile: ResumeProfile, ai: dict, template: TemplateSettings) -> str:
    contact = profile.contact
    contact_line = " | ".join([x for x in [
        contact.location,
        contact.phone,
        contact.email,
        contact.linkedin,
        contact.github,
        contact.portfolio,
    ] if x])

    lines = [
        contact.full_name or "YOUR NAME",
        contact_line,
        "",
        "SUMMARY",
        ai["generated_summary"],
        "",
        "TECHNICAL SKILLS",
        ", ".join(ai["generated_skills"]),
        "",
        "PROFESSIONAL EXPERIENCE",
    ]

    for exp in profile.professional_experience:
        header = " | ".join([x for x in [exp.title, exp.company, exp.location, f"{exp.start_date} - {exp.end_date}".strip(" -")] if x])
        if header:
            lines.append(header)
        bullets = ai["generated_bullets"][:8] if ai.get("generated_bullets") else exp.bullets[:8]
        for b in bullets:
            lines.append(f"• {b}")

    if template.show_projects and profile.projects:
        lines.extend(["", "PROJECTS"])
        for project in profile.projects[:4]:
            lines.append(project.name or "Project")
            if project.description:
                lines.append(project.description)
            for b in project.bullets[:4]:
                lines.append(f"• {b}")

    if profile.education:
        lines.extend(["", "EDUCATION"])
        for edu in profile.education:
            edu_line = " | ".join([x for x in [edu.degree, edu.school, edu.location, edu.graduation] if x])
            if edu_line:
                lines.append(edu_line)

    if template.show_certifications and profile.certifications:
        lines.extend(["", "CERTIFICATIONS"])
        for cert in profile.certifications:
            lines.append(f"• {cert}")

    if template.show_interests and profile.interests:
        lines.extend(["", "INTERESTS"])
        lines.append(", ".join(profile.interests))

    return "\n".join(lines)


def create_resume_docx(output_path: Path, profile: ResumeProfile, ai: dict, template: TemplateSettings, watermark: bool = True) -> str:
    contact = profile.contact
    contact_line = " | ".join([x for x in [
        contact.location,
        contact.phone,
        contact.email,
        contact.linkedin,
        contact.github,
        contact.portfolio,
    ] if x])

    body = []
    body.append(_p(contact.full_name or "YOUR NAME", "Name"))
    if contact_line:
        body.append(_p(contact_line, "Contact"))

    body.append(_heading("Summary"))
    body.append(_p(ai["generated_summary"]))

    body.append(_heading("Technical Skills"))
    body.append(_p(", ".join(ai["generated_skills"])))

    if profile.professional_experience:
        body.append(_heading("Professional Experience"))
        for exp in profile.professional_experience:
            header = " | ".join([x for x in [exp.title, exp.company, exp.location, f"{exp.start_date} - {exp.end_date}".strip(" -")] if x])
            if header:
                body.append(_p(header, "JobTitle"))
            bullets = ai["generated_bullets"][:8] if ai.get("generated_bullets") else exp.bullets[:8]
            for b in bullets:
                body.append(_bullet(b))

    if template.show_projects and profile.projects:
        body.append(_heading("Projects"))
        for project in profile.projects[:4]:
            body.append(_p(project.name or "Project", "JobTitle"))
            if project.description:
                body.append(_p(project.description))
            for b in project.bullets[:4]:
                body.append(_bullet(b))

    if profile.education:
        body.append(_heading("Education"))
        for edu in profile.education:
            edu_line = " | ".join([x for x in [edu.degree, edu.school, edu.location, edu.graduation] if x])
            if edu_line:
                body.append(_p(edu_line))

    if template.show_certifications and profile.certifications:
        body.append(_heading("Certifications"))
        for cert in profile.certifications:
            body.append(_bullet(cert))

    if template.show_interests and profile.interests:
        body.append(_heading("Interests"))
        body.append(_p(", ".join(profile.interests)))

    if watermark:
        body.append(_p(""))
        body.append(_p("Created with Resume Tailor Pro", "Watermark"))

    margins = _twips(template.margin_inches)
    document_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document
 xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"
 xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
 xmlns:v="urn:schemas-microsoft-com:vml"
 xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing"
 xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
 xmlns:w10="urn:schemas-microsoft-com:office:word"
 xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"
 xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"
 xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk"
 xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml"
 xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
 mc:Ignorable="w14 wp14">
  <w:body>
    {"".join(body)}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="{margins}" w:right="{margins}" w:bottom="{margins}" w:left="{margins}" w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>'''

    font = _x(template.font_family)
    styles = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/><w:sz w:val="{_sz(template.body_font_size)}"/></w:rPr>
    <w:pPr><w:spacing w:after="0" w:before="0"/></w:pPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Name">
    <w:name w:val="Name"/>
    <w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/><w:b/><w:sz w:val="{_sz(template.name_font_size)}"/></w:rPr>
    <w:pPr><w:jc w:val="center"/><w:spacing w:after="0" w:before="0"/></w:pPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Contact">
    <w:name w:val="Contact"/>
    <w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/><w:sz w:val="{_sz(template.body_font_size)}"/></w:rPr>
    <w:pPr><w:jc w:val="center"/><w:spacing w:after="80" w:before="0"/></w:pPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading">
    <w:name w:val="Heading"/>
    <w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/><w:b/><w:sz w:val="{_sz(template.heading_font_size)}"/></w:rPr>
    <w:pPr><w:spacing w:before="120" w:after="30"/><w:pBdr><w:bottom w:val="single" w:sz="4" w:space="1" w:color="808080"/></w:pBdr></w:pPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="JobTitle">
    <w:name w:val="JobTitle"/>
    <w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/><w:b/><w:sz w:val="{_sz(template.body_font_size)}"/></w:rPr>
    <w:pPr><w:spacing w:before="60" w:after="0"/></w:pPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Bullet">
    <w:name w:val="Bullet"/>
    <w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/><w:sz w:val="{_sz(template.body_font_size)}"/></w:rPr>
    <w:pPr><w:spacing w:before="0" w:after="0"/></w:pPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Watermark">
    <w:name w:val="Watermark"/>
    <w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/><w:color w:val="999999"/><w:sz w:val="14"/></w:rPr>
    <w:pPr><w:jc w:val="right"/></w:pPr>
  </w:style>
</w:styles>'''

    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>'''

    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

    doc_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>'''

    with ZipFile(output_path, "w", ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types)
        docx.writestr("_rels/.rels", rels)
        docx.writestr("word/_rels/document.xml.rels", doc_rels)
        docx.writestr("word/styles.xml", styles)
        docx.writestr("word/document.xml", document_xml)

    return build_resume_text(profile, ai, template)
