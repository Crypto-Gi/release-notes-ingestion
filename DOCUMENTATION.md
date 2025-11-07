# Complete Documentation Guide

**Last Updated:** November 7, 2025  
**Purpose:** Comprehensive guide for setup, configuration, and testing

This document consolidates setup instructions, configuration reference, and testing guides into one complete resource.

---

**Table of Contents:**
- [1. Setup Guide](#1-setup-guide)
- [2. Configuration Reference](#2-configuration-reference)
- [3. Testing Guide](#3-testing-guide)

---

# Complete Setup Guide

Step-by-step guide to set up the Release Notes Ingestion Pipeline from scratch.

---

## 📋 **Prerequisites**

Before starting, ensure you have:

- ✅ Python 3.11+
- ✅ Access to Cloudflare R2 bucket
- ✅ Qdrant server running (192.168.254.22:6333)
- ✅ Ollama server running (192.168.254.22:11434)
- ✅ Docling service running (192.168.254.22:5010)

---

## 🚀 **Step 1: Clone and Install**

```bash
cd /home/mir/projects/release-notes-ingestion

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🔧 **Step 2: Configure Environment Variables**

### **Copy Template**

```bash
cp .env.example .env
nano .env
```

### **Critical Configuration Notes**

#### **1. R2 Endpoint Configuration** ⚠️

**IMPORTANT:** The `R2_ENDPOINT` should be the **base URL only**, WITHOUT the bucket name!

```bash
# ✅ CORRECT
R2_ENDPOINT=https://d6f496280c17d62157f00817db422fb2.r2.cloudflarestorage.com
R2_BUCKET_NAME=releasenotes

# ❌ WRONG - Don't include bucket in endpoint
R2_ENDPOINT=https://d6f496280c17d62157f00817db422fb2.r2.cloudflarestorage.com/releasenotes
R2_BUCKET_NAME=releasenotes
```

**Why?** The S3-compatible API constructs URLs as: `{endpoint}/{bucket}/{key}`

If you include the bucket in the endpoint, it would create:
```
https://.../releasenotes/releasenotes/source/file.pdf
              ^^^^^^^^^^^  ^^^^^^^^^^^
              from endpoint from bucket_name (WRONG!)
```

#### **2. Complete .env Configuration**

```bash
# ============================================
# Cloudflare R2 Configuration
# ============================================
R2_ENDPOINT=https://d6f496280c17d62157f00817db422fb2.r2.cloudflarestorage.com
R2_ACCESS_KEY=your-actual-access-key
R2_SECRET_KEY=your-actual-secret-key
R2_BUCKET_NAME=releasenotes
R2_SOURCE_PREFIX=source/
R2_MARKDOWN_PREFIX=markdown/

# ============================================
# Qdrant Configuration
# ============================================
QDRANT_HOST=192.168.254.22
QDRANT_PORT=6333
QDRANT_FILENAME_COLLECTION=filename-granite-embedding30m
QDRANT_CONTENT_COLLECTION=releasenotes-bge-m3

# ============================================
# Ollama Configuration
# ============================================
OLLAMA_HOST=192.168.254.22
OLLAMA_PORT=11434
OLLAMA_FILENAME_MODEL=granite-embedding:30m
OLLAMA_CONTENT_MODEL=bge-m3

# ============================================
# Docling Configuration
# ============================================
DOCLING_BASE_URL=http://192.168.254.22:5010
DOCLING_TIMEOUT=300
DOCLING_POLL_INTERVAL=2

# ============================================
# Chunking Configuration
# ============================================
CHUNK_SIZE_TOKENS=500
CHUNK_OVERLAP_TOKENS=0

# ============================================
# Logging Configuration
# ============================================
LOG_DIR=logs/
CONVERSION_LOG=conversion.json
UPLOAD_LOG=upload.json
FAILED_LOG=failed.json
```

---

## 📊 **Step 3: Setup Qdrant Collections**

### **Important: Collections Must Exist Before Running Pipeline!**

The ingestion pipeline **does NOT automatically create collections**. You must create them first.

### **Option A: Use Setup Script (Recommended)** ✅

```bash
# Run the automated setup script
python scripts/setup_qdrant_collections.py

# Expected output:
# ============================================================
# QDRANT COLLECTION SETUP
# ============================================================
# Host: 192.168.254.22
# Port: 6333
# Filename Collection: filename-granite-embedding30m
# Content Collection: releasenotes-bge-m3
# ============================================================
# 
# Connecting to Qdrant...
# ✅ Connected! Found X existing collections
# 
# Creating collection: filename-granite-embedding30m
# ✅ Collection 'filename-granite-embedding30m' created
# ✅ Text index added to 'pagecontent' field
# ✅ Text index added to 'metadata.filename' field
# 🎉 Collection 'filename-granite-embedding30m' setup complete!
# 
# Creating collection: releasenotes-bge-m3
# ✅ Collection 'releasenotes-bge-m3' created
# ℹ️  No text indexing (pure vector search)
# 🎉 Collection 'releasenotes-bge-m3' setup complete!
# 
# ============================================================
# VERIFYING COLLECTIONS
# ============================================================
# 
# 📊 filename-granite-embedding30m:
#   Vector size: 384
#   Distance: Cosine
#   Points: 0
#   Status: green
# 
# 📊 releasenotes-bge-m3:
#   Vector size: 1024
#   Distance: Cosine
#   Points: 0
#   Status: green
# 
# ✅ All collections verified successfully!
# 
# ============================================================
# 🎉 SETUP COMPLETE!
# ============================================================
```

### **Option B: Manual Creation** 🔧

If you prefer to create collections manually:

#### **Create Filename Collection (384D, with tokenizer)**

```bash
# Create collection
curl -X PUT "http://192.168.254.22:6333/collections/filename-granite-embedding30m" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 384,
      "distance": "Cosine"
    },
    "optimizers_config": {
      "default_segment_number": 2
    }
  }'

# Add text index to pagecontent field
curl -X PUT "http://192.168.254.22:6333/collections/filename-granite-embedding30m/index" \
  -H "Content-Type: application/json" \
  -d '{
    "field_name": "pagecontent",
    "field_schema": {
      "type": "text",
      "tokenizer": "word",
      "min_token_len": 1,
      "max_token_len": 15,
      "lowercase": true
    }
  }'

