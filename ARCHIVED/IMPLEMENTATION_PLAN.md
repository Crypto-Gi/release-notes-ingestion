# Release Notes Ingestion Pipeline - Implementation Plan

## 📋 Document Information

**Project:** Release Notes Ingestion Pipeline  
**Version:** 1.0  
**Last Updated:** November 7, 2025  
**Status:** ✅ **FULLY IMPLEMENTED - PRODUCTION READY**  
**Original Timeline:** 9-10 days  
**Actual Completion:** November 7, 2025

---

## 🎉 **IMPLEMENTATION COMPLETE**

This document contains the **original implementation plan**. For complete implementation status, detailed documentation, and agent knowledge base, see:

📖 **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** - Complete implementation documentation with:
- All components implemented (100% complete)
- Comprehensive configuration guide
- Critical implementation details
- Issues fixed and resolutions
- Production deployment instructions
- Knowledge base for future reference
- No assumptions - everything documented

**Quick Links:**
- Implementation Status: [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)
- Setup Guide: [SETUP_GUIDE.md](SETUP_GUIDE.md)
- Configuration: [CONFIGURATION.md](CONFIGURATION.md)
- Qdrant Setup: [QDRANT_SETUP.md](QDRANT_SETUP.md)
- Docker Guide: [DOCKER.md](DOCKER.md)
- Testing Guide: [TESTING_GUIDE.md](TESTING_GUIDE.md)  

---

## 🎯 Project Overview

### Purpose
Build an automated ingestion pipeline to:
1. Read PDF/Word documents from Cloudflare R2 bucket
2. Convert documents to Markdown using Docling service
3. Chunk markdown content semantically (500 tokens, no overlap)
4. Generate embeddings using Ollama (granite-embedding:30m and bge-m3)
5. Upload to Qdrant vector database (two collections)
6. Enable two-stage vector search via existing search-api

### Key Requirements
- ✅ Incremental processing (skip already processed files via hash tracking)
- ✅ Hash-based file tracking with JSON logs
- ✅ Mirrored directory structure for markdown files in R2
- ✅ Two-collection Qdrant upload (filename + content)
- ✅ Full compatibility with existing search-api
- ✅ Robust error handling and retry logic

---

## 🏗️ Architecture Overview

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Pipeline Core** | Python 3.9+ | Main processing logic |
| **Orchestration** | n8n | Scheduling & monitoring |
| **Storage** | Cloudflare R2 (S3) | Source files & markdown |
| **Conversion** | Docling Service | PDF/Word → Markdown |
| **Chunking** | LangChain | Semantic text splitting |
| **Embeddings** | Ollama | Vector generation |
| **Vector DB** | Qdrant | Vector storage & search |
| **Logging** | JSON files | Processing tracking |

### Data Flow

```
Cloudflare R2 Bucket (Source Files)
         ↓
   File Discovery & Hashing
         ↓
   Check Conversion Log → Skip if exists
         ↓
   Docling Service (PDF/Word → Markdown)
         ↓
   Store Markdown in R2 (mirrored structure)
         ↓
   Log Conversion Success
         ↓
   Check Upload Log → Skip if exists
         ↓
   Semantic Chunking (500 tokens)
         ↓
   Generate Embeddings (Ollama)
         ↓
   Upload to Qdrant (2 collections)
         ↓
   Log Upload Success
```

---

## 📂 Project Structure

