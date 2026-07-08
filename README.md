# Resume Tailor Pro V7.1 — Frontend UX Upgrade

This package keeps the V7 backend/intelligence layer and upgrades the frontend experience.

## Frontend fixes added

- Dark mode / light mode toggle
- Editor starts empty on browser refresh
- Saved profile no longer auto-loads into fields
- New "Load Saved Profile" button
- New "Clear Screen" button
- New "Clear Profile Fields" button
- New "Reset Saved Data" button
- Uploading a new file clears old extracted resume fields first
- Dropdown template settings:
  - Font family
  - Body font size
  - Heading size
  - Name size
  - Margins
  - Page target
- Professional glass-style UI
- Responsive layout
- Live word counts
- Live skills count
- Live bullet count
- Dashboard progress meters
- Improved result cards:
  - Adaptive Analysis
  - Change Log
  - Final Result
  - Recruiter Warnings
  - 90+ Action Plan
- Cleaner user-requested additions/replacements field

## Important behavior change

The page no longer does this on refresh:

```text
load previous resume into Summary / Technical Skills / Experience automatically
```

Now it starts clean. Saved profile remains in browser storage, but the user must click:

```text
Load Saved Profile
```

## Run locally

```powershell
cd S:\jd_tailoring_api_starter\resume_tailor_pro_v7_1_frontend_ux

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

## Copy into existing repo

```powershell
$V71 = "S:\jd_tailoring_api_starter\resume_tailor_pro_v7_1_frontend_ux"
$OLD = "S:\jd_tailoring_api_starter\jd_tailoring_public_app"

robocopy $V71 $OLD /MIR /XD .git venv .venv __pycache__ /XF .env *.pyc *.log
```

Then:

```powershell
cd S:\jd_tailoring_api_starter\jd_tailoring_public_app

git add .
git commit -m "Upgrade frontend UX for Resume Tailor Pro V7.1"
git push
```

Render:

```text
Manual Deploy → Deploy latest commit
```

## Note about poor preview output

If the preview says things like:

```text
using verified experience from the master profile
```

that means the backend is likely running in mock mode or fallback mode. For stronger output, set:

```text
AI_PROVIDER=openai
OPENAI_API_KEY=your_real_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```
