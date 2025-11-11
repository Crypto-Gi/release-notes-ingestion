#!/usr/bin/env python3
"""
Retry Failed Files Script

This script:
1. Reads failed.json to get list of failed files
2. Searches R2 recursively for those files (source or markdown)
3. Reprocesses failed files through the pipeline
4. Removes successfully processed files from failed.json
5. Logs results with same format as pipeline/reprocess

Use this to automatically retry files that failed in previous runs.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from components.config import load_config
from components.r2_client import R2Client
from components.file_hasher import FileHasher
from components.log_manager import LogManager
from components.docling_client import DoclingClient
from components.markdown_storage import MarkdownStorage
from components.chunker import SemanticChunker
from components.embedding_client import EmbeddingClient
from components.qdrant_uploader import QdrantUploader

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FailedFileRetry:
    """Retry processing of failed files"""
    
    def __init__(self):
        """Initialize retry processor with all pipeline components"""
        self.config = load_config()
        
        # Initialize components
        self.r2_client = R2Client(
            endpoint=self.config.r2.endpoint,
            access_key=self.config.r2.access_key,
            secret_key=self.config.r2.secret_key,
            bucket_name=self.config.r2.bucket_name
        )
        
        self.file_hasher = FileHasher()
        self.log_manager = LogManager(log_dir=self.config.log.log_dir)
        
        self.docling_client = DoclingClient(
            base_url=self.config.docling.base_url,
            timeout=self.config.docling.timeout,
            poll_interval=self.config.docling.poll_interval
        )
        
        self.markdown_storage = MarkdownStorage(
            r2_client=self.r2_client,
            source_prefix=self.config.r2.source_prefix,
            markdown_prefix=self.config.r2.markdown_prefix
        )
        
        self.chunker = SemanticChunker(
            chunk_size_tokens=self.config.chunking.chunk_size_tokens,
            chunk_overlap_tokens=self.config.chunking.chunk_overlap_tokens
        )
        
        # Get embedding models
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
        
        # Get force reprocess flag
        self.force_reprocess = os.getenv('FORCE_REPROCESS', 'false').lower() == 'true'
        
        logger.info("Failed file retry processor initialized")
        logger.info(f"  Force reprocess: {self.force_reprocess}")
    
    def load_failed_files(self) -> List[Dict]:
        """Load failed files from failed.json"""
        failed_log = Path(self.config.log.log_dir) / "failed.json"
        
        if not failed_log.exists():
            logger.warning(f"No failed.json found at {failed_log}")
            return []
        
        try:
            with open(failed_log, 'r') as f:
                failed_files = json.load(f)
            
            logger.info(f"Loaded {len(failed_files)} failed files from log")
            return failed_files
        except Exception as e:
            logger.error(f"Error loading failed.json: {e}")
            return []
    
    def remove_from_failed_log(self, file_hash: str):
        """Remove successfully processed file from failed.json"""
        failed_log = Path(self.config.log.log_dir) / "failed.json"
        
        try:
            with open(failed_log, 'r') as f:
                failed_files = json.load(f)
            
            # Filter out the successfully processed file
            updated_files = [f for f in failed_files if f.get('file_hash') != file_hash]
            
            with open(failed_log, 'w') as f:
                json.dump(updated_files, f, indent=2)
            
            removed_count = len(failed_files) - len(updated_files)
            if removed_count > 0:
                logger.info(f"✅ Removed {removed_count} entry from failed.json")
        except Exception as e:
            logger.error(f"Error updating failed.json: {e}")
    
    def find_file_in_r2(self, filename: str) -> Optional[Dict]:
        """
        Search for file in R2 (both source and markdown directories)
        
        Args:
            filename: Filename to search for
            
        Returns:
            Dict with file info if found, None otherwise
        """
        # Try source directory first
        logger.debug(f"Searching for {filename} in source directory...")
        source_files = self.r2_client.list_files(prefix=self.config.r2.source_prefix)
        
        for file_info in source_files:
            if Path(file_info['key']).name == filename:
                logger.info(f"✅ Found in source: {file_info['key']}")
                return {'key': file_info['key'], 'type': 'source'}
        
        # Try markdown directory
        logger.debug(f"Searching for {filename} in markdown directory...")
        markdown_files = self.r2_client.list_files(prefix=self.config.r2.markdown_prefix)
        
        # For markdown, try matching stem (without .md extension)
        filename_stem = Path(filename).stem
        
        for file_info in markdown_files:
            md_stem = Path(file_info['key']).stem
            if md_stem == filename_stem or Path(file_info['key']).name == filename:
                logger.info(f"✅ Found in markdown: {file_info['key']}")
                return {'key': file_info['key'], 'type': 'markdown'}
        
        logger.warning(f"❌ File not found in R2: {filename}")
        return None
    
    def process_source_file(self, file_key: str, filename: str, file_hash: str) -> bool:
        """
        Process file from source directory (full pipeline)
        
        Args:
            file_key: R2 key for source file
            filename: Original filename
            file_hash: File hash from failed log
            
        Returns:
            True if successful
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing source file: {file_key}")
        logger.info(f"{'='*60}")
        
        try:
            # Step 1: Download from R2
            logger.info(f"[1/9] Downloading from R2...")
            file_content = self.r2_client.download_file_to_memory(file_key)
            if not file_content:
                raise Exception("Failed to download file")
            
            # Step 2: Generate file hash
            logger.info(f"[2/9] Generating file hash...")
            calculated_hash = self.file_hasher.hash_file(file_content)
            
            # Step 3: Convert to markdown
            logger.info(f"[3/9] Converting to markdown...")
            markdown = self.docling_client.convert_from_memory(file_content, filename)
            if not markdown:
                self.log_manager.add_failed_entry(filename, calculated_hash, "Conversion failed", "docling")
                return False
            
            self.log_manager.add_conversion_entry(filename, calculated_hash)
            
            # Step 4: Upload markdown to R2
            logger.info(f"[4/9] Uploading markdown to R2...")
            if not self.markdown_storage.upload_markdown(file_key, markdown):
                self.log_manager.add_failed_entry(filename, calculated_hash, "Markdown upload failed", "r2")
                return False
            
            # Step 5: Chunk markdown
            logger.info(f"[5/9] Chunking markdown...")
            chunks = self.chunker.chunk_markdown(markdown, filename, self.file_hasher)
            if not chunks:
                self.log_manager.add_failed_entry(filename, calculated_hash, "Chunking failed", "chunker")
                return False
            
            logger.info(f"Created {len(chunks)} chunks")
            
            # Step 6: Generate filename embedding
            logger.info(f"[6/9] Generating filename embedding...")
            filename_embedding = self.embedding_client.generate_filename_embedding(
                filename=filename,
                file_content=file_content,
                collection_name=self.config.qdrant.filename_collection,
                log_to_phase3=True
            )
            if not filename_embedding:
                self.log_manager.add_failed_entry(filename, calculated_hash, "Filename embedding failed", "ollama")
                return False
            
            # Step 7: Generate content embeddings with deduplication
            logger.info(f"[7/9] Generating content embeddings...")
            content_texts = [chunk.text for chunk in chunks]
            content_embeddings = self.embedding_client.generate_batch_embeddings_with_dedup(
                filename=filename,
                file_content=file_content,
                chunks=content_texts,
                collection_name=self.config.qdrant.content_collection,
                model_type="content",
                qdrant_client=self.qdrant_uploader.client,
                force_reprocess=self.force_reprocess
            )
            
            if content_embeddings is None:
                logger.info(f"⏭️  Content embeddings already exist for {filename}")
                self.log_manager.add_upload_entry(filename, calculated_hash)
                return True
            
            # Step 8: Upload to Qdrant
            logger.info(f"[8/9] Uploading to Qdrant...")
            
            lightweight_hash = self.file_hasher.hash_file_lightweight(file_content)
            if not self.qdrant_uploader.upload_filename(filename, filename_embedding, lightweight_hash):
                self.log_manager.add_failed_entry(filename, calculated_hash, "Filename upload failed", "qdrant")
                return False
            
            if not self.qdrant_uploader.upload_content_chunks(filename, chunks, content_embeddings):
                self.log_manager.add_failed_entry(filename, calculated_hash, "Content upload failed", "qdrant")
                return False
            
            # Step 9: Log success
            logger.info(f"[9/9] Logging success...")
            self.log_manager.add_upload_entry(filename, calculated_hash)
            logger.info(f"✅ Successfully processed: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing source file: {e}")
            self.log_manager.add_failed_entry(filename, file_hash, str(e), "retry_pipeline")
            return False
    
    def process_markdown_file(self, file_key: str, filename: str, file_hash: str) -> bool:
        """
        Process file from markdown directory (skip conversion)
        
        Args:
            file_key: R2 key for markdown file
            filename: Original filename
            file_hash: File hash from failed log
            
        Returns:
            True if successful
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing markdown file: {file_key}")
        logger.info(f"{'='*60}")
        
        try:
            # Step 1: Download markdown from R2
            logger.info(f"[1/5] Downloading markdown from R2...")
            markdown_content = self.r2_client.download_file_to_memory(file_key)
            if not markdown_content:
                raise Exception("Failed to download markdown")
            
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
            
            # Step 4: Generate content embeddings with deduplication
            logger.info(f"[4/5] Generating content embeddings...")
            content_texts = [chunk.text for chunk in chunks]
            content_embeddings = self.embedding_client.generate_batch_embeddings_with_dedup(
                filename=filename,
                file_content=markdown_content,
                chunks=content_texts,
                collection_name=self.config.qdrant.content_collection,
                model_type="content",
                qdrant_client=self.qdrant_uploader.client,
                force_reprocess=self.force_reprocess
            )
            
            if content_embeddings is None:
                logger.info(f"⏭️  Skipped {filename} - already processed")
                return True
            
            if not content_embeddings:
                raise Exception("Content embeddings failed")
            
            logger.info(f"  Generated: {len(content_embeddings)} vectors")
            
            # Step 5: Upload to Qdrant
            logger.info(f"[5/5] Uploading to Qdrant...")
            
            lightweight_hash = self.file_hasher.hash_file_lightweight(markdown_content)
            
            if not self.qdrant_uploader.upload_filename(filename, filename_embedding, lightweight_hash):
                raise Exception("Filename upload failed")
            
            if not self.qdrant_uploader.upload_content_chunks(filename, chunks, content_embeddings):
                raise Exception("Content upload failed")
            
            logger.info(f"✅ Successfully processed: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to process {file_key}: {e}")
            self.log_manager.add_failed_entry(filename, file_hash, str(e), "retry_reprocess")
            return False
    
    def run(self) -> Dict:
        """
        Run retry processing on all failed files
        
        Returns:
            Dictionary with processing statistics
        """
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info("Starting failed file retry processing")
        logger.info("=" * 60)
        
        # Load failed files
        failed_files = self.load_failed_files()
        
        if not failed_files:
            logger.info("No failed files to retry")
            return {
                "total_files": 0,
                "processed": 0,
                "still_failed": 0,
                "not_found": 0,
                "duration_seconds": 0
            }
        
        results = {
            "total_files": len(failed_files),
            "processed": 0,
            "still_failed": 0,
            "not_found": 0
        }
        
        for i, failed_entry in enumerate(failed_files, 1):
            filename = failed_entry.get('filename', 'unknown')
            file_hash = failed_entry.get('file_hash', '')
            error_msg = failed_entry.get('error_message', 'unknown')
            
            logger.info(f"\n[{i}/{len(failed_files)}] Retrying: {filename}")
            logger.info(f"  Previous error: {error_msg}")
            
            # Find file in R2
            file_info = self.find_file_in_r2(filename)
            
            if not file_info:
                logger.warning(f"⏭️  Skipping {filename} - not found in R2")
                results["not_found"] += 1
                continue
            
            # Process based on file type
            success = False
            if file_info['type'] == 'source':
                success = self.process_source_file(file_info['key'], filename, file_hash)
            else:  # markdown
                success = self.process_markdown_file(file_info['key'], filename, file_hash)
            
            if success:
                results["processed"] += 1
                # Remove from failed.json
                self.remove_from_failed_log(file_hash)
            else:
                results["still_failed"] += 1
        
        # Final statistics
        elapsed = (datetime.now() - start_time).total_seconds()
        results["duration_seconds"] = elapsed
        
        logger.info("=" * 60)
        logger.info("Retry processing complete!")
        logger.info(f"  Total failed files: {results['total_files']}")
        logger.info(f"  Successfully processed: {results['processed']}")
        logger.info(f"  Still failed: {results['still_failed']}")
        logger.info(f"  Not found in R2: {results['not_found']}")
        logger.info(f"  Duration: {elapsed:.1f}s")
        logger.info("=" * 60)
        
        return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Retry processing failed files from failed.json"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without actually processing"
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No files will be processed")
        # Just load and show failed files
        config = load_config()
        failed_log = Path(config.log.log_dir) / "failed.json"
        if failed_log.exists():
            with open(failed_log, 'r') as f:
                failed_files = json.load(f)
            logger.info(f"Found {len(failed_files)} failed files:")
            for entry in failed_files:
                logger.info(f"  - {entry.get('filename')}: {entry.get('error_message')}")
        else:
            logger.info("No failed.json found")
    else:
        retry_processor = FailedFileRetry()
        results = retry_processor.run()
        
        print("\nFinal Results:")
        print(f"  Total failed files: {results['total_files']}")
        print(f"  Successfully processed: {results['processed']}")
        print(f"  Still failed: {results['still_failed']}")
        print(f"  Not found in R2: {results['not_found']}")
        print(f"  Duration: {results['duration_seconds']:.1f}s")
