# Resume Tailor Pro V7 All-in-One

This package includes the full V6 Adaptive Engine plus the new V7 ATS Recruiter Workflow Engine.

## Included from V6

- Resume role classification
- Job description role classification
- Role-family alignment detection
- Role-specific playbooks
- JD must-have analyzer
- Evidence mapping
- Unsupported requirement detection
- Adaptive AI prompt engine
- Human-tone validator
- Generic AI phrase warnings
- Truth caps for ATS score

## New in V7

- Baseline ATS score before generation
- Gap analysis split into missing hard skills, semantic gaps, and unsupported requirements
- Semantic mapping, such as MongoDB → NoSQL, PostgreSQL → Relational Databases, Jenkins → CI/CD, AWS/Azure/GCP → Cloud Experience
- Summary rules with 110-120 word target and no generic filler phrases
- Bullet-count target of 7-8 bullets per employer/client where enough source evidence exists
- Change Log for semantic mappings, keyword rephrasing, user-requested additions/replacements, unsupported JD skills not added, and title/structure adjustments
- Post-optimization ATS score and score improvement summary
- User-requested additions field in the UI

## Run locally

```powershell
cd S:\jd_tailoring_api_starter\resume_tailor_pro_v7_all_in_one

python -m venv venv
.\venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

copy .env.example .env
python -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## Enable real AI

```text
AI_PROVIDER=openai
OPENAI_API_KEY=your_real_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```

## Deploy to Render

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Environment variables:

```text
AI_PROVIDER=openai
OPENAI_API_KEY=your_real_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
MAX_UPLOAD_MB=10
TARGET_ATS_SCORE=90
FREE_DOWNLOAD_WATERMARK=true
```

## Copy into existing repo

```powershell
$V7 = "S:\jd_tailoring_api_starter\resume_tailor_pro_v7_all_in_one"
$OLD = "S:\jd_tailoring_api_starter\jd_tailoring_public_app"

robocopy $V7 $OLD /MIR /XD .git venv .venv __pycache__ /XF .env *.pyc *.log
```

Then:

```powershell
cd S:\jd_tailoring_api_starter\jd_tailoring_public_app

python -m py_compile app\services\adaptive_ai_engine.py
python -m py_compile app\services\ats_engine.py
python -m py_compile app\services\evidence_mapper.py
python -m py_compile app\services\semantic_mapper.py
python -m py_compile app\services\change_log_builder.py

git add .
git commit -m "Upgrade to Resume Tailor Pro V7 all-in-one ATS recruiter workflow"
git push
```

Then Render:

```text
Manual Deploy → Deploy latest commit
```
