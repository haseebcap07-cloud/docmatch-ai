from __future__ import annotations
import re
from app.schemas import ResumeProfile
from app.services.resume_quality_rules import strip_bullet_prefix, extract_metrics, dedupe_keep_order

def _tokens(t:str)->set[str]: return {x.lower() for x in re.findall(r"[A-Za-z][A-Za-z0-9+#./-]{2,}",t or '')}
def _score(text:str,terms:list[str],jd_tokens:set[str])->int:
    low=(text or '').lower(); return sum(5 for t in terms if t and t.lower() in low)+len(_tokens(text)&jd_tokens)
def build_experience_matrix(profile:ResumeProfile,jd_analysis:dict,match:dict,job_description:str='')->list[dict]:
    terms=dedupe_keep_order(list(jd_analysis.get('must_haves',[]))+list(jd_analysis.get('technical_keywords',[]))+list(match.get('matched',[])))
    jd_tokens=_tokens(job_description+' '+' '.join(terms)); matrix=[]
    for i,exp in enumerate(profile.professional_experience):
        bullets=[strip_bullet_prefix(x) for x in (exp.bullets or []) if strip_bullet_prefix(x)]
        ev=' '.join([exp.title,exp.company,exp.location,' '.join(bullets)])
        ranked=sorted(bullets,key=lambda b:_score(b,terms,jd_tokens),reverse=True)
        matrix.append({'index':i,'title':exp.title,'company':exp.company,'location':exp.location,'start_date':exp.start_date,'end_date':exp.end_date,'source_bullet_count':len(bullets),'target_bullet_count':max(8,min(12,len(bullets) or 8)),'matched_terms':[t for t in terms if t and t.lower() in ev.lower()][:24],'source_metrics':extract_metrics(ev),'strongest_source_bullets':ranked[:12],'all_source_bullets':bullets})
    return matrix
def flatten_generated_experience(items:list[dict])->list[str]:
    out=[]
    for it in items or []: out += [strip_bullet_prefix(x) for x in it.get('bullets',[]) if strip_bullet_prefix(str(x))]
    return out
