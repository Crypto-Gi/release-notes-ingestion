# Universal Batch Size Configuration

## Overview

The system now uses a **single universal `BATCH_SIZE`** variable that controls ALL batch operations across the entire pipeline:

- ✅ **Ollama embedding API calls** (native batch support via `/api/embed`)
- ✅ **Gemini embedding API calls** (native batch support)
- ✅ **Qdrant vector uploads** (batch point insertion)

## Configuration

### Simple Setup

In your `.env` file, set ONE variable:

```bash
# Universal batch size for ALL operations
BATCH_SIZE=100
```

That's it! This single value now controls:
1. How many texts are sent to Ollama/Gemini in one API call
2. How many vector points are uploaded to Qdrant in one batch

### Previous Configuration (DEPRECATED)

❌ **Old way** (no longer needed):
```bash
OLLAMA_BATCH_SIZE=100
GEMINI_BATCH_SIZE=100
QDRANT_BATCH_SIZE=100
```

✅ **New way** (simplified):
```bash
BATCH_SIZE=100
```

## How It Works

### Example: Processing 500 Chunks with `BATCH_SIZE=100`

**Ollama Backend:**
1. **Embedding Generation:** 5 API calls to Ollama (100 texts each)
2. **Qdrant Upload:** 5 batch uploads (100 points each)

**Gemini Backend:**
1. **Embedding Generation:** 5 API calls to Gemini (100 texts each)
2. **Qdrant Upload:** 5 batch uploads (100 points each)

**Total API Calls:** 10 (5 embedding + 5 Qdrant) instead of 1000!

## Native Batch Support

### Ollama

Ollama's `/api/embed` endpoint supports native batch processing:

```bash
curl http://localhost:11434/api/embed -d '{
  "model": "bge-m3",
  "input": ["text1", "text2", "text3", ...]
}'
```

**Response:**
```json
{
  "embeddings": [[...], [...], [...], ...]
}
```

### Gemini

Gemini's `embed_content` method supports native batch processing:

```python
result = genai.embed_content(
    model="gemini-embedding-001",
    content=["text1", "text2", "text3", ...],
    task_type="RETRIEVAL_DOCUMENT",
    output_dimensionality=768
)
```

**Response:**
```python
{
  'embedding': [[...], [...], [...], ...]
}
```

## Benefits

### 1. **Simplified Configuration**
- One variable instead of three
- No confusion about which batch size to use
- Guaranteed synchronization across all operations

### 2. **Performance Optimization**
- Fewer API calls = lower latency
- Batch operations are more efficient
- Reduced network overhead

### 3. **Consistency**
- Same batch size for embeddings and uploads
- No mismatch between embedding batches and Qdrant batches
- Easier to tune performance

### 4. **Flexibility**
- Adjust ONE value to control all batch operations
- Easy to experiment with different batch sizes
- Works identically for both Ollama and Gemini

## Tuning Guidelines

### Small Batch Size (50-100)
**Use when:**
- Limited memory
- Testing/development
- Frequent progress updates needed

**Pros:**
- Lower memory usage
- More granular progress logging
- Faster failure recovery

**Cons:**
- More API calls
- Slightly higher latency

### Medium Batch Size (100-200)
**Use when:**
- Production workloads
- Balanced performance/memory
- Standard use case

**Pros:**
- Good balance
- Reasonable memory usage
- Efficient API usage

**Cons:**
- None (recommended default)

### Large Batch Size (200-500)
**Use when:**
- High-performance requirements
- Large memory available
- Bulk processing

**Pros:**
- Maximum efficiency
- Fewest API calls
- Best throughput

**Cons:**
- Higher memory usage
- Less frequent progress updates
- Larger failure impact

## Implementation Details

### Configuration Loading

```python
# config.py
batch_size = int(os.getenv("BATCH_SIZE", "100"))

embedding_config = EmbeddingConfig(
    backend="gemini",  # or "ollama"
    batch_size=batch_size,  # Universal batch size
    ...
)
```

### Backend Usage

```python
# Both backends use the same batch_size
if backend == "ollama":
    backend = OllamaBackend(
        host=host,
        port=port,
        batch_size=config.embedding.batch_size  # Universal
    )
elif backend == "gemini":
    backend = GeminiBackend(
        api_key=api_key,
        model=model,
        batch_size=config.embedding.batch_size  # Universal
    )
```

### Qdrant Upload

```python
# Qdrant uses the same batch_size
qdrant_uploader = QdrantUploader(
    host=host,
    port=port,
    batch_size=config.embedding.batch_size  # Universal
)
```

## Migration Guide

If you have existing `.env` files with separate batch sizes:

### Step 1: Add Universal Batch Size

```bash
# Add this line
BATCH_SIZE=100
```

### Step 2: Remove Old Variables (Optional)

```bash
# These are no longer used (safe to remove)
# OLLAMA_BATCH_SIZE=100
# GEMINI_BATCH_SIZE=100
# QDRANT_BATCH_SIZE=100
```

### Step 3: Test

```bash
python scripts/reprocess_from_markdown.py
```

Look for log output:
```
Gemini backend initialized
  Batch size: 100
...
Qdrant uploader initialized
  Batch size: 100
```

Both should show the same value!

## Monitoring

The logs will show batch processing progress:

```
Generating batch embeddings for 500 texts (native batch, batch_size=100)
Processing batch 1/5 (100 texts)
Processing batch 2/5 (100 texts)
...
Processed 500/500 embeddings
Batch embedding complete: 500 vectors
```

## Troubleshooting

### Issue: "Batch size mismatch"

**Cause:** Old environment variables still present

**Solution:** Remove `OLLAMA_BATCH_SIZE`, `GEMINI_BATCH_SIZE`, `QDRANT_BATCH_SIZE` from `.env`

### Issue: "Memory errors during batch processing"

**Cause:** Batch size too large for available memory

**Solution:** Reduce `BATCH_SIZE` (try 50 or 25)

### Issue: "Too many API calls"

**Cause:** Batch size too small

**Solution:** Increase `BATCH_SIZE` (try 200 or 500)

## Summary

✅ **One variable** controls everything
✅ **Native batch support** for both Ollama and Gemini
✅ **Synchronized** embedding and upload operations
✅ **Simplified** configuration
✅ **Optimized** performance

**Configuration:**
```bash
BATCH_SIZE=100
```

**That's all you need!** 🚀