```
/home/mir/projects/release-notes-ingestion/
├── .env                          # Environment configuration
├── .gitignore                    # Git ignore rules
├── requirements.txt              # Python dependencies
├── README.md                     # Project documentation
├── IMPLEMENTATION_PLAN.md        # This document
├── QDRANT_COLLECTIONS.md         # Qdrant schema reference
│
├── src/                          # Source code
│   ├── __init__.py
│   ├── config.py                 # Configuration loader
│   ├── r2_client.py              # R2/S3 operations
│   ├── file_hasher.py            # File hashing logic
│   ├── log_manager.py            # JSON log operations
│   ├── docling_client.py         # Docling API client
│   ├── markdown_storage.py       # Markdown file storage
│   ├── chunker.py                # Semantic chunking
│   ├── embedding_client.py       # Ollama embeddings
│   ├── qdrant_uploader.py        # Qdrant operations
│   └── pipeline.py               # Main pipeline orchestrator
│
├── logs/                         # JSON logs
│   ├── conversion.json           # Conversion tracking
│   ├── upload.json               # Upload tracking
│   └── failed.json               # Failed files tracking
│
├── scripts/                      # Utility scripts
│   ├── run_pipeline.py           # Main entry point
│   ├── verify_logs.py            # Log verification
│   ├── reset_logs.py             # Log reset utility
│   └── test_connections.py       # Connection testing
│
├── tests/                        # Unit tests
│   ├── test_hasher.py
│   ├── test_chunker.py
│   ├── test_qdrant_uploader.py
│   └── test_pipeline.py
│
└── n8n/                          # n8n workflows
    ├── ingestion_workflow.json   # Main workflow
    └── monitoring_workflow.json  # Monitoring workflow
```

---

## 🔧 Configuration Specifications

### Environment Variables (.env)

```bash
# ============================================
# R2/S3 Configuration
# ============================================
R2_ENDPOINT_URL=https://your-account.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET_NAME=your-bucket-name
R2_SOURCE_PREFIX=source/
R2_MARKDOWN_PREFIX=markdown/

# ============================================
# Docling Service Configuration
# ============================================
DOCLING_URL=http://docling.mynetwork.ing
DOCLING_TIMEOUT=300
DOCLING_MAX_RETRIES=3
DOCLING_RETRY_DELAY=5

# ============================================
# Qdrant Configuration
# ============================================
QDRANT_HOST=192.168.254.22
QDRANT_PORT=6333
FILENAME_COLLECTION=filename-granite-embedding30m
CONTENT_COLLECTION=releasenotes-bge-m3

# ============================================
# Ollama Configuration
# ============================================
OLLAMA_HOST=192.168.254.22
OLLAMA_PORT=11434
FILENAME_EMBEDDING_MODEL=granite-embedding:30m
CONTENT_EMBEDDING_MODEL=bge-m3
EMBEDDING_TIMEOUT=30

# ============================================
# Chunking Configuration
# ============================================
CHUNK_SIZE_TOKENS=500
CHUNK_OVERLAP_TOKENS=0
DETECT_ELEMENT_TYPES=true

# ============================================
# Processing Configuration
# ============================================
BATCH_SIZE=100
MAX_RETRIES=3
RETRY_DELAY=5
PARALLEL_PROCESSING=false

# ============================================
# Logging Configuration
# ============================================
LOG_DIR=logs/
CONVERSION_LOG=logs/conversion.json
UPLOAD_LOG=logs/upload.json
FAILED_LOG=logs/failed.json
LOG_LEVEL=INFO
```

### Python Dependencies (requirements.txt)

```
# Core Dependencies
boto3>=1.34.0              # S3/R2 client
qdrant-client>=1.7.0       # Qdrant operations
langchain>=0.1.0           # Chunking & text splitting
tiktoken>=0.5.0            # Token counting
requests>=2.31.0           # HTTP requests
python-dotenv>=1.0.0       # Environment variables
pydantic>=2.5.0            # Data validation
tenacity>=8.2.0            # Retry logic
xxhash>=3.4.0              # Lightweight hashing (optional: use CRC32 from zlib if not available)

# Development & Testing
pytest>=7.4.0              # Testing framework
pytest-cov>=4.1.0          # Coverage reporting
black>=23.0.0              # Code formatting
flake8>=6.0.0              # Linting
```

---

## 📊 Data Specifications

### 1. Qdrant Collection: filename-granite-embedding30m

**Purpose:** Fast filename indexing and document discovery (Stage 1 search)

**Configuration:**
- Vector Dimensions: 384
- Embedding Model: granite-embedding:30m
- Distance Metric: Cosine
- Payload Indexing: ✅ Enabled with word tokenizer

**Payload Structure:**
```json
{
  "pagecontent": "Orchestrator_Release_Notes_Version_9.3.4_RevA.pdf",
  "source": "Orchestrator_Release_Notes_Version_9.3.4_RevA.pdf",
  "metadata": {
    "hash": "e06ca683e7aef63c3663f0fa41273562"
  }
}
```

