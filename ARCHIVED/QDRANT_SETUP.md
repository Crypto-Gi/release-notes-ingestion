# Qdrant Collection Setup Guide

Complete guide for creating and configuring Qdrant collections with full flexibility.

---

## 🎯 **Overview**

The setup script (`scripts/setup_qdrant_collections.py`) creates Qdrant collections based on your `.env` configuration. All settings are fully customizable with sensible defaults.

---

## ⚙️ **Configuration Options**

### **Collection Names**

```bash
# Customize collection names as needed
QDRANT_FILENAME_COLLECTION=filename-granite-embedding30m
QDRANT_CONTENT_COLLECTION=releasenotes-bge-m3
```

---

### **Filename Collection Configuration**

#### **Vector Settings**

```bash
# Vector dimensions (default: 384 for granite-embedding:30m)
# MUST match your Ollama embedding model output!
QDRANT_FILENAME_VECTOR_SIZE=384

# Distance metric (default: Cosine)
# Options: Cosine, Euclid, Dot, Manhattan
QDRANT_FILENAME_DISTANCE=Cosine
```

**Distance Metrics Explained:**
- **Cosine**: Best for normalized embeddings, measures angle similarity (0-2, lower = more similar)
- **Euclid**: Euclidean distance, measures straight-line distance
- **Dot**: Dot product, good for non-normalized vectors
- **Manhattan**: L1 distance, sum of absolute differences

#### **Text Indexing**

```bash
# Enable text indexing (default: true for filename collection)
QDRANT_FILENAME_TEXT_INDEX=true

# Tokenizer type (default: word)
# Options: word, whitespace, prefix, multilingual
QDRANT_FILENAME_TOKENIZER=word

# Token length constraints
QDRANT_FILENAME_MIN_TOKEN_LEN=1
QDRANT_FILENAME_MAX_TOKEN_LEN=15

# Lowercase normalization (default: true)
QDRANT_FILENAME_LOWERCASE=true
```

**Tokenizer Types:**
- **word**: Splits on spaces, punctuation, special characters (best for English)
- **whitespace**: Splits only on whitespace characters
- **prefix**: Like word but creates prefixes for autocomplete
- **multilingual**: Supports CJK (Chinese, Japanese, Korean) languages

#### **HNSW Index Tuning**

```bash
# Number of neighbors per node (default: 16)
# Higher = better recall, more memory
QDRANT_FILENAME_HNSW_M=16

# Construction parameter (default: 100)
# Higher = better quality index, slower build
QDRANT_FILENAME_HNSW_EF_CONSTRUCT=100

# Full scan threshold (default: 10000)
# Switch to brute-force below this point count
QDRANT_FILENAME_HNSW_FULL_SCAN_THRESHOLD=10000

# Store HNSW index on disk (default: false)
# true = saves RAM, slightly slower queries
QDRANT_FILENAME_HNSW_ON_DISK=false
```

---

### **Content Collection Configuration**

#### **Vector Settings**

```bash
# Vector dimensions (default: 1024 for bge-m3)
# MUST match your Ollama embedding model output!
QDRANT_CONTENT_VECTOR_SIZE=1024

# Distance metric (default: Cosine)
QDRANT_CONTENT_DISTANCE=Cosine
```

#### **Text Indexing**

```bash
# Enable text indexing (default: false for pure vector search)
QDRANT_CONTENT_TEXT_INDEX=false
```

**Why disabled by default?**
- Content collection uses pure vector search for semantic similarity
- Text indexing adds overhead without benefit for this use case
- Enable only if you need keyword filtering on content

#### **HNSW Index Tuning**

```bash
QDRANT_CONTENT_HNSW_M=16
QDRANT_CONTENT_HNSW_EF_CONSTRUCT=100
QDRANT_CONTENT_HNSW_FULL_SCAN_THRESHOLD=10000
QDRANT_CONTENT_HNSW_ON_DISK=false
```

---

### **General Collection Settings**

```bash
# Number of shards (default: 1)
# Increase for distributed deployment
QDRANT_SHARD_NUMBER=1

# Replication factor (default: 1)
# Number of replicas for high availability
QDRANT_REPLICATION_FACTOR=1

# Write consistency factor (default: 1)
# How many replicas must confirm writes
QDRANT_WRITE_CONSISTENCY_FACTOR=1

# Store payload on disk (default: true)
# true = saves RAM, slightly slower queries
QDRANT_ON_DISK_PAYLOAD=true
```

