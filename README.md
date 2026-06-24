## DOC_GUARD v7.0 (Scaffold)

Manufacturing-grade documentation compliance backend.

### What exists in this workspace
- `backend/`: FastAPI service scaffold implementing **fail-closed** compliance gating.

### Non-negotiable behavior (implemented)
- **OpenCV diff JSON is the only source of truth** (this service ingests and validates it).
- **Fail-closed** on any ambiguity, missing inputs, or AI unavailability.
- **No OpenAI usage**.
- Produces an **audit ZIP** containing:
  - input spec diff + hash
  - AI availability status
  - AI decision artifacts (even when unavailable)
  - final compliance status + reasons

### Run locally

1. Create venv and install:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Start API:

```bash
uvicorn app.main:app --reload
```

3. Health check:

- `GET /health`

