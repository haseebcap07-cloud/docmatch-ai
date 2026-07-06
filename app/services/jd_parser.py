import re


TECH_KEYWORDS = [
    "python", "sql", "java", "javascript", "react", "node", "fastapi",
    "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd",
    "databricks", "spark", "pyspark", "etl", "data pipeline",
    "api", "rest", "postgresql", "mysql", "mongodb", "power bi",
    "tableau", "machine learning", "ai", "llm"
]


def extract_keywords(text: str) -> list[str]:
    lowered = text.lower()
    found = []

    for keyword in TECH_KEYWORDS:
        if keyword in lowered:
            found.append(keyword)

    # Capture common capitalized tools/terms.
    capitalized_terms = re.findall(r"\b[A-Z][A-Za-z0-9+#.\-]{2,}\b", text)
    for term in capitalized_terms:
        normalized = term.strip()
        if normalized.lower() not in [item.lower() for item in found]:
            found.append(normalized)

    return sorted(set(found), key=lambda x: x.lower())


def split_bullets(text: str) -> list[str]:
    lines = [line.strip(" -•\t") for line in text.splitlines() if line.strip()]
    useful = [line for line in lines if len(line) > 25]
    return useful[:12]
