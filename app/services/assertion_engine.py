from __future__ import annotations
from app.schemas import ResumeProfile, TemplateSettings
from app.services.resume_quality_rules import has_banned_generated_phrase,has_summary_filler,looks_like_jd_copy,word_count,strip_bullet_prefix

def run_generation_assertions(profile:ResumeProfile,ai:dict,job_description:str,template:TemplateSettings,experience_matrix:list[dict])->tuple[dict,list[str]]:
    warnings=[]; summary=str(ai.get('generated_summary') or '').strip()
    if looks_like_jd_copy(summary,job_description): warnings.append('Assertion: Summary looked copied from JD; evidence-based fallback required.'); ai['generated_summary']=''
    if has_banned_generated_phrase(summary) or has_summary_filler(summary): warnings.append('Assertion: Summary contained generic/filler language; fallback rewrite required.'); ai['generated_summary']=''
    wc=word_count(summary)
    if summary and wc>135: warnings.append(f'Assertion: Summary too long ({wc} words).')
    gen=ai.get('generated_experience') or []
    if getattr(template,'preserve_source_structure',True) and len(gen)!=len(profile.professional_experience): warnings.append('Assertion: Employer count was not preserved; source-company fallback used.')
    for i,exp in enumerate(profile.professional_experience):
        if i < len(gen) and isinstance(gen[i],dict):
            gen[i]['company']=exp.company; gen[i]['title']=exp.title; gen[i]['location']=exp.location; gen[i]['start_date']=exp.start_date; gen[i]['end_date']=exp.end_date
    for item in gen:
        clean=[]
        for b in item.get('bullets',[]) or []:
            x=strip_bullet_prefix(str(b))
            if not x: continue
            if has_banned_generated_phrase(x): warnings.append('Assertion: Removed generic generated bullet.'); continue
            clean.append(x)
        item['bullets']=clean
    ai['generated_experience']=gen
    return ai,warnings