# Add text index to metadata.filename field
curl -X PUT "http://192.168.254.22:6333/collections/filename-granite-embedding30m/index" \
  -H "Content-Type: application/json" \
  -d '{
    "field_name": "metadata.filename",
    "field_schema": {
      "type": "text",
      "tokenizer": "word",
      "min_token_len": 1,
      "max_token_len": 15,
      "lowercase": true
    }
  }'
```

#### **Create Content Collection (1024D, no tokenizer)**

```bash
# Create collection
curl -X PUT "http://192.168.254.22:6333/collections/releasenotes-bge-m3" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 1024,
      "distance": "Cosine"
    },
    "optimizers_config": {
      "default_segment_number": 2
    }
  }'
```

### **Verify Collections**

```bash
# List all collections
curl http://192.168.254.22:6333/collections | jq .

# Check filename collection
curl http://192.168.254.22:6333/collections/filename-granite-embedding30m | jq .

# Check content collection
curl http://192.168.254.22:6333/collections/releasenotes-bge-m3 | jq .
```

**Expected:**
- ✅ Both collections exist
- ✅ Filename collection: 384 dimensions, Cosine distance
- ✅ Content collection: 1024 dimensions, Cosine distance
- ✅ Status: "green"

---

## 🧪 **Step 4: Test Services**

### **Test R2 Connection**

```bash
python -c "
from src.components.r2_client import R2Client
from dotenv import load_dotenv
import os

load_dotenv()

