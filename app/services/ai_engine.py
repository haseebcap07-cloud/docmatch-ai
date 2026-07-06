from __future__ import annotations

import json
from typing import Any

from app.core.config import settings
from app.schemas import ResumeProfile, TemplateSettings
from app.services.ats_engine import compute_breakdown, ACTION_WORDS


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
    "required": [
        "score_reason", "generated_summary", "generated_skills", "generated_bullets",
        "matched_keywords", "missing_keywords", "weak_requirements",
        "truthful_90_plus_actions", "recruiter_warnings",
    ],
}


def _safe_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return []


class V5TailoringEngine:
    def tailor(
        self,
        profile: ResumeProfile,
        job_description: str,
        target_role: str,
        custom_instructions: str,
        template: TemplateSettings,
    ) -> dict:
        breakdown, match = compute_breakdown(profile, job_description, template)
        provider = (settings.AI_PROVIDER or "mock").lower().strip()

        if provider == "openai" and settings.OPENAI_API_KEY:
            try:
                ai = self._openai_tailor(profile, job_description, target_role, custom_instructions, template, match, breakdown.model_dump())
            except Exception as exc:
                ai = self._rule_tailor(profile, job_description, target_role, custom_instructions, template, match)
                ai["recruiter_warnings"].insert(0, f"OpenAI failed; rule-based fallback used: {str(exc)[:180]}")
        else:
            ai = self._rule_tailor(profile, job_description, target_role, custom_instructions, template, match)

        ai["score_breakdown"] = breakdown
        ai["matched_keywords"] = _safe_list(ai.get("matched_keywords")) or match["matched"]
        ai["missing_keywords"] = _safe_list(ai.get("missing_keywords")) or match["missing"][:18]
        ai["weak_requirements"] = _safe_list(ai.get("weak_requirements")) or match["missing"][:12]
        ai["truthful_90_plus_actions"] = _safe_list(ai.get("truthful_90_plus_actions")) or [
            f"Add truthful evidence for {x}" for x in match["missing"][:8]
        ]
        ai["recruiter_warnings"] = _safe_list(ai.get("recruiter_warnings")) or [
            "Review all AI-generated content before submitting.",
            "Do not add unsupported skills, certifications, employers, dates, or achievements.",
        ]
        ai["generated_skills"] = _safe_list(ai.get("generated_skills")) or match["matched"][:20]
        ai["generated_bullets"] = _safe_list(ai.get("generated_bullets")) or self._fallback_bullets(match["matched"], target_role)
        ai["generated_summary"] = str(ai.get("generated_summary") or self._fallback_summary(profile, target_role, match["matched"])).strip()
        ai["score_reason"] = str(ai.get("score_reason") or "Score is based on resume completeness, JD keyword coverage, experience relevance, leadership fit, formatting, and recruiter readability.").strip()

        return ai

    def _openai_tailor(
        self,
        profile: ResumeProfile,
        job_description: str,
        target_role: str,
        custom_instructions: str,
        template: TemplateSettings,
        match: dict,
        breakdown: dict,
    ) -> dict:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        prompt = f'''
You are Resume Tailor Pro V5, a master-profile-based resume generation engine.

The user has a saved structured profile. This profile is the source of truth.

Strict rules:
1. Never invent experience, companies, dates, degrees, certifications, tools, numbers, or achievements.
2. Use accurate ATS words only when supported by the profile.
3. If a JD requirement is not supported, list it as missing/weak and explain how the user can truthfully fix it.
4. Follow the user's custom instructions only if they do not violate truthfulness.
5. Generate concise bullets that fit the selected template settings.
6. Optimize wording for ATS and recruiter shortlisting.
7. Return JSON only.

Target role:
{target_role or "Not specified"}

Custom instructions:
{custom_instructions or "No custom instructions provided."}

Template settings:
{template.model_dump_json(indent=2)}

Current deterministic score breakdown:
{json.dumps(breakdown, indent=2)}

Matched JD keywords:
{json.dumps(match["matched"][:40])}

Missing JD keywords:
{json.dumps(match["missing"][:40])}

Structured master profile:
{profile.model_dump_json(indent=2)}

Job description:
{job_description}
'''

        try:
            response = client.responses.create(
                model=settings.OPENAI_MODEL,
                temperature=0.15,
                max_output_tokens=5500,
                input=prompt,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "resume_tailor_v5_result",
                        "schema": RESULT_SCHEMA,
                        "strict": True,
                    }
                },
            )
            return json.loads(response.output_text)
        except TypeError:
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                temperature=0.15,
                max_tokens=5500,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a truthful ATS resume tailoring engine. Return JSON only."},
                    {"role": "user", "content": prompt},
                ],
            )
            return json.loads(response.choices[0].message.content or "{}")

    def _fallback_summary(self, profile: ResumeProfile, target_role: str, matched: list[str]) -> str:
        title = target_role or (profile.target_titles[0] if profile.target_titles else "Target Role")
        skills = ", ".join(matched[:8] or profile.technical_skills[:8])
        return f"Results-driven professional targeting {title}, with experience aligned to {skills}. Skilled in delivery support, troubleshooting, documentation, stakeholder collaboration, and operational improvement."

    def _fallback_bullets(self, matched: list[str], target_role: str) -> list[str]:
        terms = matched[:8] or ["project delivery", "technical operations", "stakeholder communication", "quality improvement"]
        return [
            f"{ACTION_WORDS[i % len(ACTION_WORDS)]} {term}-aligned responsibilities using verified experience from the master profile."
            for i, term in enumerate(terms)
        ]

    def _rule_tailor(
        self,
        profile: ResumeProfile,
        job_description: str,
        target_role: str,
        custom_instructions: str,
        template: TemplateSettings,
        match: dict,
    ) -> dict:
        matched = match["matched"]
        missing = match["missing"]
        return {
            "score_reason": "Rule-based mode uses structured profile completeness, JD keyword match, experience relevance, leadership fit, formatting, and readability. Enable OpenAI mode for deeper rewriting.",
            "generated_summary": self._fallback_summary(profile, target_role, matched),
            "generated_skills": list(dict.fromkeys((matched[:24] + profile.technical_skills[:20]))),
            "generated_bullets": self._fallback_bullets(matched, target_role),
            "matched_keywords": matched,
            "missing_keywords": missing[:18],
            "weak_requirements": missing[:12],
            "truthful_90_plus_actions": [f"Add truthful evidence, project details, or measurable impact for: {x}" for x in missing[:8]],
            "recruiter_warnings": [
                "Mock mode cannot deeply rewrite content. Set AI_PROVIDER=openai for production-quality output.",
                "Do not add unsupported tools, certifications, employers, dates, numbers, or claims.",
            ] + ([f"Custom instruction received: {custom_instructions[:160]}"] if custom_instructions else []),
        }


engine = V5TailoringEngine()
