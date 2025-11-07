# Configuration Guide

All configuration is managed through environment variables in the `.env` file. **Nothing is hardcoded** - every parameter can be controlled via environment variables.

## 📋 Complete Configuration Reference

### 🗄️ Cloudflare R2 Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `R2_ENDPOINT` | ✅ Yes | - | R2 endpoint URL from Cloudflare dashboard |
| `R2_ACCESS_KEY` | ✅ Yes | - | R2 access key ID |
| `R2_SECRET_KEY` | ✅ Yes | - | R2 secret access key |
| `R2_BUCKET_NAME` | ✅ Yes | - | Name of your R2 bucket |
| `R2_SOURCE_PREFIX` | No | `source/` | Folder prefix for source files |
| `R2_MARKDOWN_PREFIX` | No | `markdown/` | Folder prefix for markdown files |

**Example:**
```bash
R2_ENDPOINT=https://abc123.r2.cloudflarestorage.com
R2_ACCESS_KEY=your-access-key
R2_SECRET_KEY=your-secret-key
R2_BUCKET_NAME=release-notes
R2_SOURCE_PREFIX=source/
R2_MARKDOWN_PREFIX=markdown/
```

---

### 🔍 Qdrant Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `QDRANT_HOST` | ✅ Yes | - | Qdrant server hostname or IP |
| `QDRANT_PORT` | No | `6333` | Qdrant server port |
| `QDRANT_FILENAME_COLLECTION` | No | `filename-granite-embedding30m` | Collection name for filenames |
| `QDRANT_CONTENT_COLLECTION` | No | `releasenotes-bge-m3` | Collection name for content |

**Example:**
```bash
QDRANT_HOST=192.168.254.22
QDRANT_PORT=6333
QDRANT_FILENAME_COLLECTION=filename-granite-embedding30m
QDRANT_CONTENT_COLLECTION=releasenotes-bge-m3
```

---

### 🤖 Ollama Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OLLAMA_HOST` | ✅ Yes | - | Ollama server hostname or IP |
| `OLLAMA_PORT` | No | `11434` | Ollama server port |
| `OLLAMA_FILENAME_MODEL` | No | `granite-embedding:30m` | Model for filename embeddings (384D) |
| `OLLAMA_CONTENT_MODEL` | No | `bge-m3` | Model for content embeddings (1024D) |

**Example:**
```bash
OLLAMA_HOST=192.168.254.22
OLLAMA_PORT=11434
OLLAMA_FILENAME_MODEL=granite-embedding:30m
OLLAMA_CONTENT_MODEL=bge-m3
```

**Model Requirements:**
- Filename model must produce 384-dimensional vectors
- Content model must produce 1024-dimensional vectors
- Models must be pre-installed on Ollama server:
  ```bash
  ollama pull granite-embedding:30m
  ollama pull bge-m3
  ```

---

### 📄 Docling Service Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DOCLING_BASE_URL` | ✅ Yes | - | Docling service base URL |
| `DOCLING_TIMEOUT` | No | `300` | Conversion timeout in seconds |
| `DOCLING_POLL_INTERVAL` | No | `2` | Status poll interval in seconds |

**Example:**
```bash
DOCLING_BASE_URL=http://192.168.254.22:5010
DOCLING_TIMEOUT=300
DOCLING_POLL_INTERVAL=2
```

---

### ✂️ Chunking Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CHUNK_SIZE_TOKENS` | No | `500` | Target chunk size in tokens |
| `CHUNK_OVERLAP_TOKENS` | No | `0` | Overlap between chunks in tokens |

**Example:**
```bash
CHUNK_SIZE_TOKENS=500
CHUNK_OVERLAP_TOKENS=0
```

**Notes:**
- Token counting uses `cl100k_base` encoding (GPT-4 tokenizer)
- Chunks are created using semantic boundaries (paragraphs, sentences)
- Element types are auto-detected: Text, Table, List, Code, Image

---

### 📝 Logging Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LOG_DIR` | No | `logs/` | Directory for log files |
| `CONVERSION_LOG` | No | `conversion.json` | Filename for conversion log |
| `UPLOAD_LOG` | No | `upload.json` | Filename for upload log |
| `FAILED_LOG` | No | `failed.json` | Filename for failed files log |

**Example:**
```bash
LOG_DIR=logs/
CONVERSION_LOG=conversion.json
UPLOAD_LOG=upload.json
FAILED_LOG=failed.json
```

