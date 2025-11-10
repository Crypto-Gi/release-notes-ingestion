# Qdrant Payload Indexing - Complete Guide

> **Comprehensive guide for creating and managing Qdrant payload indexes**

---

## 📚 Table of Contents

1. [Quick Start](#quick-start)
2. [Interactive Script](#interactive-script)
3. [All 8 Index Types](#all-8-index-types)
4. [Tokenizer Explained](#tokenizer-explained)
5. [API Reference](#api-reference)
6. [Best Practices](#best-practices)

---

## 🚀 Quick Start

### Run the Interactive Script

```bash
cd /home/mir/projects/release-notes-ingestion
source .venv/bin/activate
python scripts/create_payload_indexes_advanced.py
```

### Manual API Call Example

```bash
# Create a keyword index on metadata.filename
curl -X PUT "http://192.168.254.22:6333/collections/content/index?wait=true" \
  -H "Content-Type: application/json" \
  -d '{
    "field_name": "metadata.filename",
    "field_schema": {
      "type": "keyword",
      "is_tenant": true
    }
  }'
```

---

## 🎯 Interactive Script

### Features

- ✅ Select collection to work on
- ✅ View existing indexes
- ✅ Index one field at a time
- ✅ All 8 index types supported
- ✅ Interactive configuration
- ✅ Detailed explanations

### Workflow

```
1. Select Collection (filenames or content)
   ↓
2. View Collection Details & Existing Indexes
   ↓
3. Select Field to Index
   ↓
4. Choose Index Type
   ↓
5. Configure Options
   ↓
6. Create Index
   ↓
7. Continue or Switch Collections
```

### Example Session

```
================================================================================
Content Collection: content
================================================================================

Collection Info:
  Points: 96
  Vector Size: 1024D
  Distance Metric: Cosine

📋 Existing Payload Indexes:
────────────────────────────────────────────────────────────────────────────────
  ✓ metadata.filename              → text       (tokenizer=word, min=1, max=15, lowercase=True)
────────────────────────────────────────────────────────────────────────────────

Available Fields:
────────────────────────────────────────────────────────────────────────────────
  1. pagecontent                    (str       ) → Text Index
  2. metadata.filename              (str       ) → Text Index ✓ (indexed)
  3. metadata.page_number           (int       ) → Integer Index
  4. metadata.element_type          (str       ) → Keyword Index
  5. metadata.md5_hash              (str       ) → Keyword Index
────────────────────────────────────────────────────────────────────────────────

Select a field to index (0-5): 3
```

---

## 📋 All 8 Index Types

### 1. Keyword Index 🔤

**For:** Exact string matching (IDs, hashes, filenames, categories)

**Options:**
- `is_tenant` - Optimizes for multi-value filtering
- `on_disk` - Stores index on disk

**Example:**
```python
client.create_payload_index(
    collection_name="content",
    field_name="metadata.filename",
    field_schema=models.KeywordIndexParams(
        type="keyword",
        is_tenant=True,
        on_disk=False
    )
)
```

**Use Cases:**
- ✅ Filenames, document IDs
- ✅ Categories, tags, labels
- ✅ Status codes, error codes

---

### 2. Integer Index 🔢

**For:** Whole number fields (counts, page numbers, IDs)

**Options:**
- `is_principal` - Optimizes for range queries and sorting
- `on_disk` - Stores index on disk

**Example:**
```python
client.create_payload_index(
    collection_name="content",
    field_name="metadata.page_number",
    field_schema=models.IntegerIndexParams(
        type="integer",
        is_principal=True,
        on_disk=False
    )
)
```

**Use Cases:**
- ✅ Page numbers, chapter numbers
- ✅ Counts, quantities
- ✅ Timestamps (Unix epoch)

---

### 3. Float Index 💯

**For:** Decimal number fields (scores, ratings, prices)

**Options:**
- `is_principal` - Optimizes for range queries and sorting
- `on_disk` - Stores index on disk

**Example:**
```python
client.create_payload_index(
    collection_name="content",
    field_name="metadata.confidence_score",
    field_schema=models.FloatIndexParams(
        type="float",
        is_principal=True,
        on_disk=False
    )
)
```

**Use Cases:**
- ✅ Confidence scores, probabilities
- ✅ Ratings, rankings
- ✅ Prices, costs

---

### 4. Boolean Index ✅

**For:** True/false fields (flags, status)

**Options:**
- `on_disk` - Stores index on disk

**Example:**
```python
client.create_payload_index(
    collection_name="content",
    field_name="metadata.is_processed",
    field_schema=models.BoolIndexParams(
        type="bool",
        on_disk=False
    )
)
```

**Use Cases:**
- ✅ Processing flags (is_processed, is_verified)
- ✅ Status indicators (is_active, is_deleted)

---

### 5. Geo Index 🌍

**For:** Geographic coordinates (latitude/longitude)

**Options:**
- `on_disk` - Stores index on disk

**Data Format:**
```json
{
    "location": {
        "lon": 52.5200,
        "lat": 13.4050
    }
}
```

**Example:**
```python
client.create_payload_index(
    collection_name="locations",
    field_name="coordinates",
    field_schema=models.GeoIndexParams(
        type="geo",
        on_disk=False
    )
)
```

---

### 6. DateTime Index 📅

**For:** Timestamp fields (created_at, updated_at)

**Options:**
- `on_disk` - Stores index on disk

**Data Format:** RFC 3339
```json
{
    "created_at": "2024-01-15T10:30:00Z"
}
```

**Example:**
```python
client.create_payload_index(
    collection_name="content",
    field_name="metadata.created_at",
    field_schema=models.DatetimeIndexParams(
        type="datetime",
        on_disk=False
    )
)
```

---

### 7. UUID Index 🆔

**For:** UUID fields (v1.11.0+) - optimized for UUIDs

**Options:**
- `on_disk` - Stores index on disk

**Example:**
```python
client.create_payload_index(
    collection_name="content",
    field_name="metadata.document_id",
    field_schema=models.UuidIndexParams(
        type="uuid",
        on_disk=False
    )
)
```

**Note:** More efficient than keyword index for UUID fields!

---

### 8. Text Index 📝

**For:** Full-text search (content, descriptions)

**Options:**
- `tokenizer` - How to split text (word, whitespace, prefix, multilingual)
- `min_token_len` - Minimum token length (default: 2)
- `max_token_len` - Maximum token length (default: 15)
- `lowercase` - Convert to lowercase (default: true)
- `phrase_matching` - Enable exact phrase search
- `on_disk` - Stores index on disk

**Example:**
```python
client.create_payload_index(
    collection_name="content",
    field_name="pagecontent",
    field_schema=models.TextIndexParams(
        type="text",
        tokenizer=models.TokenizerType.WORD,
        min_token_len=2,
        max_token_len=15,
        lowercase=True,
        phrase_matching=True,
        on_disk=False
    )
)
```

---

## 🔤 Tokenizer Explained

### What is a Tokenizer?

A **tokenizer** splits text into searchable **tokens** (words) for full-text search.

**Example:**
```
Input:  "The quick brown fox"
Tokens: ["the", "quick", "brown", "fox"]
```

### 4 Tokenizer Types

#### 1. WORD (Default) ⭐

**Splits by:** Word boundaries (spaces, punctuation)

**Example:**
```
Input:  "Hello, world!"
Tokens: ["hello", "world"]
```

**Use for:** General text, natural language

---

#### 2. WHITESPACE

**Splits by:** Spaces only (keeps punctuation)

**Example:**
```
Input:  "Hello, world!"
Tokens: ["Hello,", "world!"]
```

**Use for:** Code, technical content

---

#### 3. PREFIX

**Splits by:** All prefixes of words

**Example:**
```
Input:  "document"
Tokens: ["d", "do", "doc", "docu", "docum", "docume", "documen", "document"]
```

**Use for:** Autocomplete, prefix matching

---

#### 4. MULTILINGUAL

**Splits by:** Language-aware boundaries

**Example:**
```
Input:  "Hello 世界"
Tokens: ["hello", "世界"]
```

**Use for:** Multi-language content

---

### TEXT Index vs KEYWORD Index

| Feature | TEXT Index | KEYWORD Index |
|---------|------------|---------------|
| **Purpose** | Full-text search | Exact filtering |
| **Tokenizer** | ✅ Yes | ❌ No |
| **Field Type** | Long text | Short strings |
| **Example** | `pagecontent` | `metadata.filename` |
| **Search** | "Find 'bug fix' in content" | "Filter by filename='doc.pdf'" |

---

## 📖 API Reference

### HTTP API

#### Create Keyword Index
```bash
curl -X PUT "http://192.168.254.22:6333/collections/content/index?wait=true" \
  -H "Content-Type: application/json" \
  -d '{
    "field_name": "metadata.filename",
    "field_schema": {
      "type": "keyword",
      "is_tenant": true,
      "on_disk": false
    }
  }'
```

#### Create Integer Index
```bash
curl -X PUT "http://192.168.254.22:6333/collections/content/index?wait=true" \
  -H "Content-Type: application/json" \
  -d '{
    "field_name": "metadata.page_number",
    "field_schema": {
      "type": "integer",
      "is_principal": true,
      "on_disk": false
    }
  }'
```

#### Create Text Index
```bash
curl -X PUT "http://192.168.254.22:6333/collections/content/index?wait=true" \
  -H "Content-Type: application/json" \
  -d '{
    "field_name": "pagecontent",
    "field_schema": {
      "type": "text",
      "tokenizer": "word",
      "min_token_len": 2,
      "max_token_len": 15,
      "lowercase": true,
      "phrase_matching": true,
      "on_disk": false
    }
  }'
```

### Python Client

```python
from qdrant_client import QdrantClient, models

client = QdrantClient(host="192.168.254.22", port=6333)

# Keyword index
client.create_payload_index(
    collection_name="content",
    field_name="metadata.filename",
    field_schema=models.KeywordIndexParams(
        type="keyword",
        is_tenant=True
    )
)

# Integer index
client.create_payload_index(
    collection_name="content",
    field_name="metadata.page_number",
    field_schema=models.IntegerIndexParams(
        type="integer",
        is_principal=True
    )
)

# Text index
client.create_payload_index(
    collection_name="content",
    field_name="pagecontent",
    field_schema=models.TextIndexParams(
        type="text",
        tokenizer=models.TokenizerType.WORD,
        min_token_len=2,
        max_token_len=15,
        lowercase=True,
        phrase_matching=True
    )
)
```

---

## 🎯 Best Practices

### 1. Index Only What You Filter

Don't index fields you never filter on. Indexes consume memory.

### 2. Use is_tenant for High-Cardinality Fields

Enable `is_tenant` for fields with many unique values (filenames, user IDs).

```python
# Good: filename field with 1000s of files
field_schema=models.KeywordIndexParams(
    type="keyword",
    is_tenant=True  # ✅ Recommended
)
```

### 3. Use is_principal for Range Queries

Enable `is_principal` for fields used in range queries or sorting.

```python
# Good: page_number for range queries
field_schema=models.IntegerIndexParams(
    type="integer",
    is_principal=True  # ✅ Recommended for ranges
)
```

### 4. Use on_disk for Large Indexes

Store indexes on disk to save RAM in production.

```python
field_schema=models.KeywordIndexParams(
    type="keyword",
    on_disk=True  # Save RAM
)
```

### 5. Use Text Index Sparingly

Text indexes are memory-intensive. Only use for actual full-text search needs.

### 6. Test Performance

Measure query speed before/after indexing.

### 7. Monitor Memory Usage

Indexes increase RAM consumption. Monitor your system.

---

## 📊 Recommended Indexes

### Content Collection

```python
# 1. Filename (keyword with tenant optimization)
client.create_payload_index(
    collection_name="content",
    field_name="metadata.filename",
    field_schema=models.KeywordIndexParams(type="keyword", is_tenant=True)
)

# 2. Page number (integer with principal optimization)
client.create_payload_index(
    collection_name="content",
    field_name="metadata.page_number",
    field_schema=models.IntegerIndexParams(type="integer", is_principal=True)
)

# 3. Element type (keyword)
client.create_payload_index(
    collection_name="content",
    field_name="metadata.element_type",
    field_schema=models.KeywordIndexParams(type="keyword")
)

# 4. MD5 hash (keyword)
client.create_payload_index(
    collection_name="content",
    field_name="metadata.md5_hash",
    field_schema=models.KeywordIndexParams(type="keyword")
)
```

### Filenames Collection

```python
# 1. Hash (keyword)
client.create_payload_index(
    collection_name="filenames",
    field_name="metadata.hash",
    field_schema=models.KeywordIndexParams(type="keyword")
)

# 2. Source (keyword)
client.create_payload_index(
    collection_name="filenames",
    field_name="source",
    field_schema=models.KeywordIndexParams(type="keyword")
)
```

---

## 🔗 Additional Resources

- **Qdrant Official Docs:** https://qdrant.tech/documentation/concepts/indexing/
- **Interactive Script:** `scripts/create_payload_indexes_advanced.py`
- **Debug Script:** `scripts/debug_indexes.py`

---

## 📝 Quick Reference

| Index Type | For | Key Options |
|------------|-----|-------------|
| **Keyword** | Exact strings | `is_tenant`, `on_disk` |
| **Integer** | Whole numbers | `is_principal`, `on_disk` |
| **Float** | Decimals | `is_principal`, `on_disk` |
| **Bool** | True/False | `on_disk` |
| **Geo** | Coordinates | `on_disk` |
| **DateTime** | Timestamps | `on_disk` |
| **UUID** | UUIDs | `on_disk` |
| **Text** | Full-text search | `tokenizer`, `phrase_matching`, `on_disk` |

---

**Created with ❤️ for efficient Qdrant indexing!**