**Payload Fields:**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `pagecontent` | string | Filename **with extension** | `"ECOS_9.3.7.1_Release_Notes.pdf"` |
| `source` | string | Same as pagecontent (original filename with extension) | `"ECOS_9.3.7.1_Release_Notes.pdf"` |
| `metadata.hash` | string | Lightweight hash of file (xxHash or CRC32) | `"e06ca683..."` |

**Key Rules:**
- ✅ Keep original file extension in `pagecontent` (.pdf, .docx, etc.)
- ✅ Keep original file extension in `source` (same as pagecontent)
- ✅ Add lightweight hash in `metadata.hash` (xxHash or CRC32)
- ✅ One point per source file
- ✅ Point ID: UUID based on original filename

**Example Transformation:**
```
Input:  "ECOS_9.3.7.1_Release_Notes.pdf"
Output: {
  "pagecontent": "ECOS_9.3.7.1_Release_Notes.pdf",
  "source": "ECOS_9.3.7.1_Release_Notes.pdf",
  "metadata": {
    "hash": "a3f5b9c2d8e1f4a7"
  }
}
```

---

### 2. Qdrant Collection: releasenotes-bge-m3

**Purpose:** Semantic content search within documents (Stage 2 search)

**Configuration:**
- Vector Dimensions: 1024
- Embedding Model: bge-m3
- Distance Metric: Cosine
- Payload Indexing: ❌ No text indexing (pure vector search)

**Payload Structure:**
```json
{
  "pagecontent": "# Bug Fixes\n\nFixed memory leak in authentication module...",
  "metadata": {
    "filename": "Orchestrator_Release_Notes_Version_9.3.4_RevA.pdf",
    "page_number": 1,
    "element_type": "Text",
    "md5_hash": "e06ca683e7aef63c3663f0fa41273562"
  }
}
```

**Metadata Fields (Required):**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `filename` | string | Filename **with extension** | `"ECOS_9.3.7.1_Release_Notes.pdf"` |
| `page_number` | integer | Sequential chunk number (1, 2, 3...) | `1` |
| `element_type` | string | Content type (Text/Table/Image/List) | `"Text"` |
| `md5_hash` | string | MD5 hash of chunk content | `"e06ca683..."` |

**Key Rules:**
- ✅ Keep original file extension in `metadata.filename` (.pdf, .docx, etc.)
- ✅ `page_number` = sequential chunk number per file (starts at 1)
- ✅ `md5_hash` = hash of chunk content (not file)
- ✅ `element_type` = auto-detected from markdown syntax
- ✅ Multiple points per file (one per chunk)
- ✅ Point ID: UUID based on filename + chunk number

**Element Type Detection:**
```
"Text"  → Default for paragraphs and headers
"Table" → Detected by markdown table syntax (|---|)
"Image" → Detected by markdown image syntax (![...])
"List"  → Detected by list markers (-, *, 1.)
```

---

### 3. JSON Log Format

**Purpose:** Track processed files to enable incremental updates

**Log Files:**
1. `logs/conversion.json` - Successfully converted files
2. `logs/upload.json` - Successfully uploaded files
3. `logs/failed.json` - Failed files with error details

**Entry Structure:**
```json
[
  {
    "filename": "source/orchestrator/release1/Orchestrator_9.3.4.pdf",
    "hash": "e06ca683e7aef63c3663f0fa41273562",
    "datetime": "2025-11-07T05:30:15.123456Z"
  }
]
```

**Field Specifications:**
- `filename`: Full R2 path (e.g., "source/ecos/release1/file.pdf")
- `hash`: MD5 hash of file content (32 hex characters)
- `datetime`: ISO 8601 format with timezone (UTC)

**Log Operations:**
- Load entire log into memory at startup
- Use in-memory set for O(1) lookup performance
- Append new entries during processing
- Atomic write at end (temp file + rename)

---

### 4. Markdown Storage Structure

**Purpose:** Store converted markdown files with mirrored directory structure

