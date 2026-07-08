from __future__ import annotations

import re

GENERIC_PHRASES = [
    "results-driven professional",
    "proven track record",
    "dynamic professional",
    "highly motivated",
    "detail-oriented",
    "team player",
    "fast-paced environment",
    "responsible for",
]


def validate_generated_resume(ai: dict, evidence_map: dict, profile_text: str) -> dict:
    warnings = []
    unsupported_terms = []
    generated_text = " ".join([
        str(ai.get("generated_summary", "")),
        " ".join(ai.get("generated_skills", []) or []),
        " ".join(ai.get("generated_bullets", []) or []),
    ]).lower()
    profile_lower = profile_text.lower()

    for term in evidence_map.get("unsupported_terms", [])[:30]:
        term_lower = term.lower()
        if term_lower in generated_text and term_lower not in profile_lower:
            unsupported_terms.append(term)

    for phrase in GENERIC_PHRASES:
        if phrase in generated_text:
            warnings.append(f"Generic phrase detected: '{phrase}'. Replace with specific evidence when possible.")

    bullets = ai.get("generated_bullets", []) or []
    if bullets:
        long_bullets = [b for b in bullets if len(str(b).split()) > 34]
        if len(long_bullets) > 3:
            warnings.append("Several generated bullets are long. Shorten them for recruiter readability.")
        weak_starts = [b for b in bullets if not re.match(r"^\s*[A-Z][a-z]+", str(b))]
        if weak_starts:
            warnings.append("Some bullets do not start with a clear action verb.")

    if unsupported_terms:
        warnings.append("Generated content may include unsupported terms: " + ", ".join(unsupported_terms[:10]))

    return {
        "validator_warnings": warnings[:12],
        "unsupported_generated_terms": unsupported_terms[:20],
        "is_safe": not unsupported_terms,
    }
