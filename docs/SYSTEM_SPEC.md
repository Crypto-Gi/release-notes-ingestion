# SYSTEM SPECIFICATION – RELEASE NOTES INGESTION PIPELINE

## 1. PURPOSE & SCOPE

- Provide a single, authoritative specification for the **Release Notes Ingestion Pipeline**.
- Make the system immediately understandable to **new developers**, **LLMs**, and **operators** without reading code.
- Describe **architecture**, **runtime workflows**, **APIs**, **data models**, **configuration**, and **operational behavior**.
- This document is **descriptive**, not prescriptive: it reflects the current implementation as of version **0.4.1 / 0.2.0 Qdrant update**, based on `README.md`, `env.example`, `docs/*.md`, and the current source tree.

Non-goals:
- No code-level refactors or design changes.
- No deployment-specific secrets or credentials.

---

## 2. HIGH-LEVEL SYSTEM OVERVIEW

### 2.1 Problem Statement

The system ingests PDF/Word release notes and related documents from **Cloudflare R2**, converts them to markdown via **Docling**, semantically chunks them, generates embeddings with **Ollama**, and uploads vectors to **Qdrant** to support semantic search and a two-stage search workflow.

### 2.2 Primary Use Cases

- **Release Notes Search** across multiple products and versions.
- **Technical documentation ingestion** into a vector store.
- **RAG backends** for chat/search systems.
- **Knowledge base indexing** for internal docs.

### 2.3 Core Guarantees

- **Idempotent ingestion** via hash-based tracking and Phase 3 deduplication.
- **Mirrored markdown storage** from source prefix to markdown prefix in R2.
- **Two-collection Qdrant design**:
  - Filename-level discovery (small 384D vectors).
  - Content-level semantic search (1024D vectors).
- **Comprehensive JSON logging** of conversion, uploads, embeddings, and skips.

---

## 3. ARCHITECTURE

### 3.1 Textual Architecture Diagram

