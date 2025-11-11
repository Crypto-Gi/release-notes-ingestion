"""Main ingestion pipeline orchestration"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from components.config import load_config
from components.r2_client import R2Client
from components.file_hasher import FileHasher
from components.log_manager import LogManager
from components.docling_client import DoclingClient
from components.markdown_storage import MarkdownStorage
from components.chunker import SemanticChunker
from components.embedding_client import EmbeddingClient
from components.qdrant_uploader import QdrantUploader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Main ingestion pipeline orchestrator"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize pipeline with all components
        
        Args:
            config_path: Optional path to .env file
        """
        logger.info("Initializing ingestion pipeline...")
        
        # Load configuration
        self.config = load_config(config_path)
        
        # Initialize components
        self.r2_client = R2Client(
            endpoint=self.config.r2.endpoint,
            access_key=self.config.r2.access_key,
            secret_key=self.config.r2.secret_key,
            bucket_name=self.config.r2.bucket_name
        )
        
        self.file_hasher = FileHasher()
        
        self.log_manager = LogManager(self.config.log.log_dir)
        
        # Get force reprocess flag from environment
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
        
        self.chunker = SemanticChunker(
            chunk_size_tokens=self.config.chunking.chunk_size_tokens,
            chunk_overlap_tokens=self.config.chunking.chunk_overlap_tokens
        )
        
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
            dimensions=self.config.ollama.dimensions
        )
        
        self.qdrant_uploader = QdrantUploader(
            host=self.config.qdrant.host,
            port=self.config.qdrant.port,
            use_https=self.config.qdrant.use_https,
            api_key=self.config.qdrant.api_key,
            grpc_port=self.config.qdrant.grpc_port,
            prefer_grpc=self.config.qdrant.prefer_grpc,
            filename_collection=self.config.qdrant.filename_collection,
            content_collection=self.config.qdrant.content_collection
        )
        
        logger.info("Pipeline initialized successfully")
        logger.info(f"  Force reprocess: {self.force_reprocess}")
    
    def health_check(self) -> Dict[str, bool]:
        """
        Check health of all external services
        
        Returns:
            Dictionary with service health status
        """
        return {
            "docling": self.docling_client.health_check(),
            "ollama": self.embedding_client.health_check(),
            "qdrant": self.qdrant_uploader.health_check()
        }
    
    def should_skip_file(self, file_key: str) -> bool:
        """
        Check if file should be skipped based on extension
        
        Args:
            file_key: R2 object key
            
        Returns:
            True if file should be skipped
        """
        if not self.config.processing.skip_extensions:
            return False
        
        filename = Path(file_key).name
        for ext in self.config.processing.skip_extensions:
            if filename.endswith(ext):
                logger.info(f"Skipping file (extension filter): {filename}")
                return True
        return False
    
    def process_file(self, file_key: str) -> bool:
        """
        Process a single file through the entire pipeline
        
        Args:
            file_key: R2 object key (e.g., "source/orchestrator/file.pdf")
            
        Returns:
            True if successful
        """
        filename = Path(file_key).name
        logger.info(f"Processing file: {file_key}")
        
        # Check if file should be skipped
        if self.should_skip_file(file_key):
            return True  # Return True to not count as failure
        
        try:
            # Step 1: Download file from R2
            logger.info(f"[1/9] Downloading from R2...")
            file_content = self.r2_client.download_file_to_memory(file_key)
            if not file_content:
                raise Exception("Failed to download file")
            
            # Step 2: Generate file hash
            logger.info(f"[2/9] Generating file hash...")
            file_hash = self.file_hasher.hash_file(file_content)
            
            # Step 3: Check if already processed
            logger.info(f"[3/9] Checking if already processed...")
            if self.log_manager.is_uploaded(file_hash):
                logger.info(f"File already processed: {filename}")
                return True
            
            # Step 4: Convert to markdown
            logger.info(f"[4/9] Converting to markdown...")
            markdown = self.docling_client.convert_from_memory(file_content, filename)
            if not markdown:
                self.log_manager.add_failed_entry(filename, file_hash, "Conversion failed", "docling")
                return False
            
            self.log_manager.add_conversion_entry(filename, file_hash)
            
            # Step 5: Upload markdown to R2
            logger.info(f"[5/9] Uploading markdown to R2...")
            if not self.markdown_storage.upload_markdown(file_key, markdown):
                self.log_manager.add_failed_entry(filename, file_hash, "Markdown upload failed", "r2")
                return False
            
            # Step 6: Chunk markdown
            logger.info(f"[6/9] Chunking markdown...")
            chunks = self.chunker.chunk_markdown(markdown, filename, self.file_hasher)
            if not chunks:
                self.log_manager.add_failed_entry(filename, file_hash, "Chunking failed", "chunker")
                return False
            
            logger.info(f"Created {len(chunks)} chunks")
            
            # Step 7: Generate filename embedding
            logger.info(f"[7/9] Generating filename embedding...")
            filename_embedding = self.embedding_client.generate_filename_embedding(
                filename=filename,
                file_content=file_content,
                collection_name=self.config.qdrant.filename_collection,
                log_to_phase3=True
            )
            if not filename_embedding:
                self.log_manager.add_failed_entry(filename, file_hash, "Filename embedding failed", "ollama")
                return False
            
            # Step 8: Generate content embeddings with deduplication
            logger.info(f"[8/9] Generating content embeddings...")
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
            
            # If None returned, file was skipped due to deduplication
            if content_embeddings is None:
                logger.info(f"⏭️  Content embeddings already exist for {filename}")
                # Still mark as successful since embeddings exist
                self.log_manager.add_upload_entry(filename, file_hash)
                return True
            
            # Step 9: Upload to Qdrant
            logger.info(f"[9/9] Uploading to Qdrant...")
            
            # Upload filename
            lightweight_hash = self.file_hasher.hash_file_lightweight(file_content)
            if not self.qdrant_uploader.upload_filename(filename, filename_embedding, lightweight_hash):
                self.log_manager.add_failed_entry(filename, file_hash, "Filename upload failed", "qdrant")
                return False
            
            # Upload content chunks
            if not self.qdrant_uploader.upload_content_chunks(filename, chunks, content_embeddings):
                self.log_manager.add_failed_entry(filename, file_hash, "Content upload failed", "qdrant")
                return False
            
            # Log success
            self.log_manager.add_upload_entry(filename, file_hash)
            logger.info(f"✅ Successfully processed: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            self.log_manager.add_failed_entry(filename, file_hash, str(e), "pipeline")
            return False
    
    def run(self) -> Dict:
        """
        Run the full pipeline on all unprocessed files
        
        Returns:
            Dictionary with processing statistics
        """
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info("Starting ingestion pipeline")
        logger.info("=" * 60)
        
        # Health check
        health = self.health_check()
        logger.info(f"Service health: {health}")
        
        if not all(health.values()):
            logger.error("Some services are unhealthy. Aborting.")
            return {"error": "Services unhealthy", "health": health}
        
        # List files in R2
        logger.info(f"Listing files in {self.config.r2.source_prefix}...")
        files = self.r2_client.list_files(prefix=self.config.r2.source_prefix)
        logger.info(f"Found {len(files)} files")
        
        # Get processed hashes
        processed_hashes = self.log_manager.get_processed_hashes()
        logger.info(f"Already processed: {len(processed_hashes)} files")
        
        # Filter new files
        new_files = []
        for file_info in files:
            # Quick check using etag (not perfect but fast)
            if file_info['etag'] not in processed_hashes:
                new_files.append(file_info)
        
        logger.info(f"New files to process: {len(new_files)}")
        
        # Process each file
        results = {
            "total_files": len(files),
            "new_files": len(new_files),
            "processed": 0,
            "failed": 0,
            "skipped": len(files) - len(new_files)
        }
        
        for i, file_info in enumerate(new_files, 1):
            logger.info(f"\n[{i}/{len(new_files)}] Processing: {file_info['key']}")
            
            if self.process_file(file_info['key']):
                results["processed"] += 1
            else:
                results["failed"] += 1
        
        # Final statistics
        elapsed = (datetime.now() - start_time).total_seconds()
        results["duration_seconds"] = elapsed
        results["files_per_second"] = results["processed"] / elapsed if elapsed > 0 else 0
        
        logger.info("=" * 60)
        logger.info("Pipeline complete!")
        logger.info(f"  Processed: {results['processed']}")
        logger.info(f"  Failed: {results['failed']}")
        logger.info(f"  Skipped: {results['skipped']}")
        logger.info(f"  Duration: {elapsed:.1f}s")
        logger.info("=" * 60)
        
        return results


if __name__ == "__main__":
    # Run pipeline
    pipeline = IngestionPipeline()
    results = pipeline.run()
    
    print("\nFinal Results:")
    print(f"  Total files: {results.get('total_files', 0)}")
    print(f"  Processed: {results.get('processed', 0)}")
    print(f"  Failed: {results.get('failed', 0)}")
    print(f"  Duration: {results.get('duration_seconds', 0):.1f}s")
