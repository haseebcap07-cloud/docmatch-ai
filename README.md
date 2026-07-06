# Resume Tailor Pro V3 — ATS 90+ Target Engine

This is the upgraded version focused on truthful ATS optimization.

## What this version does

- Upload DOCX, PDF, TXT, or MD resume
- Paste a job description
- Estimate ATS score
- Target 90+ alignment when truthfully possible
- Show matched must-have requirements
- Show missing keywords and weak requirements
- Generate a truthful 90+ action plan
- Rewrite summary, headline, skills, and bullets
- Download a tailored DOCX

## Important honesty rule

This app should not fake candidate experience. A 90+ score is only realistic when the resume genuinely supports the job requirements or when the candidate can truthfully add missing evidence.

## Run locally in VS Code

```powershell
cd S:\jd_tailoring_api_starter\resume_tailor_pro_v3

python -m venv venv
.\venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

copy .env.example .env
notepad .env
```

For free testing, keep:

```text
AI_PROVIDER=mock
OPENAI_API_KEY=
```

For high-quality resume tailoring, set:

```text
AI_PROVIDER=openai
OPENAI_API_KEY=your_real_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```

Run:

```powershell
python -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

## GitHub update

```powershell
git add .
git commit -m "Upgrade to Resume Tailor Pro V3 ATS 90 target"
git push
```

## Render settings

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Health check:

```text
/health
```

Environment variables on Render:

```text
AI_PROVIDER=openai
OPENAI_API_KEY=your_real_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
MAX_UPLOAD_MB=8
TARGET_ATS_SCORE=90
```
