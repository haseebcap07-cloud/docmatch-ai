from __future__ import annotations
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import html,re
from app.schemas import ResumeProfile, TemplateSettings
DOCX_MIME='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
def clean_filename(name:str)->str:
    cleaned=re.sub(r'[^A-Za-z0-9_.-]+','_',name).strip('_'); return cleaned or 'resume_tailor_pro_v8.docx'
def _x(v:str)->str: return html.escape(v or '',quote=False)
def _sz(points:float)->int: return max(12,int(float(points)*2))
def _twips(inches:float)->int: return int(float(inches)*1440)
def _p(text:str,style:str='Normal')->str: return f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr><w:r><w:t xml:space="preserve">{_x(text)}</w:t></w:r></w:p>'
def _p_runs(runs,style='Normal'):
    body=''.join(f'<w:r><w:rPr>{"<w:b/>" if b else ""}</w:rPr><w:t xml:space="preserve">{_x(t)}</w:t></w:r>' for t,b in runs)
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr>{body}</w:p>'
def _bullet(text:str)->str: return _p('• '+text,'Bullet')
def _heading(text:str)->str: return _p(text.upper(),'Heading')
def _skill_paragraph(line:str)->str:
    if ':' in line:
        left,right=line.split(':',1); return _p_runs([(left.strip()+':',True),(' '+right.strip(),False)])
    return _p(line)
def _gen_exp(profile,ai):
    ge=ai.get('generated_experience') or []
    if ge: return ge
    flat=ai.get('generated_bullets') or []; out=[]
    for i,e in enumerate(profile.professional_experience): out.append({'title':e.title,'company':e.company,'location':e.location,'start_date':e.start_date,'end_date':e.end_date,'bullets':flat[:8] if i==0 and flat else e.bullets[:8],'environment':''})
    return out
def build_resume_text(profile:ResumeProfile,ai:dict,template:TemplateSettings)->str:
    c=profile.contact; contact=' | '.join([x for x in [c.location,c.phone,c.email,c.linkedin,c.github,c.portfolio] if x]); lines=[c.full_name or 'YOUR NAME',contact,'','SUMMARY',ai['generated_summary'],'','TECHNICAL SKILLS']
    lines += [str(x) for x in ai.get('generated_skills',[]) if str(x).strip()]; lines += ['','PROFESSIONAL EXPERIENCE']
    for it in _gen_exp(profile,ai):
        title=' — '.join([x for x in [it.get('company'),it.get('title')] if x]); date=' | '.join([x for x in [it.get('location'),f"{it.get('start_date','')} - {it.get('end_date','')}".strip(' -')] if x])
        if title: lines.append(title)
        if date: lines.append(date)
        for b in it.get('bullets',[]): lines.append('• '+b)
        if it.get('environment'): lines.append('Environment: '+it['environment'])
    if template.show_projects and profile.projects:
        lines += ['','PROJECTS RELATED']
        for p in profile.projects[:4]:
            lines.append(p.name or 'Project')
            if p.description: lines.append(p.description)
            for b in p.bullets[:4]: lines.append('• '+b)
    if profile.education:
        lines += ['','EDUCATION']
        for e in profile.education:
            line=' | '.join([x for x in [e.degree,e.school,e.location,e.graduation] if x])
            if line: lines.append(line)
    return '\n'.join(lines)
