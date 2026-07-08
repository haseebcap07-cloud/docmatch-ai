from __future__ import annotations

import re
from app.services.generation_policy import SUMMARY_MIN_WORDS, SUMMARY_MAX_WORDS, FORBIDDEN_GENERIC_PHRASES


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def clean_summary(summary: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    output = summary.strip()
    for phrase in FORBIDDEN_GENERIC_PHRASES:
        if phrase.lower() in output.lower():
            warnings.append(f"Avoid generic phrase: {phrase}")
    count = word_count(output)
    if count < SUMMARY_MIN_WORDS:
        warnings.append(f"Summary is under {SUMMARY_MIN_WORDS} words; expand with truthful role-specific evidence.")
    elif count > SUMMARY_MAX_WORDS:
        words = output.split()
        output = " ".join(words[:SUMMARY_MAX_WORDS]).rstrip(" ,;") + "."
        warnings.append(f"Summary trimmed to {SUMMARY_MAX_WORDS} words.")
    return output, warnings
