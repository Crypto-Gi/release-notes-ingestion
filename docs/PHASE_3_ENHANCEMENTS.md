# Phase 3 Enhancements - Advanced Logging & Deduplication

**Status:** 📋 Planning Phase  
**Priority:** High  
**Target:** Enhanced observability and deduplication

---

## 🎯 Overview

Enhance the pipeline with comprehensive logging for embeddings and Qdrant operations, plus intelligent deduplication to avoid reprocessing files.

---

## 📊 Current State

### **Existing Logs:**
```
logs/
├── conversion.json          # PDF/Word → Markdown conversion
├── upload.json              # Markdown → R2 upload
└── failed.json              # Failed processing attempts
```

### **What's Missing:**
- ❌ No embedding creation logs
- ❌ No Qdrant upload logs
- ❌ No deduplication checks before embedding
- ❌ No hash-based skip logic

---

## 🚀 Phase 3 Enhancements

### **1. New Log Files**

#### **A. Embedding Creation Log** (`logs/embedding.json`)

**Purpose:** Track successful embedding generation

**Schema:**
```json
{
  "timestamp": "2025-11-10T07:49:00Z",
  "filename": "release-notes-v1.2.pdf",
  "md5_hash": "a1b2c3d4e5f6g7h8",
  "collection_type": "content",
  "chunks_created": 15,
  "embedding_model": "bge-m3",
  "embedding_dimensions": 1024,
  "total_tokens": 7500,
  "processing_time_seconds": 2.34,
  "status": "success"
}
```

**Fields:**
- `timestamp` - ISO 8601 datetime
- `filename` - Original file name
- `md5_hash` - **xxHash64 value** (field name kept for compatibility, but uses xxHash for speed)
- `collection_type` - Target collection (filename/content)
- `chunks_created` - Number of chunks generated
- `embedding_model` - Ollama model used (bge-m3, granite-embedding:30m)
- `embedding_dimensions` - Vector dimensions (384 or 1024)
- `total_tokens` - Total tokens across all chunks
- `processing_time_seconds` - Time to generate embeddings
- `status` - success/failed

**Hash Strategy:**
- **xxHash64** - ALL hash calculations (fast, lightweight)
- **Field name** - Keep as `md5_hash` for compatibility (but stores xxHash value)
- **Note:** Despite the field name, we use xxHash for speed. Field name kept for backward compatibility.

---

#### **B. Qdrant Upload Log** (`logs/qdrant_upload.json`)

**Purpose:** Track successful Qdrant vector uploads

**Schema:**
```json
{
  "timestamp": "2025-11-10T07:49:05Z",
  "filename": "release-notes-v1.2.pdf",
  "md5_hash": "a1b2c3d4e5f6g7h8",
  "collection_name": "content",
  "points_uploaded": 15,
  "point_ids": ["uuid-1", "uuid-2", "..."],
  "batch_size": 100,
  "upload_time_seconds": 0.87,
  "status": "success"
}
```

**Fields:**
- `timestamp` - ISO 8601 datetime
- `filename` - Original file name
- `md5_hash` - **xxHash64 value** (field name kept for compatibility)
- `collection_name` - Qdrant collection (filenames/content)
- `points_uploaded` - Number of vectors uploaded
- `point_ids` - List of Qdrant point UUIDs
- `batch_size` - Batch size used for upload
- `upload_time_seconds` - Time to upload
- `status` - success/failed

---

#### **C. Skipped Files Log** (`logs/skipped.json`)

**Purpose:** Track files skipped due to deduplication

**Schema:**
```json
{
  "timestamp": "2025-11-10T07:49:10Z",
  "filename": "release-notes-v1.2.pdf",
  "md5_hash": "a1b2c3d4e5f6g7h8",
  "skip_reason": "already_embedded",
  "found_in": "log_file",
  "collection_name": "content",
  "original_processing_date": "2025-11-09T14:23:00Z"
}
```

**Fields:**
- `timestamp` - ISO 8601 datetime when skip occurred
- `filename` - Original file name
- `md5_hash` - **xxHash64 value** (field name kept for compatibility)
- `skip_reason` - Reason for skipping (already_embedded, already_in_qdrant, force_skip)
- `found_in` - Where duplicate was found (log_file, qdrant_collection, both)
- `collection_name` - Target collection that would have been used
- `original_processing_date` - When file was originally processed (if available)

