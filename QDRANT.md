# Qdrant Configuration & Collections Guide

**Last Updated:** November 7, 2025  
**Purpose:** Complete Qdrant setup and collection schema reference

This document consolidates Qdrant collection setup instructions and collection structure details.

---

**Table of Contents:**
- [1. Qdrant Collection Setup](#1-qdrant-collection-setup)
- [2. Collection Structure & Schema](#2-collection-structure--schema)

---

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

---

# Qdrant Collections Structure for Search-API

## Overview

This document describes the Qdrant vector database collections used in our release notes search system. The architecture implements a **two-stage search workflow** for efficient document discovery and content retrieval.

---

## Collections

### 1. `filename-granite-embedding30m` (Document Discovery)

**Purpose:** Fast filename indexing and document discovery

**Use Case:** Stage 1 of two-stage search - finding relevant release notes documents

**Configuration:**
- **Vector Dimensions:** 384
- **Embedding Model:** `granite-embedding:30m` (Ollama)
- **Distance Metric:** Cosine
- **Total Points:** 53 documents
- **Payload Indexing:** ✅ Enabled with text tokenizer
- **Tokenizer:** `word` (min: 1, max: 15 tokens)
- **Text Processing:** Lowercase enabled

**Complete Collection Structure (JSON):**
```json
{
  "status": "green",
  "optimizer_status": "ok",
  "indexed_vectors_count": 0,
  "points_count": 53,
  "segments_count": 3,
  "config": {
    "params": {
      "vectors": {
        "size": 384,
        "distance": "Cosine"
      },
      "shard_number": 1,
      "replication_factor": 1,
      "write_consistency_factor": 1,
      "on_disk_payload": true
    },
    "hnsw_config": {
      "m": 16,
      "ef_construct": 100,
      "full_scan_threshold": 10000,
      "max_indexing_threads": 0,
      "on_disk": false
    },
    "optimizer_config": {
      "deleted_threshold": 0.2,
      "vacuum_min_vector_number": 1000,
      "default_segment_number": 0,
      "max_segment_size": null,
      "memmap_threshold": null,
      "indexing_threshold": 20000,
      "flush_interval_sec": 5,
      "max_optimization_threads": null
    },
    "wal_config": {
      "wal_capacity_mb": 32,
      "wal_segments_ahead": 0,
      "wal_retain_closed": 1
    },
    "quantization_config": null,
    "strict_mode_config": {
      "enabled": false
    }
  },
  "payload_schema": {
    "metadata.filename": {
      "data_type": "text",
      "params": {
        "type": "text",
        "tokenizer": "word",
        "min_token_len": 1,
        "max_token_len": 15,
        "lowercase": true,
        "on_disk": false
      },
      "points": 0
    },
    "pagecontent": {
      "data_type": "text",
      "params": {
        "type": "text",
        "tokenizer": "word",
        "min_token_len": 1,
        "max_token_len": 15,
        "lowercase": true,
        "on_disk": false
      },
      "points": 53
    }
  }
}
```

**Key Configuration Notes:**
- `vectors.size: 384` - Small vector size for fast filename matching
- `vectors.distance: "Cosine"` - Cosine similarity for vector comparison
- `payload_schema.pagecontent.tokenizer: "word"` - Word-based tokenization for filenames
- `payload_schema.pagecontent.lowercase: true` - Case-insensitive search
- `on_disk_payload: true` - Payload stored on disk to save memory

**Payload Structure:**
```json
{
  "pagecontent": "ECOS_9.3.7.1_Release_Notes_RevH.pdf",
  "source": "ECOS_9.3.7.1_Release_Notes_RevH.json"
}
```

**Payload Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `pagecontent` | string | PDF filename (used as searchable content) |
| `source` | string | Original JSON source file |

**Search Example:**
```bash
# User query: "ECOS version 9.3.7"
# Returns: ["ECOS_9.3.7.1_Release_Notes_RevH.pdf", "ECOS_9.3.7.0_Release_Notes_RevD.pdf"]
```

**API Endpoint:** `/simple-search`

---

### 2. `releasenotes-bge-m3` (Content Search)

**Purpose:** Detailed content search within specific documents

**Use Case:** Stage 2 of two-stage search - retrieving relevant content chunks with context

**Configuration:**
- **Vector Dimensions:** 1024
- **Embedding Model:** `bge-m3` (Ollama)
- **Distance Metric:** Cosine
- **Total Points:** 2,826 content chunks
- **Payload Indexing:** ❌ No text indexing (vector-only search)
- **Tokenizer:** None (relies purely on vector similarity)

**Complete Collection Structure (JSON):**
```json
{
  "status": "green",
  "optimizer_status": "ok",
  "indexed_vectors_count": 0,
  "points_count": 2826,
  "segments_count": 3,
  "config": {
    "params": {
      "vectors": {
        "size": 1024,
        "distance": "Cosine"
      },
      "shard_number": 1,
      "replication_factor": 1,
      "write_consistency_factor": 1,
      "on_disk_payload": true
    },
    "hnsw_config": {
      "m": 16,
      "ef_construct": 100,
      "full_scan_threshold": 10000,
      "max_indexing_threads": 0,
      "on_disk": false
    },
    "optimizer_config": {
      "deleted_threshold": 0.2,
      "vacuum_min_vector_number": 1000,
      "default_segment_number": 0,
      "max_segment_size": null,
      "memmap_threshold": null,
      "indexing_threshold": 20000,
      "flush_interval_sec": 5,
      "max_optimization_threads": null
    },
    "wal_config": {
      "wal_capacity_mb": 32,
      "wal_segments_ahead": 0,
      "wal_retain_closed": 1
    },
    "quantization_config": null,
    "strict_mode_config": {
      "enabled": false
    }
  },
  "payload_schema": {}
}
```

**Key Configuration Notes:**
- `vectors.size: 1024` - Large vector size for semantic understanding
- `vectors.distance: "Cosine"` - Cosine similarity for vector comparison
- `payload_schema: {}` - **No text indexing** - pure vector search only
- `on_disk_payload: true` - Payload stored on disk to save memory
- **No tokenizer** - Relies entirely on vector embeddings for semantic search

**Payload Structure:**
```json
{
  "pagecontent": "Bug fixes in version 9.3.7.1: Fixed memory leak in authentication module...",
  "metadata": {
    "filename": "ECOS_9.3.7.1_Release_Notes_RevH.pdf",
    "page_number": 47,
    "element_type": "Table",
    "md5_hash": "98193a77c33b48ac1ea543dff7623d83"
  }
}
```

**Payload Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `pagecontent` | string | Actual content chunk (200-300 words) |
| `metadata.filename` | string | Source PDF filename |
| `metadata.page_number` | integer | Page number in original document |
| `metadata.element_type` | string | Content type (Text, Table, Image, etc.) |
| `metadata.md5_hash` | string | Content hash for deduplication |

**Search Example:**
```bash
# Filter by filename from Stage 1
# Query: "bug fixes", "new features"
# Returns: Relevant content chunks with context windows
```

**API Endpoint:** `/search`

---

## Collection Configuration Explained

### Understanding the JSON Structure

Both collections share similar base configurations but differ in payload indexing:

#### **Common Configuration Parameters:**

**Vector Configuration (`config.params.vectors`):**
- `size` - Vector dimensions (384 for filenames, 1024 for content)
- `distance: "Cosine"` - Similarity metric for comparing vectors
  - Range: -1 (opposite) to 1 (identical)
  - Best for normalized embeddings

**HNSW Index (`config.hnsw_config`):**
- `m: 16` - Number of bi-directional links per node (higher = better recall, more memory)
- `ef_construct: 100` - Size of dynamic candidate list during index construction
- `full_scan_threshold: 10000` - Switch to brute-force search below this point count
- `on_disk: false` - Keep HNSW index in memory for speed

**Optimizer (`config.optimizer_config`):**
- `deleted_threshold: 0.2` - Trigger optimization when 20% of vectors are deleted
- `vacuum_min_vector_number: 1000` - Minimum vectors before vacuum runs
- `indexing_threshold: 20000` - Start indexing after this many vectors
- `flush_interval_sec: 5` - Write to disk every 5 seconds

**Write-Ahead Log (`config.wal_config`):**
- `wal_capacity_mb: 32` - WAL file size limit
- `wal_segments_ahead: 0` - Number of segments to pre-allocate
- `wal_retain_closed: 1` - Keep 1 closed WAL segment for recovery

**Storage:**
- `on_disk_payload: true` - Store payload on disk (saves RAM)
- `shard_number: 1` - Single shard (no distribution)
- `replication_factor: 1` - No replication

#### **Key Difference: Payload Schema**

**Filename Collection - WITH Indexing:**
```json
"payload_schema": {
  "pagecontent": {
    "data_type": "text",
    "params": {
      "tokenizer": "word",      // Split on word boundaries
      "min_token_len": 1,       // Minimum token length
      "max_token_len": 15,      // Maximum token length
      "lowercase": true,        // Normalize to lowercase
      "on_disk": false          // Keep index in memory
    }
  }
}
```
**Purpose:** Enable fast text-based filtering and hybrid search

**Content Collection - NO Indexing:**
```json
"payload_schema": {}
```
**Purpose:** Pure vector search without text indexing overhead

---

## Key Differences Between Collections

### Collection Comparison

| Feature | filename-granite-embedding30m | releasenotes-bge-m3 |
|---------|------------------------------|---------------------|
| **Vector Dimensions** | 384 | 1024 |
| **Embedding Model** | granite-embedding:30m | bge-m3 |
| **Points Count** | 53 | 2,826 |
| **Payload Indexing** | ✅ Yes | ❌ No |
| **Text Tokenizer** | `word` tokenizer | None |
| **Token Length** | 1-15 tokens | N/A |
| **Lowercase** | ✅ Enabled | N/A |
| **Search Type** | Hybrid (vector + text) | Pure vector |
| **Use Case** | Fast filename matching | Semantic content search |

### Why Different Configurations?

**1. Filename Collection (with tokenizer):**
- **Purpose:** Fast exact and fuzzy filename matching
- **Tokenizer Benefits:**
  - Enables keyword search on filenames
  - Supports partial matches (e.g., "ECOS 9.3.7" matches "ECOS_9.3.7.1")
  - Lowercase normalization for case-insensitive search
  - Word-based tokenization for version numbers
- **Performance:** Very fast due to small vector size (384D) and text indexing

**2. Content Collection (no tokenizer):**
- **Purpose:** Pure semantic similarity search
- **No Tokenizer Benefits:**
  - Relies entirely on vector embeddings for meaning
  - Better for semantic understanding vs exact matches
  - No overhead from text indexing
  - Optimal for "find similar content" queries
- **Performance:** Moderate speed with high-quality semantic results (1024D)

### Payload Schema Differences

**Filename Collection - Indexed Fields:**
```json
{
  "pagecontent": {
    "data_type": "text",
    "tokenizer": "word",
    "min_token_len": 1,
    "max_token_len": 15,
    "lowercase": true
  },
  "metadata.filename": {
    "data_type": "text",
    "tokenizer": "word",
    "min_token_len": 1,
    "max_token_len": 15,
    "lowercase": true
  }
}
```

**Content Collection - No Indexed Fields:**
```json
{
  "payload_schema": {}
}
```
*Note: All filtering happens on raw payload data, not indexed fields*

---

## Two-Stage Search Workflow

### Stage 1: Document Discovery

**Endpoint:** `POST /simple-search`

**Collection:** `filename-granite-embedding30m`

**Purpose:** Find relevant release notes documents

**Request:**
```json
{
  "collection_name": "filename-granite-embedding30m",
  "queries": ["ECOS version 9.3.7"],
  "embedding_model": "granite-embedding:30m",
  "limit": 5
}
```

**Response:**
```json
{
  "status": "success",
  "total_results": 2,
  "hits": [
    {
      "id": "uuid-1",
      "score": 0.85,
      "payload": {
        "pagecontent": "ECOS_9.3.7.1_Release_Notes_RevH.pdf"
      }
    }
  ]
}
```

**Output:** List of relevant filenames

---

### Stage 2: Content Search

**Endpoint:** `POST /search`

**Collection:** `releasenotes-bge-m3`

**Purpose:** Search within specific documents found in Stage 1

**Request:**
```json
{
  "collection_name": "releasenotes-bge-m3",
  "search_queries": ["bug fixes", "new features"],
  "filter": {
    "metadata.filename": {
      "match_value": "ECOS_9.3.7.1_Release_Notes_RevH.pdf"
    }
  },
  "embedding_model": "bge-m3",
  "limit": 5,
  "context_window_size": 3
}
```

**Response:**
```json
{
  "results": [
    [
      {
        "filename": "ECOS_9.3.7.1_Release_Notes_RevH.pdf",
        "score": 0.92,
        "center_page": 15,
        "combined_page": "Bug fixes in version 9.3.7.1: Fixed memory leak...",
        "page_numbers": [13, 14, 15, 16, 17]
      }
    ]
  ]
}
```

**Output:** Content chunks with surrounding context

---

## Search-API Compatibility

### Required Payload Schema

For content to be searchable via search-API, it must follow this structure:

```json
{
  "pagecontent": "text content here",
  "metadata": {
    "filename": "document.pdf",
    "page_number": 1
  }
}
```

**Critical Fields:**
- `pagecontent` - Main searchable text content
- `metadata.filename` - Required for filtering in Stage 2
- `metadata.page_number` - Required for context window retrieval

---

## Context Window Retrieval

The search-API retrieves surrounding pages for better context:

**Configuration:**
- Default window size: 5 pages (configurable)
- Range: `[center_page - window_size, center_page + window_size]`
- Result limit: `(window_size * 2) + 1` pages

**Example:**
- Center page: 15
- Window size: 3
- Retrieved pages: [12, 13, 14, 15, 16, 17, 18]

---

## Embedding Models

### Granite Embedding 30M
- **Model:** `granite-embedding:30m`
- **Dimensions:** 384
- **Size:** 62 MB
- **Use:** Fast filename/document matching
- **Collection:** `filename-granite-embedding30m`

### BGE-M3
- **Model:** `bge-m3`
- **Dimensions:** 1024
- **Size:** 1.2 GB
- **Use:** Semantic content search
- **Collection:** `releasenotes-bge-m3`

---

## Data Ingestion Pipeline

### Current Workflow

```
PDF Files
   ↓
Docling Service (PDF → Markdown)
   ↓
Semantic Chunker (Markdown → JSON chunks)
   ↓
Ollama Embeddings (Text → Vectors)
   ↓
Qdrant Upload (Vectors → Collections)
```

### Chunk Size Configuration
- **Target:** 200-300 words per chunk
- **Token Range:** 150-225 tokens (using GPT-3.5-turbo tokenizer)
- **Overlap:** Handled by semantic splitter

---

## Filtering Capabilities

### Supported Filter Types

**1. Exact Match (match_value):**
```json
{
  "metadata.filename": {
    "match_value": "ECOS_9.3.7.1_Release_Notes.pdf"
  }
}
```

**2. Text Match (match_text):**
```json
{
  "metadata.element_type": {
    "match_text": "Table"
  }
}
```

**3. Array Match (match_any):**
```json
{
  "metadata.filename": {
    "match_value": ["file1.pdf", "file2.pdf", "file3.pdf"]
  }
}
```

**4. Range Filters:**
```json
{
  "metadata.page_number": {
    "range": {
      "gte": 10,
      "lte": 50
    }
  }
}
```

---

## Performance Considerations

### Stage 1 (Filename Collection)
- **Speed:** Very fast (384D vectors, 53 points)
- **Purpose:** Quick document discovery
- **No context retrieval:** Returns only filenames

### Stage 2 (Content Collection)
- **Speed:** Moderate (1024D vectors, 2,826 points)
- **Purpose:** Detailed content search
- **Context retrieval:** Fetches surrounding pages

### Optimization Tips
1. Always use Stage 1 to narrow down documents first
2. Filter Stage 2 searches by filename from Stage 1
3. Adjust context window size based on needs
4. Use appropriate embedding models for each stage

---

## Connection Details

### Qdrant Server
- **Host:** `192.168.254.22`
- **Port:** `6333`
- **API Port:** `6334`
- **Dashboard:** `http://192.168.254.22:6333/dashboard`

### Ollama Server
- **Host:** `192.168.254.22`
- **Port:** `11434`
- **API:** `http://192.168.254.22:11434/api`

---

## API Examples

### Simple Search (Stage 1)
```bash
curl -X POST "http://localhost:8000/simple-search" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "filename-granite-embedding30m",
    "queries": ["ECOS version 9.3.7"],
    "embedding_model": "granite-embedding:30m",
    "limit": 5
  }'
```

### Advanced Search (Stage 2)
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "releasenotes-bge-m3",
    "search_queries": ["bug fixes", "performance improvements"],
    "filter": {
      "metadata.filename": {
        "match_value": "ECOS_9.3.7.1_Release_Notes.pdf"
      }
    },
    "embedding_model": "bge-m3",
    "limit": 5,
    "context_window_size": 3
  }'
```

---

## Maintenance

### Adding New Documents
1. Convert PDF to markdown using Docling
2. Chunk markdown content (200-300 words)
3. Generate embeddings with appropriate model
4. Upload to correct collection with proper metadata

### Collection Management
```bash
# List collections
curl http://192.168.254.22:6333/collections

# Get collection info
curl http://192.168.254.22:6333/collections/releasenotes-bge-m3

# Count points
curl http://192.168.254.22:6333/collections/releasenotes-bge-m3/points/count
```

---

## Future Enhancements

### Planned Improvements
- [ ] Image description integration for multimodal RAG
- [ ] Automated ingestion pipeline via N8N
- [ ] Version-specific collections for faster filtering
- [ ] Metadata enrichment (product, version, date)
- [ ] Hybrid search (vector + keyword)

---

## References

- **Search-API Repository:** `/home/mir/search-api`
- **Qdrant Documentation:** https://qdrant.tech/documentation/
- **Ollama Models:** https://ollama.ai/library
- **Project Directory:** `/home/mir/projects/release-notes-ingestion`

---

## Quick Reference: Collection Creation

### Create Filename Collection (with tokenizer)

```bash
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
```

### Create Content Collection (no tokenizer)

```bash
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

### Verify Collection Structure

```bash
# Get full collection info
curl http://192.168.254.22:6333/collections/filename-granite-embedding30m | jq .

# Get just payload schema
curl http://192.168.254.22:6333/collections/filename-granite-embedding30m | jq .result.payload_schema

# Count points
curl http://192.168.254.22:6333/collections/filename-granite-embedding30m/points/count | jq .
```

---

**Last Updated:** November 7, 2025  
**Maintained By:** Release Notes Search Team
