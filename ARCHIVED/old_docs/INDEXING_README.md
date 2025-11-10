# Qdrant Payload Indexing - Complete Guide

## 🎯 **Overview**

This guide covers everything you need to know about creating payload indexes in Qdrant for optimal search performance.

---

## 📁 **Available Tools**

### **1. Simple Interactive Script** (Recommended for beginners)
**File:** `scripts/create_payload_indexes.py`

**Features:**
- ✅ Simple field selection
- ✅ Automatic type detection
- ✅ Basic options (is_tenant)
- ✅ Quick setup

**Usage:**
```bash
python scripts/create_payload_indexes.py
```

---

### **2. Advanced Interactive Script** (Recommended for power users)
**File:** `scripts/create_payload_indexes_advanced.py`

**Features:**
- ✅ All 8 index types supported
- ✅ Detailed explanations for each type
- ✅ All configuration options
- ✅ Smart suggestions based on field type
- ✅ Interactive option configuration

**Usage:**
```bash
python scripts/create_payload_indexes_advanced.py
```

---

## 📚 **Documentation Files**

1. **`QDRANT_INDEX_TYPES.md`** - Complete reference for all 8 index types
2. **`QDRANT_INDEXING_API.md`** - API calls and code examples
3. **`INDEXING_EXAMPLE.md`** - Quick start examples

---

## 🚀 **Quick Start**

### **Step 1: Choose Your Approach**

**Option A: Interactive (Easiest)**
```bash
cd /home/mir/projects/release-notes-ingestion
source .venv/bin/activate
python scripts/create_payload_indexes_advanced.py
```

**Option B: Manual API Call**
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

**Option C: Python Code**
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

## 📊 **All 8 Index Types**

| # | Type | For | Example Field | Options |
|---|------|-----|---------------|---------|
| 1 | **Keyword** | Exact strings | filename, ID, hash | `is_tenant`, `on_disk` |
| 2 | **Integer** | Whole numbers | page_number, count | `is_principal`, `on_disk` |
| 3 | **Float** | Decimals | score, rating, price | `is_principal`, `on_disk` |
| 4 | **Bool** | True/False | is_processed, is_active | `on_disk` |
| 5 | **Geo** | Coordinates | location (lat/lon) | `on_disk` |
| 6 | **DateTime** | Timestamps | created_at, updated_at | `on_disk` |
| 7 | **UUID** | UUIDs | document_id (UUID) | `on_disk` |
| 8 | **Text** | Full-text | content, description | `tokenizer`, `phrase_matching`, `on_disk` |

---

## 🎓 **Index Type Selection Guide**

### **When to use each type:**

**Keyword** 🔤
```
Use for: Filenames, IDs, categories, tags
Example: metadata.filename, metadata.element_type
Options: is_tenant=True for high-cardinality fields
```

**Integer** 🔢
```
Use for: Page numbers, counts, version numbers
Example: metadata.page_number
Options: is_principal=True for range queries
```

**Float** 💯
```
Use for: Scores, ratings, probabilities
Example: metadata.confidence_score
Options: is_principal=True for range queries
```

**Bool** ✅
```
Use for: Flags, status indicators
Example: metadata.is_processed
Options: None (simple)
```

**Geo** 🌍
```
Use for: Geographic coordinates
Example: location {"lon": 52.52, "lat": 13.40}
Options: None (simple)
```

**DateTime** 📅
```
Use for: Timestamps (RFC 3339 format)
Example: metadata.created_at "2024-01-15T10:30:00Z"
Options: None (simple)
```

**UUID** 🆔
```
Use for: UUID identifiers (faster than keyword)
Example: metadata.document_id "550e8400-e29b-41d4-a716-446655440000"
Options: None (simple)
```

**Text** 📝
```
Use for: Full-text search, content search
Example: pagecontent
Options: tokenizer, phrase_matching
```

---

## 🎯 **Special Options Explained**

### **is_tenant** (Keyword, Integer)
**What:** Optimizes for filtering by this field  
**When:** Field has many unique values, frequently filtered  
**Example:** `metadata.filename` with 1000s of files  
**Benefit:** Faster multi-value queries

### **is_principal** (Integer, Float)
**What:** Optimizes for range queries and sorting  
**When:** Used for ranges (`>`, `<`) or sorting  
**Example:** `metadata.page_number` for page ranges  
**Benefit:** Faster range queries

### **on_disk** (All types)
**What:** Stores index on disk instead of RAM  
**When:** Large indexes, memory constraints  
**Example:** Large collections (millions of points)  
**Benefit:** Saves RAM, slightly slower queries

### **phrase_matching** (Text only)
**What:** Enables exact phrase search  
**When:** Users search for exact phrases  
**Example:** "release notes" as exact phrase  
**Benefit:** More accurate phrase searches

---

