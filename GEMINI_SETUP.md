# Gemini Backend Setup - Final Steps

## ✅ Completed

1. **Multi-backend embedding system implemented**
   - Abstract `EmbeddingBackend` base class
   - `OllamaBackend` for local embeddings
   - `GeminiBackend` for Google Gemini API
   - Unified `EmbeddingClient` dispatcher

2. **Configuration updated**
   - `.env` now has `EMBEDDING_BACKEND=gemini`
   - Gemini configuration section added
   - Qdrant vector sizes updated to 768D (matching Gemini)

3. **Pipelines updated**
   - `src/pipeline.py` - Full pipeline with backend selection
   - `scripts/reprocess_from_markdown.py` - Reprocess with backend selection
   - `scripts/convert_to_markdown.py` - NEW markdown-only pipeline

4. **Dependencies installed**
   - `google-generativeai>=0.3.0` installed
   - All imports working correctly

5. **Script tested**
   - `reprocess_from_markdown.py` initializes successfully
   - All components load correctly
   - Qdrant connection established

## ⚠️ Action Required

### 1. Add Your Gemini API Key

Edit `.env` and replace the placeholder:

```bash
# Universal batch size for all operations
BATCH_SIZE=100

# Backend selection
EMBEDDING_BACKEND=gemini

# Gemini configuration
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-embedding-001
GEMINI_TASK_TYPE=RETRIEVAL_DOCUMENT
GEMINI_DIMENSIONS=768
```

### 2. Verify Qdrant Collections Match

Your Qdrant collections must be configured for 768-dimensional vectors:

```bash
# Current settings in .env (already updated):
QDRANT_FILENAME_VECTOR_SIZE=768
QDRANT_CONTENT_VECTOR_SIZE=768
```

**If your existing Qdrant collections are still 384D/1024D (Ollama dimensions):**

You have two options:

**Option A: Create new collections** (recommended)
```bash
# Update collection names in .env
QDRANT_FILENAME_COLLECTION=filenames-gemini-768
QDRANT_CONTENT_COLLECTION=content-gemini-768

# Create new collections
python scripts/setup_qdrant_collections.py
```

**Option B: Delete and recreate existing collections**
```bash
# This will delete all existing vectors!
# Use Qdrant UI or API to delete collections
# Then run:
python scripts/setup_qdrant_collections.py
```

### 3. Test the Pipeline

Once you've added your API key:

```bash
# Test with a single file (dry run simulation)
python scripts/reprocess_from_markdown.py

# Or test the full pipeline
python src/pipeline.py
```

## 📊 Current Configuration

```
Embedding Backend: Gemini
Model: gemini-embedding-001
Dimensions: 768
Task Type: RETRIEVAL_DOCUMENT
Batch Size: 100 (universal for Gemini API + Qdrant uploads)

Qdrant Collections:
- Filename: filenames-2 (768D)
- Content: content-2 (768D)
```

## 🔄 Switching Back to Ollama

If you need to switch back to Ollama:

1. Edit `.env`:
   ```bash
   BATCH_SIZE=100  # Universal batch size (works for both)
   EMBEDDING_BACKEND=ollama
   QDRANT_FILENAME_VECTOR_SIZE=384
   QDRANT_CONTENT_VECTOR_SIZE=1024
   ```

2. Use different collection names or recreate collections with correct dimensions.

**Note:** `BATCH_SIZE` is now universal and controls:
- Ollama batch embedding API calls
- Gemini batch embedding API calls
- Qdrant upload batch size

## 🚀 What's New

### Pipeline A: Markdown-Only Conversion
```bash
python scripts/convert_to_markdown.py
```
- Converts source files to markdown
- Uploads to R2
- **Stops before embedding** (no Qdrant upload)

### Pipeline B: Markdown to Qdrant
```bash
python scripts/reprocess_from_markdown.py
```
- Processes existing markdown files
- Generates embeddings (Ollama or Gemini)
- Uploads to Qdrant

### Full Pipeline
```bash
python src/pipeline.py
```
- Complete flow: source → markdown → embeddings → Qdrant

## 📝 Notes

- **Gemini native batch API** is implemented for efficiency (single API call for multiple texts)
- **Separate Qdrant points** are created for each chunk (not bundled)
- **Phase 3 deduplication** works across both backends
- All existing logging and monitoring features preserved

## ❓ Troubleshooting

### "Invalid API key" error
- Verify your `GEMINI_API_KEY` in `.env`
- Check key has embedding permissions at https://ai.google.dev/

### "Vector dimension mismatch" error
- Ensure Qdrant collections are 768D
- Recreate collections if needed

### "Cannot import genai" error
- Already fixed! The import path was corrected to `google.generativeai`

---

**Status:** ✅ Ready to test with your Gemini API key!
