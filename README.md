# Release Notes Ingestion Pipeline

**Version:** 0.2.0  
**Status:** ✅ Production Ready

A production-ready ingestion pipeline for converting PDF/Word documents to markdown, chunking content, generating embeddings, and uploading to Qdrant vector database.

**Latest Updates (v0.2.0):**
- ✅ Qdrant production support (HTTPS + API key authentication)
- ✅ File extension filtering to skip unwanted files
- ✅ Enhanced security with credential masking
- ✅ gRPC support for improved performance

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    n8n (Orchestration)                  │
│  • Cron scheduling                                      │
│  • HTTP API calls to Python                             │
│  • Monitoring & alerts                                  │
└──────────────┬──────────────────────────────────────────┘
               │
               v
┌─────────────────────────────────────────────────────────┐
│              Python Pipeline (FastAPI)                  │
│  1. List R2 files                                       │
│  2. Download & hash files                               │
│  3. Convert via Docling (PDF/Word → Markdown)           │
│  4. Upload markdown to R2                               │
│  5. Semantic chunking (500 tokens)                      │
│  6. Generate embeddings (Ollama)                        │
│  7. Upload to Qdrant                                    │
│  8. Log processing                                      │
└─────────────────────────────────────────────────────────┘
```

## 📦 Components

1. **Config Loader** - Environment variables & Pydantic models
2. **R2 Client** - S3-compatible operations for Cloudflare R2
3. **File Hasher** - xxHash (lightweight) & MD5 hashing
4. **Log Manager** - JSON logging with thread safety
5. **Docling Client** - PDF/Word to Markdown conversion
6. **Markdown Storage** - R2 upload with mirrored paths
7. **Chunker** - Semantic chunking with LangChain
8. **Embedding Client** - Ollama embeddings (384D & 1024D)
9. **Qdrant Uploader** - Vector database operations

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
# Cloudflare R2
R2_ENDPOINT=https://your-account.r2.cloudflarestorage.com
R2_ACCESS_KEY=your-access-key
R2_SECRET_KEY=your-secret-key
R2_BUCKET_NAME=your-bucket

# Qdrant
QDRANT_HOST=192.168.254.22:6333

# Ollama
OLLAMA_HOST=192.168.254.22:11434

# Docling
DOCLING_BASE_URL=http://docling.mynetwork.ing
```

### 3. Run Pipeline

**Option A: Docker (Recommended for Production)** 🐳
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**Option B: Direct Python**
```bash
python src/pipeline.py
```

**Option C: FastAPI Server**
```bash
# Start API server
python api/main.py

# Or with uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8060
```

**Option D: With n8n**
- Import workflow from `n8n/ingestion_workflow.json`
- Configure cron trigger
- Set API endpoint to `http://localhost:8060`

> 💡 **Need Help?** See [DOCUMENTATION.md](DOCUMENTATION.md) for complete setup, configuration, and testing guide!

## 📊 API Endpoints

### Health & Status
- `GET /health` - Service health check
- `GET /api/pipeline/status/{task_id}` - Get task status
- `GET /api/pipeline/summary` - Get processing summary

### Pipeline Control
- `POST /api/pipeline/start` - Start ingestion pipeline
- Returns `task_id` for tracking

### Logs
- `GET /api/logs/conversion` - Conversion log
- `GET /api/logs/upload` - Upload log
- `GET /api/logs/failed` - Failed files log

### Collections
- `GET /api/collections/info` - Qdrant collection info

## 📁 Project Structure

```
release-notes-ingestion/
├── src/
│   ├── components/
│   │   ├── config.py              # Configuration loader
│   │   ├── r2_client.py           # R2/S3 operations
│   │   ├── file_hasher.py         # File hashing
│   │   ├── log_manager.py         # JSON logging
│   │   ├── docling_client.py      # Docling API client
│   │   ├── markdown_storage.py    # Markdown R2 storage
│   │   ├── chunker.py             # Semantic chunking
│   │   ├── embedding_client.py    # Ollama embeddings
│   │   └── qdrant_uploader.py     # Qdrant operations
│   └── pipeline.py                # Main orchestrator
├── api/
│   └── main.py                    # FastAPI wrapper
├── n8n/
│   ├── ingestion_workflow.json   # Main workflow
│   └── monitoring_workflow.json  # Monitoring
├── logs/                          # JSON logs
│   ├── conversion.json
│   ├── upload.json
│   └── failed.json
├── tests/                         # Test suite
├── requirements.txt
├── .env
└── README.md
```

## 🔄 Data Flow

1. **List Files** - Scan R2 bucket for new files
2. **Download** - Fetch file content
3. **Hash** - Generate MD5 hash for deduplication
4. **Check Logs** - Skip if already processed
5. **Convert** - Docling converts to Markdown
6. **Store Markdown** - Upload to R2 (mirrored structure)
7. **Chunk** - Semantic chunking (500 tokens, no overlap)
8. **Embed** - Generate vectors via Ollama
9. **Upload** - Store in Qdrant collections
10. **Log** - Record success/failure

## 📝 Qdrant Collections

### 1. `filename-granite-embedding30m`
- **Purpose:** Fast filename indexing
- **Model:** granite-embedding:30m (384D)
- **Payload:**
  ```json
  {
    "pagecontent": "file.pdf",
    "source": "file.pdf",
    "metadata": {"hash": "xxhash"}
  }
  ```

### 2. `releasenotes-bge-m3`
- **Purpose:** Content search
- **Model:** bge-m3 (1024D)
- **Payload:**
  ```json
  {
    "pagecontent": "chunk text...",
    "metadata": {
      "filename": "file.pdf",
      "page_number": 1,
      "element_type": "Text",
      "md5_hash": "hash"
    }
  }
  ```

## 🧪 Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=src tests/

# Lint
flake8 src/ api/

# Format
black src/ api/
```

## 📈 Monitoring

### Logs
- `logs/conversion.json` - Successfully converted files
- `logs/upload.json` - Successfully uploaded files
- `logs/failed.json` - Failed processing attempts

### Metrics
- Files processed per run
- Processing time per file
- Success/failure rates
- Collection sizes

## 🔧 Configuration

### Chunking
- `CHUNK_SIZE_TOKENS=500` - Target chunk size
- `CHUNK_OVERLAP_TOKENS=0` - No overlap

### Timeouts
- `DOCLING_TIMEOUT=300` - Docling conversion timeout
- `DOCLING_POLL_INTERVAL=2` - Status poll interval

### Logging
- `LOG_DIR=logs/` - Log directory
- JSON format with filename, hash, datetime

## 🐛 Troubleshooting

### Docling Service Unreachable
```bash
# Check service
curl http://docling.mynetwork.ing/health
```

### Ollama Models Missing
```bash
# Pull models
ollama pull granite-embedding:30m
ollama pull bge-m3
```

### Qdrant Connection Failed
```bash
# Check Qdrant
curl http://192.168.254.22:6333/collections
```

## 📚 Documentation

- **[DOCUMENTATION.md](DOCUMENTATION.md)** - Complete setup, configuration, and testing guide
- **[QDRANT.md](QDRANT.md)** - Qdrant setup and collection schema
- **[DOCKER.md](DOCKER.md)** - Docker deployment guide
- **[REFERENCE.md](REFERENCE.md)** - Implementation details and historical documentation
- **[ARCHIVED/](ARCHIVED/)** - Original documentation files (archived)

## 🤝 Contributing

1. Follow existing code style
2. Add tests for new features
3. Update documentation
4. Run linters before committing

## 📄 License

MIT License

## 👥 Authors

Release Notes Search Team

---

**Last Updated:** November 7, 2025
