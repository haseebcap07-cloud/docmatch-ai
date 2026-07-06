from __future__ import annotations

import json
from typing import Any

from app.core.config import settings
from app.services.keyword_engine import score_keywords, extract_keywords


RESULT_KEYS = [
    "ats_score", "score_reason", "job_title_guess", "matched_must_haves",
    "matched_keywords", "missing_keywords", "weak_requirements",
    "truthful_90_plus_actions", "recruiter_warnings", "optimized_headline",
    "optimized_summary", "optimized_skills", "optimized_bullets",
    "project_suggestions", "interview_pitch", "final_resume_text"
]

RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "ats_score": {"type": "integer"},
        "score_reason": {"type": "string"},
        "job_title_guess": {"type": "string"},
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
        "project_suggestions": {"type": "array", "items": {"type": "string"}},
        "interview_pitch": {"type": "string"},
        "final_resume_text": {"type": "string"},
    },
    "required": RESULT_KEYS,
}


def safe_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return []


def normalize_result(data: dict[str, Any], job_description: str, resume_text: str, target_role: str | None) -> dict[str, Any]:
    base = score_keywords(job_description, resume_text)

    try:
        ats = int(data.get("ats_score", base["score"]))
    except Exception:
        ats = base["score"]

    missing_count = len(base["missing"])
    jd_count = max(1, len(base["jd_terms"]))
    keyword_ratio = len(base["matched"]) / jd_count

    # Guardrail: do not allow a fake 90 if many obvious JD keywords are missing.
    if keyword_ratio < 0.55:
        ats = min(ats, 72)
    elif keyword_ratio < 0.70:
        ats = min(ats, 82)
    elif keyword_ratio < 0.82:
        ats = min(ats, 89)

    ats = max(0, min(100, ats))
    gap = max(0, settings.TARGET_ATS_SCORE - ats)

    result = {
        "ats_score": ats,
        "target_score": settings.TARGET_ATS_SCORE,
        "score_gap_to_90": gap,
        "score_reason": str(data.get("score_reason") or "Score is based on keyword coverage, requirement alignment, specificity, and recruiter readability.").strip(),
        "job_title_guess": str(data.get("job_title_guess") or target_role or "Target Role").strip(),
        "matched_must_haves": safe_list(data.get("matched_must_haves")) or base["matched"][:10],
        "matched_keywords": safe_list(data.get("matched_keywords")) or base["matched"],
        "missing_keywords": safe_list(data.get("missing_keywords")) or base["missing"][:15],
        "weak_requirements": safe_list(data.get("weak_requirements")) or base["missing"][:10],
        "truthful_90_plus_actions": safe_list(data.get("truthful_90_plus_actions")),
        "recruiter_warnings": safe_list(data.get("recruiter_warnings")),
        "optimized_headline": str(data.get("optimized_headline") or "").strip(),
        "optimized_summary": str(data.get("optimized_summary") or "").strip(),
        "optimized_skills": safe_list(data.get("optimized_skills")),
        "optimized_bullets": safe_list(data.get("optimized_bullets")),
        "project_suggestions": safe_list(data.get("project_suggestions")),
        "interview_pitch": str(data.get("interview_pitch") or "").strip(),
        "final_resume_text": str(data.get("final_resume_text") or "").strip(),
    }

    if not result["truthful_90_plus_actions"]:
        result["truthful_90_plus_actions"] = [
            f"Add truthful project evidence for: {item}" for item in result["missing_keywords"][:8]
        ] or ["Resume is close to target. Add measurable impact numbers where possible."]

    if not result["recruiter_warnings"]:
        result["recruiter_warnings"] = [
            "Do not add any tool, certification, employer, or accomplishment unless it is true.",
            "Review all AI-written bullets before using them.",
        ]

    if not result["final_resume_text"]:
        result["final_resume_text"] = build_final_resume_text(result)

    return result


