# Resume Tailor Pro V7.2 — Structure Preservation Mode

This version adds a structure/length preservation layer.

## What it fixes

When a user uploads a resume, the generated output should preserve the uploaded resume's:

- section order
- employer/client order
- bullet counts where detected
- project order
- education order
- approximate page count
- approximate length
- Environment lines if present

## New frontend controls

Template Settings now includes:

```text
Preserve uploaded structure
Match original length
```

Both are ON by default.

## Important PDF vs DOCX note

PDF uploads can preserve extracted text structure and approximate length.

For truly exact editable formatting, DOCX uploads are the best input because DOCX contains editable layout, style, font, spacing, and XML structure. PDF extraction does not reliably preserve all formatting metadata.

## Copy into current repo

```powershell
$V72 = "S:\jd_tailoring_api_starter\resume_tailor_pro_v7_2_structure_preserve"
$OLD = "S:\jd_tailoring_api_starter\jd_tailoring_public_app"

robocopy $V72 $OLD /MIR /XD .git venv .venv __pycache__ /XF .env *.pyc *.log
```

Then:

```powershell
cd S:\jd_tailoring_api_starter\jd_tailoring_public_app

python -m py_compile app\services\layout_analyzer.py
python -m py_compile app\services\profile_parser.py
python -m py_compile app\services\adaptive_ai_engine.py

git add .
git commit -m "Add V7.2 structure preservation mode"
git push
```

Render:

```text
Manual Deploy → Deploy latest commit
```
