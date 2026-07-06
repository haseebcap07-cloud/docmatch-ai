# DocMatch AI — Public Website + FastAPI Backend

This package gives you a working public-style website UI and backend API.

Users can:

1. Upload a document: DOCX, TXT, or MD
2. Paste a job description
3. Enter target role title
4. Click generate
5. Download a tailored DOCX output document

The backend is built with **Python + FastAPI** and is compatible with **Python 3.14**.

---

## Run in VS Code on Windows

Open VS Code terminal in the project folder and run:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

copy .env.example .env

python -m uvicorn app.main:app --reload
```

Open the public website UI:

```text
http://localhost:8000
```

Open API docs:

```text
http://localhost:8000/docs
```

---

## Important Files

```text
public/index.html       Main website UI
public/styles.css       Website styling
public/app.js           Upload + download frontend logic
app/main.py             FastAPI app + public UI serving
app/routers/documents.py Upload and document tailoring routes
app/services/docx_utils.py DOCX extraction and DOCX generation
app/services/ai_provider.py Tailoring logic
```

---

## Main Public Flow

The website calls:

```http
POST /api/v1/documents/tailor-file
```

Form fields:

```text
job_description
target_role
file
```

Response:

```text
tailored_document.docx
```

---

## Supported Uploads

Currently supported:

- DOCX
- TXT
- MD

PDF upload needs an additional PDF extraction library. It can be added later.

---

## Production Notes

This starter works as a real upload/generate/download app.  
Before making it public for real users, add:

- Authentication
- User accounts
- Payment/subscription
- File size limits
- File deletion policy
- Malware scanning
- Error logging
- HTTPS deployment
- Real AI provider such as OpenAI or Azure OpenAI
- Privacy policy and terms page

---

## Production AI Note

The current version uses rule-based/mock tailoring so it works immediately without an API key.

For higher-quality real-world rewriting, connect an AI model in:

```text
app/services/ai_provider.py
```
