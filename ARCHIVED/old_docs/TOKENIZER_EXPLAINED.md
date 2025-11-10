# Tokenizer Explained - Full-Text Search in Qdrant

## 🎯 **What is a Tokenizer?**

A **tokenizer** is a component that splits text into searchable **tokens** (words or terms) for full-text search.

Think of it like this:
- **Input:** "The quick brown fox jumps"
- **Tokenizer:** Splits into tokens
- **Output:** ["the", "quick", "brown", "fox", "jumps"]

These tokens are then indexed so you can search for individual words within the text.

---

## 📚 **Where is it Used?**

### **In `setup_qdrant_collections.py`:**

Tokenizers are used when creating **TEXT indexes** on fields like:
- `pagecontent` - The actual content of documents
- `metadata.filename` - Filenames (optional)

**Example from the script:**
```python
client.create_payload_index(
    collection_name="content",
    field_name="pagecontent",
    field_schema=TextIndexParams(
        type="text",
        tokenizer=TokenizerType.WORD,  # ← This is the tokenizer!
        min_token_len=1,
        max_token_len=15,
        lowercase=True
    )
)
```

---

## 🔤 **4 Types of Tokenizers**

### **1. WORD Tokenizer** (Default, Most Common) ⭐

**How it works:** Splits text by word boundaries (spaces, punctuation, etc.)

**Example:**
```
Input:  "Hello, world! How are you?"
Tokens: ["hello", "world", "how", "are", "you"]
```

**Use Cases:**
- ✅ General text search
- ✅ English and most languages
- ✅ Natural language content
- ✅ **Most common choice**

**Configuration:**
```python
tokenizer=TokenizerType.WORD
```

---

### **2. WHITESPACE Tokenizer**

**How it works:** Splits ONLY by whitespace (spaces, tabs, newlines)

**Example:**
```
Input:  "Hello, world! How are you?"
Tokens: ["Hello,", "world!", "How", "are", "you?"]
```

Notice: Punctuation is kept with words!

**Use Cases:**
- ✅ Code snippets (preserve symbols)
- ✅ Technical content with special characters
- ✅ When you want to keep punctuation

**Configuration:**
```python
tokenizer=TokenizerType.WHITESPACE
```

---

### **3. PREFIX Tokenizer**

**How it works:** Creates tokens for all prefixes of words

**Example:**
```
Input:  "document"
Tokens: ["d", "do", "doc", "docu", "docum", "docume", "documen", "document"]
```

**Use Cases:**
- ✅ Autocomplete search
- ✅ Prefix matching ("doc" finds "document")
- ✅ Partial word search
- ⚠️ **Warning:** Uses more storage!

**Configuration:**
```python
tokenizer=TokenizerType.PREFIX
```

**Example Search:**
```python
# User types "doc"
# Finds: "document", "documentation", "docker", etc.
```

---

### **4. MULTILINGUAL Tokenizer**

**How it works:** Handles multiple languages with proper word boundaries

**Example:**
```
Input:  "Hello 世界 مرحبا"
Tokens: ["hello", "世界", "مرحبا"]
```

**Use Cases:**
- ✅ Multi-language content
- ✅ International documents
- ✅ Mixed language text
- ✅ Unicode support

**Configuration:**
```python
tokenizer=TokenizerType.MULTILINGUAL
```

---

## ⚙️ **Additional Tokenizer Options**

### **min_token_len** (Minimum Token Length)

**What:** Ignore tokens shorter than this length

**Example:**
```python
min_token_len=2  # Ignore single-character tokens

Input:  "I am a developer"
Tokens: ["am", "developer"]  # "I" and "a" are ignored
```

**Use Cases:**
- Skip common single letters
- Reduce index size
- Filter out noise

---

### **max_token_len** (Maximum Token Length)

**What:** Truncate tokens longer than this length

**Example:**
```python
max_token_len=15

Input:  "supercalifragilisticexpialidocious"
Token:  "supercalifragil"  # Truncated to 15 chars
```

**Use Cases:**
- Prevent extremely long tokens
- Control index size
- Handle malformed data

---

### **lowercase** (Convert to Lowercase)

**What:** Convert all tokens to lowercase

**Example:**
```python
lowercase=True

Input:  "Hello WORLD"
Tokens: ["hello", "world"]
```

**Benefits:**
- ✅ Case-insensitive search
- ✅ "Hello" matches "hello" matches "HELLO"
- ✅ **Recommended: True** (default)

---

## 🎯 **Tokenizer vs Payload Index**

### **TEXT Index (Tokenizer)** 📝
- **Purpose:** Full-text search within content
- **Field:** `pagecontent` (long text)
- **Search:** "Find documents containing 'release notes'"
- **Tokenizer:** Splits text into searchable words

**Example:**
```python
# TEXT index with tokenizer
client.create_payload_index(
    collection_name="content",
    field_name="pagecontent",
    field_schema=TextIndexParams(
        type="text",
        tokenizer=TokenizerType.WORD
    )
)

# Search for words in content
results = client.query(
    collection_name="content",
    query_text="release notes"  # Searches within pagecontent
)
```

