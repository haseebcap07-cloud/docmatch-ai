# Resume Tailor Pro V8 — AI Quality Engine

V8 adds evidence-based writing, company-by-company experience rewriting, skill cleanup, assertion checks, and stronger DOCX style preservation.

## Fixes
- Summary no longer copies full JD content
- Summary is rewritten from JD priorities + uploaded resume evidence
- Technical skills cleanup removes junk tokens
- Skill category labels before colon are bolded in DOCX
- Each employer is preserved separately
- Employer name, title, dates, and order are preserved
- Generic bullets like "using verified experience from the master profile" are blocked
- Post-score now considers bullets across all employers
- Structure preservation remains ON by default

## New services
```text
app/services/resume_quality_rules.py
app/services/experience_matrix.py
app/services/assertion_engine.py
```

## Manual copy into GitHub repo
```powershell
$V8 = "S:\jd_tailoring_api_starter\resume_tailor_pro_v8_ai_quality_engine"
$OLD = "S:\jd_tailoring_api_starter\docmatch-ai"
robocopy $V8 $OLD /MIR /XD .git venv .venv __pycache__ /XF .env *.pyc *.log
```

Then:
```powershell
cd S:\jd_tailoring_api_starter\docmatch-ai
python -m py_compile app\services\resume_quality_rules.py
python -m py_compile app\services\experience_matrix.py
python -m py_compile app\services\assertion_engine.py
python -m py_compile app\services\adaptive_ai_engine.py
python -m py_compile app\services\docx_generator.py
python -m py_compile app\services\post_score_engine.py
git add .
git commit -m "Upgrade to V8 AI quality engine"
git push
```
