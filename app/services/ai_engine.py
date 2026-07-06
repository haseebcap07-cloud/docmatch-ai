from __future__ import annotations

import json
from typing import Any

from app.core.config import settings
from app.services.keyword_engine import score_keywords, SHORTLIST_ACTION_WORDS


RESULT_KEYS = [
    "job_title_guess",
    "score_reason",
    "matched_must_haves",
    "matched_keywords",
    "missing_keywords",
    "weak_requirements",
    "truthful_90_plus_actions",
    "recruiter_warnings",
    "optimized_headline",
    "optimized_summary",
    "optimized_skills",
    "optimized_bullets",
    "role_shortlist_words",
    "project_suggestions",
    "interview_pitch",
    "final_resume_text",
]

RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "job_title_guess": {"type": "string"},
        "score_reason": {"type": "string"},
        "matched_must_haves": {"type": "array", "items": {"type": "string"}},
        "matched_keywords": {"type": "array", "items": {"type": "string"}},
        "missing_keywords": {"type": "array", "items": {"type": "string"}},
        "weak_requirements": {"type": "array", "items": {"type": "string"}},
        "truthful_90_plus_actions": {"type": "array", "items": {"type": "string"}},
        "recruiter_warnings": {"type": "array", "items": {"type": "string"}},
        "optimized_headline": {"type": "string"},
        "optimized_summary": {"type": "string"},
        "optimized_skills": {"type": "array", "items": {"type": "string"}},
        "optimized_bullets": {"type": "array", "items": {"type": "string"}},
        "role_shortlist_words": {"type": "array", "items": {"type": "string"}},
        "project_suggestions": {"type": "array", "items": {"type": "string"}},
        "interview_pitch": {"type": "string"},
        "final_resume_text": {"type": "string"},
    },
    "required": RESULT_KEYS,
}


def _safe_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return []


def build_final_resume_text(result: dict[str, Any]) -> str:
    skills = ", ".join(result.get("optimized_skills", [])) or "Add role-specific skills here"
    bullets = "\n".join(f"- {b}" for b in result.get("optimized_bullets", []))
    projects = "\n".join(f"- {p}" for p in result.get("project_suggestions", []))
    matched = ", ".join(result.get("matched_keywords", [])) or "No strong matches found yet"
    gaps = "\n".join(f"- {g}" for g in result.get("weak_requirements", []))
    actions = "\n".join(f"- {a}" for a in result.get("truthful_90_plus_actions", []))
    warnings = "\n".join(f"- {w}" for w in result.get("recruiter_warnings", []))

    return f"""ATS SCORE REPORT
Before score: {result.get('ats_score_before', 0)}/100
After score: {result.get('ats_score_after', 0)}/100
Target score: {result.get('target_score', 90)}+
Gap to target: {result.get('score_gap_to_90', 0)} points
Reason: {result.get('score_reason', '')}

TARGET ROLE
{result.get('job_title_guess', 'Target Role')}

OPTIMIZED HEADLINE
{result.get('optimized_headline', '')}

PROFESSIONAL SUMMARY
{result.get('optimized_summary', '')}

CORE SKILLS
{skills}

TAILORED EXPERIENCE
{bullets}

PROJECTS TO HIGHLIGHT
{projects}

REQUIREMENTS MATCHED
{matched}

GAPS TO FIX FOR 90+
{gaps}

TRUTHFUL 90+ ACTION PLAN
{actions}

RECRUITER WARNINGS
{warnings}

INTERVIEW PITCH
{result.get('interview_pitch', '')}
"""