client = R2Client(
    endpoint=os.getenv('R2_ENDPOINT'),
    access_key=os.getenv('R2_ACCESS_KEY'),
    secret_key=os.getenv('R2_SECRET_KEY'),
    bucket_name=os.getenv('R2_BUCKET_NAME')
)

files = client.list_files(prefix='source/')
print(f'✅ R2 Connected! Found {len(files)} files')
"
```

### **Test Qdrant Connection**

```bash
curl http://192.168.254.22:6333/collections
```

### **Test Ollama Models**

```bash
# Check if models are available
curl http://192.168.254.22:11434/api/tags

# If models are missing, pull them:
ssh user@192.168.254.22
ollama pull granite-embedding:30m
ollama pull bge-m3
```

### **Test Docling Service**

```bash
curl http://192.168.254.22:5010/health
```

---

## ▶️ **Step 5: Run the Pipeline**

### **Option A: Direct Python**

```bash
python src/pipeline.py
```

### **Option B: API Server**

```bash
# Start server
python api/main.py

# In another terminal, trigger pipeline
curl -X POST http://localhost:8060/api/pipeline/start
```

### **Option C: Docker**

```bash
docker-compose up -d
curl -X POST http://localhost:8060/api/pipeline/start
```

---

## 📊 **Step 6: Monitor Progress**

### **Check Logs**

```bash
# View conversion log
cat logs/conversion.json | jq .

# View upload log
cat logs/upload.json | jq .

# View failed files
cat logs/failed.json | jq .
```

### **Check Qdrant Collections**

```bash
# Count points in filename collection
curl http://192.168.254.22:6333/collections/filename-granite-embedding30m/points/count

# Count points in content collection
curl http://192.168.254.22:6333/collections/releasenotes-bge-m3/points/count
```

### **API Status**

```bash
# Health check
curl http://localhost:8060/health

# Pipeline summary
curl http://localhost:8060/api/pipeline/summary
```

---

## ✅ **Verification Checklist**

After setup, verify:

- [ ] R2 connection works
- [ ] Qdrant collections exist (both)
- [ ] Ollama models are pulled
- [ ] Docling service responds
- [ ] Pipeline processes at least one file
- [ ] Embeddings uploaded to Qdrant
- [ ] Logs are created
- [ ] API server starts

---

## 🐛 **Troubleshooting**

### **R2 Connection Fails**

```bash
# Check endpoint format
echo $R2_ENDPOINT
# Should be: https://account-id.r2.cloudflarestorage.com
# Should NOT include bucket name!

# Test credentials
aws s3 ls s3://releasenotes --endpoint-url=$R2_ENDPOINT
```

### **Qdrant Collections Don't Exist**

```bash
# Run setup script
python scripts/setup_qdrant_collections.py

# Or create manually (see Step 3)
```

### **Ollama Models Missing**

```bash
# SSH to Ollama server
ssh user@192.168.254.22

# Pull models
ollama pull granite-embedding:30m
ollama pull bge-m3

# Verify
ollama list
```

### **Docling Service Down**

```bash
# Check if service is running
curl http://192.168.254.22:5010/health

# If down, restart the service
ssh user@192.168.254.22
# (restart docling service)
```

---

## 📚 **Next Steps**

After successful setup:

1. **Test with Sample Files**
   - Upload a test PDF to R2 `source/` folder
   - Run pipeline
   - Verify in Qdrant

2. **Set Up Automation**
   - Configure n8n workflow
   - Set up cron job
   - Enable monitoring

3. **Production Deployment**
   - Use Docker deployment
   - Set up log rotation
   - Configure backups

---

## 📖 **Additional Resources**

- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing instructions
- [DOCKER.md](DOCKER.md) - Docker deployment
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration reference
- [QDRANT_COLLECTIONS.md](QDRANT_COLLECTIONS.md) - Collection details
- [README.md](README.md) - General overview

---

## 🎯 **Quick Reference**

### **Key URLs**

- API: `http://localhost:8060`
- Qdrant: `http://192.168.254.22:6333`
- Ollama: `http://192.168.254.22:11434`
- Docling: `http://192.168.254.22:5010`

