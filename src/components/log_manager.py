"""Log manager for tracking processed files"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Set
from pathlib import Path
import logging
from threading import Lock

logger = logging.getLogger(__name__)


class LogManager:
    """Manages JSON logs for conversion, upload, and failed files"""
    
    def __init__(self, log_dir: str):
        """
        Initialize log manager
        
        Args:
            log_dir: Directory for log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.conversion_log = self.log_dir / "conversion.json"
        self.upload_log = self.log_dir / "upload.json"
        self.failed_log = self.log_dir / "failed.json"
        
        # Phase 3: New log files
        self.embedding_log = self.log_dir / "embedding.json"
        self.qdrant_upload_log = self.log_dir / "qdrant_upload.json"
        self.skipped_log = self.log_dir / "skipped.json"
        
        # Thread locks for concurrent access
        self._conversion_lock = Lock()
        self._upload_lock = Lock()
        self._failed_lock = Lock()
        self._embedding_lock = Lock()
        self._qdrant_upload_lock = Lock()
        self._skipped_lock = Lock()
        
        # Initialize log files if they don't exist
        self._init_log_file(self.conversion_log)
        self._init_log_file(self.upload_log)
        self._init_log_file(self.failed_log)
        self._init_log_file(self.embedding_log)
        self._init_log_file(self.qdrant_upload_log)
        self._init_log_file(self.skipped_log)
        
        logger.info(f"Log manager initialized: {log_dir}")
    
    def _init_log_file(self, log_path: Path):
        """Initialize log file with empty array if it doesn't exist"""
        if not log_path.exists():
            with open(log_path, 'w') as f:
                json.dump([], f)
            logger.debug(f"Created log file: {log_path}")
    
    def _load_log(self, log_path: Path) -> List[Dict]:
        """
        Load log entries from file
        
        Args:
            log_path: Path to log file
            
        Returns:
            List of log entries
        """
        try:
            with open(log_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Error loading log {log_path}: {e}. Returning empty list.")
            return []
    
    def _save_log(self, log_path: Path, entries: List[Dict]):
        """
        Save log entries to file
        
        Args:
            log_path: Path to log file
            entries: List of log entries
        """
        try:
            with open(log_path, 'w') as f:
                json.dump(entries, f, indent=2, default=str)
            logger.debug(f"Saved {len(entries)} entries to {log_path}")
        except Exception as e:
            logger.error(f"Error saving log {log_path}: {e}")
            raise
    
    def add_conversion_entry(
        self,
        filename: str,
        file_hash: str,
        error: Optional[str] = None
    ) -> bool:
        """
        Add entry to conversion log
        
        Args:
            filename: Name of the file
            file_hash: Hash of the file
            error: Optional error message if conversion failed
            
        Returns:
            True if successful
        """
        with self._conversion_lock:
            try:
                entries = self._load_log(self.conversion_log)
                
                entry = {
                    "filename": filename,
                    "hash": file_hash,
                    "datetime": datetime.utcnow().isoformat() + "Z"
                }
                
                if error:
                    entry["error"] = error
                
                entries.append(entry)
                self._save_log(self.conversion_log, entries)
                
                logger.info(f"Added conversion entry: {filename}")
                return True
                
            except Exception as e:
                logger.error(f"Error adding conversion entry: {e}")
                return False
    
    def add_upload_entry(
        self,
        filename: str,
        file_hash: str,
        error: Optional[str] = None
    ) -> bool:
        """
        Add entry to upload log
        
        Args:
            filename: Name of the file
            file_hash: Hash of the file
            error: Optional error message if upload failed
            
        Returns:
            True if successful
        """
        with self._upload_lock:
            try:
                entries = self._load_log(self.upload_log)
                
                entry = {
                    "filename": filename,
                    "hash": file_hash,
                    "datetime": datetime.utcnow().isoformat() + "Z"
                }
                
                if error:
                    entry["error"] = error
                
                entries.append(entry)
                self._save_log(self.upload_log, entries)
                
                logger.info(f"Added upload entry: {filename}")
                return True
                
            except Exception as e:
                logger.error(f"Error adding upload entry: {e}")
                return False
    
    def add_failed_entry(
        self,
        filename: str,
        file_hash: str,
        error: str,
        stage: str
    ) -> bool:
        """
        Add entry to failed log
        
        Args:
            filename: Name of the file
            file_hash: Hash of the file
            error: Error message
            stage: Stage where failure occurred (conversion, upload, etc.)
            
        Returns:
            True if successful
        """
        with self._failed_lock:
            try:
                entries = self._load_log(self.failed_log)
                
                entry = {
                    "filename": filename,
                    "hash": file_hash,
                    "datetime": datetime.utcnow().isoformat() + "Z",
                    "error": error,
                    "stage": stage
                }
                
                entries.append(entry)
                self._save_log(self.failed_log, entries)
                
                logger.error(f"Added failed entry: {filename} at stage {stage}")
                return True
                
            except Exception as e:
                logger.error(f"Error adding failed entry: {e}")
                return False
    
    # ============================================
    # Phase 3: Enhanced Logging Methods
    # ============================================
    
    def log_embedding_success(
        self,
        filename: str,
        md5_hash: str,
        collection_name: str,
        chunks_created: int,
        embedding_time: float,
        model_name: str
    ) -> bool:
        """
        Log successful embedding creation
        
        Args:
            filename: Name of the file
            md5_hash: xxHash64 value (field name kept for compatibility)
            collection_name: Target Qdrant collection
            chunks_created: Number of chunks/embeddings created
            embedding_time: Time taken to create embeddings (seconds)
            model_name: Ollama model used
            
        Returns:
            True if successful
        """
        with self._embedding_lock:
            try:
                entries = self._load_log(self.embedding_log)
                
                entry = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "filename": filename,
                    "md5_hash": md5_hash,  # xxHash64 value
                    "collection_name": collection_name,
                    "chunks_created": chunks_created,
                    "embedding_time_seconds": round(embedding_time, 3),
                    "model_name": model_name,
                    "status": "success"
                }
                
                entries.append(entry)
                self._save_log(self.embedding_log, entries)
                
                logger.info(f"✅ Logged embedding success: {filename} ({chunks_created} chunks)")
                return True
                
            except Exception as e:
                logger.error(f"Error logging embedding success: {e}")
                return False
    
    def log_qdrant_upload_success(
        self,
        filename: str,
        md5_hash: str,
        collection_name: str,
        points_uploaded: int,
        point_ids: List[str],
        batch_size: int,
        upload_time: float
    ) -> bool:
        """
        Log successful Qdrant upload
        
        Args:
            filename: Name of the file
            md5_hash: xxHash64 value (field name kept for compatibility)
            collection_name: Qdrant collection name
            points_uploaded: Number of points uploaded
            point_ids: List of Qdrant point UUIDs
            batch_size: Batch size used
            upload_time: Time taken to upload (seconds)
            
        Returns:
            True if successful
        """
        with self._qdrant_upload_lock:
            try:
                entries = self._load_log(self.qdrant_upload_log)
                
                entry = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "filename": filename,
                    "md5_hash": md5_hash,  # xxHash64 value
                    "collection_name": collection_name,
                    "points_uploaded": points_uploaded,
                    "point_ids": point_ids[:10],  # Store first 10 IDs only
                    "batch_size": batch_size,
                    "upload_time_seconds": round(upload_time, 3),
                    "status": "success"
                }
                
                entries.append(entry)
                self._save_log(self.qdrant_upload_log, entries)
                
                logger.info(f"✅ Logged Qdrant upload: {filename} ({points_uploaded} points)")
                return True
                
            except Exception as e:
                logger.error(f"Error logging Qdrant upload: {e}")
                return False
    
    def log_skipped_file(
        self,
        filename: str,
        md5_hash: str,
        skip_reason: str,
        found_in: str,
        collection_name: str,
        original_processing_date: Optional[str] = None
    ) -> bool:
        """
        Log skipped file due to deduplication
        
        Args:
            filename: Name of the file
            md5_hash: xxHash64 value (field name kept for compatibility)
            skip_reason: Reason for skipping (already_embedded, already_in_qdrant, etc.)
            found_in: Where duplicate was found (log_file, qdrant_collection, both)
            collection_name: Target collection that would have been used
            original_processing_date: When file was originally processed (if available)
            
        Returns:
            True if successful
        """
        with self._skipped_lock:
            try:
                entries = self._load_log(self.skipped_log)
                
                entry = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "filename": filename,
                    "md5_hash": md5_hash,  # xxHash64 value
                    "skip_reason": skip_reason,
                    "found_in": found_in,
                    "collection_name": collection_name
                }
                
                if original_processing_date:
                    entry["original_processing_date"] = original_processing_date
                
                entries.append(entry)
                self._save_log(self.skipped_log, entries)
                
                logger.info(f"⏭️  Logged skipped file: {filename} ({skip_reason})")
                return True
                
            except Exception as e:
                logger.error(f"Error logging skipped file: {e}")
                return False
    
    def check_embedding_exists(self, md5_hash: str, collection_name: Optional[str] = None) -> bool:
        """
        Check if file has already been embedded (from log)
        
        Args:
            md5_hash: xxHash64 value to check
            collection_name: Optional collection name to filter by (e.g., 'content', 'filenames')
            
        Returns:
            True if file is in embedding log (optionally filtered by collection)
        """
        with self._embedding_lock:
            entries = self._load_log(self.embedding_log)
            
            # If collection_name specified, check for that specific collection
            if collection_name:
                return any(
                    entry.get("md5_hash") == md5_hash and 
                    entry.get("collection_name") == collection_name 
                    for entry in entries
                )
            
            # Otherwise check if hash exists in any collection
            return any(entry.get("md5_hash") == md5_hash for entry in entries)
    
    def check_qdrant_exists(
        self,
        client,
        collection_name: str,
        md5_hash: str
    ) -> bool:
        """
        Check if file already exists in Qdrant collection
        
        Args:
            client: QdrantClient instance
            collection_name: Name of the collection
            md5_hash: xxHash64 value to check
            
        Returns:
            True if file exists in Qdrant, False if not or if check fails
        """
        try:
            from qdrant_client import models
            
            results = client.scroll(
                collection_name=collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="metadata.md5_hash",
                            match=models.MatchValue(value=md5_hash)
                        )
                    ]
                ),
                limit=1
            )
            
            return len(results[0]) > 0
            
        except Exception as e:
            error_msg = str(e)
            
            # Check if error is due to missing index
            if "Index required but not found" in error_msg and "metadata.md5_hash" in error_msg:
                # Missing index - this is expected for new collections
                # Log warning once, then skip Qdrant check
                if not hasattr(self, '_index_warning_shown'):
                    logger.warning(f"⚠️  Index 'metadata.md5_hash' not found in collection '{collection_name}'")
                    logger.warning(f"   Skipping Qdrant deduplication check (will rely on log file)")
                    logger.warning(f"   To enable Qdrant deduplication, create the index:")
                    logger.warning(f"   python scripts/create_payload_indexes_advanced.py")
                    self._index_warning_shown = True
                
                # Return False to indicate file doesn't exist (safe assumption)
                return False
            else:
                # Other error - log and return False
                logger.error(f"Error checking Qdrant for hash {md5_hash}: {e}")
                return False
    
    def is_converted(self, file_hash: str) -> bool:
        """
        Check if file has been converted
        
        Args:
            file_hash: Hash of the file
            
        Returns:
            True if file is in conversion log
        """
        with self._conversion_lock:
            entries = self._load_log(self.conversion_log)
            return any(entry.get("hash") == file_hash for entry in entries)
    
    def is_uploaded(self, file_hash: str) -> bool:
        """
        Check if file has been uploaded
        
        Args:
            file_hash: Hash of the file
            
        Returns:
            True if file is in upload log
        """
        with self._upload_lock:
            entries = self._load_log(self.upload_log)
            return any(entry.get("hash") == file_hash for entry in entries)
    
    def get_processed_hashes(self) -> Set[str]:
        """
        Get set of all processed file hashes (converted OR uploaded)
        
        Returns:
            Set of file hashes
        """
        hashes = set()
        
        with self._conversion_lock:
            conversion_entries = self._load_log(self.conversion_log)
            hashes.update(entry.get("hash") for entry in conversion_entries if entry.get("hash"))
        
        with self._upload_lock:
            upload_entries = self._load_log(self.upload_log)
            hashes.update(entry.get("hash") for entry in upload_entries if entry.get("hash"))
        
        return hashes
    
    def get_failed_files(self) -> List[Dict]:
        """
        Get list of failed files
        
        Returns:
            List of failed file entries
        """
        with self._failed_lock:
            return self._load_log(self.failed_log)
    
    def get_conversion_log(self) -> List[Dict]:
        """Get all conversion log entries"""
        with self._conversion_lock:
            return self._load_log(self.conversion_log)
    
    def get_upload_log(self) -> List[Dict]:
        """Get all upload log entries"""
        with self._upload_lock:
            return self._load_log(self.upload_log)
    
    def get_embedding_log(self) -> List[Dict]:
        """Get all embedding log entries"""
        with self._embedding_lock:
            return self._load_log(self.embedding_log)
    
    def get_qdrant_upload_log(self) -> List[Dict]:
        """Get all Qdrant upload log entries"""
        with self._qdrant_upload_lock:
            return self._load_log(self.qdrant_upload_log)
    
    def get_skipped_log(self) -> List[Dict]:
        """Get all skipped files log entries"""
        with self._skipped_lock:
            return self._load_log(self.skipped_log)
    
    def get_stats(self) -> Dict:
        """
        Get statistics about processed files
        
        Returns:
            Dictionary with counts
        """
        return {
            "converted": len(self.get_conversion_log()),
            "uploaded": len(self.get_upload_log()),
            "failed": len(self.get_failed_files()),
            "embedded": len(self.get_embedding_log()),
            "qdrant_uploaded": len(self.get_qdrant_upload_log()),
            "skipped": len(self.get_skipped_log())
        }


if __name__ == "__main__":
    # Test log manager
    log_mgr = LogManager("logs/")
    
    # Add test entries
    log_mgr.add_conversion_entry("test.pdf", "abc123", None)
    log_mgr.add_upload_entry("test.pdf", "abc123", None)
    
    # Check if processed
    print(f"Is converted: {log_mgr.is_converted('abc123')}")
    print(f"Is uploaded: {log_mgr.is_uploaded('abc123')}")
    
    # Get stats
    print(f"Stats: {log_mgr.get_stats()}")