class ResumeTailorEngine:
    def tailor(self, job_description: str, resume_text: str, target_role: str | None = None) -> dict[str, Any]:
        provider = (settings.AI_PROVIDER or "mock").lower().strip()

        if provider == "openai" and settings.OPENAI_API_KEY:
            try:
                return self._tailor_with_openai(job_description, resume_text, target_role)
            except Exception as exc:
                fallback = self._tailor_with_rules(job_description, resume_text, target_role)
                fallback["recruiter_warnings"].insert(0, f"OpenAI failed; rule-based fallback used: {str(exc)[:180]}")
                return fallback

        return self._tailor_with_rules(job_description, resume_text, target_role)

    def _tailor_with_openai(self, job_description: str, resume_text: str, target_role: str | None) -> dict[str, Any]:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        prompt = f"""
You are Resume Tailor Pro, an expert ATS resume optimization engine.

Goal:
Create the strongest truthful resume tailoring possible for the job. Target score is {settings.TARGET_ATS_SCORE}+ only when the resume genuinely supports it.

Strict rules:
1. Never fabricate experience, employers, dates, degrees, certifications, tools, numbers, or achievements.
2. If a requirement is not supported, list it as weak/missing and explain how the candidate can truthfully fix it.
3. Rewrite supported resume content to match the job description using ATS-friendly wording.
4. Prioritize must-have requirements over nice-to-have requirements.
5. Use strong action verbs, measurable impact language, and job-specific keywords.
6. Keep the final resume text clean, simple, and ATS-readable.
7. Do not promise interviews or job offers.
8. Return JSON only.

Target role entered by user:
{target_role or "Not specified"}

Job description:
{job_description}

Candidate resume/document:
{resume_text}
"""

        try:
            response = client.responses.create(
                model=settings.OPENAI_MODEL,
                input=prompt,
                temperature=0.15,
                max_output_tokens=5000,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "resume_tailor_result",
                        "schema": RESULT_SCHEMA,
                        "strict": True,
                    }
                },
            )
            raw = response.output_text
            data = json.loads(raw)
            return normalize_result(data, job_description, resume_text, target_role)
        except TypeError:
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                temperature=0.15,
                max_tokens=5000,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "You are an ATS resume optimization engine. Return valid JSON only. Never fabricate candidate experience."
                    },
                    {
                        "role": "user",
                        "content": prompt + "\\nReturn JSON with these exact keys: " + ", ".join(RESULT_KEYS)
                    },
                ],
            )
            raw = response.choices[0].message.content or "{}"
            data = json.loads(raw)
            return normalize_result(data, job_description, resume_text, target_role)

    def _tailor_with_rules(self, job_description: str, resume_text: str, target_role: str | None) -> dict[str, Any]:
        base = score_keywords(job_description, resume_text)
        score = min(base["score"], 86)

        role = target_role or "Target Role"
        jd_terms = extract_keywords(job_description, 40)

        optimized_skills = base["matched"][:18] or jd_terms[:10]

        summary = (
            f"Results-driven professional targeting {role}, with experience aligned to "
            f"{', '.join(base['matched'][:8]) if base['matched'] else 'the role requirements'}. "
            f"Skilled at translating business needs into practical execution and presenting experience in an ATS-friendly format."
        )

        bullets = []
        resume_lines = [line.strip(" -•\\t") for line in resume_text.splitlines() if len(line.strip()) > 20]
        action_verbs = ["Designed", "Developed", "Improved", "Automated", "Supported", "Validated", "Optimized", "Implemented"]
        for i, term in enumerate((base["matched"] or jd_terms)[:8]):
            source = resume_lines[i % len(resume_lines)] if resume_lines else f"experience related to {term}"
            bullets.append(f"{action_verbs[i % len(action_verbs)]} {term}-aligned work by strengthening this supported experience: {source}")

        result = {
            "ats_score": score,
            "target_score": settings.TARGET_ATS_SCORE,
            "score_gap_to_90": max(0, settings.TARGET_ATS_SCORE - score),
            "score_reason": "Rule-based score from keyword overlap. Use OpenAI mode for deeper requirement analysis and stronger rewriting.",
            "job_title_guess": role,
            "matched_must_haves": base["matched"][:10],
            "matched_keywords": base["matched"],
            "missing_keywords": base["missing"][:15],
            "weak_requirements": base["missing"][:10],
            "truthful_90_plus_actions": [f"Add real resume evidence for {x}" for x in base["missing"][:8]],
            "recruiter_warnings": [
                "This is mock/rule-based mode. Add OpenAI API key for stronger tailoring.",
                "Do not add tools or claims unless they are true.",
            ],
            "optimized_headline": f"{role} Candidate | {', '.join(optimized_skills[:5])}",
            "optimized_summary": summary,
            "optimized_skills": optimized_skills,
            "optimized_bullets": bullets,
            "project_suggestions": [f"Highlight a project proving {x}" for x in base["missing"][:5]],
            "interview_pitch": f"My background aligns with {role} through {', '.join(base['matched'][:6])}.",
            "final_resume_text": "",
        }
        result["final_resume_text"] = build_final_resume_text(result)
        return result


def build_final_resume_text(result: dict[str, Any]) -> str:
    skills = ", ".join(result.get("optimized_skills", [])) or "Add role-specific skills here"
    bullets = "\\n".join(f"- {b}" for b in result.get("optimized_bullets", []))
    projects = "\\n".join(f"- {p}" for p in result.get("project_suggestions", []))
    matched = ", ".join(result.get("matched_keywords", [])) or "No strong matches found yet"
    gaps = "\\n".join(f"- {g}" for g in result.get("weak_requirements", []))
    actions = "\\n".join(f"- {a}" for a in result.get("truthful_90_plus_actions", []))
    warnings = "\\n".join(f"- {w}" for w in result.get("recruiter_warnings", []))

    return f"""ATS TARGET SCORE
Current estimated score: {result.get('ats_score', 0)}/100
Target score: {result.get('target_score', 90)}+
Gap to target: {result.get('score_gap_to_90', 0)} points
Reason: {result.get('score_reason', '')}

JOB TARGET
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


engine = ResumeTailorEngine()
