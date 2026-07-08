from __future__ import annotations

SEMANTIC_MAP = {
    "mongodb": ["NoSQL", "document database"],
    "postgresql": ["Relational Databases", "SQL databases"],
    "mysql": ["Relational Databases", "SQL databases"],
    "sql server": ["Relational Databases", "SQL databases"],
    "oracle": ["Relational Databases", "SQL databases"],
    "jenkins": ["CI/CD", "CI/CD Pipeline"],
    "azure devops": ["CI/CD", "DevOps"],
    "github actions": ["CI/CD", "DevOps"],
    "gitlab": ["CI/CD", "DevOps"],
    "aws": ["Cloud Experience", "Cloud Platforms"],
    "azure": ["Cloud Experience", "Cloud Platforms"],
    "gcp": ["Cloud Experience", "Cloud Platforms"],
    "power bi": ["Reporting", "Dashboards", "BI"],
    "tableau": ["Reporting", "Dashboards", "BI"],
    "looker": ["Reporting", "Dashboards", "BI"],
    "cisco": ["Network Infrastructure", "Enterprise Networking"],
    "solarwinds": ["Monitoring Tools", "Infrastructure Monitoring"],
    "splunk": ["Monitoring Tools", "Log Analysis"],
    "wireshark": ["Packet Analysis", "Network Troubleshooting"],
    "jira": ["Agile Tracking", "Project Tracking"],
    "servicenow": ["ITSM", "Incident Management"],
    "active directory": ["Identity Management", "Access Management"],
}


def apply_semantic_mappings(profile_text: str, jd_terms: list[str]) -> dict:
    profile_lower = profile_text.lower()
    applied: list[str] = []
    likely_rephrasing: list[str] = []
    missing_hard: list[str] = []

    for raw_term in jd_terms:
        term = str(raw_term).strip()
        term_lower = term.lower()
        if not term or term_lower in profile_lower:
            continue

        mapped = False
        for source, categories in SEMANTIC_MAP.items():
            if source in profile_lower and any(cat.lower() == term_lower or term_lower in cat.lower() for cat in categories):
                applied.append(f"{source} → {term}")
                likely_rephrasing.append(f"{source} supports JD language '{term}'")
                mapped = True
                break
            if term_lower == source:
                for cat in categories:
                    if cat.lower() in profile_lower:
                        applied.append(f"{cat} → {term}")
                        likely_rephrasing.append(f"{cat} supports JD language '{term}'")
                        mapped = True
                        break
            if mapped:
                break
        if not mapped:
            missing_hard.append(term)

    return {
        "semantic_mappings_applied": applied[:30],
        "likely_possessed_rephrasing": likely_rephrasing[:30],
        "missing_hard_skills_not_added": missing_hard[:40],
    }