### **Key Commands**

```bash
# Setup collections
python scripts/setup_qdrant_collections.py

# Run pipeline
python src/pipeline.py

# Start API
python api/main.py

# Docker
docker-compose up -d
```

---

**Last Updated:** November 7, 2025

---

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

---

# Testing & Usage Guide

Complete guide for testing the ingestion pipeline with and without Docker.

## 🎯 **Can I Test Without Docker? YES!** ✅

You can **absolutely test without Docker first**. In fact, it's **recommended** to test locally before containerizing.

---

## 📋 **Testing Approaches**

### **Approach 1: Local Testing (Recommended First)** 🔧
- ✅ Faster iteration
- ✅ Easier debugging
- ✅ Direct access to code
- ✅ No Docker overhead

### **Approach 2: Docker Testing (Production-like)** 🐳
- ✅ Consistent environment
- ✅ Isolated dependencies
- ✅ Production parity
- ✅ Easy deployment

---

## 🚀 **Method 1: Testing WITHOUT Docker**

### **Prerequisites**

1. **Python 3.11+**
   ```bash
   python --version  # Should be 3.11 or higher
   ```

2. **Virtual Environment (Recommended)**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate it
   source venv/bin/activate  # Linux/Mac
   # OR
   venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   # Copy and edit .env
   cp .env.example .env
   nano .env
   ```

---

### **Step-by-Step Local Testing**

#### **Step 1: Test Individual Components** 🧪

```bash
# Test configuration loading
python src/components/config.py

# Test R2 connection
python src/components/r2_client.py

# Test Docling service
python src/components/docling_client.py

# Test Ollama embeddings
python src/components/embedding_client.py

# Test Qdrant connection
python src/components/qdrant_uploader.py

# Test file hasher
python src/components/file_hasher.py

# Test log manager
python src/components/log_manager.py

# Test chunker
python src/components/chunker.py
```

**Expected Output:**
- ✅ No errors
- ✅ Connection successful messages
- ✅ Service health checks pass

---

#### **Step 2: Test Full Pipeline** 🔄

```bash
# Run the complete pipeline
python src/pipeline.py
```

**What Happens:**
1. Lists files in R2
2. Filters new files
3. Downloads and processes each file
4. Converts to markdown
5. Chunks content
6. Generates embeddings
7. Uploads to Qdrant
8. Logs results

**Expected Output:**
```
2025-11-07 07:00:00 - INFO - Initializing ingestion pipeline...
2025-11-07 07:00:01 - INFO - Pipeline initialized successfully
2025-11-07 07:00:02 - INFO - Service health: {'docling': True, 'ollama': True, 'qdrant': True}
2025-11-07 07:00:03 - INFO - Found 42 files
2025-11-07 07:00:04 - INFO - New files to process: 5
2025-11-07 07:00:05 - INFO - Processing file: source/file1.pdf
...
2025-11-07 07:05:00 - INFO - Pipeline complete!
```

---

#### **Step 3: Test API Server** 🌐

```bash
# Start API server
python api/main.py

# OR with uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8060 --reload
```

**API will be available at:** `http://localhost:8060`

**Test Endpoints:**

```bash
# Health check
curl http://localhost:8060/health

# Expected response:
{
  "status": "healthy",
  "services": {
    "docling": true,
    "ollama": true,
    "qdrant": true
  }
}

# Start pipeline
curl -X POST http://localhost:8060/api/pipeline/start

# Expected response:
{
  "task_id": "abc-123-def-456",
  "status": "pending",
  "message": "Pipeline task started"
}

# Check status
curl http://localhost:8060/api/pipeline/status/abc-123-def-456

# Get summary
curl http://localhost:8060/api/pipeline/summary

# View logs
curl http://localhost:8060/api/logs/conversion
curl http://localhost:8060/api/logs/upload
curl http://localhost:8060/api/logs/failed
```