## 📋 **Recommended Indexes**

### **For Content Collection:**
```python
# Priority 1: Essential
✅ metadata.filename (keyword, is_tenant=True)
✅ metadata.page_number (integer, is_principal=True)

# Priority 2: Useful
✅ metadata.element_type (keyword)
✅ metadata.md5_hash (keyword)

# Priority 3: Optional
⚪ pagecontent (text, phrase_matching=True)
```

### **For Filenames Collection:**
```python
# Priority 1: Essential
✅ metadata.hash (keyword)

# Priority 2: Useful
✅ source (keyword)
```

---

## 🔍 **Example: Advanced Interactive Session**

```
================================================================================
Content Collection: content
================================================================================

Available Fields:
────────────────────────────────────────────────────────────────────────────────
  1. pagecontent                 (str       ) → Text Index
  2. metadata.filename           (str       ) → Keyword Index
  3. metadata.page_number        (int       ) → Integer Index
  4. metadata.element_type       (str       ) → Keyword Index
  5. metadata.md5_hash           (str       ) → Keyword Index
────────────────────────────────────────────────────────────────────────────────

🎯 Let's configure indexes for each field:

────────────────────────────────────────────────────────────────────────────────
Field: metadata.filename
Type: str
Sample: ECOS_9.2.4.0_Release_Notes_RevB.pdf
────────────────────────────────────────────────────────────────────────────────

💡 Suggested Index Type: Keyword Index
   For exact string matching (IDs, hashes, filenames, categories)

Available Index Types:
  ⭐ 1. Keyword Index
      For exact string matching (IDs, hashes, filenames, categories)
   2. UUID Index
      For UUID fields (v1.11.0+) - optimized for UUIDs
   3. DateTime Index
      For timestamp fields (created_at, updated_at)
   4. Text Index
      For full-text search (content, descriptions)

  0. Skip this field

Select index type (0-4) [default: 1]: 1

📋 Keyword Index
   For exact string matching (IDs, hashes, filenames, categories)

   Use Cases:
     • Exact match filters (filename="doc.pdf")
     • Multi-value filters with is_tenant (all chunks from file X)
     • Category/tag filtering

   Available Options: is_tenant, on_disk

📝 Configure Index Options for keyword:

   ℹ️  Tenant Optimization
      Optimizes for filtering by this field (multi-value queries)
      When to use: When field has many unique values and is frequently filtered
      Example: filename field with 1000s of different files
   Enable is_tenant? (y/n) [recommended: y]: y

   ℹ️  On-Disk Storage
      Stores index on disk instead of RAM (saves memory)
      When to use: For large indexes or when RAM is limited
      Example: Large collections with memory constraints
   Enable on_disk? (y/n) [default: n]: n

Creating keyword index on 'metadata.filename'...
✅ Index created successfully!
   Type: keyword
   Options: is_tenant=True, on_disk=False
```

---

## 💡 **Best Practices**

1. **Start Simple**
   - Begin with keyword and integer indexes
   - Add advanced types as needed

2. **Index Only What You Filter**
   - Don't index fields you never filter on
   - Indexes consume memory

3. **Use Tenant Optimization**
   - Enable `is_tenant` for high-cardinality fields
   - Especially for filename, user_id fields

4. **Use Principal Optimization**
   - Enable `is_principal` for range queries
   - Especially for timestamps, page numbers

5. **Monitor Performance**
   - Measure query speed before/after indexing
   - Check memory usage

6. **Use On-Disk for Large Indexes**
   - Save RAM in production
   - Acceptable for slightly slower queries

7. **Test Text Indexes**
   - Text indexes are memory-intensive
   - Only use for actual full-text search needs

---

## 🐛 **Troubleshooting**

### **Index creation fails**
```
Error: Field not found
Solution: Ensure field exists in at least one point
```

### **Wrong index type**
```
Error: Type mismatch
Solution: Check field data type, use correct index type
```

### **Memory issues**
```
Error: Out of memory
Solution: Enable on_disk=True for large indexes
```

### **Slow queries after indexing**
```
Issue: Queries slower than expected
Solution: Check if on_disk=True, consider moving to RAM
```

---

## 📚 **Additional Resources**

- **Complete Index Types Reference:** `docs/QDRANT_INDEX_TYPES.md`
- **API Reference:** `docs/QDRANT_INDEXING_API.md`
- **Quick Examples:** `docs/INDEXING_EXAMPLE.md`
- **Qdrant Official Docs:** https://qdrant.tech/documentation/concepts/indexing/

---

## 🎉 **Summary**

You now have:
- ✅ 2 interactive scripts (simple + advanced)
- ✅ Complete documentation for all 8 index types
- ✅ API reference with examples
- ✅ Best practices and recommendations
- ✅ Troubleshooting guide

**Ready to optimize your Qdrant searches!** 🚀
