# Qdrant Payload Indexing API Reference

## 🔧 **API Calls for Creating Indexes**

### **1. Keyword Index (for string fields)**

#### **HTTP API:**
```bash
curl -X PUT "http://192.168.254.22:6333/collections/content/index" \
  -H "Content-Type: application/json" \
  -d '{
    "field_name": "metadata.filename",
    "field_schema": {
      "type": "keyword"
    }
  }'
```

#### **Python Client:**
```python
from qdrant_client import QdrantClient, models

client = QdrantClient(host="192.168.254.22", port=6333)

# Simple keyword index
client.create_payload_index(
    collection_name="content",
    field_name="metadata.filename",
    field_schema=models.KeywordIndexParams(
        type="keyword"
    )
)
```

---

### **2. Keyword Index with Tenant Optimization**

#### **HTTP API:**
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

#### **Python Client:**
```python
# Keyword index with tenant optimization (for multi-file queries)
client.create_payload_index(
    collection_name="content",
    field_name="metadata.filename",
    field_schema=models.KeywordIndexParams(
        type="keyword",
        is_tenant=True  # Optimizes for filtering by this field
    )
)
```

**When to use `is_tenant=True`:**
- Field is frequently used in filters
- Field has many unique values (like filename)
- You often query "all items where field=X"

---

### **3. Integer Index (for numeric fields)**

#### **HTTP API:**
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

#### **Python Client:**
```python
# Integer index for page numbers
client.create_payload_index(
    collection_name="content",
    field_name="metadata.page_number",
    field_schema=models.IntegerIndexParams(
        type="integer"
    )
)
```

---

### **4. Text Index (for full-text search)**

#### **HTTP API:**
```bash
curl -X PUT "http://192.168.254.22:6333/collections/content/index" \
  -H "Content-Type: application/json" \
  -d '{
    "field_name": "pagecontent",
    "field_schema": {
      "type": "text",
      "tokenizer": "word",
      "min_token_len": 2,
      "max_token_len": 15,
      "lowercase": true
    }
  }'
```

#### **Python Client:**
```python
# Text index for full-text search
client.create_payload_index(
    collection_name="content",
    field_name="pagecontent",
    field_schema=models.TextIndexParams(
        type="text",
        tokenizer=models.TokenizerType.WORD,
        min_token_len=2,
        max_token_len=15,
        lowercase=True
    )
)
```

---

## 📊 **Complete Example: Index All Metadata Fields**

### **For Content Collection:**

```python
from qdrant_client import QdrantClient, models

client = QdrantClient(host="192.168.254.22", port=6333)

# 1. Keyword index on filename (tenant-optimized)
client.create_payload_index(
    collection_name="content",
    field_name="metadata.filename",
    field_schema=models.KeywordIndexParams(
        type="keyword",
        is_tenant=True
    )
)
print("✅ Indexed: metadata.filename")

# 2. Integer index on page_number
client.create_payload_index(
    collection_name="content",
    field_name="metadata.page_number",
    field_schema=models.IntegerIndexParams(
        type="integer"
    )
)
print("✅ Indexed: metadata.page_number")

# 3. Keyword index on element_type
client.create_payload_index(
    collection_name="content",
    field_name="metadata.element_type",
    field_schema=models.KeywordIndexParams(
        type="keyword"
    )
)
print("✅ Indexed: metadata.element_type")

# 4. Keyword index on md5_hash
client.create_payload_index(
    collection_name="content",
    field_name="metadata.md5_hash",
    field_schema=models.KeywordIndexParams(
        type="keyword"
    )
)
print("✅ Indexed: metadata.md5_hash")

print("\n🎉 All indexes created for 'content' collection!")
```

---

### **For Filenames Collection:**

```python
# 1. Keyword index on hash
client.create_payload_index(
    collection_name="filenames",
    field_name="metadata.hash",
    field_schema=models.KeywordIndexParams(
        type="keyword"
    )
)
print("✅ Indexed: metadata.hash")

# 2. Keyword index on source
client.create_payload_index(
    collection_name="filenames",
    field_name="source",
    field_schema=models.KeywordIndexParams(
        type="keyword"
    )
)
print("✅ Indexed: source")

print("\n🎉 All indexes created for 'filenames' collection!")
```

---

## 🔍 **Verify Indexes**

### **HTTP API:**
```bash
# Get collection info (includes payload schema with indexes)
curl "http://192.168.254.22:6333/collections/content"
```

### **Python Client:**
```python
# Get collection info
info = client.get_collection("content")

# Check payload schema (indexes)
if hasattr(info.config.params, 'payload_schema'):
    print("\nPayload Indexes:")
    for field_name, field_schema in info.config.params.payload_schema.items():
        print(f"  {field_name}: {field_schema}")
else:
    print("\nNo payload indexes configured")
```

---

## 🚀 **Using Indexed Fields in Queries**

### **Filter by Filename (with index):**
```python
results = client.search(
    collection_name="content",
    query_vector=embedding,
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="metadata.filename",
                match=models.MatchValue(value="ECOS_9.2.4.0_Release_Notes_RevB.pdf")
            )
        ]
    ),
    limit=10
)
```

### **Filter by Page Range (with index):**
```python
results = client.search(
    collection_name="content",
    query_vector=embedding,
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="metadata.page_number",
                range=models.Range(
                    gte=1,   # Greater than or equal to 1
                    lte=10   # Less than or equal to 10
                )
            )
        ]
    ),
    limit=10
)
```

### **Filter by Element Type (with index):**
```python
results = client.search(
    collection_name="content",
    query_vector=embedding,
    query_filter=models.Filter(
        must=[
            models.FieldCondition(
                key="metadata.element_type",
                match=models.MatchValue(value="Table")
            )
        ]
    ),
    limit=10
)
```

---

## 📋 **Quick Reference**

| Field Type | Index Type | Use Case | Example |
|------------|------------|----------|---------|
| String (exact match) | `keyword` | IDs, hashes, filenames | `metadata.filename` |
| String (tenant) | `keyword` + `is_tenant=True` | Multi-value filters | `metadata.filename` |
| Integer/Float | `integer` | Numeric ranges | `metadata.page_number` |
| Text (search) | `text` | Full-text search | `pagecontent` |
| Boolean | `keyword` | True/False filters | `metadata.is_processed` |

---

## ⚠️ **Important Notes**

1. **Indexes are created asynchronously** - they build in the background
2. **Existing data is indexed automatically** - no need to re-insert
3. **Indexes consume memory** - only index fields you actually filter on
4. **Tenant optimization** (`is_tenant=True`) is best for high-cardinality fields
5. **Check index status** with `get_collection()` to see `payload_schema`

---

## 🎯 **Recommended Indexes for Your Collections**

### **Content Collection:**
```python
# Priority 1: High-impact
✅ metadata.filename (keyword, is_tenant=True)
✅ metadata.page_number (integer)

# Priority 2: Useful
✅ metadata.element_type (keyword)
✅ metadata.md5_hash (keyword)
```

### **Filenames Collection:**
```python
# Priority 1: High-impact
✅ metadata.hash (keyword)

# Priority 2: Useful
✅ source (keyword)
```

---

## 📚 **Additional Resources**

- [Qdrant Indexing Documentation](https://qdrant.tech/documentation/concepts/indexing/)
- [Qdrant Payload Documentation](https://qdrant.tech/documentation/concepts/payload/)
- [Qdrant Filtering Documentation](https://qdrant.tech/documentation/concepts/filtering/)
