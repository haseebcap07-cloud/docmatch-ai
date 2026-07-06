# Resume Tailor Pro V4 — Resume Intelligence + DOCX Layout Preservation

V4 upgrades the product from a plain resume text generator to a resume-intelligence platform.

## What V4 adds

- Resume structure detection
- DOCX font and font-size detection
- DOCX margin detection
- Estimated page count
- Detected section list
- Before/after ATS score
- Role-shortlisting word engine
- Truthful 90+ action plan
- DOCX in-place layout preservation mode
- Clean fallback DOCX for PDF/TXT/MD uploads

## Important

For best layout preservation, upload DOCX.

V4 copies the original DOCX package and edits targeted text in `word/document.xml`.
This preserves most original styles, margins, headers, footers, borders, images, and layout metadata.
It cannot guarantee perfect Word pagination because exact page rendering depends on Microsoft Word, installed fonts, and the user's system.

## Run locally

```powershell
cd S:\jd_tailoring_api_starter\resume_tailor_pro_v4

python -m venv venv
.\venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

copy .env.example .env
notepad .env
```

For free local testing:

```text
AI_PROVIDER=mock
OPENAI_API_KEY=
```

For real tailoring:

```text
AI_PROVIDER=openai
OPENAI_API_KEY=your_real_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
PRESERVE_DOCX_LAYOUT=true
```

Run:

```powershell
python -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## Push to GitHub

```powershell
git add .
git commit -m "Upgrade to Resume Tailor Pro V4 layout preservation"
git push
```

## Render environment variables

```text
AI_PROVIDER=openai
OPENAI_API_KEY=your_real_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
MAX_UPLOAD_MB=10
TARGET_ATS_SCORE=90
PRESERVE_DOCX_LAYOUT=true
```

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

## Production roadmap after V4

- User accounts
- Resume history
- Database and object storage
- Background job queue
- File scanning
- Auto-delete uploaded files
- Country-specific resume formats
- Multi-language resumes
- Payment system
- Analytics and monitoring