def normalize_result(data: dict[str, Any], job_description: str, resume_text: str, target_role: str | None, profile: dict) -> dict[str, Any]:
    before = score_keywords(job_description, resume_text)
    before_score = before["score"]

    matched = _safe_list(data.get("matched_keywords")) or before["matched"]
    missing = _safe_list(data.get("missing_keywords")) or before["missing"][:18]

    keyword_ratio = len(matched) / max(1, len(before["jd_terms"]))
    after_score = min(98, round(before_score + 18 + (keyword_ratio * 12)))

    if keyword_ratio < 0.55:
        after_score = min(after_score, 72)
    elif keyword_ratio < 0.70:
        after_score = min(after_score, 82)
    elif keyword_ratio < 0.82:
        after_score = min(after_score, 89)

    after_score = max(before_score, min(100, after_score))
    gap = max(0, settings.TARGET_ATS_SCORE - after_score)

    result = {
        "ats_score_before": before_score,
        "ats_score_after": after_score,
        "target_score": settings.TARGET_ATS_SCORE,
        "score_gap_to_90": gap,
        "score_reason": str(data.get("score_reason") or "Score compares JD keywords, must-have alignment, layout readability, and truthful resume coverage.").strip(),
        "job_title_guess": str(data.get("job_title_guess") or target_role or "Target Role").strip(),
        "resume_profile": profile,
        "matched_must_haves": _safe_list(data.get("matched_must_haves")) or matched[:10],
        "matched_keywords": matched,
        "missing_keywords": missing,
        "weak_requirements": _safe_list(data.get("weak_requirements")) or missing[:12],
        "truthful_90_plus_actions": _safe_list(data.get("truthful_90_plus_actions")) or [f"Add real project evidence for {x}" for x in missing[:8]],
        "recruiter_warnings": _safe_list(data.get("recruiter_warnings")) or [
            "Do not add any skill, tool, certification, employer, or achievement unless it is true.",
            "Review all AI-written content before submitting.",
        ],
        "optimized_headline": str(data.get("optimized_headline") or "").strip(),
        "optimized_summary": str(data.get("optimized_summary") or "").strip(),
        "optimized_skills": _safe_list(data.get("optimized_skills")) or matched[:18],
        "optimized_bullets": _safe_list(data.get("optimized_bullets")),
        "role_shortlist_words": _safe_list(data.get("role_shortlist_words")) or SHORTLIST_ACTION_WORDS[:14],
        "project_suggestions": _safe_list(data.get("project_suggestions")),
        "interview_pitch": str(data.get("interview_pitch") or "").strip(),
        "final_resume_text": str(data.get("final_resume_text") or "").strip(),
    }

    if not result["optimized_summary"]:
        result["optimized_summary"] = (
            f"Results-driven professional targeting {result['job_title_guess']}, with experience aligned to "
            f"{', '.join(matched[:8]) if matched else 'the target role requirements'}."
        )

    if not result["optimized_headline"]:
        result["optimized_headline"] = f"{result['job_title_guess']} | {', '.join(result['optimized_skills'][:5])}"

    if not result["optimized_bullets"]:
        result["optimized_bullets"] = [
            f"{SHORTLIST_ACTION_WORDS[i % len(SHORTLIST_ACTION_WORDS)]} work aligned with {term} using supported experience from the uploaded resume."
            for i, term in enumerate((matched or before["jd_terms"])[:8])
        ]

    if not result["project_suggestions"]:
        result["project_suggestions"] = [f"Highlight a truthful project proving {x}" for x in missing[:5]]

    if not result["interview_pitch"]:
        result["interview_pitch"] = f"My background aligns with {result['job_title_guess']} through {', '.join(matched[:6])}."

    if not result["final_resume_text"]:
        result["final_resume_text"] = build_final_resume_text(result)

    return result