**Skip Reasons:**
- `already_embedded` - Found in embedding.json log
- `already_in_qdrant` - Found in Qdrant collection
- `force_skip` - Manually skipped via configuration
- `duplicate_detected` - Found in both log and Qdrant

---

### **2. Deduplication Logic**

#### **A. Three-Level Deduplication Check**

**Before creating embeddings, check:**

1. **Log File Check** (`logs/embedding.json`) - **PRIMARY CHECK**
   ```python
   # Quick check using xxHash: Has this file been embedded before?
   # Note: Field is named md5_hash but stores xxHash value
   file_hash = FileHasher.hash_file_lightweight(file_content)  # xxHash64
   
   if file_hash in embedding_log['md5_hash']:
       logger.info(f"⏭️  Skipping {filename} - already embedded (log)")
       logger.debug(f"   Hash (xxHash64): {file_hash}")
       
       # Log the skip
       log_manager.log_skipped_file(
           filename=filename,
           md5_hash=file_hash,
           skip_reason="already_embedded",
           found_in="log_file",
           collection_name=collection_name
       )
       return
   ```
   **Why xxHash?** Ultra-fast calculation and lookup (64-bit hash, 16 chars)

2. **Qdrant Collection Check** (`metadata.md5_hash`) - **SECONDARY CHECK**
   ```python
   # Check if hash exists in Qdrant collection
   # Note: metadata.md5_hash field stores xxHash value (not actual MD5)
   file_hash = FileHasher.hash_file_lightweight(file_content)  # xxHash64
   
   results = client.scroll(
       collection_name="content",
       scroll_filter=models.Filter(
           must=[
               models.FieldCondition(
                   key="metadata.md5_hash",
                   match=models.MatchValue(value=file_hash)  # xxHash value
               )
           ]
       ),
       limit=1
   )
   
   if results[0]:  # Hash found in collection
       logger.info(f"⏭️  Skipping {filename} - already in Qdrant")
       logger.debug(f"   Hash (xxHash64): {file_hash}")
       
       # Log the skip
       log_manager.log_skipped_file(
           filename=filename,
           md5_hash=file_hash,
           skip_reason="already_in_qdrant",
           found_in="qdrant_collection",
           collection_name=collection_name
       )
       return
   ```
   **Why same hash?** Both log and Qdrant use xxHash for consistency and speed

3. **Force Reprocess Flag** (optional)
   ```python
   # Allow manual override
   if force_reprocess:
       logger.info(f"🔄 Force reprocessing {filename}")
       # Continue with embedding
   ```

---

#### **B. Deduplication Workflow**

```
┌─────────────────────────────────────────────────────────┐
│  1. Calculate file hash                                 │
│     - xxHash64 (fast, 16 chars)                         │
│     - Store in field named "md5_hash" (compatibility)   │
└──────────────┬──────────────────────────────────────────┘
               │
               v
┌─────────────────────────────────────────────────────────┐
│  2. Check logs/embedding.json (xxHash lookup)           │
│     - Hash exists in md5_hash field? → Skip ⏭️  (FAST)  │
│     - Hash missing? → Continue ✓                        │
└──────────────┬──────────────────────────────────────────┘
               │
               v
┌─────────────────────────────────────────────────────────┐
│  3. Check Qdrant collection (metadata.md5_hash)         │
│     - Hash exists? → Skip ⏭️                            │
│     - Hash missing? → Continue ✓                        │
└──────────────┬──────────────────────────────────────────┘
               │
               v
┌─────────────────────────────────────────────────────────┐
│  4. Create embeddings + Upload to Qdrant                │
│     - Log to logs/embedding.json (xxHash in md5_hash)   │
│     - Log to logs/qdrant_upload.json (xxHash in md5_hash)│
│     - Store in Qdrant metadata.md5_hash (xxHash value)  │
└─────────────────────────────────────────────────────────┘
```

**Hash Strategy Explained:**
- **Step 1:** Calculate **xxHash64** only (ultra-fast, 16 chars)
- **Step 2:** Lookup in log file using xxHash (primary dedup)
- **Step 3:** Query Qdrant using same xxHash (secondary dedup)
- **Step 4:** Store xxHash everywhere in field named `md5_hash`

