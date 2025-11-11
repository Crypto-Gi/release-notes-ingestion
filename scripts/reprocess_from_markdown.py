#!/usr/bin/env python3
"""
Reprocess pipeline from existing markdown files in R2

This script:
1. Lists markdown files from R2 (skips download and conversion)
2. Downloads markdown from R2
3. Chunks the markdown
4. Generates embeddings
5. Uploads to Qdrant

Use this when you already have markdown files and want to:
- Re-embed with different models
- Upload to new/recreated collections
- Skip the slow Docling conversion step
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from components.config import load_config
from components.r2_client import R2Client
from components.embedding_client import EmbeddingClient
from components.qdrant_uploader import QdrantUploader
from components.chunker import SemanticChunker
from components.file_hasher import FileHasher
from components.log_manager import LogManager
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MarkdownReprocessor:
    """Reprocess existing markdown files from R2"""
    
    def __init__(self):
        """Initialize with configuration"""
        self.config = load_config()
        
        # Initialize components
        self.r2_client = R2Client(
            endpoint=self.config.r2.endpoint,
            access_key=self.config.r2.access_key,
            secret_key=self.config.r2.secret_key,
            bucket_name=self.config.r2.bucket_name
        )
        
        # Initialize LogManager first (needed for Phase 3)
        self.log_manager = LogManager(log_dir=self.config.log.log_dir)
        
        # Use models from config (which already supports OLLAMA_FILENAME_MODEL env var)
        filename_model = self.config.ollama.filename_model
        content_model = self.config.ollama.content_model
        
        logger.info("Using filename embedding model: %s", filename_model)
        logger.info("Using content embedding model: %s", content_model)

        self.embedding_client = EmbeddingClient(
            host=self.config.ollama.host,
            port=self.config.ollama.port,
            filename_model=filename_model,
            content_model=content_model,
            truncate=self.config.ollama.truncate,
            keep_alive=self.config.ollama.keep_alive,
            dimensions=self.config.ollama.dimensions,
            log_manager=self.log_manager,
            enable_deduplication=True,
            enable_logging=True
        )
        
        self.qdrant_uploader = QdrantUploader(
            host=self.config.qdrant.host,
            port=self.config.qdrant.port,
            use_https=self.config.qdrant.use_https,
            api_key=self.config.qdrant.api_key,
            grpc_port=self.config.qdrant.grpc_port,
            prefer_grpc=self.config.qdrant.prefer_grpc,
            filename_collection=self.config.qdrant.filename_collection,
            content_collection=self.config.qdrant.content_collection,
            log_manager=self.log_manager,
            enable_logging=True,
            batch_size=int(os.getenv('QDRANT_BATCH_SIZE', '100'))
        )
        
        self.chunker = SemanticChunker(
            chunk_size_tokens=self.config.chunking.chunk_size_tokens,
            chunk_overlap_tokens=self.config.chunking.chunk_overlap_tokens
        )
        
        self.file_hasher = FileHasher()
        
        # Get force reprocess flag from environment
        self.force_reprocess = os.getenv('FORCE_REPROCESS', 'false').lower() == 'true'
        
        logger.info("Markdown reprocessor initialized")
        logger.info(f"  Markdown prefix: {self.config.r2.markdown_prefix}")
        logger.info(f"  Filename collection: {self.config.qdrant.filename_collection}")
        logger.info(f"  Content collection: {self.config.qdrant.content_collection}")
        logger.info(f"  Phase 3 deduplication: enabled")
        logger.info(f"  Force reprocess: {self.force_reprocess}")
    
    def process_markdown_file(self, markdown_key: str) -> bool:
        """
        Process a single markdown file from R2
        
        Args:
            markdown_key: R2 key for markdown file
            
        Returns:
            True if successful
        """
        # Extract filename from markdown key
        # e.g., "markdown/path/to/file.md" → "file.pdf"
        # Try to preserve original extension if stored in path, otherwise assume PDF
        markdown_path = Path(markdown_key)
        stem = markdown_path.stem
        
        # Check if stem contains original extension (e.g., "file.pdf" or "file.docx")
        if '.' in stem:
            filename = stem  # Already has extension
        else:
            filename = stem + ".pdf"  # Default to PDF
        
        logger.info(f"\nProcessing: {markdown_key}")
        logger.info(f"  Original filename: {filename}")
        
        try:
            # Step 1: Download markdown from R2
            logger.info(f"[1/5] Downloading markdown from R2...")
            markdown_content = self.r2_client.download_file_to_memory(markdown_key)
            if not markdown_content:
                raise Exception("Failed to download markdown")
            
            # Try UTF-8 first, fallback to latin-1 if needed
            try:
                markdown = markdown_content.decode('utf-8')
            except UnicodeDecodeError:
                logger.warning("  UTF-8 decode failed, trying latin-1...")
                markdown = markdown_content.decode('latin-1')
            
            logger.info(f"  Downloaded: {len(markdown)} characters")
            
            # Step 2: Chunk markdown
            logger.info(f"[2/5] Chunking markdown...")
            chunks = self.chunker.chunk_markdown(markdown, filename, self.file_hasher)
            if not chunks:
                raise Exception("Chunking failed")
            
            logger.info(f"  Created {len(chunks)} chunks")
            
            # Step 3: Generate filename embedding
            logger.info(f"[3/5] Generating filename embedding...")
            filename_embedding = self.embedding_client.generate_filename_embedding(
                filename=filename,
                file_content=markdown_content,
                collection_name=self.config.qdrant.filename_collection,
                log_to_phase3=True
            )
            if not filename_embedding:
                raise Exception("Filename embedding failed")
            
            logger.info(f"  Generated: {len(filename_embedding)}D vector")
            
            # Step 4: Generate content embeddings with Phase 3 deduplication
            logger.info(f"[4/5] Generating content embeddings...")
            content_texts = [chunk.text for chunk in chunks]
            
            # Use Phase 3 method with deduplication
            content_embeddings = self.embedding_client.generate_batch_embeddings_with_dedup(
                filename=filename,
                file_content=markdown_content,  # Use original bytes for hash
                chunks=content_texts,
                collection_name=self.config.qdrant.content_collection,
                model_type="content",
                qdrant_client=self.qdrant_uploader.client,
                force_reprocess=self.force_reprocess
            )
            
            # If None, file was skipped due to deduplication
            if content_embeddings is None:
                logger.info(f"⏭️  Skipped {filename} - already processed")
                return True  # Not a failure, just skipped
            
            if not content_embeddings:
                raise Exception("Content embeddings failed")
            
            logger.info(f"  Generated: {len(content_embeddings)} vectors")
            
            # Step 5: Upload to Qdrant
            logger.info(f"[5/5] Uploading to Qdrant...")
            
            # Generate xxHash for filename (use file content for consistency)
            lightweight_hash = self.file_hasher.hash_file_lightweight(markdown_content)
            
            # Upload filename
            if not self.qdrant_uploader.upload_filename(
                filename, filename_embedding, lightweight_hash
            ):
                raise Exception("Filename upload failed")
            
            # Upload content chunks
            if not self.qdrant_uploader.upload_content_chunks(
                filename, chunks, content_embeddings
            ):
                raise Exception("Content upload failed")
            
            logger.info(f"✅ Successfully processed: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to process {markdown_key}: {e}")
            return False
    
    def run(self, limit: int = None) -> dict:
        """
        Run reprocessing on all markdown files
        
        Args:
            limit: Optional limit on number of files to process
            
        Returns:
            Dictionary with processing statistics
        """
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info("Starting markdown reprocessing")
        logger.info("=" * 60)
        
        # List markdown files in R2
        logger.info(f"Listing markdown files in {self.config.r2.markdown_prefix}...")
        all_files = self.r2_client.list_files(
            prefix=self.config.r2.markdown_prefix
        )
        
        logger.info(f"Total files found: {len(all_files)}")
        
        # Filter to only .md files (case-insensitive)
        markdown_files = [f for f in all_files if f['key'].lower().endswith('.md')]
        
        # Log filtered vs total
        filtered_out = len(all_files) - len(markdown_files)
        if filtered_out > 0:
            logger.warning(f"Filtered out {filtered_out} non-markdown files")
            # Show sample of filtered files
            non_md = [f['key'] for f in all_files if not f['key'].lower().endswith('.md')][:5]
            if non_md:
                logger.warning(f"Sample non-markdown files: {non_md}")
        
        logger.info(f"Found {len(markdown_files)} markdown files (.md)")
        
        # Log directory distribution
        directories = {}
        for f in markdown_files:
            # Extract directory from key (e.g., "markdown/orchestrator/file.md" -> "orchestrator")
            parts = f['key'].split('/')
            if len(parts) > 2:  # Has subdirectory
                dir_name = parts[1]  # First directory after markdown/
                directories[dir_name] = directories.get(dir_name, 0) + 1
        
        if directories:
            logger.info(f"Files by directory:")
            for dir_name, count in sorted(directories.items()):
                logger.info(f"  {dir_name}/: {count} files")
        
        if limit:
            markdown_files = markdown_files[:limit]
            logger.info(f"Limited to {limit} files")
        
        # Process each file
        results = {
            "total_files": len(markdown_files),
            "processed": 0,
            "skipped": 0,
            "failed": 0
        }
        
        for i, file_info in enumerate(markdown_files, 1):
            logger.info(f"\n[{i}/{len(markdown_files)}] Processing: {file_info['key']}")
            
            # Check if file was already processed (before downloading)
            # This is a quick check using the log
            file_hash = self.file_hasher.hash_text(file_info['key'])
            if not self.force_reprocess and self.log_manager.check_embedding_exists(file_hash):
                logger.info(f"⏭️  Skipping (already in log): {file_info['key']}")
                results["skipped"] += 1
                continue
            
            if self.process_markdown_file(file_info['key']):
                results["processed"] += 1
            else:
                results["failed"] += 1
        
        # Final statistics
        elapsed = (datetime.now() - start_time).total_seconds()
        results["duration_seconds"] = elapsed
        results["files_per_second"] = results["processed"] / elapsed if elapsed > 0 else 0
        
        logger.info("=" * 60)
        logger.info("Reprocessing complete!")
        logger.info(f"  Processed: {results['processed']}")
        logger.info(f"  Skipped: {results['skipped']}")
        logger.info(f"  Failed: {results['failed']}")
        logger.info(f"  Duration: {elapsed:.1f}s")
        logger.info(f"  Speed: {results['files_per_second']:.2f} files/sec")
        logger.info("=" * 60)
        
        return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Reprocess markdown files from R2 (skip conversion)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of files to process (for testing)"
    )
    
    args = parser.parse_args()
    
    # Run reprocessor
    reprocessor = MarkdownReprocessor()
    results = reprocessor.run(limit=args.limit)
    
    print("\nFinal Results:")
    print(f"  Total files: {results.get('total_files', 0)}")
    print(f"  Processed: {results.get('processed', 0)}")
    print(f"  Skipped: {results.get('skipped', 0)}")
    print(f"  Failed: {results.get('failed', 0)}")
    print(f"  Duration: {results.get('duration_seconds', 0):.1f}s")