**Log Format:**
```json
{
  "filename": "file.pdf",
  "hash": "abc123...",
  "datetime": "2025-11-07T07:00:00Z"
}
```

---

### 🔄 N8N Configuration (Optional)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `N8N_API_KEY` | No | - | N8N API key for authentication |
| `N8N_URL` | No | - | N8N instance URL |

**Example:**
```bash
N8N_API_KEY=your-api-key
N8N_URL=https://n8n.mynetwork.ing/
```

---

## 🚀 Quick Setup

### 1. Copy Example Configuration
```bash
cp .env.example .env
```

### 2. Edit Configuration
```bash
nano .env  # or use your preferred editor
```

### 3. Fill Required Values

**Minimum Required Configuration:**
```bash
# R2 (Required)
R2_ENDPOINT=https://your-account.r2.cloudflarestorage.com
R2_ACCESS_KEY=your-access-key
R2_SECRET_KEY=your-secret-key
R2_BUCKET_NAME=your-bucket

# Qdrant (Required)
QDRANT_HOST=192.168.254.22

# Ollama (Required)
OLLAMA_HOST=192.168.254.22

# Docling (Required)
DOCLING_BASE_URL=http://192.168.254.22:5010
```

### 4. Verify Configuration
```bash
python src/components/config.py
```

This will print loaded configuration and validate all settings.

---

## 🔧 Advanced Configuration

### Custom Collection Names

If you want to use different Qdrant collections:

```bash
QDRANT_FILENAME_COLLECTION=my-custom-filename-collection
QDRANT_CONTENT_COLLECTION=my-custom-content-collection
```

**Important:** Collections must already exist in Qdrant with correct vector dimensions:
- Filename collection: 384 dimensions
- Content collection: 1024 dimensions

### Custom Embedding Models

To use different Ollama models:

```bash
OLLAMA_FILENAME_MODEL=your-filename-model:tag
OLLAMA_CONTENT_MODEL=your-content-model:tag
```

**Requirements:**
- Filename model must output 384D vectors
- Content model must output 1024D vectors
- Models must be pulled: `ollama pull model-name`

### Chunking Tuning

Adjust chunk size based on your content:

```bash
# Smaller chunks (more granular)
CHUNK_SIZE_TOKENS=300
CHUNK_OVERLAP_TOKENS=50

# Larger chunks (more context)
CHUNK_SIZE_TOKENS=800
CHUNK_OVERLAP_TOKENS=100
```

**Guidelines:**
- Smaller chunks: Better for precise search, more vectors
- Larger chunks: More context, fewer vectors
- Overlap: Helps maintain context across boundaries

### Timeout Adjustments

For large files or slow networks:

```bash
# Increase Docling timeout for large PDFs
DOCLING_TIMEOUT=600

# Faster polling for quick conversions
DOCLING_POLL_INTERVAL=1
```

---

## ✅ Configuration Validation

### Test Individual Components

```bash
# Test R2 connection
python src/components/r2_client.py

# Test Docling service
python src/components/docling_client.py

# Test Ollama embeddings
python src/components/embedding_client.py

# Test Qdrant connection
python src/components/qdrant_uploader.py
```

### Test Full Configuration

```bash
# Load and validate all settings
python src/components/config.py
```

### API Health Check

```bash
# Start API server
python api/main.py

# Check health
curl http://localhost:8001/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "docling": true,
    "ollama": true,
    "qdrant": true
  }
}
```

---

## 🔒 Security Best Practices

1. **Never commit `.env` to git**
   - Already in `.gitignore`
   - Use `.env.example` for documentation

2. **Rotate credentials regularly**
   - R2 access keys
   - N8N API keys

3. **Use environment-specific configs**
   ```bash
   # Development
   .env.development
   
   # Production
   .env.production
   ```

4. **Restrict file permissions**
   ```bash
   chmod 600 .env
   ```

---

## 📚 Related Documentation

- [README.md](README.md) - General overview
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Detailed implementation
- [QDRANT_COLLECTIONS.md](QDRANT_COLLECTIONS.md) - Collection schemas
- [INGESTION_PIPELINE_SPEC.md](INGESTION_PIPELINE_SPEC.md) - Pipeline specification

---

**Last Updated:** November 7, 2025