**Why "md5_hash" field name?**
- Backward compatibility with existing code
- Existing Qdrant collections use this field name
- No need to migrate existing data
- Just the name - actual value is xxHash for speed!

---

### **3. Affected Pipelines**

Phase 3 enhancements must be implemented in **both** processing pipelines:

#### **A. Main Ingestion Pipeline** (`src/pipeline.py`)

**Current Flow:**
```
PDF/Word → Docling Conversion → Markdown → R2 Upload
                                         ↓
                                    Chunking → Embeddings → Qdrant
```

**Phase 3 Changes:**
1. Add deduplication check before embedding creation
2. Log embedding success to `logs/embedding.json`
3. Log Qdrant upload to `logs/qdrant_upload.json`
4. Use xxHash for all hash calculations
5. Store hash in `metadata.md5_hash` field

**Key Integration Points:**
- After markdown conversion, before chunking
- After embedding creation, before Qdrant upload
- Use existing `FileHasher.hash_file_lightweight()` for xxHash

---

#### **B. Reprocess Pipeline** (`scripts/reprocess_from_markdown.py`)

**Current Flow:**
```
R2 Markdown → Download → Chunking → Embeddings → Qdrant
```

**Phase 3 Changes:**
1. Add deduplication check before embedding creation
2. Log embedding success to `logs/embedding.json`
3. Log Qdrant upload to `logs/qdrant_upload.json`
4. Use xxHash for all hash calculations
5. Store hash in `metadata.md5_hash` field

**Key Integration Points:**
- After markdown download, before chunking
- After embedding creation, before Qdrant upload
- Use existing `FileHasher.hash_file_lightweight()` for xxHash

**Special Considerations:**
- Reprocess script may intentionally re-embed files (force_reprocess flag)
- Should still log all operations for audit trail
- Deduplication can be skipped with `FORCE_REPROCESS=true`

---

### **4. Requirements**

#### **A. Python Dependencies**

Add to `requirements.txt`:
```txt
# Existing dependencies (already present)
xxhash>=3.0.0          # Fast hashing for deduplication
python-dotenv>=1.0.0   # Environment variables
qdrant-client>=1.7.0   # Vector database client

# No new dependencies required for Phase 3
# All functionality uses existing libraries
```

#### **B. Environment Variables**

Add to `.env`:
```bash
# ============================================
# Phase 3: Deduplication & Logging
# ============================================

# Force reprocess files even if already embedded
# Set to 'true' to skip deduplication checks
FORCE_REPROCESS=false

# Batch size for Qdrant uploads (default: 100)
QDRANT_BATCH_SIZE=100

# Enable detailed embedding logs (default: true)
LOG_EMBEDDINGS=true

# Enable detailed Qdrant upload logs (default: true)
LOG_QDRANT_UPLOADS=true
```

#### **C. Log Directory Structure**

Ensure log directory exists:
```bash
logs/
├── conversion.json          # Existing: PDF/Word → Markdown
├── upload.json              # Existing: Markdown → R2
├── failed.json              # Existing: Failed attempts
├── embedding.json           # NEW: Embedding creation ✨
└── qdrant_upload.json       # NEW: Qdrant uploads ✨
```

#### **D. System Requirements**

**No changes required:**
- ✅ xxHash already installed (existing dependency)
- ✅ File system has write access to `logs/` directory
- ✅ Qdrant collections already have `metadata.md5_hash` field
- ✅ Existing `FileHasher` class supports xxHash64

---

### **5. Implementation Plan**

#### **Step 1: Create New Log Manager Methods**

**File:** `src/components/log_manager.py`

```python
def log_embedding_success(
    self,
    filename: str,
    md5_hash: str,
    xxhash: str,
    chunks_created: int,
    embedding_model: str,
    embedding_dimensions: int,
    total_tokens: int,
    processing_time: float
) -> None:
    """Log successful embedding creation"""
    
def log_qdrant_upload_success(
    self,
    filename: str,
    md5_hash: str,
    collection_name: str,
    points_uploaded: int,
    point_ids: List[str],
    batch_size: int,
    upload_time: float
) -> None:
    """Log successful Qdrant upload"""

def log_skipped_file(
    self,
    filename: str,
    md5_hash: str,
    skip_reason: str,
    found_in: str,
    collection_name: str,
    original_processing_date: Optional[str] = None
) -> None:
    """Log skipped file due to deduplication"""

def check_embedding_exists(self, md5_hash: str) -> bool:
    """Check if file already embedded (from log)"""
    
def check_qdrant_exists(
    self,
    client: QdrantClient,
    collection_name: str,
    md5_hash: str
) -> bool:
    """Check if file already in Qdrant collection"""
```

