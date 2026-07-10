from __future__ import annotations
import re
BANNED_GENERATED_PHRASES=["using verified experience from the master profile","work aligned with","professional aligned with","relevant background includes","skilled in translating technical work into delivery-focused outcomes"]
SUMMARY_FILLER_PHRASES=["team player","fast learner","passionate","detail-oriented","highly motivated","results-driven professional","proven track record","dynamic professional"]
SKILL_JUNK_WORDS={"data","engineer","design","develop","collaborate","computer","science","remote","company","physical","using","tools","support","ability","capacity","systems","technical","requirements","quality","developed","built","help","schools","organizations","solutions","platforms"}
def normalize_text(v:str)->str: return re.sub(r"\s+"," ",v or "").strip()
def word_count(v:str)->int: return len(re.findall(r"\b\w+\b",v or ""))
def has_banned_generated_phrase(v:str)->bool:
    low=normalize_text(v).lower(); return any(p in low for p in BANNED_GENERATED_PHRASES)
def has_summary_filler(v:str)->bool:
    low=normalize_text(v).lower(); return any(p in low for p in SUMMARY_FILLER_PHRASES)
def looks_like_jd_copy(summary:str,jd:str)->bool:
    s=normalize_text(summary).lower()
    if not s: return False
    for line in [normalize_text(x).lower() for x in (jd or '').splitlines() if len(normalize_text(x))>70]:
        if line and line[:95] in s: return True
    sw=re.findall(r"[a-z]{4,}",s); jw=re.findall(r"[a-z]{4,}",(jd or '').lower())
    if len(sw)<16 or len(jw)<16: return False
    ss={" ".join(sw[i:i+8]) for i in range(max(0,len(sw)-7))}; js={" ".join(jw[i:i+8]) for i in range(max(0,len(jw)-7))}
    return bool(ss) and len(ss & js)/max(1,len(ss))>0.28
def extract_metrics(text:str)->list[str]:
    pats=[r"\b\d+(?:\.\d+)?%",r"\b\d+(?:\.\d+)?\s*(?:seconds|minutes|hours|days|weeks|months|years)\b",r"\b\d+(?:\.\d+)?x\b",r"\b\d+\+?\s*(?:users|customers|clients|applications|services|apis|pipelines|jobs|modules|workflows|teams|systems|platforms|deployments|tickets|incidents)\b"]
    out=[]
    for p in pats: out+=re.findall(p,text or '',flags=re.I)
    return dedupe_keep_order([normalize_text(x) for x in out if normalize_text(x)])
def clean_skill_token(t:str)->str:
    c=normalize_text(str(t).strip(' •-–—,;'))
    if not c or c.lower() in SKILL_JUNK_WORDS: return ''
    if len(c)<=2 and c.upper() not in {'R','C','C#','JS'}: return ''
    return c
def dedupe_keep_order(items:list[str])->list[str]:
    seen=set(); out=[]
    for it in items:
        c=normalize_text(str(it)); k=c.lower()
        if c and k not in seen: seen.add(k); out.append(c)
    return out
def strip_bullet_prefix(v:str)->str: return re.sub(r"^\s*(?:[•*\-–—]|\d+[.)])\s*",'',v or '').strip()
