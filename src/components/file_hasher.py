"""File hashing utilities for deduplication and tracking"""

import hashlib
import xxhash
from typing import Union
import logging

logger = logging.getLogger(__name__)


class FileHasher:
    """Utility class for generating file and content hashes"""
    
    @staticmethod
    def hash_file_lightweight(file_content: bytes) -> str:
        """
        Generate lightweight hash for filename collection metadata (xxHash64)
        
        Args:
            file_content: File content as bytes
            
        Returns:
            16-character hex string (64-bit xxHash)
        """
        hasher = xxhash.xxh64()
        hasher.update(file_content)
        return hasher.hexdigest()
    
    @staticmethod
    def hash_file(file_content: bytes) -> str:
        """
        Generate MD5 hash of file content for logs
        
        Args:
            file_content: File content as bytes
            
        Returns:
            32-character hex string (MD5)
        """
        return hashlib.md5(file_content).hexdigest()
    
    @staticmethod
    def hash_file_fast(file_content: bytes, file_size: int) -> str:
        """
        For large files: hash first 1MB + file size
        Use this for files >= 10MB
        
        Args:
            file_content: File content as bytes (at least first 1MB)
            file_size: Total file size in bytes
            
        Returns:
            32-character hex string (MD5)
        """
        # Hash first 1MB
        chunk_size = 1024 * 1024  # 1MB
        chunk = file_content[:chunk_size]
        
        # Combine with file size
        hasher = hashlib.md5()
        hasher.update(chunk)
        hasher.update(str(file_size).encode())
        
        return hasher.hexdigest()
    
    @staticmethod
    def hash_text(text: str) -> str:
        """
        Generate MD5 hash of text (for chunks)
        
        Args:
            text: Text content
            
        Returns:
            32-character hex string (MD5)
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    @staticmethod
    def hash_file_from_path(file_path: str, use_fast: bool = False) -> str:
        """
        Generate hash from file path
        
        Args:
            file_path: Path to file
            use_fast: If True, use fast hashing for large files
            
        Returns:
            Hash string
        """
        try:
            with open(file_path, 'rb') as f:
                # Get file size
                f.seek(0, 2)  # Seek to end
                file_size = f.tell()
                f.seek(0)  # Seek back to start
                
                # Determine hashing strategy
                if use_fast and file_size >= 10 * 1024 * 1024:  # 10MB
                    # Read first 1MB
                    content = f.read(1024 * 1024)
                    hash_value = FileHasher.hash_file_fast(content, file_size)
                    logger.debug(f"Fast hash for {file_path} ({file_size} bytes): {hash_value}")
                else:
                    # Read entire file
                    content = f.read()
                    hash_value = FileHasher.hash_file(content)
                    logger.debug(f"Full hash for {file_path} ({file_size} bytes): {hash_value}")
                
                return hash_value
                
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {e}")
            raise
    
    @staticmethod
    def hash_content_for_collection(content: bytes, collection_type: str) -> str:
        """
        Generate appropriate hash based on collection type
        
        Args:
            content: Content to hash
            collection_type: 'filename' or 'content'
            
        Returns:
            Hash string
        """
        if collection_type == 'filename':
            return FileHasher.hash_file_lightweight(content)
        elif collection_type == 'content':
            return FileHasher.hash_file(content)
        else:
            raise ValueError(f"Unknown collection type: {collection_type}")


def compare_hashes(hash1: str, hash2: str) -> bool:
    """
    Compare two hashes for equality
    
    Args:
        hash1: First hash
        hash2: Second hash
        
    Returns:
        True if hashes match
    """
    return hash1.lower() == hash2.lower()


if __name__ == "__main__":
    # Test hashing functions
    test_content = b"This is a test file content for hashing"
    test_text = "This is a test text chunk"
    
    print("Testing hash functions:")
    print(f"Lightweight hash (xxHash64): {FileHasher.hash_file_lightweight(test_content)}")
    print(f"MD5 hash: {FileHasher.hash_file(test_content)}")
    print(f"Text hash: {FileHasher.hash_text(test_text)}")
    
    # Test fast hash
    large_content = b"x" * (2 * 1024 * 1024)  # 2MB
    print(f"Fast hash (2MB file): {FileHasher.hash_file_fast(large_content, len(large_content))}")