---

#### **Step 2: Update Embedding Client**

**File:** `src/components/embedding_client.py`

```python
def create_embeddings_with_dedup(
    self,
    chunks: List[str],
    md5_hash: str,
    filename: str,
    force_reprocess: bool = False
) -> Optional[List[List[float]]]:
    """
    Create embeddings with deduplication check
    
    Args:
        chunks: Text chunks to embed
        md5_hash: MD5 hash of source file
        filename: Original filename
        force_reprocess: Skip dedup checks
    
    Returns:
        List of embeddings or None if skipped
    """
    # Check 1: Log file
    if not force_reprocess and self.log_manager.check_embedding_exists(md5_hash):
        logger.info(f"⏭️  Skipping {filename} - already embedded (log)")
        return None
    
    # Check 2: Qdrant collection
    if not force_reprocess and self.log_manager.check_qdrant_exists(
        self.qdrant_client, "content", md5_hash
    ):
        logger.info(f"⏭️  Skipping {filename} - already in Qdrant")
        return None
    
    # Create embeddings
    start_time = time.time()
    embeddings = self.create_embeddings(chunks)
    processing_time = time.time() - start_time
    
    # Log success
    self.log_manager.log_embedding_success(
        filename=filename,
        md5_hash=md5_hash,
        xxhash=self.xxhash,  # From file hasher
        chunks_created=len(chunks),
        embedding_model=self.model_name,
        embedding_dimensions=len(embeddings[0]),
        total_tokens=sum(len(chunk.split()) for chunk in chunks),
        processing_time=processing_time
    )
    
    return embeddings
```

---

#### **Step 3: Update Qdrant Uploader**

**File:** `src/components/qdrant_uploader.py`

```python
def upload_with_logging(
    self,
    collection_name: str,
    points: List[PointStruct],
    filename: str,
    md5_hash: str,
    batch_size: int = 100
) -> None:
    """
    Upload points to Qdrant with logging
    
    Args:
        collection_name: Target collection
        points: List of points to upload
        filename: Original filename
        md5_hash: MD5 hash for deduplication
        batch_size: Batch size for upload
    """
    start_time = time.time()
    
    # Upload to Qdrant
    self.client.upsert(
        collection_name=collection_name,
        points=points,
        wait=True
    )
    
    upload_time = time.time() - start_time
    
    # Extract point IDs
    point_ids = [str(point.id) for point in points]
    
    # Log success
    self.log_manager.log_qdrant_upload_success(
        filename=filename,
        md5_hash=md5_hash,
        collection_name=collection_name,
        points_uploaded=len(points),
        point_ids=point_ids,
        batch_size=batch_size,
        upload_time=upload_time
    )
    
    logger.info(f"✅ Uploaded {len(points)} points to {collection_name}")
```

---

#### **Step 4: Update Pipeline**

**File:** `src/pipeline.py`

```python
# Add force_reprocess flag
force_reprocess = os.getenv("FORCE_REPROCESS", "false").lower() == "true"

# In processing loop
for file in files:
    # ... existing code ...
    
    # Create embeddings with deduplication
    embeddings = embedding_client.create_embeddings_with_dedup(
        chunks=chunks,
        md5_hash=md5_hash,
        filename=filename,
        force_reprocess=force_reprocess
    )
    
    if embeddings is None:
        # File was skipped (already processed)
        continue
    
    # Upload to Qdrant with logging
    qdrant_uploader.upload_with_logging(
        collection_name="content",
        points=points,
        filename=filename,
        md5_hash=md5_hash,
        batch_size=100
    )
```

---

### **4. Environment Variables**

**Add to `.env`:**

```bash
# ============================================
# Phase 3: Deduplication & Logging
# ============================================

# Force reprocess files even if already embedded
# Set to 'true' to skip deduplication checks
FORCE_REPROCESS=false

# Batch size for Qdrant uploads (default: 100)
QDRANT_BATCH_SIZE=100

# Enable detailed embedding logs (default: true)
LOG_EMBEDDINGS=true

# Enable detailed Qdrant upload logs (default: true)
LOG_QDRANT_UPLOADS=true
```