**Directory Mapping:**
```
Source Structure:
source/
├── orchestrator/
│   ├── release1/
│   │   └── Orchestrator_9.3.4_RevA.pdf
│   └── release2/
│       └── Orchestrator_9.3.5_RevB.pdf
├── ecos/
│   ├── release1/
│   │   └── ECOS_9.3.7.1_Release_Notes.pdf
│   └── release2/
└── srx/

Markdown Structure (Mirrored):
markdown/
├── orchestrator/
│   ├── release1/
│   │   └── Orchestrator_9.3.4_RevA.md
│   └── release2/
│       └── Orchestrator_9.3.5_RevB.md
├── ecos/
│   ├── release1/
│   │   └── ECOS_9.3.7.1_Release_Notes.md
│   └── release2/
└── srx/
```

**Path Transformation Rules:**
1. Replace `source/` prefix with `markdown/`
2. Preserve all subdirectories exactly
3. Change file extension to `.md`
4. Keep original filename (without extension change)

**Example:**
```
Input:  source/ecos/release1/ECOS_9.3.7.1_Release_Notes.pdf
Output: markdown/ecos/release1/ECOS_9.3.7.1_Release_Notes.md
```

---

## 🔨 Component Specifications

### Component 1: Configuration Loader (config.py)

**Purpose:** Load and validate all environment variables

**Key Functions:**
```python
class Config:
    # R2 Configuration
    r2_endpoint_url: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_bucket_name: str
    r2_source_prefix: str
    r2_markdown_prefix: str
    
    # Docling Configuration
    docling_url: str
    docling_timeout: int
    docling_max_retries: int
    
    # Qdrant Configuration
    qdrant_host: str
    qdrant_port: int
    filename_collection: str
    content_collection: str
    
    # Ollama Configuration
    ollama_host: str
    ollama_port: int
    filename_embedding_model: str
    content_embedding_model: str
    
    # Chunking Configuration
    chunk_size_tokens: int
    chunk_overlap_tokens: int
    
    @classmethod
    def load_from_env() -> Config:
        """Load configuration from .env file"""
    
    def validate(self):
        """Validate all configuration values"""
```

**Validation Checks:**
- Verify all required environment variables are set
- Test R2 connection
- Test Docling service availability
- Test Qdrant connection
- Test Ollama connection

---

### Component 2: R2 Client (r2_client.py)

**Purpose:** Handle all R2/S3 operations

**Key Functions:**
```python
class R2Client:
    def __init__(endpoint_url, access_key, secret_key, bucket_name)
    
    def list_files_recursive(prefix: str) -> List[FileInfo]:
        """
        Recursively list all files under prefix
        Returns: [{key, size, last_modified, etag}]
        """
    
    def download_file(key: str) -> bytes:
        """Download file content as bytes"""
    
    def upload_file(key: str, content: bytes, content_type: str):
        """Upload file to R2 with content type"""
    
    def file_exists(key: str) -> bool:
        """Check if file exists in bucket"""
```

**Implementation Details:**
- Use `boto3.client('s3', endpoint_url=R2_ENDPOINT_URL)`
- Paginate results with `list_objects_v2` for large buckets
- Stream large files (>100MB) to avoid memory issues
- Handle connection errors with retry logic

---

### Component 3: File Hasher (file_hasher.py)

**Purpose:** Generate fast, consistent file hashes

**Key Functions:**
```python
def hash_file_lightweight(file_content: bytes) -> str:
    """
    Generate lightweight hash for filename collection (xxHash or CRC32)
    Returns: 16-character hex string (64-bit)
    Fastest option for deduplication
    """

def hash_file(file_content: bytes) -> str:
    """
    Generate MD5 hash of file content for logs
    Returns: 32-character hex string
    """

def hash_file_fast(file_content: bytes, size: int) -> str:
    """
    For large files: hash first 1MB + file size
    Returns: 32-character hex string
    """

def hash_text(text: str) -> str:
    """
    Generate MD5 hash of text (for chunks)
    Returns: 32-character hex string
    """
```

**Hashing Strategy:**
- **Filename collection metadata**: xxHash64 or CRC32 (ultra-fast, 8-16 chars)
- **Content collection chunks**: MD5 (standard, 32 chars)
- **Log tracking**: MD5 (standard, 32 chars)
- Files <10MB: Hash entire content
- Files ≥10MB: Hash first 1MB + file size