---

## 🚀 **Usage**

### **Basic Usage**

```bash
# Create collections using .env configuration
python scripts/setup_qdrant_collections.py
```

### **Dry Run (Preview Configuration)**

```bash
# Show configuration without creating collections
python scripts/setup_qdrant_collections.py --dry-run
```

**Output:**
```
============================================================
QDRANT COLLECTION SETUP
============================================================
Qdrant Server: 192.168.254.22:6333
Ollama Server: 192.168.254.22:11434

Filename Collection: filename-granite-embedding30m
  Model: granite-embedding:30m
  Dimensions: 384D
  Distance: Cosine
  Text Index: True
  Tokenizer: word

Content Collection: releasenotes-bge-m3
  Model: bge-m3
  Dimensions: 1024D
  Distance: Cosine
  Text Index: False

General Settings:
  Shards: 1
  Replication: 1
  Write Consistency: 1
  On-disk Payload: True
============================================================

🔍 DRY RUN MODE - No collections will be created

Configuration loaded successfully!
Remove --dry-run flag to create collections
```

### **Validate Ollama Dimensions**

```bash
# Verify Ollama models produce expected dimensions
python scripts/setup_qdrant_collections.py --validate-ollama
```

**What it does:**
- Connects to Ollama server
- Generates test embeddings with your models
- Verifies dimensions match `.env` configuration
- Prevents dimension mismatch errors

**Example Output:**
```
Validating Ollama model dimensions...

✅ Model 'granite-embedding:30m' produces 384D embeddings (matches expected 384D)
✅ Model 'bge-m3' produces 1024D embeddings (matches expected 1024D)

✅ All Ollama models validated successfully!
```

### **Override Settings**

```bash
# Override host/port from command line
python scripts/setup_qdrant_collections.py --host 192.168.1.100 --port 6333
```

---

## 📊 **Common Configurations**

### **Configuration 1: Default (Current Setup)**

```bash
# Filename Collection
QDRANT_FILENAME_VECTOR_SIZE=384
QDRANT_FILENAME_DISTANCE=Cosine
QDRANT_FILENAME_TEXT_INDEX=true
QDRANT_FILENAME_TOKENIZER=word

# Content Collection
QDRANT_CONTENT_VECTOR_SIZE=1024
QDRANT_CONTENT_DISTANCE=Cosine
QDRANT_CONTENT_TEXT_INDEX=false
```

**Use Case:** Fast filename matching + semantic content search

---

### **Configuration 2: Multilingual Support**

```bash
# For CJK (Chinese, Japanese, Korean) documents
QDRANT_FILENAME_TOKENIZER=multilingual
QDRANT_CONTENT_TEXT_INDEX=true
QDRANT_CONTENT_TOKENIZER=multilingual
```

**Use Case:** Documents in multiple languages

---

### **Configuration 3: Memory Optimized**

```bash
# Store everything on disk to save RAM
QDRANT_FILENAME_HNSW_ON_DISK=true
QDRANT_CONTENT_HNSW_ON_DISK=true
QDRANT_ON_DISK_PAYLOAD=true
```

**Use Case:** Limited RAM, acceptable query latency

---

### **Configuration 4: High Performance**

```bash
# Keep everything in RAM for fastest queries
QDRANT_FILENAME_HNSW_ON_DISK=false
QDRANT_CONTENT_HNSW_ON_DISK=false
QDRANT_ON_DISK_PAYLOAD=false

# Increase HNSW parameters
QDRANT_FILENAME_HNSW_M=32
QDRANT_CONTENT_HNSW_M=32
QDRANT_FILENAME_HNSW_EF_CONSTRUCT=200
QDRANT_CONTENT_HNSW_EF_CONSTRUCT=200
```

**Use Case:** High-performance production deployment with ample RAM

---

### **Configuration 5: Different Embedding Models**

```bash
# Using smaller models
OLLAMA_FILENAME_MODEL=all-minilm
QDRANT_FILENAME_VECTOR_SIZE=384

OLLAMA_CONTENT_MODEL=all-minilm
QDRANT_CONTENT_VECTOR_SIZE=384
```

**Use Case:** Faster embeddings, lower accuracy

---

## 🔍 **Dimension Validation**

### **Why It Matters**

If your Qdrant collection expects 384D vectors but your Ollama model produces 1024D vectors, **uploads will fail**!

### **How to Validate**