def create_resume_docx(output_path:Path,profile:ResumeProfile,ai:dict,template:TemplateSettings,watermark:bool=True)->str:
    c=profile.contact; contact=' | '.join([x for x in [c.location,c.phone,c.email,c.linkedin,c.github,c.portfolio] if x]); body=[_p(c.full_name or 'YOUR NAME','Name')]
    if contact: body.append(_p(contact,'Contact'))
    body += [_heading('Summary'),_p(ai['generated_summary']),_heading('Technical Skills')]
    skills=[str(x) for x in ai.get('generated_skills',[]) if str(x).strip()]
    if any(':' in x for x in skills): body += [_skill_paragraph(x) for x in skills]
    else: body.append(_p(', '.join(skills)))
    if profile.professional_experience:
        body.append(_heading('Professional Experience'))
        for it in _gen_exp(profile,ai):
            title=' — '.join([x for x in [it.get('company'),it.get('title')] if x]); date=' | '.join([x for x in [it.get('location'),f"{it.get('start_date','')} - {it.get('end_date','')}".strip(' -')] if x])
            if title: body.append(_p(title,'JobTitle'))
            if date: body.append(_p(date))
            for b in it.get('bullets',[]): body.append(_bullet(b))
            if it.get('environment'): body.append(_skill_paragraph('Environment: '+it['environment']))
    if template.show_projects and profile.projects:
        body.append(_heading('Projects Related'))
        for p in profile.projects[:4]:
            body.append(_p(p.name or 'Project','JobTitle'))
            if p.description: body.append(_p(p.description))
            for b in p.bullets[:4]: body.append(_bullet(b))
    if profile.education:
        body.append(_heading('Education'))
        for e in profile.education:
            line=' | '.join([x for x in [e.degree,e.school,e.location,e.graduation] if x])
            if line: body.append(_p(line))
    if watermark: body.append(_p('')); body.append(_p('Created with Resume Tailor Pro','Watermark'))
    margins=_twips(template.margin_inches); font=_x(template.font_family)
    document=f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{''.join(body)}<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="{margins}" w:right="{margins}" w:bottom="{margins}" w:left="{margins}" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr></w:body></w:document>"""
    styles=f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/><w:sz w:val="{_sz(template.body_font_size)}"/></w:rPr><w:pPr><w:spacing w:after="0" w:before="0"/></w:pPr></w:style><w:style w:type="paragraph" w:styleId="Name"><w:name w:val="Name"/><w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/><w:b/><w:sz w:val="{_sz(template.name_font_size)}"/></w:rPr><w:pPr><w:jc w:val="center"/></w:pPr></w:style><w:style w:type="paragraph" w:styleId="Contact"><w:name w:val="Contact"/><w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/><w:sz w:val="{_sz(template.body_font_size)}"/></w:rPr><w:pPr><w:jc w:val="center"/><w:spacing w:after="80"/></w:pPr></w:style><w:style w:type="paragraph" w:styleId="Heading"><w:name w:val="Heading"/><w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/><w:b/><w:sz w:val="{_sz(template.heading_font_size)}"/></w:rPr><w:pPr><w:spacing w:before="120" w:after="30"/><w:pBdr><w:bottom w:val="single" w:sz="4" w:space="1" w:color="808080"/></w:pBdr></w:pPr></w:style><w:style w:type="paragraph" w:styleId="JobTitle"><w:name w:val="JobTitle"/><w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/><w:b/><w:sz w:val="{_sz(template.body_font_size)}"/></w:rPr><w:pPr><w:spacing w:before="60"/></w:pPr></w:style><w:style w:type="paragraph" w:styleId="Bullet"><w:name w:val="Bullet"/><w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/><w:sz w:val="{_sz(template.body_font_size)}"/></w:rPr><w:pPr><w:spacing w:before="0" w:after="0"/></w:pPr></w:style><w:style w:type="paragraph" w:styleId="Watermark"><w:name w:val="Watermark"/><w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/><w:color w:val="999999"/><w:sz w:val="14"/></w:rPr><w:pPr><w:jc w:val="right"/></w:pPr></w:style></w:styles>"""
    cts='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>'
    rels='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'
    with ZipFile(output_path,'w',ZIP_DEFLATED) as d:
        d.writestr('[Content_Types].xml',cts); d.writestr('_rels/.rels',rels); d.writestr('word/_rels/document.xml.rels','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>'); d.writestr('word/styles.xml',styles); d.writestr('word/document.xml',document)
    return build_resume_text(profile,ai,template)
