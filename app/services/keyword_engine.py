import re


COMMON_TECH_TERMS = [
    "python", "sql", "java", "javascript", "typescript", "react", "angular", "node",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins", "git",
    "ci/cd", "rest api", "graphql", "microservices", "linux", "windows",
    "spark", "pyspark", "databricks", "snowflake", "redshift", "bigquery",
    "azure data factory", "adf", "etl", "elt", "data pipeline", "airflow",
    "dbt", "delta lake", "data lake", "data warehouse", "power bi", "tableau",
    "looker", "postgresql", "mysql", "sql server", "oracle", "mongodb",
    "machine learning", "ai", "llm", "nlp", "analytics", "dashboard",
    "agile", "scrum", "jira", "devops", "data quality", "data governance",
    "security", "api", "automation", "testing", "validation",
]


def extract_keywords(text: str, limit: int = 60) -> list[str]:
    lowered = text.lower()
    found: list[str] = []

    for term in COMMON_TECH_TERMS:
        if term in lowered:
            found.append(term)

    caps = re.findall(r"\b[A-Z][A-Za-z0-9+#./-]{2,}\b", text)
    for token in caps:
        if token.lower() not in [x.lower() for x in found]:
            found.append(token)

    for line in text.splitlines():
        l = line.strip()
        if len(l) > 25 and any(w in l.lower() for w in ["experience", "required", "must", "proficient", "knowledge", "skills"]):
            words = re.findall(r"[A-Za-z][A-Za-z0-9+#./-]+", l)
            for w in words:
                if len(w) >= 4 and w.lower() not in {"with", "that", "this", "from", "will", "have", "required", "experience"}:
                    if w.lower() not in [x.lower() for x in found]:
                        found.append(w)

    return found[:limit]


def score_keywords(job_description: str, resume_text: str) -> dict:
    jd_terms = extract_keywords(job_description, 80)
    resume_lower = resume_text.lower()

    matched = [t for t in jd_terms if t.lower() in resume_lower]
    missing = [t for t in jd_terms if t.lower() not in resume_lower]

    score = round((len(matched) / max(1, len(jd_terms))) * 100) if jd_terms else 35

    return {
        "score": max(0, min(100, score)),
        "matched": matched,
        "missing": missing,
        "jd_terms": jd_terms,
    }
