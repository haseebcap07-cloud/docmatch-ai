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
from app.services.bullet_count_enforcer import enforce_bullet_count
from app.services.summary_word_count_enforcer import clean_summary
from app.services.post_score_engine import score_generated_resume


RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "score_reason": {"type": "string"},
        "generated_summary": {"type": "string"},
        "generated_skills": {"type": "array", "items": {"type": "string"}},
        "generated_bullets": {"type": "array", "items": {"type": "string"}},
        "matched_keywords": {"type": "array", "items": {"type": "string"}},
        "missing_keywords": {"type": "array", "items": {"type": "string"}},
        "weak_requirements": {"type": "array", "items": {"type": "string"}},
        "truthful_90_plus_actions": {"type": "array", "items": {"type": "string"}},
        "recruiter_warnings": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["score_reason", "generated_summary", "generated_skills", "generated_bullets", "matched_keywords", "missing_keywords", "weak_requirements", "truthful_90_plus_actions", "recruiter_warnings"],
}


def _safe_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return []


class AdaptiveResumeEngine:
    def tailor(self, profile: ResumeProfile, job_description: str, target_role: str, custom_instructions: str, template: TemplateSettings, user_requested_additions: list[str] | None = None, user_requested_replacements: list[str] | None = None) -> dict:
        user_requested_additions = user_requested_additions or []
        user_requested_replacements = user_requested_replacements or []
        profile_text = profile_to_text(profile)
        source_layout = profile.source_layout or {}
        preserve_structure = bool(getattr(template, 'preserve_source_structure', True))

        baseline_breakdown, match = compute_breakdown(profile, job_description, template)
        baseline_score = baseline_breakdown.final_ats_estimate
        resume_class = classify_resume_role(profile)
        jd_class = classify_jd_role(job_description, target_role)
        role_alignment = alignment_label(resume_class["role_family"], jd_class["role_family"])
        selected_family = jd_class["role_family"] if jd_class["role_family"] != "general" else resume_class["role_family"]
        playbook = get_playbook(selected_family)
        jd_analysis = analyze_job_description(job_description, target_role)
        evidence = map_evidence(profile, jd_analysis, match)
        semantic_result = apply_semantic_mappings(profile_text, match.get("missing", []))

        provider = (settings.AI_PROVIDER or "mock").lower().strip()
        if provider == "openai" and settings.OPENAI_API_KEY:
            try:
                ai = self._openai_tailor(profile, job_description, target_role, custom_instructions, template, baseline_breakdown.model_dump(), match, resume_class, jd_class, role_alignment, playbook, jd_analysis, evidence, semantic_result, user_requested_additions, user_requested_replacements)
            except Exception as exc:
                ai = self._rule_tailor(profile, target_role, match, playbook, evidence, role_alignment, jd_analysis, semantic_result, user_requested_additions)
                ai["recruiter_warnings"].insert(0, f"OpenAI failed; adaptive fallback used: {str(exc)[:180]}")
        else:
            ai = self._rule_tailor(profile, target_role, match, playbook, evidence, role_alignment, jd_analysis, semantic_result, user_requested_additions)

        ai["matched_keywords"] = _safe_list(ai.get("matched_keywords")) or match.get("matched", [])
        ai["missing_keywords"] = _safe_list(ai.get("missing_keywords")) or match.get("missing", [])[:18]
        ai["weak_requirements"] = _safe_list(ai.get("weak_requirements")) or evidence.get("unsupported_requirements", [])[:10] or match.get("missing", [])[:10]
        ai["truthful_90_plus_actions"] = _safe_list(ai.get("truthful_90_plus_actions")) or match.get("ats_change_plan", [])
        ai["recruiter_warnings"] = _safe_list(ai.get("recruiter_warnings")) or ["Review all generated content before submitting.", "Do not add unsupported skills, tools, certifications, employers, dates, or metrics unless user-requested and flagged."]
        ai["generated_skills"] = _safe_list(ai.get("generated_skills")) or self._fallback_skills(profile, match, playbook, semantic_result, user_requested_additions)
        ai["generated_bullets"] = _safe_list(ai.get("generated_bullets")) or self._fallback_bullets(playbook, evidence, match)

        source_bullets = []
        for exp in profile.professional_experience:
            source_bullets.extend(exp.bullets or [])
        ai["generated_bullets"], bullet_warnings = enforce_bullet_count(ai["generated_bullets"], source_bullets)
        ai["recruiter_warnings"].extend(bullet_warnings)

        ai["generated_summary"] = str(ai.get("generated_summary") or self._fallback_summary(profile, target_role, match, playbook, role_alignment, jd_analysis)).strip()
        ai["generated_summary"], summary_warnings = clean_summary(ai["generated_summary"])
        ai["recruiter_warnings"].extend(summary_warnings)
        ai["score_reason"] = str(ai.get("score_reason") or self._score_reason(role_alignment)).strip()

        validation = validate_generated_resume(ai, evidence, profile_text)
        ai["recruiter_warnings"].extend(validation.get("validator_warnings", []))

        post = score_generated_resume(profile, ai["generated_summary"], ai["generated_skills"], ai["generated_bullets"], job_description, template)
        post_breakdown = post["breakdown"]
        post_score = max(post["post_score"], baseline_score) if ai["generated_bullets"] else post["post_score"]
        improvement = post_score - baseline_score

        change_log = build_change_log(semantic_result, match, user_requested_additions, user_requested_replacements, evidence, f"Target title aligned toward {target_role or jd_analysis.get('title_guess', 'target role')} where appropriate; original employer titles preserved.")

        ai["score_breakdown"] = post_breakdown
        ai["adaptive_analysis"] = {
            "resume_role_family": resume_class["role_family"],
            "jd_role_family": jd_class["role_family"],
            "role_alignment": role_alignment,
            "selected_playbook": playbook["name"],
            "top_3_jd_priorities": jd_analysis.get("top_3_priorities", [])[:3],
            "supported_requirements": evidence.get("supported_requirements", [])[:10],
            "partially_supported_requirements": evidence.get("partially_supported_requirements", [])[:10],
            "unsupported_requirements": evidence.get("unsupported_requirements", [])[:10],
            "rewrite_focus": match.get("rewrite_focus", [])[:10],
            "validator_warnings": validation.get("validator_warnings", [])[:10],
        }
        ai["initial_analysis"] = {
            "baseline_ats_score": baseline_score,
            "resume_role_family": resume_class["role_family"],
            "jd_role_family": jd_class["role_family"],
            "role_alignment": role_alignment,
            "summary": self._baseline_summary(baseline_score, role_alignment, match, evidence),
        }
        ai["gap_analysis"] = {
            "missing_hard_skills_not_added": semantic_result.get("missing_hard_skills_not_added", [])[:20],
            "semantic_gaps": semantic_result.get("semantic_mappings_applied", [])[:20],
            "likely_possessed_rephrasing": semantic_result.get("likely_possessed_rephrasing", [])[:20],
            "unsupported_requirements": evidence.get("unsupported_requirements", [])[:12],
        }
        ai["change_log"] = change_log
        ai["final_result"] = {
            "post_optimization_ats_score": post_score,
            "score_improvement": f"{baseline_score}% → {post_score}% | {improvement:+d} points",
            "score_improvement_points": improvement,
        }
        return ai

    def _openai_tailor(self, profile, job_description, target_role, custom_instructions, template, baseline_breakdown, match, resume_class, jd_class, role_alignment, playbook, jd_analysis, evidence, semantic_result, user_requested_additions, user_requested_replacements):
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        prompt = f"""
<role>
Act as an expert ATS optimization specialist and technical recruiter. Your goal is to help achieve an ATS score of 85-90% for the target role while maintaining truthfulness by default.
</role>

<workflow>
1. Analyze original profile/resume against the JD.
2. Use baseline score and gap analysis.
3. Generate a full optimized resume.
4. Maintain similar structure and length.
5. Generate exactly 7-8 bullets per employer/client when enough evidence exists.
6. Re-score after optimization.
</workflow>

<structure_preservation_rules>
- If preserve_source_structure is true, the uploaded resume is the blueprint.
- Preserve section order, employer order, project order, education order, and approximate page length.
- Preserve employer/client bullet counts when source layout provides counts.
- Preserve Environment lines if present.
- Do not convert the uploaded resume into a generic new format.
- For PDF uploads, preserve extracted structure and length as closely as possible.
</structure_preservation_rules>

<summary_rules>
- Rewrite the summary specifically for this role.
- Reposition title only if appropriate and flag in Change Log.
- Lead with the top 3 JD priorities where supported by evidence.
- Mirror company/JD language naturally, not as keyword stuffing.
- Remove irrelevant content.
- Match company tone.
- Never use filler phrases: team player, fast learner, passionate, detail-oriented, highly motivated.
- Summary target: 110-120 words.
</summary_rules>

<tech_stack_rules>
DEFAULT MODE — No Fabrication:
- Do NOT add specific technologies, tools, frameworks, certifications, employers, projects, dates, or metrics not present in the profile.
SEMANTIC MAPPING — Always Allowed:
- Broader category mapping is allowed when supported.
USER-REQUESTED OVERRIDE MODE:
- User-requested additions/replacements may be included, but must be clearly flagged in Change Log.
</tech_stack_rules>

Return JSON only with the requested keys.

Target role: {target_role or jd_analysis.get('title_guess') or 'Target Role'}
Custom instructions: {custom_instructions or 'No custom instructions provided.'}
User-requested additions: {json.dumps(user_requested_additions, indent=2)}
User-requested replacements: {json.dumps(user_requested_replacements, indent=2)}
Resume classification: {json.dumps(resume_class, indent=2)}
JD classification: {json.dumps(jd_class, indent=2)}
Role alignment: {role_alignment}
Selected playbook: {json.dumps(playbook, indent=2)}
JD analysis: {json.dumps(jd_analysis, indent=2)}
Baseline score: {json.dumps(baseline_breakdown, indent=2)}
ATS match/change plan: {json.dumps(match, indent=2)}
Semantic mapping result: {json.dumps(semantic_result, indent=2)}
Evidence map: {json.dumps(evidence, indent=2)}
Template settings: {template.model_dump_json(indent=2)}
Structured profile: {profile.model_dump_json(indent=2)}
Job description: {job_description}
"""
        try:
            response = client.responses.create(model=settings.OPENAI_MODEL, temperature=0.10, max_output_tokens=7000, input=prompt, text={"format": {"type": "json_schema", "name": "resume_tailor_v7_result", "schema": RESULT_SCHEMA, "strict": True}})
            return json.loads(response.output_text)
        except TypeError:
            response = client.chat.completions.create(model=settings.OPENAI_MODEL, temperature=0.10, max_tokens=7000, response_format={"type": "json_object"}, messages=[{"role": "system", "content": "You are a truthful ATS resume optimization specialist and technical recruiter. Return JSON only."}, {"role": "user", "content": prompt}])
            return json.loads(response.choices[0].message.content or "{}")

    def _fallback_summary(self, profile, target_role, match, playbook, role_alignment, jd_analysis):
        title = target_role or (profile.target_titles[0] if profile.target_titles else playbook["name"])
        top = jd_analysis.get("top_3_priorities", [])[:3]
        priorities = "; ".join(top) if top else ", ".join(playbook.get("summary_focus", [])[:3])
        skills = ", ".join((match.get("matched") or profile.technical_skills)[:8])
        return f"Professional aligned with {title} roles, bringing verified experience across {skills}. Relevant background includes {priorities}. Skilled in translating technical work into delivery-focused outcomes, supporting stakeholders, improving operations, documenting work clearly, and strengthening quality across project or production environments. This resume has been repositioned toward the target role using supported evidence from the master profile while avoiding unsupported technologies, certifications, dates, or project claims."

    def _fallback_skills(self, profile, match, playbook, semantic_result, user_requested_additions):
        mapped = []
        for item in semantic_result.get("semantic_mappings_applied", []):
            if "→" in item:
                mapped.append(item.split("→")[-1].strip())
        return list(dict.fromkeys((match.get("matched", [])[:24] + mapped + playbook.get("keywords", []) + profile.technical_skills[:20] + user_requested_additions)))[:45]

    def _fallback_bullets(self, playbook, evidence, match):
        verbs = playbook.get("verbs", ["Delivered", "Supported", "Improved"])
        bullets = []
        supported = evidence.get("supported_requirements", []) or match.get("must_haves", []) or match.get("matched", [])
        for idx, item in enumerate(supported[:8]):
            bullets.append(f"{verbs[idx % len(verbs)]} work aligned with {item} using verified experience from the master profile.")
        if not bullets:
            for idx, term in enumerate((match.get("matched") or playbook.get("keywords", []))[:8]):
                bullets.append(f"{verbs[idx % len(verbs)]} {term}-related responsibilities using verified experience from the master profile.")
        return bullets[:8]

    def _rule_tailor(self, profile, target_role, match, playbook, evidence, role_alignment, jd_analysis, semantic_result, user_requested_additions):
        return {
            "score_reason": self._score_reason(role_alignment),
            "generated_summary": self._fallback_summary(profile, target_role, match, playbook, role_alignment, jd_analysis),
            "generated_skills": self._fallback_skills(profile, match, playbook, semantic_result, user_requested_additions),
            "generated_bullets": self._fallback_bullets(playbook, evidence, match),
            "matched_keywords": match.get("matched", []),
            "missing_keywords": match.get("missing", [])[:18],
            "weak_requirements": evidence.get("unsupported_requirements", [])[:10] or match.get("missing", [])[:10],
            "truthful_90_plus_actions": match.get("ats_change_plan", []),
            "recruiter_warnings": ["Adaptive mock mode is active. Enable AI_PROVIDER=openai for deeper role-aware rewriting.", "The engine used V6 role intelligence plus V7 ATS recruiter workflow, semantic mapping, change log, and post scoring."],
        }

    def _score_reason(self, role_alignment: str) -> str:
        return f"V7 score uses role alignment ({role_alignment}), must-have coverage, keyword match, semantic mapping, experience evidence, leadership fit, resume quality, formatting, recruiter readability, and post-generation validation. Truth caps prevent fake 90+ scores when the profile does not support the JD."

    def _baseline_summary(self, baseline_score: int, role_alignment: str, match: dict, evidence: dict) -> str:
        return f"Baseline ATS estimate is {baseline_score}/100. Role alignment is {role_alignment}. Matched {len(match.get('matched', []))} JD terms and missed {len(match.get('missing', []))}. Supported requirements: {len(evidence.get('supported_requirements', []))}; unsupported requirements: {len(evidence.get('unsupported_requirements', []))}."


engine = AdaptiveResumeEngine()
