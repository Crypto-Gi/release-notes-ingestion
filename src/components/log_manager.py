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
        
        # Thread locks for concurrent access
        self._conversion_lock = Lock()
        self._upload_lock = Lock()
        self._failed_lock = Lock()
        
        # Initialize log files if they don't exist
        self._init_log_file(self.conversion_log)
        self._init_log_file(self.upload_log)
        self._init_log_file(self.failed_log)
        
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
    
    def get_stats(self) -> Dict:
        """
        Get statistics about processed files
        
        Returns:
            Dictionary with counts
        """
        return {
            "converted": len(self.get_conversion_log()),
            "uploaded": len(self.get_upload_log()),
            "failed": len(self.get_failed_files())
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