---

### **Step 4: Test with Sample File** 📄

```bash
# Create a test script
cat > test_single_file.py << 'EOF'
from src.pipeline import IngestionPipeline

# Initialize pipeline
pipeline = IngestionPipeline()

# Test with a single file
result = pipeline.process_file("source/test/sample.pdf")

if result:
    print("✅ File processed successfully!")
else:
    print("❌ File processing failed!")
EOF

# Run test
python test_single_file.py
```

---

## 🐳 **Method 2: Testing WITH Docker**

### **Prerequisites**

1. **Docker Installed**
   ```bash
   docker --version
   docker-compose --version
   ```

2. **Configure Environment**
   ```bash
   # .env file should be configured
   cat .env  # Verify settings
   ```

---

### **Step-by-Step Docker Testing**

#### **Step 1: Build Docker Image** 🏗️

```bash
# Build the image
docker-compose build

# Expected output:
# Successfully built abc123
# Successfully tagged release-notes-ingestion:latest
```

**Verify Build:**
```bash
# List images
docker images | grep release-notes-ingestion

# Should show:
# release-notes-ingestion  latest  abc123  2 minutes ago  450MB
```

---

#### **Step 2: Start Container** 🚀

```bash
# Start in foreground (see logs)
docker-compose up

# OR start in background
docker-compose up -d
```

**Verify Container:**
```bash
# Check running containers
docker ps

# Should show:
# CONTAINER ID  IMAGE                    STATUS        PORTS
# abc123        release-notes-ingestion  Up 10 seconds 0.0.0.0:8060->8060/tcp
```

---

#### **Step 3: Test API** 🧪

```bash
# Health check
curl http://localhost:8060/health

# Start pipeline
curl -X POST http://localhost:8060/api/pipeline/start

# Check logs
docker-compose logs -f
```

---

#### **Step 4: Access Container** 🔍

```bash
# Enter container shell
docker exec -it release-notes-ingestion /bin/bash

# Inside container:
ls -la /app
cat /app/logs/conversion.json
python src/components/config.py
exit
```

---

#### **Step 5: View Logs** 📊

```bash
# All logs
docker-compose logs -f

# Last 50 lines
docker-compose logs --tail=50

# Logs from specific time
docker-compose logs --since 10m
```

---

#### **Step 6: Stop Container** 🛑

```bash
# Stop gracefully
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop and remove everything
docker-compose down --rmi all -v
```

---

## 🔄 **Comparison: Docker vs Non-Docker**

| Feature | Without Docker | With Docker |
|---------|---------------|-------------|
| **Setup Time** | 5 minutes | 10 minutes |
| **Debugging** | ✅ Easy | ⚠️ Moderate |
| **Iteration Speed** | ✅ Fast | ⚠️ Slower |
| **Environment** | ⚠️ Local Python | ✅ Isolated |
| **Deployment** | ⚠️ Manual | ✅ Automated |
| **Consistency** | ⚠️ Varies | ✅ Consistent |
| **Resource Usage** | ✅ Lower | ⚠️ Higher |
| **Production Ready** | ❌ No | ✅ Yes |

---

## 🎯 **Recommended Testing Workflow**

### **Phase 1: Local Development** (Days 1-2)

1. ✅ Install dependencies locally
2. ✅ Test individual components
3. ✅ Fix any configuration issues
4. ✅ Test with sample files
5. ✅ Verify all services connect

### **Phase 2: Integration Testing** (Day 3)

1. ✅ Run full pipeline locally
2. ✅ Test API endpoints
3. ✅ Process multiple files
4. ✅ Verify Qdrant uploads
5. ✅ Check logs

### **Phase 3: Docker Testing** (Day 4)

1. ✅ Build Docker image
2. ✅ Test in container
3. ✅ Verify same results
4. ✅ Test with docker-compose
5. ✅ Check resource usage

### **Phase 4: Production Deployment** (Day 5+)