**Hash Algorithm Comparison:**
- **xxHash64**: Fastest, 16-char hex, non-cryptographic (recommended)
- **CRC32**: Very fast, 8-char hex, non-cryptographic
- **MD5**: Fast, 32-char hex, sufficient for deduplication

---

### Component 4: Log Manager (log_manager.py)

**Purpose:** Manage JSON logs with atomic operations

**Key Functions:**
```python
class LogManager:
    def __init__(log_path: str)
    
    def load_log() -> List[Dict]:
        """Load existing log entries from disk"""
    
    def is_processed(filename: str, hash: str) -> bool:
        """Check if file already processed (O(1) lookup)"""
    
    def add_entry(filename: str, hash: str):
        """Add new entry with current UTC datetime"""
    
    def save_log():
        """Atomic write to disk (temp file + rename)"""
```

**Data Structures:**
```python
# In-memory storage for fast lookups
self._entries: List[Dict] = []
self._lookup: Set[Tuple[str, str]] = set()  # (filename, hash)
```

**Atomic Write Process:**
1. Write to temporary file: `conversion.json.tmp`
2. Flush and sync to disk
3. Rename to final name: `conversion.json`

---

### Component 5: Docling Client (docling_client.py)

**Purpose:** Convert PDF/Word documents to Markdown

**Key Functions:**
```python
class DoclingClient:
    def __init__(base_url: str, timeout: int)
    
    def convert_to_markdown(file_content: bytes, filename: str) -> str:
        """
        Convert file to markdown via Docling API
        
        Steps:
        1. POST /api/convert (upload file)
        2. Poll /api/status/{task_id} until complete
        3. GET /api/result/{task_id}/json
        
        Returns: markdown content string
        """
```

**API Flow:**
```
1. POST http://docling.mynetwork.ing/api/convert
   Response: {"task_id": "abc123..."}

2. Poll GET /api/status/{task_id} every 3 seconds
   Wait for: {"status": "completed"}

3. GET /api/result/{task_id}/json
   Response: {"markdown_content": "# Title\n\n..."}
```

---

### Component 6: Markdown Storage (markdown_storage.py)

**Purpose:** Store markdown with mirrored directory structure

**Key Functions:**
```python
class MarkdownStorage:
    def get_markdown_path(source_path: str) -> str:
        """
        Transform: source/ecos/file.pdf → markdown/ecos/file.md
        """
    
    def save_markdown(source_path: str, markdown_content: str):
        """Upload markdown to R2 with mirrored path"""
```

---

### Component 7: Chunker (chunker.py)

**Purpose:** Semantic chunking of markdown content

**Key Functions:**
```python
class SemanticChunker:
    def chunk_markdown(markdown_content: str, filename: str) -> List[Chunk]:
        """
        Returns: [{
            "text": "chunk content",
            "metadata": {
                "filename": "file.pdf",  # Keep extension
                "page_number": 1,
                "element_type": "Text",
                "md5_hash": "hash"
            }
        }]
        """
    
    def detect_element_type(chunk_text: str) -> str:
        """Detect: Text, Table, Image, List"""
```

**Element Type Detection:**
```python
def detect_element_type(chunk_text: str) -> str:
    text = chunk_text.strip()
    
    if '|' in text and ('---' in text or text.startswith('|')):
        return "Table"
    elif '![' in text:
        return "Image"
    elif text.startswith(('- ', '* ', '+ ')) or re.match(r'^\d+\. ', text):
        return "List"
    else:
        return "Text"
```

---

### Component 8: Embedding Client (embedding_client.py)

**Purpose:** Generate embeddings via Ollama

**Key Functions:**
```python
class EmbeddingClient:
    def generate_embedding(text: str, model: str) -> List[float]:
        """Generate single embedding (384 or 1024 dimensions)"""
    
    def generate_batch_embeddings(texts: List[str], model: str) -> List[List[float]]:
        """Generate embeddings in batch (10 at a time)"""
```

**API Call:**
```python
POST http://192.168.254.22:11434/api/embeddings
{
    "model": "bge-m3",
    "prompt": "text to embed"
}
```

---

### Component 9: Qdrant Uploader (qdrant_uploader.py)

**Purpose:** Upload to both Qdrant collections