```bash
# Method 1: Use validation flag
python scripts/setup_qdrant_collections.py --validate-ollama

# Method 2: Manual test
curl http://192.168.254.22:11434/api/embed -d '{
  "model": "granite-embedding:30m",
  "input": "test"
}' | jq '.embeddings[0] | length'
```

### **Common Embedding Dimensions**

| Model | Dimensions |
|-------|------------|
| `granite-embedding:30m` | 384 |
| `bge-m3` | 1024 |
| `all-minilm` | 384 |
| `nomic-embed-text` | 768 |
| `mxbai-embed-large` | 1024 |

---

## 🐛 **Troubleshooting**

### **Error: Invalid distance metric**

```bash
❌ Invalid distance metric: cosine
   Valid options: Cosine, Euclid, Dot, Manhattan
```

**Fix:** Use exact capitalization: `Cosine` not `cosine`

---

### **Error: Invalid tokenizer**

```bash
❌ Invalid tokenizer: Word
   Valid options: word, whitespace, prefix, multilingual
```

**Fix:** Use lowercase: `word` not `Word`

---

### **Error: Dimension mismatch**

```bash
❌ Model 'granite-embedding:30m' produces 384D embeddings, but collection expects 1024D!
   Update QDRANT_*_VECTOR_SIZE in .env to 384 or use a different model
```

**Fix:** Update `.env`:
```bash
QDRANT_FILENAME_VECTOR_SIZE=384  # Match model output
```

---

### **Error: Collection already exists**

```bash
✅ Collection 'filename-granite-embedding30m' already exists
```

**This is OK!** The script skips existing collections. To recreate:

```bash
# Delete existing collection
curl -X DELETE http://192.168.254.22:6333/collections/filename-granite-embedding30m

# Run setup again
python scripts/setup_qdrant_collections.py
```

---

## 📚 **Advanced Topics**

### **Changing Collection Names**

```bash
# In .env
QDRANT_FILENAME_COLLECTION=my-custom-filename-collection
QDRANT_CONTENT_COLLECTION=my-custom-content-collection
```

**Note:** Update pipeline code if you change names!

---

### **Using Different Models**

1. **Pull new model:**
   ```bash
   ssh user@192.168.254.22
   ollama pull nomic-embed-text
   ```

2. **Update .env:**
   ```bash
   OLLAMA_FILENAME_MODEL=nomic-embed-text
   QDRANT_FILENAME_VECTOR_SIZE=768  # nomic-embed-text is 768D
   ```

3. **Validate:**
   ```bash
   python scripts/setup_qdrant_collections.py --validate-ollama
   ```

4. **Create collection:**
   ```bash
   python scripts/setup_qdrant_collections.py
   ```

---

### **Distributed Deployment**

```bash
# Multiple shards for horizontal scaling
QDRANT_SHARD_NUMBER=3

# Replication for high availability
QDRANT_REPLICATION_FACTOR=2

# Write consistency (must be ≤ replication_factor)
QDRANT_WRITE_CONSISTENCY_FACTOR=2
```

---

## ✅ **Verification**

After running the setup script, verify collections:

```bash
# List all collections
curl http://192.168.254.22:6333/collections | jq .

# Check filename collection
curl http://192.168.254.22:6333/collections/filename-granite-embedding30m | jq .result.config

# Check content collection
curl http://192.168.254.22:6333/collections/releasenotes-bge-m3 | jq .result.config

# Count points
curl http://192.168.254.22:6333/collections/filename-granite-embedding30m/points/count
curl http://192.168.254.22:6333/collections/releasenotes-bge-m3/points/count
```

---

## 🎓 **Best Practices**

1. **Always run dry-run first**
   ```bash
   python scripts/setup_qdrant_collections.py --dry-run
   ```

2. **Validate Ollama dimensions**
   ```bash
   python scripts/setup_qdrant_collections.py --validate-ollama
   ```

3. **Use version control for .env**
   - Keep `.env.example` in git
   - Never commit actual `.env` with secrets

4. **Document custom configurations**
   - Add comments in `.env` explaining why you changed defaults

5. **Test with small datasets first**
   - Verify configuration works before full ingestion

---

## 📖 **Related Documentation**

- [CONFIGURATION.md](CONFIGURATION.md) - All environment variables
- [QDRANT_COLLECTIONS.md](QDRANT_COLLECTIONS.md) - Collection structure details
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Complete setup instructions
- [README.md](README.md) - General overview

---

**Last Updated:** November 7, 2025
