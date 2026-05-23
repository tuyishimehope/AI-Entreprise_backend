# Enterprise AI Backend

A FastAPI backend for uploading PDF documents, organizing document-linked chat sessions, and generating answers with retrieval-augmented generation (RAG). PostgreSQL stores document metadata, extracted text, embeddings, sessions, and chat history; uploaded files live on disk.

**Project status:** development-stage implementation. Uploads and session management are implemented, but the chat pipeline has known integration issues described under [Current limitations](#current-limitations). The API examples document the current interface, not a guarantee that the complete chat workflow succeeds.

## Contents

- [Technology and architecture](#technology-and-architecture)
- [Configuration](#configuration)
- [Run with Docker Compose](#run-with-docker-compose)
- [Run locally](#run-locally)
- [API reference](#api-reference)
- [Example workflow](#example-workflow)
- [Database and storage](#database-and-storage)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Current limitations](#current-limitations)

## Technology and architecture

| Component | Implementation |
| --- | --- |
| HTTP API | FastAPI, Pydantic, Uvicorn |
| Database | PostgreSQL 16 in Compose; SQLAlchemy async sessions with `asyncpg` |
| Migrations | Alembic using a synchronous `psycopg2` connection |
| PDF extraction | `pypdf` for uploads and reads; PyMuPDF in the RAG processor |
| AI integration | OpenAI Python SDK; `text-embedding-3-small` embeddings and `gpt-4o` answers |
| Retrieval | NumPy and scikit-learn cosine similarity |
| File storage | Local `app/storage/` directory |

Model names are hardcoded in `app/services/llm/openai.py`; they are not environment settings.

The intended flow is:

1. Upload a PDF, calculate its file hash, and reuse an existing document when the same file is uploaded again.
2. Save the file and its extracted text, then create a session linked to the document.
3. For a question, load the document and reuse or generate cached chunks and embeddings.
4. Split text into 1,000-character chunks with 200-character overlap and select the three most relevant chunks by cosine similarity.
5. Send the retrieved context and question to OpenAI, stream the answer as plain text, and save the completed answer and source chunks.

The answer prompt instructs the model to use the supplied context and say when it cannot answer. Previous session messages are stored but are not included in the model prompt. See the limitations below for differences between this intended flow and the current implementation.

```text
app/
├── main.py                  # Application, CORS, root route
├── api/v1/
│   ├── api.py               # Router registration (no /api/v1 URL prefix)
│   └── endpoints/           # Health, documents, sessions, chat
├── core/                    # Environment settings and logging
├── db/                      # SQLAlchemy engine, sessions, model metadata
├── models/                  # DocumentRecord, ChatSession, ChatRecord
├── schemas/                 # Pydantic response schemas
├── services/
│   ├── chat/                # RAG orchestration, extraction, retrieval
│   ├── document/            # PDF upload, deduplication, reads
│   ├── llm/                 # OpenAI embeddings and streaming answers
│   ├── session/             # Session operations
│   └── rag.py               # Document cache and history persistence
└── storage/                 # Uploaded PDFs
alembic/                     # Migration environment and revisions
Dockerfile                   # Python 3.11 application image
docker-compose.yml          # API and PostgreSQL development services
requirements.txt            # Pinned Python dependencies
tests/                      # Currently empty
```

## Configuration

Run commands from the repository root. Create a `.env` file there, or edit an existing one without overwriting credentials you need. No `.env.example` is included.

Example for Docker Compose (replace the API key and password):

```dotenv
APP_NAME=backend-Entreprise_ai
ENV=local
LOG_LEVEL=INFO
DB_HOST=postgres
DB_PORT=5432
DB_NAME=enterprise_ai
DB_USER=enterprise_ai
DB_PASSWORD=replace_with_local_password
OPENAI_API_KEY=replace_with_your_api_key
```

| Variable | Required | Default / purpose |
| --- | --- | --- |
| `APP_NAME` | No | `backend-Entreprise_ai`; API title and root response |
| `ENV` | No | `local`; currently does not switch runtime behavior |
| `LOG_LEVEL` | No | `INFO`; standard Python logging level |
| `DB_HOST` | Yes | Database hostname |
| `DB_PORT` | Yes | Database port |
| `DB_NAME` | Yes | Database name |
| `DB_USER` | Yes | Database user |
| `DB_PASSWORD` | Yes | Database password |
| `OPENAI_API_KEY` | Yes | Required by settings at startup; a working key is needed for AI requests |

Settings are case-insensitive and read `.env`; exported environment variables take precedence. Keep real credentials out of documentation and version control. `.env` is ignored by Git and Docker's build context.

Database addressing depends on where the API runs:

| API location | PostgreSQL location | `DB_HOST` | `DB_PORT` |
| --- | --- | --- | --- |
| Compose container | Compose `postgres` service | `postgres` | `5432` |
| Local Python process | Compose PostgreSQL | `localhost` | `5433` |
| Local Python process | Independently installed PostgreSQL | Your database host | Your configured port, typically `5432` |

The application constructs its connection URL directly from the database fields; credentials containing URL-reserved characters require appropriate handling in the connection configuration.

## Run with Docker Compose

Prerequisites: Docker with Docker Compose and the `.env` configuration above.

1. Start PostgreSQL and check readiness:

   ```bash
   docker compose up -d postgres
   docker compose exec postgres sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
   ```

   Proceed when PostgreSQL reports that it is accepting connections. Compose's `depends_on` does not wait for database readiness.

2. Build the API image and apply migrations:

   ```bash
   docker compose build api
   docker compose run --rm api alembic upgrade head
   ```

3. Start the API:

   ```bash
   docker compose up -d api
   docker compose logs -f api
   ```

The API listens on port `8000`. Compose mounts the repository into `/app`, enables auto-reload, and exposes PostgreSQL on host port `5433`. These are development defaults.

To stop the services while retaining the named database volume:

```bash
docker compose down
```

## Run locally

Use Python 3.11 to match the Docker image, plus a reachable PostgreSQL database. The pinned dependency set includes `uvloop`, so the documented local path targets macOS/Linux; use Docker or WSL on Windows.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The repository's `.gitignore` does not currently cover `.venv/`; keep that directory out of commits.

Set up `.env` using the table above. To use Compose only for the database, set `DB_HOST=localhost` and `DB_PORT=5433`, then run:

```bash
docker compose up -d postgres
docker compose exec postgres sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

For an independently installed PostgreSQL server, create the database and user specified in `.env` before continuing.

Once the database is ready:

```bash
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Migrations are required: the application does not create tables automatically on startup.

## API reference

Base URL: `http://localhost:8000`. Routes have **no `/api/v1` prefix**, despite the source directory name.

- [Swagger UI](http://localhost:8000/docs)
- [ReDoc](http://localhost:8000/redoc)
- [OpenAPI schema](http://localhost:8000/openapi.json)

| Method | Path | Input | Response / behavior |
| --- | --- | --- | --- |
| `GET` | `/` | None | Service name |
| `GET` | `/health/live` | None | `{"status":"alive"}` |
| `GET` | `/health/ready` | None | Database connectivity check: `ready` or `unready` |
| `POST` | `/files` | Multipart `file` | Document metadata; HTTP 201, including duplicate uploads |
| `GET` | `/files` | None | All document records |
| `GET` | `/files/{file_id}/download` | Document UUID | Download using the stored original filename |
| `POST` | `/session` | Multipart `file` | Upload/reuse a document and create a session; HTTP 201 |
| `GET` | `/session` | None | All sessions |
| `GET` | `/session/{session_id}` | Session UUID | Session, document summary, and messages |
| `DELETE` | `/session/{session_id}` | Session UUID | Deletes session and associated chats; returns JSON `true` on success |
| `POST` | `/chat` | Form fields `file_id`, `session_id`, `question` | Streamed `text/plain` answer |
| `GET` | `/history` | None | Up to 50 newest chat records; currently has a response-schema mismatch |
| `GET` | `/history/{session_id}` | Session UUID | Chat records for that session |

`/chat` accepts form data, not a JSON body. Its stream contains answer text, not Server-Sent Events or a JSON object with citations. Source chunks are persisted with chat history after a completed response. Session history has no explicit ordering in its query.

Readiness currently returns HTTP 200 even when its body says `unready`; it checks database connectivity, not migration status or OpenAI access.

## Example workflow

Use a PDF containing selectable text. Replace the sample path and IDs with your own values. The chat step is subject to the known issues below.

Check service health:

```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

Create a session by uploading a PDF:

```bash
curl -X POST http://localhost:8000/session \
  -F 'file=@/absolute/path/to/document.pdf'
```

The response includes `id` (the session ID), `document_id`, `title`, and `created_at`. Use the returned IDs from the same session:

```bash
SESSION_ID='replace-with-session-uuid'
FILE_ID='replace-with-document-uuid'

curl --no-buffer http://localhost:8000/chat \
  --data-urlencode "file_id=$FILE_ID" \
  --data-urlencode "session_id=$SESSION_ID" \
  --data-urlencode 'question=What are the main points in this document?'
```

Read the session and its saved history:

```bash
curl "http://localhost:8000/session/$SESSION_ID"
curl "http://localhost:8000/history/$SESSION_ID"
```

Download the original file:

```bash
curl "http://localhost:8000/files/$FILE_ID/download" --output downloaded-document.pdf
```

For a standalone upload without creating a session, use `POST /files` with the same multipart `file` field. The current API has no endpoint to create a session directly from an existing document ID; uploading the same bytes to `/session` reuses the document through deduplication.

## Database and storage

- **`documents`** stores filenames, local paths, file hashes, text chunks, embeddings, and timestamps. Chunks and embeddings use PostgreSQL JSONB; there is no vector database or vector index. The `s3_url` column exists, but S3 integration is not implemented.
- **`chat_sessions`** links each session to a document and stores its title and creation time.
- **`chat_history`** links messages to sessions and stores questions, answers, source chunks, and timestamps.

Deleting a session cascades to its chat records through the database foreign key. It does not delete its document or the uploaded file. There is no document deletion endpoint.

Uploads are stored relative to the working directory under `app/storage/`, using UUID-based filenames. With Compose's bind mount, files persist in the host checkout; PostgreSQL data persists in the `postgres_data` named volume. Back up both database data and uploaded files to preserve downloads and document reads.

## Development

Dependencies are managed through `requirements.txt`; `pyproject.toml` is currently empty. There is no configured automated test suite, formatter, linter, or CI workflow in this checkout. The health checks above provide basic manual smoke checks only.

Inspect migration state:

```bash
alembic current
alembic history
```

After changing SQLAlchemy models, generate and review a migration before applying it:

```bash
alembic revision --autogenerate -m "describe schema change"
alembic upgrade head
```

For Compose, run these commands through `docker compose run --rm api ...`. Alembic imports model metadata from `app/db/base.py` and derives its synchronous connection URL from the same settings used by the API.

The earliest checked-in migration creates the schema. A later migration adds non-nullable fields before subsequent revisions relax some constraints; upgrading an existing populated database may require a reviewed data backfill.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Startup settings validation error | Run from the repository root and supply all required database fields and `OPENAI_API_KEY`. |
| Database connection refused | Check readiness and use `postgres:5432` inside Compose or `localhost:5433` from the host. |
| Missing table or column | Apply `alembic upgrade head` against the same database used by the API. |
| Upload fails during PDF parsing | Confirm the file is a valid readable PDF. Scanned pages have no OCR fallback. |
| Chat fails when opening a PDF | See the cache-miss path issue below; the processor uses the original filename instead of the saved path. |
| OpenAI request fails | Check the configured key, account access to the hardcoded models, and outbound connectivity. |
| Browser requests fail CORS checks | The only configured origin is `http://localhost:3000`; change `app/main.py` for a different frontend origin. |
| Download cannot find the file | Confirm the database path still exists under `app/storage/` and that the API runs from the repository root. |

## Current limitations

These observations describe the checked-in code and should be considered when developing or deploying it:

- **Chat cache integration needs repair.** Upload deduplication hashes file bytes, while the chat cache hashes extracted text. On a cache miss, `ChatQuestionService._extract_text` passes the original filename to PyMuPDF instead of the stored `file_path`. A normal uploaded PDF can therefore fail before embeddings or an answer are generated.
- **Cached records share the document table.** RAG-created cache records have no local path and can appear in document listings, although response schemas require a string `file_path`. This also affects subsequent downloads or reads of those records.
- **Global history has a schema mismatch.** `GET /history` uses `ChatRead`, which requires `document_id`, but `ChatRecord` now stores `session_id`. Nonempty results can fail response validation.
- **Missing-session deletion is unreliable.** The deletion service checks an internal result attribute instead of the affected row count, so its intended 404 behavior is not dependable.
- **PDF processing has no OCR or explicit upload limits/type validation.** The upload path attempts PDF parsing regardless of extension. Empty or image-only documents may not produce usable text.
- **Authentication and authorization are absent.** Routes do not enforce user ownership, and chat does not verify that the submitted document belongs to the supplied session. Documents and history are shared across callers.
- **AI calls are synchronous within async request handling.** Heavy parsing, embeddings, and streaming requests can affect concurrency. Streaming failures can occur after response headers are sent; history is saved only after generation finishes successfully.
- **Deployment configuration is for development.** Auto-reload, the source bind mount, and the exposed database port are enabled. The standalone Docker image copies only `app/` and dependencies; migration files are available through the Compose mount but are not packaged in that image.

No license file is currently included in the repository.