```text
┌──────────────────────────────────────────────────────────────┐
│                     n8n (optional)                           │
│  • Schedules runs (cron)                                     │
│  • Calls FastAPI ingress endpoints                           │
│  • Monitors status and logs                                  │
└──────────────┬───────────────────────────────────────────────┘
               │ HTTP (REST)
               v
┌──────────────────────────────────────────────────────────────┐
│         FastAPI Service (api/main.py)                        │
│  • /health, /api/pipeline/start, /api/pipeline/status        │
│  • /api/pipeline/summary, /api/logs/*, /api/collections/info │
│  • Orchestrates background pipeline task(s)                  │
└──────────────┬───────────────────────────────────────────────┘
               │ In-process call
               v
┌──────────────────────────────────────────────────────────────┐
│       Python Ingestion Pipeline (src/pipeline.py)            │
│                                                              │
│  1) List & download files from Cloudflare R2                 │
│  2) Hash files and check logs for prior processing           │
│  3) Convert to markdown via Docling                          │
│  4) Upload markdown back to R2 (mirrored structure)          │
│  5) Chunk markdown into semantic pieces                      │
│  6) Generate filename + content embeddings via Ollama        │
│  7) Deduplicate via logs + Qdrant                           │
│  8) Upload filename vector + content chunks to Qdrant        │
│  9) Log success/failure to JSON logs                         │
└──────────────┬───────────────────────────────────────────────┘
               │ External services
               v
┌──────────────────────────────────────────────────────────────┐
│ External Dependencies                                        │
│                                                              │
│  • Cloudflare R2 (S3-compatible object storage)              │
│  • Docling service (PDF/Word → Markdown)                     │
│  • Ollama embeddings server (granite-embedding:30m, bge-m3)  │
│  • Qdrant vector database (HTTP/gRPC, 2 main collections)    │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Source Layout (High Level)

- `src/pipeline.py`
  - Defines `IngestionPipeline` orchestrator and CLI entrypoint.
- `src/components/`
  - `config.py` – configuration models + `.env` loader.
  - `r2_client.py` – R2/S3 operations.
  - `file_hasher.py` – hashing utilities (MD5 + xxHash64).
  - `log_manager.py` – JSON log management and Phase 3 helpers.
  - `docling_client.py` – Docling REST client + health checks.
  - `markdown_storage.py` – mapping source paths to markdown paths and uploading.
  - `chunker.py` – markdown → semantic chunks.
  - `embedding_client.py` – Ollama embedding client + dedup-aware batch calls.
  - `qdrant_uploader.py` – Qdrant client and collection-specific uploads.
- `api/main.py`
  - FastAPI app wrapping `IngestionPipeline` for remote orchestration.
- `scripts/`
  - `setup_qdrant_collections.py` – collection creation per `.env`.
  - `create_payload_indexes_advanced.py` – interactive payload index management.
  - `reprocess_from_markdown.py` – pipeline variant starting from markdown.
  - `retry_failed_files.py` – reuse logs to re-run failed items.
  - Additional diagnostic scripts (indexes, R2 markdown, collections).
- `docs/`
  - `REFERENCE.md`, `QDRANT.md`, `INDEXING_GUIDE.md`, `DOCKER.md`, `PHASE_3_ENHANCEMENTS.md`, `CHANGELOG.md`, `SYSTEM_SPEC.md` (this file).

---

## 4. RUNTIME WORKFLOWS

### 4.1 Main Ingestion Pipeline (PDF/Word → Qdrant)

Implemented in `src/pipeline.py` via `IngestionPipeline`.

High-level steps:

1. **Initialization**
   - Load config via `load_config()` (Pydantic models + `.env`).
   - Initialize `R2Client`, `FileHasher`, `LogManager`, `DoclingClient`,
     `MarkdownStorage`, `SemanticChunker`, `EmbeddingClient`, `QdrantUploader`.
   - Read `FORCE_REPROCESS` from environment.

2. **Service health check**
   - `DoclingClient.health_check()`
   - `EmbeddingClient.health_check()`
   - `QdrantUploader.health_check()`
   - Pipeline aborts early if any service is unhealthy.

3. **File discovery**
   - List R2 objects under `R2_SOURCE_PREFIX` via `R2Client.list_files()`.
   - Use stored log hashes (`LogManager.get_processed_hashes()`) and R2 ETags as a fast initial filter.

4. **Per-file processing (`process_file`)**
   - **Skip check** via `IngestionPipeline.should_skip_file()` against `SKIP_EXTENSIONS`.
   - **Download** file bytes from R2.
   - **Hash** the file (MD5 + lightweight hash); MD5 is used for logs, lightweight hash for filenames collection.
   - **Already processed?**
     - `LogManager.is_uploaded(file_hash)` short-circuits if file is fully processed.
   - **Docling conversion**
     - Submit file bytes + filename to Docling.
     - Poll until ready, retrieve markdown.
     - On failure: log to `failed.json` and abort this file.
   - **Markdown upload**
     - Compute target markdown key by mapping `source/…` → `markdown/…` and changing extension to `.md`.
     - Upload markdown to R2; log to `upload.json` or `failed.json`.
   - **Chunking**
     - Pass markdown to `SemanticChunker.chunk_markdown()` with `CHUNK_SIZE_TOKENS` and `CHUNK_OVERLAP_TOKENS`.
     - Annotate chunks with metadata (`filename`, `page_number`, `element_type`, `md5_hash` of content).
   - **Filename embedding**
     - `EmbeddingClient.generate_filename_embedding()` produces a single 384D vector for filename collection.
   - **Content embeddings with dedup**
     - `EmbeddingClient.generate_batch_embeddings_with_dedup()`:
       - Uses log + Qdrant checks to skip if already embedded.
       - Returns `None` if content already exists (Phase 3 dedup path).
   - **Qdrant upload**
     - **Filename collection**: `QdrantUploader.upload_filename()` with lightweight hash as payload.
     - **Content collection**: `QdrantUploader.upload_content_chunks()` with chunk payloads.
   - **Final logging**
     - `LogManager.add_upload_entry()` marks file as successfully processed.

5. **Pipeline summary**
   - Aggregate `total_files`, `new_files`, `processed`, `failed`, `skipped`,
     `duration_seconds`, `files_per_second` and return a summary dict.

### 4.2 Reprocess-from-Markdown Workflow

Implemented in `scripts/reprocess_from_markdown.py`.

- Starts from **markdown files** in `R2_MARKDOWN_PREFIX` instead of raw PDFs/Word.
- Skips Docling conversion entirely; the rest of the flow (chunking, embedding, Qdrant upload, dedup, logging) is similar to the main pipeline.
- Primary use cases:
  - Rebuilding Qdrant collections.
  - Switching embedding models.
  - Running when Docling is unavailable.

### 4.3 Retry-Failed-Files Workflow

Implemented in `scripts/retry_failed_files.py`.

- Reads `logs/failed.json` and attempts to re-run files that failed previously.
- Supports options like `--dry-run` and `FORCE_REPROCESS=true` (via env) to control behavior.
- After successful reprocessing, removes entries from `failed.json`.

### 4.4 API-Orchestrated Workflow (n8n / External Systems)

- `api/main.py` exposes endpoints for remote orchestration.
- `POST /api/pipeline/start`:
  - Creates a task entry in `tasks` dict.
  - Schedules `run_pipeline_task()` as a FastAPI background task.
  - Returns a `task_id` used to query status.
- `GET /api/pipeline/status/{task_id}`:
  - Returns current task status (`pending`, `running`, `completed`, `failed`) and result.
- `GET /api/pipeline/summary`:
  - Uses `LogManager.get_stats()` to report high-level counts.

---

## 5. COMPONENT SPECIFICATION (IMPLEMENTATION-LEVEL OVERVIEW)

### 5.1 Config Loader (`src/components/config.py`)

Responsibilities:

- Read `.env` using `python-dotenv` (and/or OS environment variables).
- Populate nested Pydantic models for:
  - `r2` – endpoint, access key, secret key, bucket name, prefixes.
  - `qdrant` – host, port, HTTPS toggle, API key, gRPC, collection names, vector sizes, distances, HNSW, on-disk payload.
  - `ollama` – host, port, filename/content models, optional truncate/keep-alive/dimensions.
  - `docling` – base URL, timeout, poll interval.
  - `chunking` – size, overlap.
  - `log` – directory and file names.
  - `processing` – `SKIP_EXTENSIONS`.

Notes:

- Fails fast for missing mandatory values.
- Provides a single typed configuration object consumed by `IngestionPipeline` and components.

### 5.2 R2 Client (`src/components/r2_client.py`)

Responsibilities:

- Wrap **boto3** S3 client pointed at `R2_ENDPOINT`.
- List files under `R2_SOURCE_PREFIX` (and other prefixes when needed).
- Download objects to memory.
- Upload markdown content back to R2.

Key behaviors:

- Uses efficient pagination for listing.
- Streams downloads/uploads to avoid excessive memory where supported.
- Returns ETag and metadata necessary for dedup and incremental processing.

### 5.3 File Hasher (`src/components/file_hasher.py`)

Responsibilities:

- Provide hashing primitives used across the pipeline.

Functions (conceptual):

- `hash_file(file_content: bytes) -> str`
  - MD5 of whole content for logs and long-term tracking.
- `hash_file_lightweight(file_content: bytes) -> str`
  - xxHash64 (fast, 64-bit) for filenames collection and Phase 3 dedup.
- `hash_text(text: str) -> str`
  - MD5 for chunk-level identification (`metadata.md5_hash`).

Notes:

- MD5 is used for compatibility and uniqueness, not for cryptographic security.
- xxHash64 is preferred where speed is critical (Phase 3).

### 5.4 Log Manager (`src/components/log_manager.py`)

Responsibilities:

- Manage JSON logs in `LOG_DIR`.
- Provide **thread-safe**, **atomic** read/write operations.
- Support Phase 3 deduplication and observability.

Log files:

- `conversion.json` – successful Docling conversions.
- `upload.json` – markdown upload successes.
- `failed.json` – failures with `filename`, `hash`, `error`, `stage`.
- `embedding.json` – embedding operations (Phase 3).
- `qdrant_upload.json` – Qdrant uploads (Phase 3).
- `skipped.json` – deduplicated/skipped files (Phase 3).

Capabilities:

- Incrementally load logs at startup into in-memory structures for fast membership tests.
- `is_uploaded(file_hash)` and similar helpers to answer "has this file already gone through full pipeline?".
- Phase 3 methods (per docs):
  - `log_embedding_success(...)`.
  - `log_qdrant_upload_success(...)`.
  - `log_skipped_file(...)`.
  - `check_embedding_exists(...)`.

Implementation details (from docs):

- Atomic file updates via `*.tmp` then rename.
- In-memory `set` for O(1) hash lookup.

### 5.5 Docling Client (`src/components/docling_client.py`)

Responsibilities:

- Encapsulate all communication with the Docling conversion service.

Key behaviors:

- `convert_from_memory(file_content: bytes, filename: str) -> str | None`
  - Uploads the file, polls for status, retrieves markdown.
- `health_check() -> bool`
  - Hits Docling’s `/healthz` endpoint (corrected from `/health` in 0.2.0).

Error handling:

- Handles timeouts via `DOCLING_TIMEOUT`.
- Uses polling interval `DOCLING_POLL_INTERVAL`.
- Logs failures appropriately through `LogManager`.

### 5.6 Markdown Storage (`src/components/markdown_storage.py`)

Responsibilities:

- Transform source R2 keys to markdown keys and upload markdown.

Rules:

- Replace `R2_SOURCE_PREFIX` with `R2_MARKDOWN_PREFIX`.
- Preserve subdirectory structure exactly.
- Replace file extension with `.md`.

Example:

- Input: `source/ecos/release1/ECOS_9.3.7.1_Release_Notes.pdf`
- Output: `markdown/ecos/release1/ECOS_9.3.7.1_Release_Notes.md`

### 5.7 Semantic Chunker (`src/components/chunker.py`)

Responsibilities:

- Convert markdown strings into semantically meaningful chunks with metadata.

Implementation details:

- Uses `langchain` + `langchain-text-splitters` (e.g. `RecursiveCharacterTextSplitter`).
- Token-based target size: `CHUNK_SIZE_TOKENS` (default 500).
- `CHUNK_OVERLAP_TOKENS` can be used for context overlap (default 0).

Chunk structure (conceptual):

```python
Chunk(
  text="...chunk content...",
  metadata={
    "filename": "Original_File.pdf",
    "page_number": <int>,  # monotonic per file
    "element_type": "Text" | "Table" | "Image" | "List",
    "md5_hash": "<MD5 of chunk text>",
  }
)
```

Element-type detection is based on markdown patterns (tables, images, lists).

### 5.8 Embedding Client (`src/components/embedding_client.py`)

Responsibilities:

- Interface with **Ollama** embedding API.
- Manage model selection, batch sizes, dedup, and logging hooks.

Key behaviors:

- `health_check()` – verifies Ollama server availability.
- `generate_filename_embedding(filename, file_content, collection_name, log_to_phase3=True)`
  - Encodes filename context (and optionally small content) using `OLLAMA_FILENAME_MODEL` (e.g. `granite-embedding:30m`, 384D).
- `generate_batch_embeddings_with_dedup(...)` (per docs and pipeline usage):
  - Accepts list of text chunks.
  - Uses `LogManager` and Qdrant client to check if embeddings already exist for a file.
  - Returns `None` if dedup decides to skip embedding.
  - Otherwise returns a list of vectors (e.g. 1024D for `bge-m3`).

Ollama API usage (from docs):

- HTTP `POST /api/embeddings` with JSON body:
  - `{"model": "bge-m3", "prompt": "text to embed"}`.

### 5.9 Qdrant Uploader (`src/components/qdrant_uploader.py`)

Responsibilities:

- Manage Qdrant connection configuration (HTTP/HTTPS/gRPC, API key).
- Upload points to **filename** and **content** collections.
- Provide collection inspection helpers.

Key behaviors:

- `health_check()` – verifies Qdrant responsiveness.
- `get_collection_info(name)` – summary of points, vector size, etc.
- `upload_filename(filename, embedding, lightweight_hash)` –
  - Inserts one point per source file into filename collection.
  - Payload: `pagecontent` and/or `metadata.filename`, and `metadata.hash`.
- `upload_content_chunks(filename, chunks, embeddings)` –
  - Inserts one point per chunk into content collection.
  - Payload: `pagecontent`, `metadata.filename`, `metadata.page_number`, `metadata.element_type`, `metadata.md5_hash`.

Phase 3 logging:

- `QdrantUploader` collaborates with `LogManager` to log upload operations into `qdrant_upload.json`.

---

## 6. DATA MODELS & STORAGE

### 6.1 Qdrant Collections

#### 6.1.1 Filename Collection (Document Discovery)

- Name: `QDRANT_FILENAME_COLLECTION` (default: `filename-granite-embedding30m`).
- Vector size: `QDRANT_FILENAME_VECTOR_SIZE` (default: 384).
- Model: `OLLAMA_FILENAME_MODEL` (default: `granite-embedding:30m`).
- Distance: `QDRANT_FILENAME_DISTANCE` (default: `Cosine`).
- Text indexing: `QDRANT_FILENAME_TEXT_INDEX` (usually `true`), tokenizer config.

Payload (typical):

```json
{
  "pagecontent": "ECOS_9.3.7.1_Release_Notes.pdf",
  "source": "ECOS_9.3.7.1_Release_Notes.pdf",
  "metadata": {
    "hash": "<lightweight file hash>"
  }
}
```

Uses:

- Stage 1 of search: quickly find relevant documents by filename.

#### 6.1.2 Content Collection (Semantic Content Search)

- Name: `QDRANT_CONTENT_COLLECTION` (default: `releasenotes-bge-m3`).
- Vector size: `QDRANT_CONTENT_VECTOR_SIZE` (default: 1024).
- Model: `OLLAMA_CONTENT_MODEL` (default: `bge-m3`).
- Distance: `QDRANT_CONTENT_DISTANCE` (default: `Cosine`).
- Text indexing: `QDRANT_CONTENT_TEXT_INDEX` (default `false` – vector-only search).

Payload (typical):

```json
{
  "pagecontent": "Bug fixes in version 9.3.7.1: Fixed memory leak...",
  "metadata": {
    "filename": "ECOS_9.3.7.1_Release_Notes.pdf",
    "page_number": 47,
    "element_type": "Text",
    "md5_hash": "<MD5 of chunk>"
  }
}
```

Uses:

- Stage 2 of search: semantic content retrieval within specific documents.

### 6.2 Log Files

All logs reside under `LOG_DIR` (default `logs/`).

- `conversion.json` – per-file Docling conversions.
- `upload.json` – per-file markdown uploads to R2.
- `failed.json` – failures; each entry includes stage (`docling`, `r2`, `chunker`, `ollama`, `qdrant`, `pipeline`).
- `embedding.json` – embedding operations with model, dims, counts, timing.
- `qdrant_upload.json` – Qdrant upload operations with point counts, ids, timing.
- `skipped.json` – deduplication decisions (why a file was skipped).

Entry example (`embedding.json`):

```json
{
  "filename": "document.pdf",
  "md5_hash": "<hash>",
  "collection_name": "content",
  "chunks_created": 26,
  "embedding_time": 7.46,
  "model_name": "bge-m3",
  "timestamp": "2025-11-11T20:00:00Z"
}
```

### 6.3 R2 Object Keys

- Source prefix: `R2_SOURCE_PREFIX` (default `source/`).
- Markdown prefix: `R2_MARKDOWN_PREFIX` (default `markdown/`).

Mapping rules:

- Replace prefix.
- Preserve all nested directories.
- Replace file extension with `.md`.

---

## 7. API SPECIFICATION (FastAPI)

All endpoints are defined in `api/main.py`.

### 7.1 Health & Root

- `GET /`
  - Returns service metadata and status.

- `GET /health`
  - Checks Docling, Qdrant, and Ollama via `IngestionPipeline.health_check()`.
  - Response sample:

```json
{
  "status": "healthy" | "degraded" | "unhealthy",
  "services": {
    "docling": true,
    "qdrant": true,
    "ollama": true
  },
  "timestamp": "<ISO8601 UTC>"
}
```

### 7.2 Pipeline Control

- `POST /api/pipeline/start`
  - Starts background pipeline execution.
  - Returns `{ "task_id": "uuid", "status": "pending", ... }`.

- `GET /api/pipeline/status/{task_id}`
  - Returns serialized `TaskStatus`:

```json
{
  "task_id": "uuid",
  "status": "pending|running|completed|failed",
  "progress": "string or null",
  "result": {"..."} | null,
  "error": "string or null",
  "started_at": "ISO8601 or null",
  "completed_at": "ISO8601 or null"
}
```

- `GET /api/pipeline/summary`
  - Summary based on logs: counts of converted, uploaded, failed.

### 7.3 Log Access

- `GET /api/logs/conversion`
- `GET /api/logs/upload`
- `GET /api/logs/failed`

Each returns parsed JSON content from the corresponding log.

### 7.4 Collections Info

- `GET /api/collections/info`
  - Returns basic info for filename and content collections (point counts, indexes, etc.).

---

## 8. CONFIGURATION & ENVIRONMENT

Reference: `env.example`, `docs/QDRANT.md`, `README.md`.

### 8.1 Core Environment Variables

#### Cloudflare R2

- `R2_ENDPOINT`
- `R2_ACCESS_KEY`
- `R2_SECRET_KEY`
- `R2_BUCKET_NAME`
- `R2_SOURCE_PREFIX` (default `source/`)
- `R2_MARKDOWN_PREFIX` (default `markdown/`)

#### Qdrant

- `QDRANT_HOST`
- `QDRANT_PORT` (default `6333`)
- `QDRANT_USE_HTTPS` (default `false`)
- `QDRANT_API_KEY` (optional)
- `QDRANT_GRPC_PORT` (optional)
- `QDRANT_PREFER_GRPC` (default `false`)
- `QDRANT_FILENAME_COLLECTION`
- `QDRANT_CONTENT_COLLECTION`
- Vector and index settings (`QDRANT_FILENAME_VECTOR_SIZE`, etc.) as detailed in `docs/QDRANT.md`.

#### Ollama

- `OLLAMA_HOST`
- `OLLAMA_PORT` (default `11434`)
- `OLLAMA_FILENAME_MODEL` (default `granite-embedding:30m`)
- `OLLAMA_CONTENT_MODEL` (default `bge-m3`)
- Optional: `OLLAMA_TRUNCATE`, `OLLAMA_KEEP_ALIVE`, `OLLAMA_DIMENSIONS`.

#### Docling

- `DOCLING_BASE_URL`
- `DOCLING_TIMEOUT` (default `300` seconds)
- `DOCLING_POLL_INTERVAL` (default `2` seconds)

#### Chunking

- `CHUNK_SIZE_TOKENS` (default `500`)
- `CHUNK_OVERLAP_TOKENS` (default `0`)

#### Logging

- `LOG_DIR` (default `logs/`)
- `CONVERSION_LOG`, `UPLOAD_LOG`, `FAILED_LOG`, `EMBEDDING_LOG`, `QDRANT_UPLOAD_LOG`, `SKIPPED_LOG`.

#### Phase 3 (Dedup & Enhanced Logging)

- `FORCE_REPROCESS` (default `false`)
- `QDRANT_BATCH_SIZE` (default `100`)
- `LOG_EMBEDDINGS` (default `true`)
- `LOG_QDRANT_UPLOADS` (default `true`)
- `LOG_SKIPPED_FILES` (default `true`)

#### Processing

- `SKIP_EXTENSIONS` – comma-separated list of extensions (e.g. `.DS_Store,.tmp`).

#### n8n (Optional)

- `N8N_API_KEY`, `N8N_URL` for external orchestration.

### 8.2 Dependency Summary

From `requirements.txt`:

- Core:
  - `boto3`, `qdrant-client`, `langchain`, `langchain-text-splitters`, `tiktoken`,
    `requests`, `python-dotenv`, `pydantic`, `tenacity`, `xxhash`.
- API:
  - `fastapi`, `uvicorn`.
- Dev/testing:
  - `pytest`, `pytest-cov`, `black`, `flake8`.

---

## 9. DEDUPLICATION & ERROR HANDLING

### 9.1 Deduplication Strategy (Phase 3)

Targets:

- Avoid re-embedding and re-uploading content already present in logs/Qdrant.
- Preserve a full audit trail of skipped operations.

Steps (per `PHASE_3_ENHANCEMENTS.md` and current pipeline behavior):

1. Compute a **lightweight file hash** with xxHash64 (via `FileHasher`).
2. Before generating embeddings:
   - Check `embedding.json` for existing records.
   - Optionally query Qdrant via `metadata.md5_hash` (storing the same hash value) to confirm.
3. If found, log a `skipped.json` entry and **skip embedding + upload**, unless `FORCE_REPROCESS=true`.
4. On success, log both embedding and upload details.

### 9.2 Error Handling

- Failures at any stage (Docling, R2, chunking, embedding, Qdrant, pipeline) produce entries in `failed.json` with:
  - `filename`, `hash`, `error`, `stage`, timestamp.
- `retry_failed_files.py` uses `failed.json` as its input.
- API-level errors surface as HTTP 5xx/503 with JSON error payloads.

---

## 10. SECURITY & OPERATIONAL CONSIDERATIONS

### 10.1 Secrets & Credentials

- `.env` is **not committed** (see `.gitignore`); only `env.example` is.
- R2, Qdrant, and n8n credentials must be set via environment or secure secrets management.
- `QDRANT_API_KEY` is never logged in plaintext; logs mask sensitive values.

### 10.2 Network & Transport

- Qdrant can be accessed over HTTP or HTTPS, controlled via `QDRANT_USE_HTTPS`.
- Ollama and Docling are usually on internal networks (e.g. private IPs).
- For Docker deployments, see `docs/DOCKER.md` for suggested network isolation and health checks.

### 10.3 Performance

- Baseline measurements (per `README.md`):
  - ~40s per document end-to-end on initial ingestion.
  - Subsequent runs with dedup reduce processing to **<1s per already-processed document**.
- Tuning knobs:
  - `QDRANT_BATCH_SIZE`, HNSW parameters, `QDRANT_PREFER_GRPC`.
  - `CHUNK_SIZE_TOKENS` / `CHUNK_OVERLAP_TOKENS`.
  - Hardware resources (cpus/memory in Docker Compose).

---

## 11. DEVELOPER & LLM USAGE NOTES

### 11.1 For New Developers

- Start with `README.md` for quick-start and high-level architecture.
- Use `SYSTEM_SPEC.md` (this file) to understand **how** pieces fit together.
- Consult:
  - `docs/REFERENCE.md` for historical plans and additional details.
  - `docs/QDRANT.md` and `docs/INDEXING_GUIDE.md` for collection/index design.
  - `docs/DOCKER.md` for deployment patterns.
  - `docs/PHASE_3_ENHANCEMENTS.md` for dedup/logging design.

### 11.2 For LLM Agents

- Use this spec as the primary reference for:
  - What each component does and how it interacts.
  - What data structures exist and how they are stored.
  - How to safely call APIs and scripts.
- When answering questions, cross-reference this file with `README.md` and `docs/` for deeper details.

---

**End of SYSTEM_SPEC – kept in sync with code and docs as of the current repository state.**
