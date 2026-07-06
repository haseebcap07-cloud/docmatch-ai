# Resume Tailor Pro V5

V5 changes the product from simple resume rewriting into a master-profile-based resume platform.

## V5 features

- Dashboard with saved master profile
- Resume upload extraction into structured sections
- Manual profile builder
- Common resume sections:
  - Contact
  - Summary
  - Technical Skills
  - Professional Experience
  - Projects
  - Education
  - Certifications
  - Interests
- Template settings:
  - Font family
  - Body font size
  - Heading font size
  - Name font size
  - Margins
  - Page limit
  - Show/hide projects
  - Show/hide certifications
  - Show/hide interests
  - Watermark on/off
- JD match scoring
- Resume-only score
- Keyword score
- Experience relevance score
- Leadership/soft-skill score
- Formatting score
- Recruiter readability score
- Final ATS estimate
- Watermarked DOCX download
- OpenAI-ready backend
- Render-ready deployment

## Important product logic

The saved master profile is the source of truth.

The system should:
1. Create or extract a structured profile.
2. Save the profile in the dashboard.
3. Compare the job description against the structured profile.
4. Generate a tailored resume using selected template settings.
5. Add accurate ATS wording only when supported by the profile.
6. Never fabricate companies, dates, skills, certifications, tools, or achievements.
7. Provide a truthful 90+ action plan when the resume cannot honestly reach 90+.

## Run locally

```powershell
cd S:\jd_tailoring_api_starter\resume_tailor_pro_v5

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

Edit `.env`:

```text
AI_PROVIDER=openai
OPENAI_API_KEY=your_real_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```

For free local testing:

```text
AI_PROVIDER=mock
OPENAI_API_KEY=
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

Health check path:

```text
/health
```

## Current limitation

The dashboard saves to browser localStorage for the MVP.
For a real production product, add:
- User login
- PostgreSQL database
- Cloud file storage
- Background jobs
- Payment system
- Watermark removal for premium users
- File expiration/deletion
- Audit and security controls
