from __future__ import annotations
import json
from typing import Any
from app.core.config import settings
from app.schemas import ResumeProfile, TemplateSettings
from app.services.ats_engine import compute_breakdown, profile_to_text
from app.services.role_classifier import classify_resume_role, classify_jd_role, alignment_label
from app.services.role_playbooks import get_playbook
from app.services.jd_analyzer import analyze_job_description
from app.services.evidence_mapper import map_evidence
from app.services.resume_validator import validate_generated_resume
from app.services.semantic_mapper import apply_semantic_mappings
from app.services.change_log_builder import build_change_log
from app.services.summary_word_count_enforcer import clean_summary
from app.services.post_score_engine import score_generated_resume
from app.services.experience_matrix import build_experience_matrix, flatten_generated_experience
from app.services.assertion_engine import run_generation_assertions
from app.services.resume_quality_rules import clean_skill_token,dedupe_keep_order,extract_metrics,strip_bullet_prefix
from app.services.docx_style_preserver import apply_blueprint_to_template_settings
from app.services.section_replacement_engine import validate_section_preservation

RESULT_SCHEMA={"type":"object","additionalProperties":False,"properties":{"score_reason":{"type":"string"},"generated_summary":{"type":"string"},"generated_skills":{"type":"array","items":{"type":"string"}},"generated_experience":{"type":"array","items":{"type":"object","additionalProperties":False,"properties":{"title":{"type":"string"},"company":{"type":"string"},"location":{"type":"string"},"start_date":{"type":"string"},"end_date":{"type":"string"},"bullets":{"type":"array","items":{"type":"string"}},"environment":{"type":"string"}},"required":["title","company","location","start_date","end_date","bullets","environment"]}},"generated_bullets":{"type":"array","items":{"type":"string"}},"matched_keywords":{"type":"array","items":{"type":"string"}},"missing_keywords":{"type":"array","items":{"type":"string"}},"weak_requirements":{"type":"array","items":{"type":"string"}},"truthful_90_plus_actions":{"type":"array","items":{"type":"string"}},"recruiter_warnings":{"type":"array","items":{"type":"string"}}},"required":["score_reason","generated_summary","generated_skills","generated_experience","generated_bullets","matched_keywords","missing_keywords","weak_requirements","truthful_90_plus_actions","recruiter_warnings"]}
def _safe_list(v:Any)->list[str]: return [str(x).strip() for x in v if str(x).strip()] if isinstance(v,list) else []

