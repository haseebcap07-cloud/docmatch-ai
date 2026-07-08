from __future__ import annotations

from app.schemas import ResumeProfile
from app.services.ats_engine import profile_to_text


ROLE_SIGNALS = {
    "data_engineering": [
        "data engineer", "etl", "elt", "pipeline", "databricks", "spark", "pyspark", "airflow",
        "data lake", "data warehouse", "adf", "azure data factory", "snowflake", "bigquery",
    ],
    "software_engineering": [
        "software engineer", "developer", "full stack", "backend", "frontend", "react", "node",
        "java", "spring", "microservices", "api", "application",
    ],
    "network_infrastructure": [
        "network engineer", "infrastructure engineer", "network", "cisco", "lan", "wan", "vlan",
        "routing", "switching", "firewall", "vpn", "ospf", "bgp", "eigrp", "solarwinds",
    ],
    "project_leadership": [
        "project lead", "project manager", "infrastructure project", "timeline", "milestone",
        "stakeholder", "resource", "deliverables", "scope", "governance", "project economics",
    ],
    "business_analysis": [
        "business analyst", "data analyst", "requirements", "uat", "stakeholder", "dashboard",
        "reporting", "kpi", "process improvement", "business rules",
    ],
    "cybersecurity": [
        "cybersecurity", "security analyst", "incident response", "vulnerability", "siem",
        "soc", "risk", "compliance", "hardening", "zero trust", "ids", "ips",
    ],
}


def _score_text(text: str) -> dict[str, int]:
    lower = text.lower()
    scores = {}
    for role, signals in ROLE_SIGNALS.items():
        score = 0
        for signal in signals:
            if signal in lower:
                score += 3 if " " in signal else 1
        scores[role] = score
    return scores


def classify_text_role(text: str) -> dict:
    scores = _score_text(text)
    best_role = max(scores, key=scores.get)
    best_score = scores.get(best_role, 0)
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    if best_score <= 1:
        best_role = "general"

    confidence = "high" if best_score >= 8 else "medium" if best_score >= 4 else "low"
    return {
        "role_family": best_role,
        "confidence": confidence,
        "scores": scores,
        "secondary_role_family": sorted_scores[1][0] if len(sorted_scores) > 1 else "general",
    }


def classify_resume_role(profile: ResumeProfile) -> dict:
    return classify_text_role(profile_to_text(profile))


def classify_jd_role(job_description: str, target_role: str = "") -> dict:
    return classify_text_role(f"{target_role}\n{job_description}")


def alignment_label(resume_family: str, jd_family: str) -> str:
    if resume_family == jd_family:
        return "strong_same_role_family"
    if "general" in {resume_family, jd_family}:
        return "unclear_needs_more_profile_detail"

    related = {
        ("network_infrastructure", "project_leadership"),
        ("project_leadership", "network_infrastructure"),
        ("data_engineering", "business_analysis"),
        ("business_analysis", "data_engineering"),
        ("software_engineering", "data_engineering"),
        ("data_engineering", "software_engineering"),
        ("network_infrastructure", "cybersecurity"),
        ("cybersecurity", "network_infrastructure"),
    }
    if (resume_family, jd_family) in related:
        return "adjacent_role_family_reposition_resume"
    return "different_role_family_gap_detected"
