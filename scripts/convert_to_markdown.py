#!/usr/bin/env python3
"""
Markdown-Only Pipeline (Pipeline A)

This script performs ONLY source → markdown conversion:
1. List R2 source files
2. Download source file
3. Compute xxHash64
4. Check logs for deduplication
5. Convert PDF/Word → Markdown (using Docling)
6. Upload Markdown to R2 (preserve folder structure)

STOPS HERE - no chunking, embedding, or Qdrant upload.

Use with scripts/reprocess_from_markdown.py (Pipeline B) for the full workflow:
  - Pipeline A: source → markdown (this script)
  - Pipeline B: markdown → embeddings → Qdrant
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from components.config import load_config
from components.r2_client import R2Client
from components.file_hasher import FileHasher
from components.log_manager import LogManager
from components.docling_client import DoclingClient
from components.markdown_storage import MarkdownStorage

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MarkdownConverter:
    """Convert source files to markdown only (no embedding/Qdrant)"""
    
    def __init__(self):
        """Initialize with configuration"""
        self.config = load_config()
        
        # Initialize components (only what we need)
        self.r2_client = R2Client(
            endpoint=self.config.r2.endpoint,
            access_key=self.config.r2.access_key,
            secret_key=self.config.r2.secret_key,
            bucket_name=self.config.r2.bucket_name
        )
        
        self.file_hasher = FileHasher()
        self.log_manager = LogManager(self.config.log.log_dir)
        
        # Get force reprocess flag
        self.force_reprocess = os.getenv('FORCE_REPROCESS', 'false').lower() == 'true'
        
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
        
        # Processing config
        self.skip_extensions = self.config.processing.skip_extensions
        
        logger.info("Markdown converter initialized (Pipeline A)")
        logger.info(f"  Source prefix: {self.config.r2.source_prefix}")
        logger.info(f"  Markdown prefix: {self.config.r2.markdown_prefix}")
        logger.info(f"  Force reprocess: {self.force_reprocess}")
    
    def should_skip_file(self, file_key: str) -> bool:
        """Check if file should be skipped based on extension"""
        for ext in self.skip_extensions:
            if file_key.endswith(ext):
                logger.info(f"⏭️  Skipping {file_key} (extension: {ext})")
                return True
        return False
    
    def process_file(self, file_key: str) -> bool:
        """
        Process single file: download → hash → check logs → convert → upload markdown
        
        Returns:
            True if successful, False otherwise
        """
        filename = Path(file_key).name
        logger.info(f"Processing file: {file_key}")
        
        try:
            
            # Check if file should be skipped
            if self.should_skip_file(file_key):
                return True  # Return True to not count as failure
            
            # Step 1: Download file from R2
            logger.info(f"[1/6] Downloading from R2...")
            file_content = self.r2_client.download_file_to_memory(file_key)
            if not file_content:
                raise Exception("Failed to download file")
            
            # Step 2: Generate file hash
            logger.info(f"[2/6] Generating file hash...")
            file_hash = self.file_hasher.hash_file(file_content)
            
            # Step 3: Check if already processed
            logger.info(f"[3/6] Checking if already processed...")
            if self.log_manager.is_converted(file_hash) and not self.force_reprocess:
                logger.info(f"File already converted: {filename}")
                return True
            
            # Step 4: Convert to markdown
            logger.info(f"[4/6] Converting to markdown...")
            markdown = self.docling_client.convert_from_memory(file_content, filename)
            if not markdown:
                self.log_manager.add_failed_entry(filename, file_hash, "Conversion failed", "docling")
                return False
            
            self.log_manager.add_conversion_entry(filename, file_hash)
            
            # Step 5: Upload markdown to R2
            logger.info(f"[5/6] Uploading markdown to R2...")
            if not self.markdown_storage.upload_markdown(file_key, markdown):
                self.log_manager.add_failed_entry(filename, file_hash, "Markdown upload failed", "r2")
                return False
            
            logger.info(f"✅ Successfully converted: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            self.log_manager.add_failed_entry(filename, file_hash if 'file_hash' in locals() else "unknown", str(e), "pipeline")
            return False
    
    def run(self) -> dict:
        """
        Run markdown conversion pipeline
        
        Returns:
            Summary dict with counts and timing
        """
        start_time = datetime.now()
        logger.info("\n" + "="*60)
        logger.info("MARKDOWN CONVERSION PIPELINE (Pipeline A)")
        logger.info("="*60)
        
        # Health check
        logger.info("\n🔍 Health Check...")
        if not self.docling_client.health_check():
            logger.error("❌ Docling service is not healthy!")
            return {"error": "Docling service unavailable"}
        logger.info("✅ Docling service is healthy")
        
        # List files from R2
        logger.info(f"\n📂 Listing files from R2 ({self.config.r2.source_prefix})...")
        files = self.r2_client.list_files(prefix=self.config.r2.source_prefix)
        
        if not files:
            logger.warning("No files found in R2")
            return {"total_files": 0, "processed": 0, "failed": 0, "skipped": 0}
        
        logger.info(f"Found {len(files)} files")
        
        # Process files
        processed = 0
        failed = 0
        skipped = 0
        
        for i, file_info in enumerate(files, 1):
            file_key = file_info['key']
            logger.info(f"\n[{i}/{len(files)}] Processing: {file_key}")
            
            result = self.process_file(file_key)
            
            if result:
                processed += 1
            elif result is False:
                skipped += 1
            else:
                failed += 1
        
        # Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        summary = {
            "total_files": len(files),
            "processed": processed,
            "failed": failed,
            "skipped": skipped,
            "duration_seconds": duration,
            "files_per_second": processed / duration if duration > 0 else 0
        }
        
        logger.info("\n" + "="*60)
        logger.info("PIPELINE SUMMARY")
        logger.info("="*60)
        logger.info(f"Total files: {summary['total_files']}")
        logger.info(f"Processed: {summary['processed']}")
        logger.info(f"Failed: {summary['failed']}")
        logger.info(f"Skipped: {summary['skipped']}")
        logger.info(f"Duration: {summary['duration_seconds']:.2f}s")
        logger.info(f"Speed: {summary['files_per_second']:.2f} files/sec")
        logger.info("="*60)
        
        return summary


def main():
    """Main entry point"""
    converter = MarkdownConverter()
    summary = converter.run()
    
    # Exit with error code if failures
    if summary.get("failed", 0) > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
