# Resume Tailor Pro V8.1 — Document Structure Engine

V8.1 adds a dedicated document-structure layer so the app stops generating a generic resume layout from scratch.

## New engines

```text
app/services/document_router.py
app/services/docx_structure_extractor.py
app/services/pdf_layout_extractor.py
app/services/layout_blueprint.py
app/services/structure_confidence_scorer.py
app/services/docx_style_preserver.py
app/services/section_replacement_engine.py
```

## What it fixes

```text
DOCX upload: extracts paragraph order, bullets, sections, employer blocks, margins, fonts, tables, images.
PDF upload: uses PyMuPDF first for blocks/fonts/pages and falls back to pypdf.
Structure assertions: employer count, certifications, section order, page target, and bullet density are checked.
Style preservation: template settings inherit source margins, dominant font, font size, heading size, and page count.
```

## Manual push

```powershell
$V81 = "S:\jd_tailoring_api_starteresume_tailor_pro_v8_1_document_structure_engine"
$OLD = "S:\jd_tailoring_api_starter\docmatch-ai"

robocopy $V81 $OLD /MIR /XD .git venv .venv __pycache__ /XF .env *.pyc *.log
```

Then:

```powershell
cd S:\jd_tailoring_api_starter\docmatch-ai

python -m py_compile app\services\document_router.py
python -m py_compile app\services\docx_structure_extractor.py
python -m py_compile app\services\pdf_layout_extractor.py
python -m py_compile app\services\layout_blueprint.py
python -m py_compile app\services\structure_confidence_scorer.py
python -m py_compile app\services\docx_style_preserver.py
python -m py_compile app\services\section_replacement_engine.py
python -m py_compile app\servicesdaptive_ai_engine.py

git add .
git commit -m "Upgrade to V8.1 document structure engine"
git push
```

## Render settings

```text
AI_PROVIDER=openai
OPENAI_API_KEY=your_real_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```

For exact editable formatting, DOCX is the strongest source input. PDF preservation is approximate because PDFs do not reliably preserve editable Word layout metadata.