class ResumeIntelligenceEngine:
    def tailor(self, job_description: str, resume_text: str, target_role: str | None, profile: dict) -> dict[str, Any]:
        provider = (settings.AI_PROVIDER or "mock").lower().strip()
        if provider == "openai" and settings.OPENAI_API_KEY:
            try:
                return self._tailor_with_openai(job_description, resume_text, target_role, profile)
            except Exception as exc:
                fallback = self._tailor_with_rules(job_description, resume_text, target_role, profile)
                fallback["recruiter_warnings"].insert(0, f"OpenAI failed; rule-based fallback used: {str(exc)[:180]}")
                return fallback
        return self._tailor_with_rules(job_description, resume_text, target_role, profile)

    def _tailor_with_openai(self, job_description: str, resume_text: str, target_role: str | None, profile: dict) -> dict[str, Any]:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        prompt = f"""
You are Resume Tailor Pro V4, a resume intelligence and ATS optimization engine.

Goal:
Improve truthful resume alignment for a target job while preserving the candidate's original resume structure. Target 90+ only when the real resume supports it.

Strict rules:
1. Never fabricate experience, tools, employers, dates, degrees, certifications, numbers, or achievements.
2. If a requirement is not supported, put it in missing/weak requirements and truthful action plan.
3. Write only content that can be supported by the uploaded resume.
4. Optimize for recruiter shortlisting words, ATS keywords, and clean professional wording.
5. Preserve the user's section structure conceptually: headline/summary/skills/experience/projects.
6. Output concise bullets that fit existing resume space.
7. Return JSON only using the requested keys.

Target role:
{target_role or "Not specified"}

Detected resume profile:
{json.dumps(profile, indent=2)}

Job description:
{job_description}

Uploaded resume text:
{resume_text}
"""

        try:
            response = client.responses.create(
                model=settings.OPENAI_MODEL,
                input=prompt,
                temperature=0.15,
                max_output_tokens=5500,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "resume_tailor_v4_result",
                        "schema": RESULT_SCHEMA,
                        "strict": True,
                    }
                },
            )
            data = json.loads(response.output_text)
            return normalize_result(data, job_description, resume_text, target_role, profile)
        except TypeError:
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                temperature=0.15,
                max_tokens=5500,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "You are a resume intelligence and ATS optimization engine. Return valid JSON only. Never fabricate experience."
                    },
                    {
                        "role": "user",
                        "content": prompt + "\nReturn JSON with these keys: " + ", ".join(RESULT_KEYS)
                    }
                ],
            )
            raw = response.choices[0].message.content or "{}"
            data = json.loads(raw)
            return normalize_result(data, job_description, resume_text, target_role, profile)

    def _tailor_with_rules(self, job_description: str, resume_text: str, target_role: str | None, profile: dict) -> dict[str, Any]:
        base = score_keywords(job_description, resume_text)
        matched = base["matched"]
        missing = base["missing"][:18]
        after = min(86, base["score"] + 16)

        data = {
            "score_reason": "Rule-based mode uses keyword overlap and resume structure. Use OpenAI mode for stronger semantic tailoring.",
            "job_title_guess": target_role or "Target Role",
            "matched_must_haves": matched[:10],
            "matched_keywords": matched,
            "missing_keywords": missing,
            "weak_requirements": missing[:12],
            "truthful_90_plus_actions": [f"Add truthful project evidence for {x}" for x in missing[:8]],
            "recruiter_warnings": [
                "Mock mode cannot deeply understand resume context. Enable OpenAI mode for production-quality tailoring.",
                "Do not add tools or accomplishments unless they are true.",
            ],
            "optimized_headline": f"{target_role or 'Target Role'} | {', '.join(matched[:5])}",
            "optimized_summary": f"Results-driven professional aligned with {target_role or 'the target role'}, with experience connected to {', '.join(matched[:8]) if matched else 'the job requirements'}.",
            "optimized_skills": matched[:18],
            "optimized_bullets": [
                f"{SHORTLIST_ACTION_WORDS[i % len(SHORTLIST_ACTION_WORDS)]} {term}-aligned work using supported experience from the uploaded resume."
                for i, term in enumerate((matched or base["jd_terms"])[:8])
            ],
            "role_shortlist_words": SHORTLIST_ACTION_WORDS[:14],
            "project_suggestions": [f"Highlight a project proving {x}" for x in missing[:5]],
            "interview_pitch": f"My background aligns with {target_role or 'this role'} through {', '.join(matched[:6])}.",
            "final_resume_text": "",
        }

        result = normalize_result(data, job_description, resume_text, target_role, profile)
        result["ats_score_after"] = max(result["ats_score_before"], after)
        result["score_gap_to_90"] = max(0, settings.TARGET_ATS_SCORE - result["ats_score_after"])
        result["final_resume_text"] = build_final_resume_text(result)
        return result


engine = ResumeIntelligenceEngine()