---

### **5. New Log Files Structure**

```
logs/
├── conversion.json          # Existing: PDF/Word → Markdown
├── upload.json              # Existing: Markdown → R2
├── failed.json              # Existing: Failed attempts
├── embedding.json           # NEW: Embedding creation ✨
├── qdrant_upload.json       # NEW: Qdrant uploads ✨
└── skipped.json             # NEW: Skipped files (deduplication) ✨
```

---

### **6. API Endpoints (Optional)**

**Add to `api/main.py`:**

```python
@app.get("/api/logs/embeddings")
async def get_embedding_logs():
    """Get embedding creation logs"""
    return read_json_log("logs/embedding.json")

@app.get("/api/logs/qdrant")
async def get_qdrant_logs():
    """Get Qdrant upload logs"""
    return read_json_log("logs/qdrant_upload.json")

@app.get("/api/logs/skipped")
async def get_skipped_logs():
    """Get skipped files logs"""
    return read_json_log("logs/skipped.json")

@app.get("/api/dedup/check/{md5_hash}")
async def check_deduplication(md5_hash: str):
    """Check if file already processed"""
    return {
        "md5_hash": md5_hash,
        "in_embedding_log": check_embedding_log(md5_hash),
        "in_qdrant": check_qdrant_collection(md5_hash),
        "should_skip": check_embedding_log(md5_hash) or check_qdrant_collection(md5_hash)
    }

@app.get("/api/stats/skipped")
async def get_skipped_stats():
    """Get statistics on skipped files"""
    skipped_log = read_json_log("logs/skipped.json")
    return {
        "total_skipped": len(skipped_log),
        "by_reason": count_by_field(skipped_log, "skip_reason"),
        "by_source": count_by_field(skipped_log, "found_in"),
        "by_collection": count_by_field(skipped_log, "collection_name")
    }
```

---

## 📊 Benefits

### **1. Better Observability**
- ✅ Track embedding creation success/failure
- ✅ Track Qdrant upload success/failure
- ✅ Monitor processing times
- ✅ Identify bottlenecks

### **2. Avoid Duplicate Work**
- ✅ Skip already-embedded files
- ✅ Save compute resources
- ✅ Faster pipeline execution
- ✅ Reduce API costs (Ollama)

### **3. Debugging & Monitoring**
- ✅ Trace file processing history
- ✅ Identify failed embeddings
- ✅ Monitor upload performance
- ✅ Audit trail for compliance

### **4. Cost Optimization**
- ✅ Avoid re-embedding same files
- ✅ Reduce Ollama API calls
- ✅ Reduce Qdrant write operations
- ✅ Save processing time

---

## 🧪 Testing Plan

### **Test 1: First Run (No Deduplication)**
```bash
# Process file for first time
python src/pipeline.py

# Expected:
# ✅ Embeddings created
# ✅ Uploaded to Qdrant
# ✅ Logged to embedding.json
# ✅ Logged to qdrant_upload.json
```

### **Test 2: Second Run (Deduplication)**
```bash
# Process same file again
python src/pipeline.py

# Expected:
# ⏭️  Skipped - already embedded (log)
# ⏭️  No embedding creation
# ⏭️  No Qdrant upload
```

### **Test 3: Force Reprocess**
```bash
# Force reprocess
FORCE_REPROCESS=true python src/pipeline.py

# Expected:
# 🔄 Force reprocessing
# ✅ Embeddings created (again)
# ✅ Uploaded to Qdrant (again)
# ✅ Logged (again)
```

### **Test 4: Log File Deleted**
```bash
# Delete embedding.json but keep Qdrant data
rm logs/embedding.json
python src/pipeline.py

# Expected:
# ⏭️  Skipped - already in Qdrant
# ✅ Fallback to Qdrant check works
```

### **Test 5: Reprocess Pipeline (First Run)**
```bash
# Reprocess existing markdown from R2
python scripts/reprocess_from_markdown.py

# Expected:
# ✅ Embeddings created
# ✅ Uploaded to Qdrant
# ✅ Logged to embedding.json
# ✅ Logged to qdrant_upload.json
```