class AdaptiveResumeEngine:
    def tailor(self,profile:ResumeProfile,job_description:str,target_role:str,custom_instructions:str,template:TemplateSettings,user_requested_additions:list[str]|None=None,user_requested_replacements:list[str]|None=None)->dict:
        user_requested_additions=user_requested_additions or []; user_requested_replacements=user_requested_replacements or []
        template=apply_blueprint_to_template_settings(profile,template); profile_text=profile_to_text(profile); source_layout=profile.source_layout or {}; preserve_structure=bool(getattr(template,'preserve_source_structure',True))
        baseline_breakdown,match=compute_breakdown(profile,job_description,template); baseline_score=baseline_breakdown.final_ats_estimate
        resume_class=classify_resume_role(profile); jd_class=classify_jd_role(job_description,target_role); role_alignment=alignment_label(resume_class['role_family'],jd_class['role_family'])
        selected_family=jd_class['role_family'] if jd_class['role_family']!='general' else resume_class['role_family']; playbook=get_playbook(selected_family)
        jd_analysis=analyze_job_description(job_description,target_role); evidence=map_evidence(profile,jd_analysis,match); semantic_result=apply_semantic_mappings(profile_text,match.get('missing',[])); exp_matrix=build_experience_matrix(profile,jd_analysis,match,job_description)
        provider=(settings.AI_PROVIDER or 'mock').lower().strip()
        if provider=='openai' and settings.OPENAI_API_KEY:
            try: ai=self._openai_tailor(profile,job_description,target_role,custom_instructions,template,baseline_breakdown.model_dump(),match,resume_class,jd_class,role_alignment,playbook,jd_analysis,evidence,semantic_result,user_requested_additions,user_requested_replacements,source_layout,preserve_structure,exp_matrix)
            except Exception as exc:
                ai=self._rule_tailor(profile,target_role,match,playbook,evidence,role_alignment,jd_analysis,semantic_result,user_requested_additions,exp_matrix); ai['recruiter_warnings'].insert(0,f'OpenAI failed; V8.1 fallback used: {str(exc)[:180]}')
        else: ai=self._rule_tailor(profile,target_role,match,playbook,evidence,role_alignment,jd_analysis,semantic_result,user_requested_additions,exp_matrix)
        ai['matched_keywords']=_safe_list(ai.get('matched_keywords')) or match.get('matched',[]); ai['missing_keywords']=_safe_list(ai.get('missing_keywords')) or match.get('missing',[])[:18]
        ai['weak_requirements']=_safe_list(ai.get('weak_requirements')) or evidence.get('unsupported_requirements',[])[:10] or match.get('missing',[])[:10]
        ai['truthful_90_plus_actions']=_safe_list(ai.get('truthful_90_plus_actions')) or match.get('ats_change_plan',[]); ai['recruiter_warnings']=_safe_list(ai.get('recruiter_warnings')) or ['Review all generated content before submitting.']
        ai['generated_skills']=self._clean_skills(_safe_list(ai.get('generated_skills')) or self._fallback_skills(profile,match,playbook,semantic_result,user_requested_additions)); ai['generated_experience']=self._normalize_generated_experience(ai.get('generated_experience'),profile,exp_matrix)
        ai['generated_summary']=str(ai.get('generated_summary') or '').strip() or self._fallback_summary(profile,target_role,match,playbook,role_alignment,jd_analysis,job_description); ai['generated_summary'],sw=clean_summary(ai['generated_summary']); ai['recruiter_warnings'].extend(sw)
        ai['generated_bullets']=flatten_generated_experience(ai['generated_experience']) or _safe_list(ai.get('generated_bullets')) or self._fallback_bullets(exp_matrix,playbook,evidence,match)
        ai,aw=run_generation_assertions(profile,ai,job_description,template,exp_matrix); ai['recruiter_warnings'].extend(aw)
        if not ai.get('generated_summary'):
            ai['generated_summary']=self._fallback_summary(profile,target_role,match,playbook,role_alignment,jd_analysis,job_description); ai['generated_summary'],sw=clean_summary(ai['generated_summary']); ai['recruiter_warnings'].extend(sw)
        ai['score_reason']=str(ai.get('score_reason') or self._score_reason(role_alignment)).strip(); validation=validate_generated_resume(ai,evidence,profile_text); ai['recruiter_warnings'].extend(validation.get('validator_warnings',[])); section_warnings=validate_section_preservation(profile,ai); ai['recruiter_warnings'].extend(section_warnings)
        post=score_generated_resume(profile,ai['generated_summary'],ai['generated_skills'],ai['generated_bullets'],job_description,template,ai.get('generated_experience',[])); post_breakdown=post['breakdown']; post_score=max(post['post_score'],baseline_score) if ai['generated_bullets'] else post['post_score']; improvement=post_score-baseline_score
        change_log=build_change_log(semantic_result,match,user_requested_additions,user_requested_replacements,evidence,f'V8.1 preserved uploaded structure where requested; original employer titles, names, and dates preserved.')
        ai['score_breakdown']=post_breakdown; ai['adaptive_analysis']={'resume_role_family':resume_class['role_family'],'jd_role_family':jd_class['role_family'],'role_alignment':role_alignment,'selected_playbook':playbook['name'],'top_3_jd_priorities':jd_analysis.get('top_3_priorities',[])[:3],'supported_requirements':evidence.get('supported_requirements',[])[:10],'partially_supported_requirements':evidence.get('partially_supported_requirements',[])[:10],'unsupported_requirements':evidence.get('unsupported_requirements',[])[:10],'rewrite_focus':match.get('rewrite_focus',[])[:10],'validator_warnings':validation.get('validator_warnings',[])[:10]}
        ai['initial_analysis']={'baseline_ats_score':baseline_score,'resume_role_family':resume_class['role_family'],'jd_role_family':jd_class['role_family'],'role_alignment':role_alignment,'summary':self._baseline_summary(baseline_score,role_alignment,match,evidence)}
        ai['gap_analysis']={'missing_hard_skills_not_added':semantic_result.get('missing_hard_skills_not_added',[])[:20],'semantic_gaps':semantic_result.get('semantic_mappings_applied',[])[:20],'likely_possessed_rephrasing':semantic_result.get('likely_possessed_rephrasing',[])[:20],'unsupported_requirements':evidence.get('unsupported_requirements',[])[:12]}
        ai['change_log']=change_log; ai['final_result']={'post_optimization_ats_score':post_score,'score_improvement':f'{baseline_score}% → {post_score}% | {improvement:+d} points','score_improvement_points':improvement}
        return ai
    def _openai_tailor(self,profile,job_description,target_role,custom_instructions,template,baseline_breakdown,match,resume_class,jd_class,role_alignment,playbook,jd_analysis,evidence,semantic_result,user_requested_additions,user_requested_replacements,source_layout,preserve_structure,exp_matrix):
        from openai import OpenAI
        client=OpenAI(api_key=settings.OPENAI_API_KEY)
        prompt=f"""
Act as a senior technical recruiter, ATS specialist, and evidence-based resume editor. Return JSON only.
CRITICAL FAILURES TO AVOID: never paste JD into summary; never write "using verified experience from the master profile"; never collapse employers; never change employer names/titles/dates; never add unsupported tools/certs/metrics.
SUMMARY: write fresh role-specific summary from JD priorities + source evidence only, 90-125 words, no JD copy over 6 consecutive words.
SKILLS: preserve categories like "Languages & Frameworks:"; include only supported JD-relevant skills; remove junk tokens.
EXPERIENCE: return one generated_experience item per source employer; preserve title/company/location/dates; write 8-9 bullets per company when evidence supports it; use action + technology/process + outcome.
STRUCTURE: preserve_source_structure={preserve_structure}; source layout={json.dumps(source_layout,indent=2)}. V8.1 document blueprint is the structure contract: preserve employer count, certifications, section order, bullet density, margins, dominant font, and page target whenever possible.
Target role: {target_role or jd_analysis.get('title_guess') or 'Target Role'}
Custom instructions: {custom_instructions or 'None'}
User requested additions: {json.dumps(user_requested_additions,indent=2)}
User requested replacements: {json.dumps(user_requested_replacements,indent=2)}
Resume classification: {json.dumps(resume_class,indent=2)}
JD classification: {json.dumps(jd_class,indent=2)}
Role alignment: {role_alignment}
Playbook: {json.dumps(playbook,indent=2)}
JD analysis: {json.dumps(jd_analysis,indent=2)}
Baseline: {json.dumps(baseline_breakdown,indent=2)}
ATS match: {json.dumps(match,indent=2)}
Semantic mapping: {json.dumps(semantic_result,indent=2)}
Evidence map: {json.dumps(evidence,indent=2)}
Company evidence matrix: {json.dumps(exp_matrix,indent=2)}
Template: {template.model_dump_json(indent=2)}
Profile: {profile.model_dump_json(indent=2)}
JD: {job_description}
"""
        try:
            res=client.responses.create(model=settings.OPENAI_MODEL,temperature=0.18,max_output_tokens=9000,input=prompt,text={'format':{'type':'json_schema','name':'resume_tailor_v8_result','schema':RESULT_SCHEMA,'strict':True}}); return json.loads(res.output_text)
        except TypeError:
            res=client.chat.completions.create(model=settings.OPENAI_MODEL,temperature=0.18,max_tokens=9000,response_format={'type':'json_object'},messages=[{'role':'system','content':'Return JSON only. You are a truthful ATS resume optimization specialist.'},{'role':'user','content':prompt}]); return json.loads(res.choices[0].message.content or '{}')
    def _fallback_summary(self,profile,target_role,match,playbook,role_alignment,jd_analysis,job_description):
        title=target_role or (profile.target_titles[0] if profile.target_titles else playbook['name']); skills=self._clean_skills((match.get('matched') or profile.technical_skills)[:10]); metrics=extract_metrics(profile_to_text(profile))[:4]; metric_clause=f" Supported outcomes include {', '.join(metrics)}." if metrics else ''
        priorities=jd_analysis.get('top_3_priorities',[])[:3]; priority_clause=', '.join(priorities) if priorities else ', '.join(playbook.get('summary_focus',[])[:3])
        return f"{title} with experience delivering role-relevant work across {', '.join(skills[:8])}. Background includes {priority_clause}, supported by hands-on experience across application delivery, technical documentation, quality validation, troubleshooting, stakeholder collaboration, and production-focused improvement. Experienced reading complex requirements, identifying implementation gaps, improving reliability, and aligning technical execution with business priorities.{metric_clause} Known for converting source evidence into clear, maintainable solutions while preserving accuracy, traceability, and delivery readiness."
    def _fallback_skills(self,profile,match,playbook,semantic_result,user_requested_additions):
        mapped=[x.split('→')[-1].strip() for x in semantic_result.get('semantic_mappings_applied',[]) if '→' in x]
        return self._clean_skills(match.get('matched',[])[:28]+mapped+profile.technical_skills+playbook.get('keywords',[])+user_requested_additions)[:60]
    def _fallback_bullets(self,exp_matrix,playbook,evidence,match):
        bullets=[]
        for it in exp_matrix:
            bullets += [strip_bullet_prefix(x) for x in it.get('strongest_source_bullets',[])[:8] if strip_bullet_prefix(x)]
        if bullets: return bullets[:18]
        verbs=playbook.get('verbs',['Delivered','Supported','Improved']); supported=evidence.get('supported_requirements',[]) or match.get('must_haves',[]) or match.get('matched',[])
        return [f"{verbs[i%len(verbs)]} {str(x).split('.')[0][:130]} through supported responsibilities, tools, documentation, and delivery-focused execution." for i,x in enumerate(supported[:8])]
    def _normalize_generated_experience(self,generated,profile,exp_matrix):
        if not isinstance(generated,list): generated=[]
        out=[]
        for i,src in enumerate(profile.professional_experience):
            incoming=generated[i] if i<len(generated) and isinstance(generated[i],dict) else {}; matrix=exp_matrix[i] if i<len(exp_matrix) else {}; bullets=[strip_bullet_prefix(x) for x in incoming.get('bullets',[]) if strip_bullet_prefix(str(x))]
            if not bullets: bullets=matrix.get('strongest_source_bullets',[])[:matrix.get('target_bullet_count',8)]
            out.append({'title':src.title,'company':src.company,'location':src.location,'start_date':src.start_date,'end_date':src.end_date,'bullets':[strip_bullet_prefix(x) for x in bullets if strip_bullet_prefix(str(x))][:max(8,min(12,matrix.get('target_bullet_count',len(bullets) or 8)))],'environment':incoming.get('environment','')})
        return out
    def _clean_skills(self,skills):
        cleaned=[]
        for item in skills or []:
            if ':' in str(item):
                left,right=str(item).split(':',1); label=clean_skill_token(left); parts=[clean_skill_token(x) for x in right.replace(';',',').split(',')]; parts=[x for x in parts if x]
                if label and parts: cleaned.append(f"{label}: {', '.join(dedupe_keep_order(parts))}")
            else:
                tok=clean_skill_token(str(item))
                if tok: cleaned.append(tok)
        return dedupe_keep_order(cleaned)
    def _rule_tailor(self,profile,target_role,match,playbook,evidence,role_alignment,jd_analysis,semantic_result,user_requested_additions,exp_matrix):
        ge=self._normalize_generated_experience([],profile,exp_matrix)
        return {'score_reason':self._score_reason(role_alignment),'generated_summary':self._fallback_summary(profile,target_role,match,playbook,role_alignment,jd_analysis,''),'generated_skills':self._fallback_skills(profile,match,playbook,semantic_result,user_requested_additions),'generated_experience':ge,'generated_bullets':flatten_generated_experience(ge),'matched_keywords':match.get('matched',[]),'missing_keywords':match.get('missing',[])[:18],'weak_requirements':evidence.get('unsupported_requirements',[])[:10] or match.get('missing',[])[:10],'truthful_90_plus_actions':match.get('ats_change_plan',[]),'recruiter_warnings':['V8.1 fallback mode is active. Enable AI_PROVIDER=openai for deeper role-aware rewriting.','V8.1 preserved employer structure and used source bullets as evidence-backed fallback content.']}
    def _score_reason(self,role_alignment:str)->str: return f"V8.1 score uses role alignment ({role_alignment}), JD priority coverage, company-by-company evidence mapping, keyword match, semantic mapping, formatting preservation, recruiter readability, and assertion checks."
    def _baseline_summary(self,baseline_score:int,role_alignment:str,match:dict,evidence:dict)->str: return f"Baseline ATS estimate is {baseline_score}/100. Role alignment is {role_alignment}. Matched {len(match.get('matched',[]))} JD terms and missed {len(match.get('missing',[]))}. Supported requirements: {len(evidence.get('supported_requirements',[]))}; unsupported requirements: {len(evidence.get('unsupported_requirements',[]))}."
engine=AdaptiveResumeEngine()
