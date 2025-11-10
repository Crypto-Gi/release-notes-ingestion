# Qdrant Indexing - Quick Start Guide

## 🚀 **Interactive Script**

### **Run the Interactive Index Creator:**
```bash
cd /home/mir/projects/release-notes-ingestion
source .venv/bin/activate
python scripts/create_payload_indexes.py
```

### **Example Session:**

```
================================================================================
QDRANT PAYLOAD INDEX CREATOR
================================================================================

Qdrant Server: 192.168.254.22:6333
Filename Collection: filenames
Content Collection: content
================================================================================

Connecting to Qdrant...
✅ Connected! Found 5 collections


================================================================================
Filename Collection: filenames
================================================================================

Collection Info:
  Points: 3
  Vector Size: 384D

Analyzing payload structure...

Available Fields for Indexing:
--------------------------------------------------------------------------------
  1. pagecontent                 (str       ) Sample: ECOS_9.2.4.0_Release_Notes_RevB.pdf
  2. source                      (str       ) Sample: ECOS_9.2.4.0_Release_Notes_RevB.pdf
  3. metadata.hash               (str       ) Sample: fceb97ec5e4a062a6017f624a89cb9a7
--------------------------------------------------------------------------------

Select fields to index (comma-separated numbers, or 'skip' to skip this collection):
Example: 1,3,5  or  skip

Your selection for filenames: 3

================================================================================
Creating Indexes for filenames
================================================================================

Creating keyword index on 'metadata.hash'...
✅ Index created successfully!

✅ Created 1/1 indexes for filenames


================================================================================
Content Collection: content
================================================================================

Collection Info:
  Points: 96
  Vector Size: 1024D

Analyzing payload structure...

Available Fields for Indexing:
--------------------------------------------------------------------------------
  1. pagecontent                 (str       ) Sample: | Issue                                           ...
  2. metadata.filename           (str       ) Sample: ECOS_9.2.4.0_Release_Notes_RevB.pdf
  3. metadata.page_number        (int       ) Sample: 22
  4. metadata.element_type       (str       ) Sample: Table
  5. metadata.md5_hash           (str       ) Sample: dda0bb74a297edee2af60e78d75d6f17
--------------------------------------------------------------------------------

Select fields to index (comma-separated numbers, or 'skip' to skip this collection):
Example: 1,3,5  or  skip

Your selection for content: 2,3,4

⚠️  You selected 'metadata.filename'
   Enable tenant optimization (is_tenant=True)?
   This optimizes for queries filtering by filename (recommended for multi-file queries)
   Enable tenant optimization? (y/n): y

================================================================================
Creating Indexes for content
================================================================================

Creating keyword index on 'metadata.filename'...
✅ Index created successfully!

Creating integer index on 'metadata.page_number'...
✅ Index created successfully!

Creating keyword index on 'metadata.element_type'...
✅ Index created successfully!

✅ Created 3/3 indexes for content

================================================================================
🎉 INDEX CREATION COMPLETE!
================================================================================
```

---

## 📝 **Manual API Calls**

### **1. Index metadata.filename (with tenant optimization):**

```bash
curl -X PUT "http://192.168.254.22:6333/collections/content/index" \
  -H "Content-Type: application/json" \
  -d '{
    "field_name": "metadata.filename",
    "field_schema": {
      "type": "keyword",
      "is_tenant": true
    }
  }'
```

**Python:**
```python
from qdrant_client import QdrantClient, models

client = QdrantClient(host="192.168.254.22", port=6333)

client.create_payload_index(
    collection_name="content",
    field_name="metadata.filename",
    field_schema=models.KeywordIndexParams(
        type="keyword",
        is_tenant=True
    )
)
```

---

### **2. Index metadata.page_number:**

```bash
curl -X PUT "http://192.168.254.22:6333/collections/content/index" \
  -H "Content-Type: application/json" \
  -d '{
    "field_name": "metadata.page_number",
    "field_schema": {
      "type": "integer"
    }
  }'
```

**Python:**
```python
client.create_payload_index(
    collection_name="content",
    field_name="metadata.page_number",
    field_schema=models.IntegerIndexParams(
        type="integer"
    )
)
```

---

### **3. Index metadata.hash (filenames collection):**

```bash
curl -X PUT "http://192.168.254.22:6333/collections/filenames/index" \
  -H "Content-Type: application/json" \
  -d '{
    "field_name": "metadata.hash",
    "field_schema": {
      "type": "keyword"
    }
  }'
```

**Python:**
```python
client.create_payload_index(
    collection_name="filenames",
    field_name="metadata.hash",
    field_schema=models.KeywordIndexParams(
        type="keyword"
    )
)
```

---

## ✅ **Verify Indexes**

### **Check Collection Info:**

```bash
curl "http://192.168.254.22:6333/collections/content"
```

**Python:**
```python
info = client.get_collection("content")

# Check if payload schema exists (contains indexes)
if hasattr(info.config.params, 'payload_schema') and info.config.params.payload_schema:
    print("\nPayload Indexes:")
    for field_name, field_schema in info.config.params.payload_schema.items():
        print(f"  ✅ {field_name}: {field_schema}")
else:
    print("\n❌ No payload indexes configured")
```

---

## 🎯 **Recommended Indexes**

### **For `content` collection:**
1. ✅ `metadata.filename` (keyword, `is_tenant=True`) - **Priority 1**
2. ✅ `metadata.page_number` (integer) - **Priority 1**
3. ✅ `metadata.element_type` (keyword) - **Priority 2**
4. ✅ `metadata.md5_hash` (keyword) - **Priority 2**

### **For `filenames` collection:**
1. ✅ `metadata.hash` (keyword) - **Priority 1**
2. ✅ `source` (keyword) - **Priority 2**

---

## 📚 **Full Documentation**

See `docs/QDRANT_INDEXING_API.md` for complete API reference and examples.
