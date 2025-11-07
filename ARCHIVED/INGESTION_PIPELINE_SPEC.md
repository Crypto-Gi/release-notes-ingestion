# 📥 Ingestion Pipeline Specification

## Overview
We need to create an **ingestion pipeline** for reading, converting, chunking, and uploading files to a Qdrant database.  
The pipeline should be modular, efficient, and capable of incremental updates by skipping already processed files.

---

## 🧠 Pipeline Technology Options
We have three options for building the ingestion pipeline:
- **n8n**
- **LangChain**
- **Haystack v2**

**Preferred Option:** `n8n` (open to other ideas if better suited).

---

## 📂 Data Source
- The pipeline must **iteratively read files** from a specified directory.
- The first source will be a **Cloudflare R2 bucket** with an **S3-compatible endpoint**.
- Additional sources can be integrated later.

### Traversal Requirements
- Recursively traverse **all subfolders** inside the root directory.
- Process **all files** found within those subfolders.

---

## 🔑 File Tracking and Hashing
Each file must have a **fast hash** generated to uniquely identify it.

### Purpose
- Track files that have been processed.
- Skip files already processed during re-runs.

### Workflow
1. Generate a hash for each file before processing.
2. Compare it with entries in the JSON log file.
3. **Skip** files with matching hashes.

---

## 🧾 Logging Requirements
Two **JSON log files** are required:

1. **Conversion Log** – Records files successfully converted to Markdown.  
2. **Upload Log** – Records files successfully uploaded to Qdrant.

### Log Fields
Each entry must contain:
- `filename`
- `hash`
- `datetime`

➡️ These logs must contain **only** these fields and no additional data.

---

## 🧩 File Conversion

- Use the **Docling Service** ([GitHub: Crypto-Gi/docling-service](https://github.com/Crypto-Gi/docling-service)) running locally at:  
  ```
  http://docling.mynetwork.ing
  ```
- This service converts **PDF** and **Word** documents into **Markdown**.

### Storage Requirements
- Store all converted Markdown files in a **separate folder named “markdown”** within the same **Cloudflare R2 bucket**.
- The **directory hierarchy** in `markdown/` must **mirror** the source structure exactly.

### Example Folder Structure

**Source:**
```
source/
 ├── orchestrator/
 │    ├── release1/
 │    └── release2/
 ├── ecos/
 │    ├── release1/
 │    └── release2/
 └── srx/
      ├── release1/
      └── release2/
```

**Markdown Output:**
```
markdown/
 ├── orchestrator/
 │    ├── release1/
 │    └── release2/
 ├── ecos/
 │    ├── release1/
 │    └── release2/
 └── srx/
      ├── release1/
      └── release2/
```

Each Markdown file must correspond one-to-one with the original document.

---

## 🔍 Chunking and Embedding

After conversion:
- Each Markdown file will be processed for **semantic chunking**.
- The **default chunk size** is **500 tokens** with **no overlap** (configurable).

### Uploading to Qdrant
- Each chunk should be uploaded to **Qdrant DB**.
- The upload process must strictly follow the schema and structure defined in `QDRANT_COLLECTIONS.md`.
- Ensure compatibility so that the **search API** continues to function correctly.

---

## ⚙️ Process Flow Summary

1. Recursively read files from Cloudflare R2 bucket.  
2. Generate a unique hash for each file.  
3. Skip already processed files based on hash match.  
4. Convert new files to Markdown using Docling Service.  
5. Store converted files under the mirrored `markdown/` folder.  
6. Record successful conversions in **Conversion Log**.  
7. Perform **semantic chunking** (default: 500 tokens).  
8. Upload chunks to Qdrant following `QDRANT_COLLECTIONS.md`.  
9. Record successful uploads in **Upload Log**.

---

## 🧱 Summary of Components

| Component | Description | Notes |
|------------|--------------|-------|
| **Source Storage** | Cloudflare R2 bucket (S3-compatible) | Will expand to other sources later |
| **Conversion Tool** | Docling Service | Converts PDFs/Word to Markdown |
| **Storage Target** | Markdown folder (same structure) | Separate from source |
| **Vector DB** | Qdrant | Schema defined in `QDRANT_COLLECTIONS.md` |
| **Chunk Size** | 500 tokens (default) | No overlaps |
| **Logging** | JSON logs for conversion & upload | Tracks filename, hash, datetime |

---

## ✅ Success Criteria

- Each processed file has a **unique hash** entry.  
- Re-runs **skip already processed files**.  
- Logs are clean, lightweight, and append-only.  
- The **Markdown hierarchy mirrors** the source structure.  
- Qdrant data structure strictly follows `QDRANT_COLLECTIONS.md`.

---

## 🚀 Future Extensions

- Support for additional sources (e.g., GCS, Azure Blob, or local directories).  
- Add event-based triggers for file ingestion.  
- Integrate monitoring for failed uploads or conversions.  
- Implement delta updates or version tracking for changed documents.
