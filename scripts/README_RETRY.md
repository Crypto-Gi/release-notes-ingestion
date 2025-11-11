# Retry Failed Files Script

## Overview

`retry_failed_files.py` automatically retries processing files that failed in previous pipeline or reprocess runs.

## Features

✅ Reads `failed.json` to get list of failed files  
✅ Searches R2 recursively (both source and markdown directories)  
✅ Reprocesses files through appropriate pipeline  
✅ Removes successfully processed files from `failed.json`  
✅ Logs with same format as pipeline/reprocess scripts  
✅ Supports both source files (full pipeline) and markdown files (skip conversion)  

## Usage

### Basic Usage
```bash
# Retry all failed files
python scripts/retry_failed_files.py
```

### Dry Run (Preview)
```bash
# See what would be processed without actually processing
python scripts/retry_failed_files.py --dry-run
```

### With Force Reprocess
```bash
# Force re-embed even if embeddings exist
FORCE_REPROCESS=true python scripts/retry_failed_files.py
```

## How It Works

### 1. Load Failed Files
Reads `logs/failed.json` to get list of files that failed:
```json
[
  {
    "filename": "document.pdf",
    "file_hash": "abc123...",
    "error_message": "Chunking failed",
    "stage": "reprocess",
    "timestamp": "2025-11-11T20:00:00Z"
  }
]
```

### 2. Search R2
For each failed file, searches:
- **Source directory** (`source/`) - Original files (PDF, DOCX, etc.)
- **Markdown directory** (`markdown/`) - Converted markdown files

### 3. Process Based on Type

#### If Found in Source:
Runs full pipeline (9 steps):
1. Download from R2
2. Generate file hash
3. Convert to markdown (Docling)
4. Upload markdown to R2
5. Chunk markdown
6. Generate filename embedding
7. Generate content embeddings (with deduplication)
8. Upload to Qdrant
9. Log success

#### If Found in Markdown:
Runs reprocess pipeline (5 steps):
1. Download markdown from R2
2. Chunk markdown
3. Generate filename embedding
4. Generate content embeddings (with deduplication)
5. Upload to Qdrant

### 4. Update Logs
- **Success**: Removes entry from `failed.json`
- **Still Failed**: Keeps entry in `failed.json` with updated error
- **Not Found**: Logs warning, keeps entry

## Output Example

```
============================================================
Starting failed file retry processing
============================================================
Loaded 3 failed files from log

[1/3] Retrying: document1.pdf
  Previous error: Chunking failed
✅ Found in markdown: markdown/path/to/document1.md
============================================================
Processing markdown file: markdown/path/to/document1.md
============================================================
[1/5] Downloading markdown from R2...
[2/5] Chunking markdown...
  Created 26 chunks
[3/5] Generating filename embedding...
[4/5] Generating content embeddings...
[5/5] Uploading to Qdrant...
✅ Successfully processed: document1.pdf
✅ Removed 1 entry from failed.json

[2/3] Retrying: document2.pdf
  Previous error: Content embeddings failed
✅ Found in source: source/path/to/document2.pdf
============================================================
Processing source file: source/path/to/document2.pdf
============================================================
[1/9] Downloading from R2...
[2/9] Generating file hash...
[3/9] Converting to markdown...
[4/9] Uploading markdown to R2...
[5/9] Chunking markdown...
[6/9] Generating filename embedding...
[7/9] Generating content embeddings...
[8/9] Uploading to Qdrant...
[9/9] Logging success...
✅ Successfully processed: document2.pdf
✅ Removed 1 entry from failed.json

[3/3] Retrying: document3.pdf
  Previous error: File not found
❌ File not found in R2: document3.pdf
⏭️  Skipping document3.pdf - not found in R2

============================================================
Retry processing complete!
  Total failed files: 3
  Successfully processed: 2
  Still failed: 0
  Not found in R2: 1
  Duration: 45.3s
============================================================
```

## Integration with Other Scripts

### Pipeline → Retry
```bash
# Run pipeline
python src/pipeline.py

# Check for failures
cat logs/failed.json

# Retry failed files
python scripts/retry_failed_files.py
```

### Reprocess → Retry
```bash
# Run reprocess
python scripts/reprocess_from_markdown.py

# Retry any failures
python scripts/retry_failed_files.py
```

## Environment Variables

All standard pipeline environment variables are supported:

- `FORCE_REPROCESS=true` - Force re-embed even if exists
- `QDRANT_BATCH_SIZE=100` - Batch size for uploads
- `LOG_EMBEDDINGS=true` - Enable embedding logs
- `LOG_QDRANT_UPLOADS=true` - Enable upload logs

## Logging

Uses same logging format as pipeline and reprocess scripts:

- **failed.json** - Failed files (updated automatically)
- **embedding.json** - Embedding operations
- **qdrant_upload.json** - Qdrant uploads
- **skipped.json** - Skipped files (deduplication)
- **conversion.json** - Docling conversions (source files only)
- **upload.json** - Successfully uploaded files

## Error Handling

### File Not Found
If file is not found in R2:
- Logs warning
- Keeps entry in `failed.json`
- Continues to next file

### Processing Fails Again
If retry fails:
- Updates error message in `failed.json`
- Logs to `failed.json` with new timestamp
- Can retry again later

### Successful Processing
If retry succeeds:
- Removes entry from `failed.json`
- Logs to appropriate success logs
- File won't be retried again

## Best Practices

### 1. Check Failures First
```bash
# See what failed
cat logs/failed.json | jq '.[] | {filename, error: .error_message}'
```

### 2. Dry Run Before Processing
```bash
# Preview what will be retried
python scripts/retry_failed_files.py --dry-run
```

### 3. Fix Root Causes
Before retrying, check if underlying issues are fixed:
- Ollama service running?
- Qdrant accessible?
- Docling service healthy?
- Network connectivity?

### 4. Monitor Progress
```bash
# Watch logs in real-time
tail -f logs/*.json
```

### 5. Iterative Retry
```bash
# Retry multiple times until all succeed
while [ $(cat logs/failed.json | jq '. | length') -gt 0 ]; do
    echo "Retrying $(cat logs/failed.json | jq '. | length') failed files..."
    python scripts/retry_failed_files.py
    sleep 5
done
```

## Troubleshooting

### No Failed Files
```bash
$ python scripts/retry_failed_files.py
No failed files to retry
```
**Solution**: Check `logs/failed.json` exists and has entries

### File Not Found in R2
```bash
❌ File not found in R2: document.pdf
```
**Solution**: File may have been deleted or moved. Check R2 bucket.

### Still Failing
```bash
Still failed: 3
```
**Solution**: Check error messages in `failed.json`, fix root cause, retry again.

## See Also

- `pipeline.py` - Main ingestion pipeline
- `reprocess_from_markdown.py` - Reprocess from markdown
- `../docs/PHASE_3_PROGRESS.md` - Phase 3 deduplication docs
