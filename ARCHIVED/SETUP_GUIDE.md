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
