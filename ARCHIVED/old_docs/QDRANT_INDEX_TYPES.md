# Qdrant Index Types - Complete Reference

## 📚 **All 8 Index Types**

### **1. Keyword Index** 🔤
**For:** Exact string matching (IDs, hashes, filenames, categories)

**When to use:**
- Exact match filters (`filename="doc.pdf"`)
- Category/tag filtering
- ID lookups

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
        is_tenant=True,  # Optimize for filtering by filename
        on_disk=False
    )
)
```

**Use Cases:**
- ✅ Filenames, document IDs
- ✅ Categories, tags, labels
- ✅ Status codes, error codes
- ✅ User IDs, session IDs

---

### **2. Integer Index** 🔢
**For:** Whole number fields (counts, page numbers, IDs)

**When to use:**
- Range queries (`page_number >= 10`)
- Exact matches (`status_code=200`)
- Sorting by numeric fields

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
        is_principal=True,  # Optimize for range queries
        on_disk=False
    )
)
```

**Use Cases:**
- ✅ Page numbers, chapter numbers
- ✅ Counts, quantities
- ✅ Timestamps (Unix epoch)
- ✅ Version numbers

---

### **3. Float Index** 💯
**For:** Decimal number fields (scores, ratings, prices)

**When to use:**
- Range queries (`price < 100.0`)
- Threshold filtering (`confidence >= 0.8`)
- Numeric comparisons

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
- ✅ Percentages

---

### **4. Boolean Index** ✅
**For:** True/false fields (flags, status)

**When to use:**
- Binary filters (`is_processed=true`)
- Status flags (`is_active=false`)
- Feature toggles

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
- ✅ Feature flags (has_images, has_tables)

---

### **5. Geo Index** 🌍
**For:** Geographic coordinates (latitude/longitude)

**When to use:**
- Location-based search (within radius)
- Proximity filtering
- Geographic boundaries

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

**Use Cases:**
- ✅ Store locations, office locations
- ✅ User locations
- ✅ Delivery addresses
- ✅ Geographic data points

---

### **6. DateTime Index** 📅
**For:** Timestamp fields (created_at, updated_at)

**When to use:**
- Time range queries (`created_at > "2024-01-01"`)
- Chronological filtering
- Date-based sorting

**Options:**
- `on_disk` - Stores index on disk

