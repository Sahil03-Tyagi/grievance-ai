# GrievanceOS

GrievanceOS is a FastAPI application that uses Google ADK agents to help file, track, and escalate citizen grievances. It classifies a complaint, maps it to the right department, drafts a formal grievance, generates an email record, and logs workflow activity for tracking.

## What It Does

- Accepts a natural-language grievance from a user
- Identifies category and location
- Looks up the responsible authority from the database
- Drafts a formal complaint
- Generates and stores an email record for the complaint
- Logs the grievance and workflow trace
- Exposes status, logs, dashboard, and email preview endpoints
- Retries transient Gemini `429 RESOURCE_EXHAUSTED` failures at the API layer

## Architecture

The app is built around a root ADK orchestrator with sub-agents:

- `classifier_agent`: extracts grievance details and finds the authority
- `drafting_agent`: generates the formal complaint letter
- `execution_agent`: calls the email generation tool and records the email
- `tracking_tool`: stores grievance and workflow log data
- `escalation_tool`: checks overdue grievances and escalates them

Main API entrypoint:

- [api.py](/Users/sahiltyagi/Desktop/grievance-ai/api.py)

Agent wiring:

- [grievance_ai_agent/agent.py](/Users/sahiltyagi/Desktop/grievance-ai/grievance_ai_agent/agent.py)

## Tech Stack

- Python 3.11
- FastAPI
- Uvicorn
- SQLAlchemy
- Google ADK
- Google GenAI / Gemini
- PostgreSQL / AlloyDB
- Docker

## Project Structure

```text
.
├── api.py
├── Dockerfile
├── requirements.txt
├── index.html
└── grievance_ai_agent/
    ├── agent.py
    ├── config.py
    ├── .env
    ├── database/
    ├── sub_agents/
    └── tools/
```

## Environment Variables

Create `grievance_ai_agent/.env` for local development.

Example:

```env
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=your-gcp-project
GOOGLE_CLOUD_LOCATION=us-central1

DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/DB_NAME

ALLOYDB_HOST=10.x.x.x
ALLOYDB_PORT=5432
ALLOYDB_DATABASE=grievance_db
ALLOYDB_USER=postgres
ALLOYDB_PASSWORD=your-password

GMAIL_SENDER_EMAIL=your-email@example.com

GRIEVANCE_MAX_PIPELINE_RETRIES=2
GRIEVANCE_PIPELINE_RETRY_BASE_SECONDS=2
```

Notes:

- For direct Gemini API usage, set `GOOGLE_GENAI_USE_VERTEXAI=FALSE` and provide `GOOGLE_API_KEY`
- For Cloud Run, do not rely on the local `.env` file; use env vars or Secret Manager
- Never commit `.env` to Git

## Local Setup

1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Configure environment variables in `grievance_ai_agent/.env`

4. Start the API

```bash
uvicorn api:app --reload
```

5. Open the UI

Visit:

```text
http://127.0.0.1:8000/
```

## Docker

Build:

```bash
docker build -t grievance-os .
```

Run:

```bash
docker run --rm -p 8080:8080 grievance-os
```

If you need environment variables at runtime, pass them with `-e` flags or an env file.

## API Endpoints

- `GET /`
  - Serves the frontend UI
- `POST /grievance`
  - Runs the grievance pipeline and returns the final response
- `POST /grievance/stream`
  - Streams pipeline progress as server-sent events
- `GET /grievance/status?keyword=...`
  - Looks up the latest grievance matching a keyword
- `GET /grievance/{grievance_id}`
  - Returns stored grievance details
- `GET /logs/{grievance_id}`
  - Returns workflow reasoning trace
- `POST /escalate?demo=true`
  - Runs escalation logic
- `GET /dashboard`
  - Returns summary stats
- `GET /emails`
  - Returns recent generated email records

## Example Request

```bash
curl -X POST http://127.0.0.1:8000/grievance \
  -H "Content-Type: application/json" \
  -d '{
    "complaint": "Water supply has been interrupted in Indirapuram Ghaziabad for 3 days",
    "session_key": "demo-user"
  }'
```

## Cloud Run Deployment

This project includes a simple Dockerfile:

```dockerfile
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-8080}"]
```

Typical deploy flow:

```bash
gcloud run deploy grievance-os \
  --source . \
  --region=us-central1 \
  --allow-unauthenticated
```

If your database is on a private IP, also configure:

- `--network`
- `--subnet`
- `--vpc-egress`

Recommended for production:

- store secrets in Secret Manager
- use a dedicated Cloud Run service account
- grant access to Vertex AI and database resources
- avoid putting credentials directly in deploy commands

## Operational Notes

- The API retries transient Gemini quota/rate-limit failures before returning an error
- Email generation is currently recorded through the application tool flow and stored in the `sent_emails` table
- Cloud Run does not read your local `grievance_ai_agent/.env`

## Security

- Keep `.env` local only
- Rotate any secret that was ever committed or pasted into terminal history
- Prefer Secret Manager for deployment secrets

## Future Improvements

- Real external email delivery instead of DB-backed email records only
- Better auth and user identity handling
- Queueing and throttling for model calls
- More robust deployment config for production