---

### **KEYWORD Index (No Tokenizer)** 🔤
- **Purpose:** Exact match filtering
- **Field:** `metadata.filename` (short strings)
- **Search:** "Find documents WHERE filename = 'doc.pdf'"
- **No Tokenizer:** Matches entire value exactly

**Example:**
```python
# KEYWORD index (no tokenizer)
client.create_payload_index(
    collection_name="content",
    field_name="metadata.filename",
    field_schema=KeywordIndexParams(
        type="keyword",
        is_tenant=True
    )
)

# Filter by exact filename
results = client.query(
    collection_name="content",
    query_filter=Filter(
        must=[
            FieldCondition(
                key="metadata.filename",
                match=MatchValue(value="doc.pdf")  # Exact match
            )
        ]
    )
)
```

---

## 📊 **Comparison Table**

| Feature | TEXT Index (Tokenizer) | KEYWORD Index |
|---------|------------------------|---------------|
| **Purpose** | Full-text search | Exact filtering |
| **Field Type** | Long text | Short strings |
| **Tokenizer** | ✅ Yes | ❌ No |
| **Search Type** | Word search | Exact match |
| **Example Field** | `pagecontent` | `metadata.filename` |
| **Use Case** | "Find 'bug fix' in content" | "Filter by filename" |

---

## 🚀 **Practical Example**

### **Scenario:** Release Notes Search System

**Collection:** `content`

**Fields:**
1. `pagecontent` - Full release notes text
2. `metadata.filename` - PDF filename
3. `metadata.version` - Version number

**Indexes:**

```python
# 1. TEXT index for full-text search in content
client.create_payload_index(
    collection_name="content",
    field_name="pagecontent",
    field_schema=TextIndexParams(
        type="text",
        tokenizer=TokenizerType.WORD,      # Split by words
        min_token_len=2,                   # Ignore single chars
        max_token_len=15,                  # Limit token length
        lowercase=True                     # Case-insensitive
    )
)

# 2. KEYWORD index for exact filename matching
client.create_payload_index(
    collection_name="content",
    field_name="metadata.filename",
    field_schema=KeywordIndexParams(
        type="keyword",
        is_tenant=True                     # Optimize for filtering
    )
)

# 3. KEYWORD index for version filtering
client.create_payload_index(
    collection_name="content",
    field_name="metadata.version",
    field_schema=KeywordIndexParams(
        type="keyword"
    )
)
```

**Search Examples:**

```python
# Example 1: Full-text search for "security patch"
results = client.query(
    collection_name="content",
    query_text="security patch",  # Uses TEXT index with tokenizer
    limit=10
)

# Example 2: Filter by exact filename
results = client.query(
    collection_name="content",
    query_filter=Filter(
        must=[
            FieldCondition(
                key="metadata.filename",
                match=MatchValue(value="release_v2.0.pdf")  # Uses KEYWORD index
            )
        ]
    )
)

# Example 3: Combined - search text + filter by version
results = client.query(
    collection_name="content",
    query_text="bug fix",  # TEXT index
    query_filter=Filter(
        must=[
            FieldCondition(
                key="metadata.version",
                match=MatchValue(value="2.0")  # KEYWORD index
            )
        ]
    )
)
```

---

## 🎓 **Best Practices**

### **1. Choose the Right Tokenizer**
```
General text → WORD (default)
Code/technical → WHITESPACE
Autocomplete → PREFIX
Multi-language → MULTILINGUAL
```

### **2. Set Reasonable Token Lengths**
```python
min_token_len=2   # Skip single letters
max_token_len=15  # Prevent huge tokens
```

### **3. Always Use Lowercase**
```python
lowercase=True  # Makes search case-insensitive
```

### **4. Use TEXT Index for Content**
- Long text fields
- Full-text search needed
- Natural language

### **5. Use KEYWORD Index for Metadata**
- Short strings
- Exact matching
- IDs, filenames, categories

---

## 📚 **Summary**

| Concept | Description |
|---------|-------------|
| **Tokenizer** | Splits text into searchable words |
| **TEXT Index** | Uses tokenizer for full-text search |
| **KEYWORD Index** | No tokenizer, exact matching |
| **WORD** | Default tokenizer, splits by word boundaries |
| **WHITESPACE** | Splits only by spaces |
| **PREFIX** | Creates prefix tokens for autocomplete |
| **MULTILINGUAL** | Handles multiple languages |

---

## 🔗 **Related Documentation**

- **Payload Indexes:** `docs/QDRANT_INDEX_TYPES.md`
- **Indexing Guide:** `docs/INDEXING_README.md`
- **Qdrant Official:** https://qdrant.tech/documentation/concepts/indexing/

---

**Now you understand tokenizers!** 🎉

Use them for full-text search in content fields, and use KEYWORD indexes for exact matching on metadata fields.
