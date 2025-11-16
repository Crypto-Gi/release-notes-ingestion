# 🚀 Release Notes Ingestion Pipeline - AI-Powered Document Processing

[![Version](https://img.shields.io/badge/version-0.4.1-blue.svg)](VERSION)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-production-success.svg)]()

> **Enterprise-grade AI document processing pipeline** for converting PDF/Word documents to searchable vector embeddings using Docling, Ollama, and Qdrant vector database.

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#️-architecture)
- [Quick Start](#-quick-start)
- [Components](#-components)
- [Phase 3: Advanced Deduplication](#-phase-3-advanced-deduplication)
- [Scripts](#-scripts)
- [API Endpoints](#-api-endpoints)
- [Configuration](#-configuration)
- [Monitoring & Logging](#-monitoring--logging)
- [Troubleshooting](#-troubleshooting)
- [Documentation](#-documentation)
- [Performance](#-performance)

---

## 🎯 Overview

**Release Notes Ingestion Pipeline** is a production-ready, AI-powered document processing system that:

- **Converts** PDF and Word documents to markdown using Docling
- **Chunks** content semantically for optimal retrieval
- **Generates** embeddings using Ollama (granite-embedding:30m & bge-m3)
- **Stores** vectors in Qdrant for lightning-fast semantic search
- **Deduplicates** intelligently using xxHash64 and metadata indexing
- **Logs** everything with comprehensive JSON tracking
- **Scales** horizontally with Docker and FastAPI

### 🎯 Use Cases

- **Release Notes Search** - Semantic search across product release notes
- **Documentation Processing** - Convert and index technical documentation
- **Knowledge Base** - Build searchable knowledge bases from documents
- **RAG Systems** - Retrieval-Augmented Generation pipelines
- **Compliance** - Track and search regulatory documents

### 🏆 Why This Pipeline?

✅ **Production-Ready** - Battle-tested with 500+ documents  
✅ **Intelligent Deduplication** - Saves time and resources  
✅ **Comprehensive Logging** - Track every operation  
✅ **Flexible Deployment** - Docker, Python, or API  
✅ **Retry Mechanism** - Automatic failure recovery  
✅ **SEO-Optimized** - Well-documented and discoverable  

---

## ✨ Key Features

### 🔄 Complete Pipeline
- **Document Conversion** - PDF/Word → Markdown via Docling
- **Semantic Chunking** - LangChain-based intelligent splitting
- **Dual Embeddings** - Filename (384D) + Content (1024D)
- **Vector Storage** - Qdrant with HNSW indexing
- **Metadata Tracking** - Comprehensive payload indexing

### 🧠 Phase 3: Advanced Deduplication
- **xxHash64** - Lightning-fast file hashing
- **Log-Based Dedup** - Check embedding.json before processing
- **Qdrant Dedup** - Query collection before uploading
- **Collection-Aware** - Separate tracking for filename vs content
- **Force Reprocess** - Override deduplication when needed

### 📊 Comprehensive Logging
- `embedding.json` - Embedding operations with model tracking
- `qdrant_upload.json` - Upload operations with point counts
- `skipped.json` - Deduplicated files with reasons
- `failed.json` - Failed operations with error details
- `conversion.json` - Docling conversion tracking

### 🔧 Flexible Scripts
1. **pipeline.py** - Full pipeline (source → Qdrant)
2. **reprocess_from_markdown.py** - Skip conversion, reprocess markdown
3. **retry_failed_files.py** - Automatic failure recovery

### 🌐 API & Integration
- **FastAPI** - RESTful API with async support
- **n8n Integration** - Workflow automation
- **Docker** - Containerized deployment
- **Health Checks** - Service monitoring

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    n8n Workflow Orchestration                   │
│  • Cron scheduling (daily/hourly)                               │
│  • HTTP API calls to FastAPI                                    │
│  • Monitoring & alerting                                        │
│  • Error handling & retries                                     │
└──────────────┬──────────────────────────────────────────────────┘
               │
               v
┌─────────────────────────────────────────────────────────────────┐
│              Python Ingestion Pipeline (FastAPI)                │
│                                                                  │
│  [1] List R2 Files → [2] Download → [3] Hash (xxHash64)        │
│         ↓                                                        │
│  [4] Check Logs (embedding.json, qdrant_upload.json)           │
│         ↓                                                        │
│  [5] Convert (Docling: PDF/Word → Markdown)                    │
│         ↓                                                        │
│  [6] Upload Markdown → R2 (mirrored structure)                 │
│         ↓                                                        │
│  [7] Semantic Chunking (LangChain, 500 tokens)                 │
│         ↓                                                        │
│  [8] Generate Embeddings (Ollama)                              │
│      • Filename: granite-embedding:30m (384D)                   │
│      • Content: bge-m3 (1024D)                                  │
│         ↓                                                        │
│  [9] Upload to Qdrant (with deduplication check)               │
│         ↓                                                        │
│  [10] Log Success/Failure (JSON logs)                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
               │
               v
┌─────────────────────────────────────────────────────────────────┐
│                    Storage & Services                           │
│                                                                  │
│  • Cloudflare R2 (S3-compatible object storage)                │
│  • Qdrant (Vector database with HNSW indexing)                 │
│  • Ollama (Local LLM inference)                                 │
│  • Docling (Document conversion service)                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Docker & Docker Compose (optional)
- Cloudflare R2 account
- Qdrant instance
- Ollama with models
- Docling service

### 1. Clone Repository

```bash
git clone https://github.com/Crypto-Gi/release-notes-ingestion.git
cd release-notes-ingestion
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example configuration
cp env.example .env

# Edit .env with your credentials
nano .env
```

**Required Configuration:**

```bash
# Cloudflare R2
R2_ENDPOINT=https://your-account.r2.cloudflarestorage.com
R2_ACCESS_KEY=your-access-key
R2_SECRET_KEY=your-secret-key
R2_BUCKET_NAME=releasenotes

# Qdrant Vector Database
QDRANT_HOST=your-qdrant-host
QDRANT_PORT=6333
QDRANT_USE_HTTPS=true
QDRANT_API_KEY=your-api-key

# Ollama Embeddings
OLLAMA_HOST=127.0.0.1
OLLAMA_PORT=11434
OLLAMA_FILENAME_MODEL=granite-embedding:30m
OLLAMA_CONTENT_MODEL=bge-m3

# Docling Conversion
DOCLING_BASE_URL=http://docling-service:5010
DOCLING_TIMEOUT=300
```

### 4. Setup Qdrant Collections

```bash
# Create collections with proper schema
python scripts/setup_qdrant_collections.py
```

### 5. Run Pipeline

**Option A: Direct Python**
```bash
python src/pipeline.py
```

**Option B: Docker (Recommended)**
```bash
docker-compose up -d
docker-compose logs -f
```

**Option C: FastAPI Server**
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8060
```

**Option D: Reprocess Markdown Only**
```bash
python scripts/reprocess_from_markdown.py
```

**Option E: Retry Failed Files**
```bash
python scripts/retry_failed_files.py
```

---

## 📦 Components

### Core Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Config Loader** | Environment & validation | Pydantic, python-dotenv |
| **R2 Client** | Object storage operations | boto3, S3-compatible |
| **File Hasher** | Deduplication hashing | xxHash64, MD5 |
| **Log Manager** | JSON logging & tracking | Thread-safe file I/O |
| **Docling Client** | Document conversion | REST API, async |
| **Markdown Storage** | Markdown persistence | R2 mirrored structure |
| **Semantic Chunker** | Intelligent splitting | LangChain, tiktoken |
| **Embedding Client** | Vector generation | Ollama API |
| **Qdrant Uploader** | Vector storage | Qdrant Python SDK |

### Component Details

#### 1. Config Loader (`src/components/config.py`)
- **Pydantic models** for type safety
- **Environment variable** loading with defaults
- **Validation** for required fields
- **Nested configuration** for services

#### 2. R2 Client (`src/components/r2_client.py`)
- **S3-compatible** operations
- **List, download, upload** files
- **Memory-efficient** streaming
- **Error handling** with retries

#### 3. File Hasher (`src/components/file_hasher.py`)
- **xxHash64** for lightweight hashing (deduplication)
- **MD5** for full file hashing (tracking)
- **Chunk hashing** for content tracking
- **Text hashing** for filename keys

#### 4. Log Manager (`src/components/log_manager.py`)
- **Thread-safe** JSON operations
- **8 logging methods** for different operations
- **Deduplication checks** (log + Qdrant)
- **Atomic writes** to prevent corruption

#### 5. Docling Client (`src/components/docling_client.py`)
- **Async conversion** with polling
- **Health checks** for service monitoring
- **Timeout handling** for long documents
- **Error recovery** with retries

#### 6. Markdown Storage (`src/components/markdown_storage.py`)
- **Mirrored structure** (source/ → markdown/)
- **R2 upload** with metadata
- **Path preservation** for organization
- **UTF-8 encoding** for compatibility

#### 7. Semantic Chunker (`src/components/chunker.py`)
- **LangChain** RecursiveCharacterTextSplitter
- **Token-based** chunking (500 tokens)
- **Metadata preservation** (page, type)
- **Hash generation** per chunk

#### 8. Embedding Client (`src/components/embedding_client.py`)
- **Dual models** (filename + content)
- **Batch processing** for efficiency
- **Deduplication** (log + Qdrant)
- **Phase 3 logging** with model tracking

#### 9. Qdrant Uploader (`src/components/qdrant_uploader.py`)
- **Batch uploads** (configurable size)
- **UUID generation** for point IDs
- **Metadata indexing** (md5_hash, filename)
- **Phase 3 logging** with point counts

---

## 🎯 Phase 3: Advanced Deduplication

### Overview

Phase 3 introduces intelligent deduplication to prevent redundant processing and save resources.

### Features

✅ **xxHash64 Hashing** - Fast, collision-resistant file hashing  
✅ **Log-Based Dedup** - Check `embedding.json` before embedding  
✅ **Qdrant Dedup** - Query collection before uploading  
✅ **Collection-Aware** - Separate tracking for filename vs content  
✅ **Graceful Fallback** - Handle missing indexes without crashing  
✅ **Force Reprocess** - Override deduplication when needed  

### How It Works

```python
# 1. Calculate file hash
file_hash = xxhash.xxh64(file_content).hexdigest()

# 2. Check embedding log
if log_manager.check_embedding_exists(file_hash, collection_name):
    return None  # Skip - already embedded

# 3. Check Qdrant collection
if qdrant_client.scroll(filter={"md5_hash": file_hash}):
    return None  # Skip - already in Qdrant

# 4. Generate embeddings (only if new)
embeddings = generate_embeddings(chunks)

# 5. Log success
log_manager.log_embedding_success(filename, file_hash, collection_name)
```

### Deduplication Logs

#### `embedding.json`
```json
{
  "filename": "document.pdf",
  "md5_hash": "a7dbfc772beecd56",
  "collection_name": "content",
  "chunks_created": 26,
  "embedding_time": 7.46,
  "model_name": "bge-m3",
  "timestamp": "2025-11-11T20:00:00Z"
}
```

#### `skipped.json`
```json
{
  "filename": "document.pdf",
  "md5_hash": "a7dbfc772beecd56",
  "skip_reason": "already_embedded",
  "found_in": "log_file",
  "collection_name": "content",
  "timestamp": "2025-11-11T20:01:00Z"
}
```

### Force Reprocess

Override deduplication when needed:

```bash
# Force re-embed everything
FORCE_REPROCESS=true python src/pipeline.py

# Or set in .env
FORCE_REPROCESS=true
```

---

## 📜 Scripts

### 1. Main Pipeline (`src/pipeline.py`)

**Full pipeline from source files to Qdrant**

```bash
python src/pipeline.py
```

**Features:**
- Downloads from R2 source directory
- Converts via Docling
- Uploads markdown to R2
- Chunks and embeds
- Uploads to Qdrant
- Comprehensive logging

**Use When:**
- Processing new source files (PDF, DOCX)
- First-time ingestion
- Need full conversion pipeline

---

### 2. Reprocess Script (`scripts/reprocess_from_markdown.py`)

**Reprocess from existing markdown files (skip conversion)**

```bash
python scripts/reprocess_from_markdown.py
```

**Features:**
- Downloads from R2 markdown directory
- Skips Docling conversion (faster)
- Re-chunks and re-embeds
- Uploads to Qdrant
- Phase 3 deduplication

**Use When:**
- Markdown files already exist
- Want to re-embed with different models
- Need to recreate Qdrant collections
- Docling service is unavailable

---

### 3. Retry Failed Files (`scripts/retry_failed_files.py`)

**Automatically retry files that failed in previous runs**

```bash
# Retry all failed files
python scripts/retry_failed_files.py

# Preview without processing
python scripts/retry_failed_files.py --dry-run

# Force re-embed
FORCE_REPROCESS=true python scripts/retry_failed_files.py
```

**Features:**
- Reads `failed.json` automatically
- Searches R2 recursively (source + markdown)
- Routes to appropriate pipeline
- Removes successes from `failed.json`
- Detailed progress reporting

**Use When:**
- Files failed due to temporary issues
- Network interruptions occurred
- Service was unavailable
- Want to clean up failed.json

---

### 4. Setup Collections (`scripts/setup_qdrant_collections.py`)

**Create Qdrant collections with proper schema**

```bash
python scripts/setup_qdrant_collections.py
```

**Features:**
- Creates filename collection (384D, Cosine)
- Creates content collection (1024D, Cosine)
- Configures HNSW indexing
- Creates payload indexes (md5_hash, filename)
- Validates configuration

---

### 5. Create Indexes (`scripts/create_payload_indexes_advanced.py`)

**Interactive payload index creation**

```bash
python scripts/create_payload_indexes_advanced.py
```

**Features:**
- Interactive field selection
- All 8 index types supported
- Configuration guidance
- Validation and verification
- Manual index creation option

---

## 🌐 API Endpoints

### Health & Status

#### `GET /health`
Check service health

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "docling": true,
    "qdrant": true,
    "ollama": true
  }
}
```

#### `GET /api/pipeline/status/{task_id}`
Get pipeline task status

**Response:**
```json
{
  "task_id": "abc123",
  "status": "completed",
  "progress": {
    "processed": 50,
    "failed": 2,
    "total": 52
  }
}
```

#### `GET /api/pipeline/summary`
Get processing summary

**Response:**
```json
{
  "total_files": 500,
  "processed": 495,
  "failed": 5,
  "last_run": "2025-11-11T20:00:00Z"
}
```

### Pipeline Control

#### `POST /api/pipeline/start`
Start ingestion pipeline

**Request:**
```json
{
  "limit": 100,
  "force_reprocess": false
}
```

**Response:**
```json
{
  "task_id": "abc123",
  "status": "started"
}
```

### Logs

#### `GET /api/logs/conversion`
Get conversion log

#### `GET /api/logs/upload`
Get upload log

#### `GET /api/logs/failed`
Get failed files log

#### `GET /api/logs/embedding`
Get embedding log

#### `GET /api/logs/skipped`
Get skipped files log

### Collections

#### `GET /api/collections/info`
Get Qdrant collection information

**Response:**
```json
{
  "filenames": {
    "points_count": 500,
    "vectors_count": 500,
    "indexed_vectors_count": 500
  },
  "content": {
    "points_count": 12500,
    "vectors_count": 12500,
    "indexed_vectors_count": 12500
  }
}
```

---

## ⚙️ Configuration

### Environment Variables

#### Cloudflare R2
```bash
R2_ENDPOINT=https://account.r2.cloudflarestorage.com
R2_ACCESS_KEY=your-access-key
R2_SECRET_KEY=your-secret-key
R2_BUCKET_NAME=releasenotes
R2_SOURCE_PREFIX=source/
R2_MARKDOWN_PREFIX=markdown/
```

#### Qdrant
```bash
QDRANT_HOST=your-host
QDRANT_PORT=6333
QDRANT_USE_HTTPS=true
QDRANT_API_KEY=your-api-key
QDRANT_PREFER_GRPC=true
QDRANT_GRPC_PORT=6334
QDRANT_FILENAME_COLLECTION=filenames
QDRANT_CONTENT_COLLECTION=content
```

#### Ollama
```bash
OLLAMA_HOST=127.0.0.1
OLLAMA_PORT=11434
OLLAMA_FILENAME_MODEL=granite-embedding:30m
OLLAMA_CONTENT_MODEL=bge-m3
OLLAMA_TRUNCATE=true
OLLAMA_KEEP_ALIVE=5m
```

#### Docling
```bash
DOCLING_BASE_URL=http://docling:5010
DOCLING_TIMEOUT=300
DOCLING_POLL_INTERVAL=2
```

#### Chunking
```bash
CHUNK_SIZE_TOKENS=500
CHUNK_OVERLAP_TOKENS=0
```

#### Logging
```bash
LOG_DIR=logs/
CONVERSION_LOG=conversion.json
UPLOAD_LOG=upload.json
FAILED_LOG=failed.json
EMBEDDING_LOG=embedding.json
QDRANT_UPLOAD_LOG=qdrant_upload.json
SKIPPED_LOG=skipped.json
```

#### Phase 3
```bash
FORCE_REPROCESS=false
QDRANT_BATCH_SIZE=100
LOG_EMBEDDINGS=true
LOG_QDRANT_UPLOADS=true
LOG_SKIPPED_FILES=true
```

---

## 📊 Monitoring & Logging

### Log Files

| Log File | Purpose | Format |
|----------|---------|--------|
| `conversion.json` | Docling conversions | filename, hash, timestamp |
| `upload.json` | Successful uploads | filename, hash, timestamp |
| `failed.json` | Failed operations | filename, hash, error, stage |
| `embedding.json` | Embedding operations | filename, hash, model, chunks, time |
| `qdrant_upload.json` | Qdrant uploads | filename, hash, points, time |
| `skipped.json` | Deduplicated files | filename, hash, reason, found_in |

### Metrics

```bash
# Check processing stats
cat logs/embedding.json | jq 'length'  # Total embeddings
cat logs/failed.json | jq 'length'     # Total failures
cat logs/skipped.json | jq 'length'    # Total skipped

# Average embedding time
cat logs/embedding.json | jq '[.[].embedding_time] | add/length'

# Failures by stage
cat logs/failed.json | jq 'group_by(.stage) | map({stage: .[0].stage, count: length})'

# Skip reasons
cat logs/skipped.json | jq 'group_by(.skip_reason) | map({reason: .[0].skip_reason, count: length})'
```

### Monitoring Dashboard

Use n8n workflow (`n8n/monitoring_workflow.json`) for:
- Daily processing reports
- Failure alerts
- Collection size tracking
- Service health monitoring

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Docling Service Unreachable
```bash
# Check service
curl http://docling-service:5010/health

# Restart service
docker-compose restart docling
```

#### 2. Ollama Models Missing
```bash
# Pull required models
ollama pull granite-embedding:30m
ollama pull bge-m3

# Verify models
ollama list
```

#### 3. Qdrant Connection Failed
```bash
# Check Qdrant
curl https://your-qdrant-host:6333/collections

# Verify API key
curl -H "api-key: your-key" https://your-qdrant-host:6333/collections
```

#### 4. Failed Files Not Logged
```bash
# Update to latest version
git pull origin main

# Failed files now logged automatically
cat logs/failed.json
```

#### 5. Deduplication Not Working
```bash
# Check if index exists
python scripts/create_payload_indexes_advanced.py

# Create md5_hash index if missing
# Select collection → Select md5_hash field → Create keyword index
```

#### 6. Memory Issues
```bash
# Reduce batch size
export QDRANT_BATCH_SIZE=50

# Enable on-disk storage in Qdrant
QDRANT_CONTENT_ON_DISK_PAYLOAD=true
```

---

## 📚 Documentation

### Core Documentation
- **[env.example](env.example)** - Complete configuration reference
- **[docs/SYSTEM_SPEC.md](docs/SYSTEM_SPEC.md)** - System-level architecture and implementation spec
- **[docs/PHASE_3_ENHANCEMENTS.md](docs/PHASE_3_ENHANCEMENTS.md)** - Phase 3 deduplication and logging design
- **[VERSION](VERSION)** - Current version

### Guides
- **[docs/QDRANT.md](docs/QDRANT.md)** - Qdrant setup and schema
- **[docs/INDEXING_GUIDE.md](docs/INDEXING_GUIDE.md)** - Complete indexing guide
- **[docs/DOCKER.md](docs/DOCKER.md)** - Docker deployment and operations
- **[docs/CHANGELOG.md](docs/CHANGELOG.md)** - Version history
- **[docs/archived/REFERENCE_legacy.md](docs/archived/REFERENCE_legacy.md)** - Legacy technical reference

### API Documentation
- **FastAPI Docs** - http://localhost:8060/docs (when running)
- **ReDoc** - http://localhost:8060/redoc (when running)

---

## ⚡ Performance

### Benchmarks

**Test Environment:**
- 500 PDF documents
- Average size: 2MB
- Total size: 1GB

**Results:**
- **Conversion:** ~30s per document (Docling)
- **Chunking:** ~0.5s per document
- **Embedding:** ~8s per document (26 chunks avg)
- **Upload:** ~2s per document
- **Total:** ~40s per document

**With Deduplication:**
- **First Run:** 40s per document
- **Subsequent Runs:** <1s per document (skipped)
- **Resource Savings:** 97.5% time saved

### Optimization Tips

1. **Use Reprocess Script** - Skip conversion when possible
2. **Enable Deduplication** - Avoid redundant processing
3. **Increase Batch Size** - Faster Qdrant uploads
4. **Use gRPC** - Better Qdrant performance
5. **Enable On-Disk** - Save RAM in Qdrant
6. **Docker Deployment** - Better resource management

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run linters
flake8 src/ api/
black src/ api/

# Type checking
mypy src/
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 👥 Authors

**Release Notes Search Team**

- AI-powered document processing
- Vector search optimization
- Production deployment

---

## 🔗 Links

- **Repository:** https://github.com/Crypto-Gi/release-notes-ingestion
- **Issues:** https://github.com/Crypto-Gi/release-notes-ingestion/issues
- **Qdrant:** https://qdrant.tech/
- **Ollama:** https://ollama.ai/
- **Docling:** https://github.com/DS4SD/docling

---

## 📈 Roadmap

### v0.5.0 (Planned)
- [ ] Multi-language support
- [ ] Advanced RAG features
- [ ] Real-time processing
- [ ] Web UI dashboard

### v0.6.0 (Future)
- [ ] Distributed processing
- [ ] Advanced analytics
- [ ] Custom model support
- [ ] API rate limiting

---

## 🙏 Acknowledgments

- **Qdrant** - High-performance vector database
- **Ollama** - Local LLM inference
- **Docling** - Document conversion
- **LangChain** - Semantic chunking
- **FastAPI** - Modern API framework

---

**Last Updated:** November 11, 2025  
**Version:** 0.4.1  
**Status:** ✅ Production Ready

---

## 🔍 Keywords

`document processing` `vector embeddings` `semantic search` `RAG` `Qdrant` `Ollama` `AI pipeline` `PDF conversion` `markdown processing` `deduplication` `FastAPI` `Docker` `Python` `machine learning` `NLP` `information retrieval` `knowledge base` `release notes` `technical documentation`
