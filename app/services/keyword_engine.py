import re


COMMON_ROLE_TERMS = [
    "python", "sql", "java", "javascript", "typescript", "react", "angular", "node",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins", "git",
    "ci/cd", "rest api", "graphql", "microservices", "linux", "windows",
    "spark", "pyspark", "databricks", "snowflake", "redshift", "bigquery",
    "azure data factory", "adf", "etl", "elt", "data pipeline", "airflow",
    "dbt", "delta lake", "data lake", "data warehouse", "power bi", "tableau",
    "looker", "postgresql", "mysql", "sql server", "oracle", "mongodb",
    "machine learning", "ai", "llm", "nlp", "analytics", "dashboard",
    "agile", "scrum", "jira", "devops", "data quality", "data governance",
    "security", "api", "automation", "testing", "validation", "stakeholders",
    "requirements", "troubleshooting", "monitoring", "deployment", "cloud",
]


SHORTLIST_ACTION_WORDS = [
    "Designed", "Developed", "Implemented", "Automated", "Optimized", "Migrated",
    "Integrated", "Validated", "Analyzed", "Improved", "Reduced", "Increased",
    "Delivered", "Collaborated", "Troubleshot", "Documented", "Monitored",
    "Deployed", "Built", "Maintained", "Streamlined", "Enhanced",
]


def extract_keywords(text: str, limit: int = 80) -> list[str]:
    lowered = text.lower()
    found: list[str] = []

    for term in COMMON_ROLE_TERMS:
        if term in lowered:
            found.append(term)

    caps = re.findall(r"\b[A-Z][A-Za-z0-9+#./-]{2,}\b", text)
    for token in caps:
        if token.lower() not in [x.lower() for x in found]:
            found.append(token)

    for line in text.splitlines():
        l = line.strip()
        if len(l) > 25 and any(w in l.lower() for w in ["required", "must", "experience", "proficient", "knowledge", "skills", "responsible"]):
            words = re.findall(r"[A-Za-z][A-Za-z0-9+#./-]+", l)
            for word in words:
                lower = word.lower()
                if len(word) >= 4 and lower not in {"with", "that", "this", "from", "will", "have", "required", "experience", "skills"}:
                    if lower not in [x.lower() for x in found]:
                        found.append(word)

    return found[:limit]


def score_keywords(job_description: str, resume_text: str) -> dict:
    jd_terms = extract_keywords(job_description, 100)
    resume_lower = resume_text.lower()

    matched = [term for term in jd_terms if term.lower() in resume_lower]
    missing = [term for term in jd_terms if term.lower() not in resume_lower]

    if not jd_terms:
        score = 35
    else:
        score = round((len(matched) / len(jd_terms)) * 100)

    return {
        "score": max(0, min(100, score)),
        "matched": matched,
        "missing": missing,
        "jd_terms": jd_terms,
        "shortlist_words": SHORTLIST_ACTION_WORDS,
    }