### **Test 6: Reprocess Pipeline (Deduplication)**
```bash
# Reprocess same files again
python scripts/reprocess_from_markdown.py

# Expected:
# ⏭️  Skipped - already embedded (log)
# ⏭️  No embedding creation
# ⏭️  No Qdrant upload
```

### **Test 7: Force Reprocess Flag**
```bash
# Force reprocess with environment variable
FORCE_REPROCESS=true python scripts/reprocess_from_markdown.py

# Expected:
# 🔄 Force reprocessing enabled
# ✅ Embeddings created (again)
# ✅ Uploaded to Qdrant (again)
# ✅ Logged (again)
```

### **Test 8: Both Pipelines Together**
```bash
# 1. Main pipeline processes PDF
python src/pipeline.py input.pdf

# 2. Reprocess pipeline tries to reprocess
python scripts/reprocess_from_markdown.py

# Expected:
# Main pipeline: ✅ Processed
# Reprocess pipeline: ⏭️  Skipped (already in Qdrant)
```

---

## 📝 Implementation Checklist

### **Core Components**
- [ ] Create `logs/embedding.json` schema
- [ ] Create `logs/qdrant_upload.json` schema
- [ ] Create `logs/skipped.json` schema
- [ ] Add `log_embedding_success()` to LogManager
- [ ] Add `log_qdrant_upload_success()` to LogManager
- [ ] Add `log_skipped_file()` to LogManager
- [ ] Add `check_embedding_exists()` to LogManager
- [ ] Add `check_qdrant_exists()` to LogManager
- [ ] Update EmbeddingClient with deduplication
- [ ] Update EmbeddingClient to log skipped files
- [ ] Update QdrantUploader with logging

### **Main Ingestion Pipeline** (`src/pipeline.py`)
- [ ] Add deduplication check before embedding
- [ ] Integrate embedding logging
- [ ] Integrate Qdrant upload logging
- [ ] Use xxHash for all calculations
- [ ] Store hash in metadata.md5_hash
- [ ] Test with sample PDFs/Word docs

### **Reprocess Pipeline** (`scripts/reprocess_from_markdown.py`)
- [ ] Add deduplication check before embedding
- [ ] Integrate embedding logging
- [ ] Integrate Qdrant upload logging
- [ ] Use xxHash for all calculations
- [ ] Store hash in metadata.md5_hash
- [ ] Respect FORCE_REPROCESS flag
- [ ] Test with existing markdown files

### **Configuration & Environment**
- [ ] Add environment variables to .env
- [ ] Update .env.example with Phase 3 variables
- [ ] Verify xxhash dependency in requirements.txt
- [ ] Create logs/ directory if not exists

### **API & Monitoring**
- [ ] Add API endpoints for new logs
- [ ] Add deduplication check endpoint
- [ ] Update API documentation

### **Testing**
- [ ] Write unit tests for LogManager methods
- [ ] Write unit tests for deduplication logic
- [ ] Write integration tests for main pipeline
- [ ] Write integration tests for reprocess pipeline
- [ ] Test force reprocess flag
- [ ] Test log file deletion recovery

### **Documentation**
- [ ] Update README.md with Phase 3 info
- [ ] Update REFERENCE.md with new log formats
- [ ] Update API documentation
- [ ] Create migration guide (if needed)

### **Deployment**
- [ ] Test on development server
- [ ] Test on production server
- [ ] Monitor log file sizes
- [ ] Verify deduplication working

---

## 🚀 Rollout Plan

### **Phase 3.1: Logging (Week 1)**
- Implement new log files
- Add logging to embedding creation
- Add logging to Qdrant uploads
- Test logging functionality

### **Phase 3.2: Deduplication (Week 2)**
- Implement log file checks
- Implement Qdrant collection checks
- Add force reprocess flag
- Test deduplication logic

### **Phase 3.3: API & Monitoring (Week 3)**
- Add API endpoints for new logs
- Create monitoring dashboard
- Add metrics collection
- Performance testing

---

## 📚 Related Documentation

- [REFERENCE.md](REFERENCE.md) - Technical reference
- [QDRANT.md](QDRANT.md) - Qdrant configuration
- [CHANGELOG.md](CHANGELOG.md) - Version history

---

**Status:** 📋 Ready for Implementation  
**Next Step:** Begin Phase 3.1 - Logging Implementation

**Last Updated:** November 10, 2025