1. ✅ Deploy to staging
2. ✅ Run load tests
3. ✅ Monitor performance
4. ✅ Deploy to production
5. ✅ Set up monitoring

---

## 🧪 **Test Checklist**

### **Before Testing**

- [ ] Python 3.11+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured
- [ ] R2 bucket accessible
- [ ] Qdrant running and accessible
- [ ] Ollama running with models pulled
- [ ] Docling service running

### **Component Tests**

- [ ] Config loads without errors
- [ ] R2 client lists files
- [ ] Docling converts sample PDF
- [ ] Ollama generates embeddings
- [ ] Qdrant accepts uploads
- [ ] File hasher generates hashes
- [ ] Log manager creates logs
- [ ] Chunker splits text

### **Integration Tests**

- [ ] Full pipeline processes one file
- [ ] API server starts
- [ ] Health check returns healthy
- [ ] Pipeline can be triggered via API
- [ ] Logs are created correctly
- [ ] Qdrant collections populated

### **Docker Tests**

- [ ] Image builds successfully
- [ ] Container starts
- [ ] Health check passes
- [ ] API accessible on port 8060
- [ ] Logs persist outside container
- [ ] Environment variables work

---

## 🐛 **Troubleshooting**

### **Local Testing Issues**

#### **Import Errors**
```bash
# Make sure you're in the right directory
cd /home/mir/projects/release-notes-ingestion

# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### **Connection Errors**
```bash
# Test service connectivity
ping 192.168.254.22

# Test Qdrant
curl http://192.168.254.22:6333/collections

# Test Ollama
curl http://192.168.254.22:11434/api/tags

# Test Docling
curl http://192.168.254.22:5010/health
```

#### **Permission Errors**
```bash
# Fix log directory permissions
chmod 755 logs/
chmod 644 logs/*.json
```

---

### **Docker Testing Issues**

#### **Build Fails**
```bash
# Clean build
docker-compose build --no-cache

# Check Dockerfile syntax
docker build -t test .
```

#### **Container Won't Start**
```bash
# Check logs
docker-compose logs

# Check container status
docker ps -a

# Remove and recreate
docker-compose down
docker-compose up --force-recreate
```

#### **Port Already in Use**
```bash
# Check what's using port 8060
lsof -i :8060

# Kill the process
kill -9 <PID>

# Or change port in docker-compose.yml
```

---

## 📊 **Performance Testing**

### **Local Performance**

```bash
# Time a single file
time python -c "
from src.pipeline import IngestionPipeline
pipeline = IngestionPipeline()
pipeline.process_file('source/test.pdf')
"
```

### **Docker Performance**

```bash
# Monitor resources
docker stats release-notes-ingestion

# Check memory usage
docker exec release-notes-ingestion free -h

# Check CPU usage
docker exec release-notes-ingestion top -bn1
```

---

## ✅ **Success Criteria**

### **Local Testing Success**

- ✅ All component tests pass
- ✅ Pipeline processes files without errors
- ✅ API server responds to requests
- ✅ Logs are created correctly
- ✅ Qdrant collections populated
- ✅ No memory leaks
- ✅ Performance acceptable

### **Docker Testing Success**

- ✅ Image builds in < 5 minutes
- ✅ Container starts in < 10 seconds
- ✅ Health check passes
- ✅ Same results as local testing
- ✅ Logs persist after restart
- ✅ Resource usage acceptable
- ✅ Can scale horizontally

---

## 🎓 **Next Steps**

### **After Local Testing**

1. Document any issues found
2. Fix configuration problems
3. Optimize performance
4. Add error handling
5. Write unit tests

### **After Docker Testing**

1. Deploy to staging
2. Run integration tests
3. Load test with multiple files
4. Monitor resource usage
5. Deploy to production

---

## 📚 **Additional Resources**

- [README.md](README.md) - General overview
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration guide
- [DOCKER.md](DOCKER.md) - Docker deployment guide
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Implementation details

---

**Last Updated:** November 7, 2025