**Data Format:** RFC 3339
```json
{
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T14:45:30+00:00"
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

**Use Cases:**
- ✅ Creation timestamps
- ✅ Modification timestamps
- ✅ Event timestamps
- ✅ Expiration dates

---

### **7. UUID Index** 🆔
**For:** UUID fields (v1.11.0+) - optimized for UUIDs

**When to use:**
- UUID exact matching (faster than keyword)
- Reference IDs
- Unique identifiers

**Options:**
- `on_disk` - Stores index on disk

**Data Format:**
```json
{
    "document_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

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

**Use Cases:**
- ✅ Document IDs
- ✅ User IDs (UUID format)
- ✅ Transaction IDs
- ✅ Reference IDs

**Note:** More efficient than keyword index for UUID fields!

---

### **8. Text Index** 📝
**For:** Full-text search (content, descriptions)

**When to use:**
- Full-text search
- Keyword search in content
- Phrase matching ("exact phrase")

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
        phrase_matching=True,  # Enable "exact phrase" search
        on_disk=False
    )
)
```

**Tokenizer Types:**
- `word` - Split by word boundaries (default)
- `whitespace` - Split by whitespace only
- `prefix` - Enable prefix search (e.g., "doc" matches "document")
- `multilingual` - Support multiple languages

**Use Cases:**
- ✅ Full-text content search
- ✅ Description search
- ✅ Title/name search
- ✅ Keyword matching

---

## 🎯 **Special Options Explained**

### **is_tenant** (Keyword, Integer)
**What it does:** Optimizes index for filtering by this field

**When to use:**
- Field has many unique values (100s-1000s)
- Frequently used in filters
- Multi-value queries (e.g., "get all chunks from file X")

**Example:**
```python
# Good use case: filename field
# Many different files, frequently filter by filename
field_schema=models.KeywordIndexParams(
    type="keyword",
    is_tenant=True  # ✅ Recommended
)
```

**Performance Impact:**
- ✅ Faster filtered searches
- ✅ Optimized for multi-value queries
- ⚠️ Slightly more memory usage

---

### **is_principal** (Integer, Float)
**What it does:** Optimizes index for range queries and sorting

**When to use:**
- Field is used for range queries (`>`, `<`, `>=`, `<=`)
- Field is used for sorting
- Sequential/chronological access patterns

**Example:**
```python
# Good use case: timestamp or page_number
field_schema=models.IntegerIndexParams(
    type="integer",
    is_principal=True  # ✅ Recommended for range queries
)
```

**Performance Impact:**
- ✅ Faster range queries
- ✅ Faster sorting
- ⚠️ Slightly more memory usage

---

### **on_disk** (All types)
**What it does:** Stores index on disk instead of RAM

**When to use:**
- Large indexes (millions of points)
- Memory constraints
- Cost optimization (RAM is expensive)

**Example:**
```python
field_schema=models.KeywordIndexParams(
    type="keyword",
    on_disk=True  # Store on disk to save RAM
)
```

**Performance Impact:**
- ✅ Saves RAM
- ⚠️ Slightly slower queries (disk I/O)
- ✅ Good for large-scale deployments

---

### **phrase_matching** (Text only)
**What it does:** Enables exact phrase search

**When to use:**
- Users need to search for exact phrases
- Multi-word queries matter
- Order of words is important

**Example:**
```python
field_schema=models.TextIndexParams(
    type="text",
    tokenizer=models.TokenizerType.WORD,
    phrase_matching=True  # Enable "machine learning" as exact phrase
)
```

**Query Example:**
```python
# Search for exact phrase "release notes"
client.query(
    collection_name="content",
    query_text="release notes",  # Finds exact phrase
    limit=10
)
```

---

## 📊 **Index Type Selection Guide**

| Field Type | Python Type | Index Type | Options |
|------------|-------------|------------|---------|
| Filename, ID, Hash | `str` | `keyword` | `is_tenant` for filenames |
| Page number, Count | `int` | `integer` | `is_principal` for ranges |
| Score, Rating | `float` | `float` | `is_principal` for ranges |
| Flag, Status | `bool` | `bool` | - |
| Coordinates | `dict` | `geo` | - |
| Timestamp | `str` (RFC 3339) | `datetime` | - |
| UUID | `str` (UUID format) | `uuid` | - |
| Content, Description | `str` (long text) | `text` | `phrase_matching` |

---

## 🚀 **Quick Start Examples**

### **Example 1: Index filename with tenant optimization**
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

### **Example 2: Index page_number with principal optimization**
```bash
curl -X PUT "http://192.168.254.22:6333/collections/content/index" \
  -H "Content-Type: application/json" \
  -d '{
    "field_name": "metadata.page_number",
    "field_schema": {
      "type": "integer",
      "is_principal": true
    }
  }'
```

### **Example 3: Index content with phrase matching**
```bash
curl -X PUT "http://192.168.254.22:6333/collections/content/index" \
  -H "Content-Type: application/json" \
  -d '{
    "field_name": "pagecontent",
    "field_schema": {
      "type": "text",
      "tokenizer": "word",
      "phrase_matching": true
    }
  }'
```

---

## 🎯 **Recommended Indexes for Your Collections**

### **Content Collection:**
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

# 5. Content (text with phrase matching) - Optional
client.create_payload_index(
    collection_name="content",
    field_name="pagecontent",
    field_schema=models.TextIndexParams(
        type="text",
        tokenizer=models.TokenizerType.WORD,
        phrase_matching=True
    )
)
```

### **Filenames Collection:**
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

## 📚 **Additional Resources**

- [Qdrant Indexing Documentation](https://qdrant.tech/documentation/concepts/indexing/)
- [Qdrant Payload Documentation](https://qdrant.tech/documentation/concepts/payload/)
- [Qdrant Filtering Documentation](https://qdrant.tech/documentation/concepts/filtering/)

---

## 🎓 **Best Practices**

1. **Only index fields you filter on** - Indexes consume memory
2. **Use `is_tenant` for high-cardinality fields** - Filenames, user IDs
3. **Use `is_principal` for range queries** - Timestamps, page numbers
4. **Use `on_disk` for large indexes** - Save RAM in production
5. **Use `text` index sparingly** - Only for full-text search needs
6. **Test performance** - Measure query speed before/after indexing
7. **Monitor memory usage** - Indexes increase RAM consumption

---

**Created with ❤️ for efficient Qdrant indexing!**