**Key Functions:**
```python
class QdrantUploader:
    def upload_filename(filename: str, embedding: List[float], file_hash: str):
        """
        Upload to filename-granite-embedding30m
        - pagecontent: filename with extension (.pdf, .docx, etc.)
        - source: same as pagecontent (original filename with extension)
        - metadata.hash: lightweight hash (xxHash64 or CRC32)
        """
    
    def upload_content_chunks(filename: str, chunks: List[Chunk], embeddings: List[List[float]]):
        """
        Upload to releasenotes-bge-m3
        - Keep extension in metadata.filename (.pdf, .docx, etc.)
        - Sequential page_number
        - MD5 hash per chunk
        """
    
```

---

## 🔄 n8n Orchestration

### Overview

n8n will orchestrate the entire ingestion pipeline, providing scheduling, monitoring, error handling, and workflow management.

### n8n Workflow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    n8n Main Workflow                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Schedule Trigger (Cron)                                │
│     ↓                                                       │
│  2. List R2 Files (HTTP Request to Python API)             │
│     ↓                                                       │
│  3. Filter New Files (Check against logs)                  │
│     ↓                                                       │
│  4. For Each File:                                         │
│     ├─ Download from R2                                    │
│     ├─ Hash File                                           │
│     ├─ Convert via Docling                                 │
│     ├─ Upload Markdown to R2                               │
│     ├─ Chunk Content                                       │
│     ├─ Generate Embeddings                                 │
│     ├─ Upload to Qdrant                                    │
│     └─ Update Logs                                         │
│     ↓                                                       │
│  5. Send Summary Notification                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Workflow Components

#### 1. **Schedule Trigger Node**
- **Type:** Cron
- **Schedule:** Daily at 2:00 AM (configurable)
- **Alternative:** Webhook trigger for manual runs

#### 2. **Python API Wrapper**
Create a FastAPI wrapper for the Python pipeline:

```python
# api/main.py
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

app = FastAPI()

@app.post("/list-files")
async def list_r2_files():
    """List all files in R2 bucket"""
    return {"files": [...]}

@app.post("/process-file")
async def process_file(file_path: str, background_tasks: BackgroundTasks):
    """Process single file through pipeline"""
    background_tasks.add_task(run_pipeline, file_path)
    return {"status": "processing", "file": file_path}

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    """Get processing status"""
    return {"status": "completed", "task_id": task_id}
```

#### 3. **n8n Workflow Nodes**

**Node 1: Schedule Trigger**
```json
{
  "name": "Schedule Trigger",
  "type": "n8n-nodes-base.cron",
  "parameters": {
    "triggerTimes": {
      "item": [
        {
          "hour": 2,
          "minute": 0
        }
      ]
    }
  }
}
```

**Node 2: List R2 Files**
```json
{
  "name": "List R2 Files",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "method": "POST",
    "url": "http://localhost:8001/list-files",
    "responseFormat": "json"
  }
}
```

**Node 3: Filter New Files**
```json
{
  "name": "Filter New Files",
  "type": "n8n-nodes-base.function",
  "parameters": {
    "functionCode": "// Check against conversion.json log\nconst processedFiles = await fetch('http://localhost:8001/processed-files');\nconst newFiles = items.filter(file => !processedFiles.includes(file.hash));\nreturn newFiles;"
  }
}
```

**Node 4: Process Each File (Loop)**
```json
{
  "name": "Process File",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "method": "POST",
    "url": "http://localhost:8001/process-file",
    "body": {
      "file_path": "={{$json.file_path}}"
    }
  }
}
```

**Node 5: Error Handler**
```json
{
  "name": "Error Handler",
  "type": "n8n-nodes-base.function",
  "parameters": {
    "functionCode": "// Log error to failed.json\nawait fetch('http://localhost:8001/log-error', {\n  method: 'POST',\n  body: JSON.stringify({error: $json.error})\n});"
  }
}
```

**Node 6: Send Notification**
```json
{
  "name": "Send Summary",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "method": "POST",
    "url": "http://localhost:8001/send-summary",
    "body": {
      "processed": "={{$json.processed_count}}",
      "failed": "={{$json.failed_count}}"
    }
  }
}
```

### Python API Endpoints

