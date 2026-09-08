# PharmaGenome
### Genomic & Pharmaceutical Data Analytics Platform

An analytical and research platform for exploring relationships between genomic variation and pharmaceutical data.

**Current delivery: Phase 1 foundation.** A real PostgreSQL schema, Python API, responsive workspace, deployment configuration and automated tests. Scientific ingestion and analytics are subsequent gated phases; this is not yet the completed analytical platform.

## Why this project exists
To demonstrate data engineering, bioinformatics and statistical reasoning through reproducible computation. The planned LLM feature explains computed results; it never substitutes for analysis.

## Architecture
```mermaid
flowchart TD
  UI[Next.js research workspace] --> Proxy[Server-side API proxy]
  Proxy --> API[Python FastAPI]
  API --> DB[(PostgreSQL)]
  CI[GitHub Actions] --> Tests[PostgreSQL integration + browser tests]
  Data[Future public source snapshots] -.-> Validate[Validate and normalize]
  Validate -.-> DB
  DB -.-> Analysis[Future statistics / bioinformatics / ML]
  Analysis -.-> Explanation[Optional evidence-based explanation]
```

## What works in Phase 1
- Normalized source, cohort, variant, gene, drug, pathway and analysis-record schema.
- Checksummed, atomic and idempotent migrations.
- Live API liveness/readiness and database inventory.
- Parameterized gene lookup, bounded filtering and pagination.
- Source catalogue, data-model explanation, dark/light mode and JSON system snapshot.
- Honest empty, loading, unavailable and connected states.
- PostgreSQL constraint tests and browser interaction tests.

## Stack
Next.js 16, React 19, TypeScript, Tailwind CSS 4, shadcn-derived controls; FastAPI, psycopg, PostgreSQL 17; Docker Compose; GitHub Actions; Vercel and Neon.

## Scientific methods
Planned mutation frequencies use distinct mutated samples divided by eligible profiled samples. Planned alignments implement Needleman-Wunsch and Smith-Waterman directly. Planned enrichment uses a documented gene universe, hypergeometric/Fisher tests and Benjamini-Hochberg adjustment. Planned statistics report assumptions, hypotheses, sample counts, effect sizes and limitations. None is implemented in this first phase.

## ML and AI
Training is gated on valid public response data, patient/study-aware splits, cross-validation and multiple evaluation metrics. Optional explanations require server-side API credentials and a model confirmed accessible to that API account. No LLM, model metrics, clinical predictions or API-key fields are faked in Phase 1.

## Quick start: Docker
Requires Docker with Compose.
```sh
cp .env.example .env
# Set a private development POSTGRES_PASSWORD in .env.
docker compose up --build
```
Frontend: http://localhost:3000 . API docs: http://localhost:8000/docs .
Compose starts PostgreSQL, applies migrations, then starts the API and frontend. Database ports bind to loopback only.

## Run services individually
Requires Python 3.12+, Node 22+ and PostgreSQL 17.
```sh
docker compose up -d db
cd backend
python -m venv .venv
# Activate .venv for your shell.
pip install -r requirements-dev.txt
# Set DATABASE_URL in your environment (see .env.example).
python -m scripts.migrate
uvicorn app.main:app --reload
```
In another terminal:
```sh
cd frontend
npm install
# Set API_BASE_URL=http://localhost:8000 in frontend/.env.local.
npm run dev
```
PowerShell environment syntax: `$env:API_BASE_URL='http://localhost:8000'`. For DATABASE_URL use your secret manager or private environment, never a committed file.

## Environment variables
| Variable | Service | Required | Purpose |
|---|---|---|---|
| DATABASE_URL | Backend / migration | Yes for database access | PostgreSQL URI; TLS in production |
| ALLOWED_ORIGINS | Backend | Recommended | Comma-separated permitted web origins |
| API_BASE_URL | Frontend server | Yes | Backend URL; not NEXT_PUBLIC |
| POSTGRES_PASSWORD | Docker only | Yes | Development database password |

No OpenAI API key is required or consumed in Phase 1.

## Tests
```sh
cd backend
ruff check app scripts tests
python -m scripts.migrate
pytest -q
cd ../frontend
npm install
npm run typecheck
npm run build
npx playwright install chromium
npm test
```
Database tests skip without DATABASE_URL; CI always provisions PostgreSQL and must execute them. Frontend tests use clearly scoped mocked API states for deterministic component interactions. Live endpoint/browser verification is separate.

## Ingestion
No ingestion command is released yet. Phase 2 must add official-source downloaders, schema validation, normalization, deduplication and reconciled reports together; merely creating empty scripts would not deliver a pipeline.

## Reproducibility example
Click **Export system snapshot** to export the actual database connection state, counts, source catalogue and timestamp. This is infrastructure evidence, not a scientific analysis. Future analysis exports must include method, filters, code revision, dataset checksums, results, limitations and sources.

## Deployment
Create two Vercel projects from this repository:
1. `pharmagenome-api`, root `backend`, FastAPI framework.
2. `pharmagenome`, root `frontend`, Next.js framework.
Connect Neon PostgreSQL to the API project only. Apply migrations once from a trusted runner with DATABASE_URL. Set the frontend API_BASE_URL to the backend production URL. Set ALLOWED_ORIGINS to the frontend origin. Deploy and verify /api/health, /api/ready, /api/system, then desktop and mobile pages.

See [ARCHITECTURE.md](ARCHITECTURE.md), [DATA_SOURCES.md](DATA_SOURCES.md) and [roadmap](docs/ROADMAP.md).

## Screenshots
GitHub Actions publishes desktop/mobile browser captures in its browser-evidence artifact. These deterministic screenshots verify the empty-database interface and do not represent real genomic results.

## Limitations
Phase 1 contains no scientific ingestion, mutation calculations, statistical analysis, sequence algorithms, drug-response dataset, ML or AI explanation layer. The schema alone does not validate biological annotations. No clinical validity is claimed.

## Scientific disclaimer
This platform is intended for educational, research, and analytical purposes. Results are not medical advice and should not be used to diagnose disease or make treatment decisions.
