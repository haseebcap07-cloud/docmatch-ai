from app.services.jd_parser import extract_keywords, split_bullets


ACTION_VERBS = [
    "Designed",
    "Developed",
    "Automated",
    "Optimized",
    "Implemented",
    "Validated",
    "Integrated",
    "Improved",
]


def _top_keywords(job_description: str, limit: int = 18) -> list[str]:
    keywords = extract_keywords(job_description)
    return keywords[:limit]


class AIProvider:
    def extract_jd(self, job_description: str) -> dict:
        keywords = _top_keywords(job_description, 25)
        bullets = split_bullets(job_description)

        return {
            "title_guess": "Role extracted from job description",
            "seniority_guess": "Mid-level or role-specific",
            "required_skills": keywords[:12],
            "preferred_skills": keywords[12:20],
            "responsibilities": bullets[:8],
            "keywords": keywords,
            "ats_focus_areas": [
                "Match core technical skills from the job description",
                "Use measurable achievements where possible",
                "Include role-specific keywords naturally",
                "Keep formatting clean and ATS-readable",
            ],
        }

    def rephrase(self, text: str, tone: str = "professional") -> str:
        cleaned = " ".join(text.split())
        return cleaned

    def tailor_document(
        self,
        job_description: str,
        document_text: str,
        target_role: str | None = None,
    ) -> dict:
        jd_keywords = _top_keywords(job_description, 25)
        doc_lower = document_text.lower()

        matched = [
            keyword for keyword in jd_keywords
            if keyword.lower() in doc_lower
        ]

        missing = [
            keyword for keyword in jd_keywords
            if keyword.lower() not in doc_lower
        ][:12]

        role = target_role or "target role"
        keyword_phrase = ", ".join(jd_keywords[:8]) if jd_keywords else "role-specific requirements"

        tailored_summary = (
            f"Results-driven professional aligned with the {role} position, "
            f"bringing hands-on experience across {keyword_phrase}. Skilled in translating job requirements "
            f"into practical execution, improving document quality, and presenting experience in an ATS-friendly format."
        )

        tailored_bullets = []
        source_lines = [line.strip(" -•\t") for line in document_text.splitlines() if len(line.strip()) > 12]

        for index, keyword in enumerate(jd_keywords[:8]):
            verb = ACTION_VERBS[index % len(ACTION_VERBS)]
            if source_lines:
                base_line = source_lines[index % len(source_lines)]
                tailored_bullets.append(
                    f"{verb} work aligned with {keyword}, based on prior experience: {base_line}"
                )
            else:
                tailored_bullets.append(
                    f"{verb} responsibilities aligned with {keyword} to support the requirements of the {role}."
                )

        if not tailored_bullets:
            tailored_bullets = [
                "Developed role-aligned experience statements using the target job description requirements.",
                "Improved document structure to support ATS readability and recruiter review.",
            ]

        final_document_text = build_final_document_text(
            tailored_summary=tailored_summary,
            tailored_bullets=tailored_bullets,
            matched_keywords=matched,
            missing_keywords=missing,
            original_text=document_text,
        )

        return {
            "tailored_summary": tailored_summary,
            "tailored_bullets": tailored_bullets,
            "missing_keywords": missing,
            "ats_recommendations": [
                "Add missing keywords only when they truthfully match your real experience.",
                "Use measurable achievements such as volume, speed, cost, accuracy, or time saved.",
                "Keep section headings simple: Summary, Skills, Experience, Education.",
                "Avoid tables, images, text boxes, and heavy columns for ATS uploads.",
            ],
            "final_document_text": final_document_text,
        }

    def format_document(self, document_text: str, format_style: str = "resume") -> dict:
        cleaned_lines = [line.strip() for line in document_text.splitlines() if line.strip()]
        formatted = "\n".join(cleaned_lines)

        return {
            "format_style": format_style,
            "formatted_text": formatted,
            "recommendations": [
                "Use consistent spacing.",
                "Use simple headings.",
                "Keep bullet points concise.",
                "Place most relevant skills near the top.",
            ],
        }


def build_final_document_text(
    tailored_summary: str,
    tailored_bullets: list[str],
    matched_keywords: list[str],
    missing_keywords: list[str],
    original_text: str,
) -> str:
    matched_text = ", ".join(matched_keywords) if matched_keywords else "No direct keyword matches found yet."
    missing_text = ", ".join(missing_keywords) if missing_keywords else "No major missing keywords detected."
    bullet_text = "\n".join(f"- {bullet}" for bullet in tailored_bullets)

    return f'''PROFESSIONAL SUMMARY
{tailored_summary}

CORE SKILLS
{matched_text}

TAILORED EXPERIENCE
{bullet_text}

ATS REQUIREMENTS MATCHED
Matched keywords: {matched_text}
Suggested truthful additions: {missing_text}

RECOMMENDATIONS
- Review every generated line before applying.
- Keep only the skills and tools you truly used.
- Add numbers/results where possible.
- Save final version as DOCX and PDF depending on the job portal.

ORIGINAL DOCUMENT CONTENT
{original_text}
'''


ai_provider = AIProvider()
