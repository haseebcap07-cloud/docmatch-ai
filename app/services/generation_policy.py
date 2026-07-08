SUMMARY_MIN_WORDS = 110
SUMMARY_MAX_WORDS = 120
MIN_BULLETS_PER_EMPLOYER = 7
MAX_BULLETS_PER_EMPLOYER = 8

FORBIDDEN_GENERIC_PHRASES = [
    "team player", "fast learner", "passionate", "detail-oriented", "highly motivated",
    "results-driven professional", "proven track record", "dynamic professional",
]

GENERATION_POLICY = {
    "role": "Expert ATS optimization specialist and technical recruiter",
    "goal": "Improve ATS compatibility to 85-90 when truthfully possible while preserving actual experience.",
    "summary_min_words": SUMMARY_MIN_WORDS,
    "summary_max_words": SUMMARY_MAX_WORDS,
    "min_bullets_per_employer": MIN_BULLETS_PER_EMPLOYER,
    "max_bullets_per_employer": MAX_BULLETS_PER_EMPLOYER,
    "default_no_fabrication": True,
    "semantic_mapping_allowed": True,
    "user_requested_override_allowed": True,
}