The Python pipeline will expose these REST endpoints for n8n:

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/list-files` | POST | List all R2 files | `{"files": [...]}` |
| `/processed-files` | GET | Get processed file hashes | `{"hashes": [...]}` |
| `/process-file` | POST | Process single file | `{"task_id": "..."}` |
| `/status/{task_id}` | GET | Get task status | `{"status": "completed"}` |
| `/logs/conversion` | GET | Get conversion log | `[{...}]` |
| `/logs/upload` | GET | Get upload log | `[{...}]` |
| `/logs/failed` | GET | Get failed files | `[{...}]` |
| `/send-summary` | POST | Send processing summary | `{"sent": true}` |

### n8n Workflow Files

**1. Main Ingestion Workflow** (`n8n/ingestion_workflow.json`)
- Scheduled daily execution
- File discovery and filtering
- Batch processing with error handling
- Progress tracking and logging

**2. Monitoring Workflow** (`n8n/monitoring_workflow.json`)
- Check pipeline health
- Monitor Qdrant collection sizes
- Alert on failures
- Generate daily reports

**3. Manual Trigger Workflow** (`n8n/manual_trigger.json`)
- Webhook-based manual execution
- Single file processing
- Reprocess failed files

### Environment Variables for n8n

```bash
# n8n Configuration
N8N_HOST=0.0.0.0
N8N_PORT=5678
N8N_PROTOCOL=http

# Pipeline API
PIPELINE_API_URL=http://localhost:8001
PIPELINE_API_KEY=your-api-key-here

# Notification Settings
NOTIFICATION_WEBHOOK=https://your-webhook-url
NOTIFICATION_EMAIL=admin@example.com
```

### Monitoring & Alerts

n8n will monitor:
- ✅ **Pipeline Health:** Check if API is responsive
- ✅ **Processing Rate:** Files processed per hour
- ✅ **Error Rate:** Failed files percentage
- ✅ **Qdrant Status:** Collection point counts
- ✅ **R2 Storage:** Available space and file counts

### Error Handling Strategy

```
Error Occurs
    ↓
Log to failed.json
    ↓
Retry (max 3 attempts)
    ↓
If still fails:
    ├─ Send alert notification
    ├─ Skip file and continue
    └─ Add to manual review queue
```

### Deployment

**Docker Compose Setup:**
```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=0.0.0.0
      - N8N_PORT=5678
    volumes:
      - ./n8n:/home/node/.n8n
      - ./n8n/workflows:/workflows
    restart: unless-stopped

  pipeline-api:
    build: ./api
    ports:
      - "8001:8001"
    environment:
      - R2_ENDPOINT=${R2_ENDPOINT}
      - R2_ACCESS_KEY=${R2_ACCESS_KEY}
      - R2_SECRET_KEY=${R2_SECRET_KEY}
      - QDRANT_HOST=${QDRANT_HOST}
      - OLLAMA_HOST=${OLLAMA_HOST}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

### Benefits of n8n Orchestration

1. ✅ **Visual Workflow:** Easy to understand and modify
2. ✅ **Scheduling:** Built-in cron triggers
3. ✅ **Error Handling:** Automatic retries and alerts
4. ✅ **Monitoring:** Real-time execution tracking
5. ✅ **Scalability:** Can process files in parallel
6. ✅ **Flexibility:** Easy to add new steps or integrations
7. ✅ **No Code Changes:** Modify workflow without redeploying

---

## 🚀 Implementation Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1 | 1 day | Project structure + dependencies |
| Phase 2 | 3-4 days | All core components |
| Phase 3 | 1 day | Main script + CLI |
| Phase 4 | 1 day | n8n integration |
| Phase 5 | 2 days | Testing + validation |
| Phase 6 | 1 day | Deployment + monitoring |
| **Total** | **9-10 days** | Production-ready pipeline |

---

## ✅ Success Criteria

- ✅ All files processed without errors
- ✅ Logs contain only required fields (filename, hash, datetime)
- ✅ Markdown structure mirrors source exactly
- ✅ Qdrant data matches schema specifications
- ✅ Search-API works correctly with uploaded data
- ✅ Re-runs skip already processed files
- ✅ Processing time <5 seconds per file

---

**End of Document**
