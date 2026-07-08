from __future__ import annotations


def build_change_log(semantic_result: dict, match: dict, user_requested_additions: list[str], user_requested_replacements: list[str], evidence_map: dict, title_adjustment: str = "") -> dict:
    user_changes: list[str] = []
    for item in user_requested_additions or []:
        if str(item).strip():
            user_changes.append(f"Added per user request: {str(item).strip()}")
    for item in user_requested_replacements or []:
        if str(item).strip():
            user_changes.append(f"Replaced per user request: {str(item).strip()}")

    keyword_rephrasing = list(semantic_result.get("likely_possessed_rephrasing", [])[:20])
    for item in match.get("matched", [])[:15]:
        keyword_rephrasing.append(f"Retained/reinforced matched JD keyword: {item}")

    title_or_structure = []
    if title_adjustment:
        title_or_structure.append(title_adjustment)
    title_or_structure.append("Maintained original resume structure while applying role-specific wording.")
    title_or_structure.append("Targeted 7-8 bullets per employer/client where enough source evidence exists.")

    return {
        "semantic_mappings_applied": semantic_result.get("semantic_mappings_applied", [])[:20],
        "keyword_rephrasing": keyword_rephrasing[:30],
        "user_requested_additions_replacements": user_changes[:20],
        "unsupported_jd_skills_not_added": evidence_map.get("unsupported_terms", [])[:25],
        "title_or_structure_adjustments": title_or_structure[:10],
    }
