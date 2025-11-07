"""Qdrant uploader for vector database operations"""

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from typing import List, Optional
import uuid
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class QdrantUploader:
    """Upload embeddings and metadata to Qdrant collections"""
    
    def __init__(
        self,
        host: str,
        port: int = 6333,
        filename_collection: str = "filename-granite-embedding30m",
        content_collection: str = "releasenotes-bge-m3"
    ):
        """
        Initialize Qdrant uploader
        
        Args:
            host: Qdrant host
            port: Qdrant port
            filename_collection: Filename collection name
            content_collection: Content collection name
        """
        self.client = QdrantClient(host=host, port=port)
        self.filename_collection = filename_collection
        self.content_collection = content_collection
        
        logger.info(f"Qdrant uploader initialized: {host}:{port}")
        logger.info(f"  Filename collection: {filename_collection}")
        logger.info(f"  Content collection: {content_collection}")
        
        # Verify collections exist
        self._verify_collections()
    
    def _verify_collections(self):
        """Verify that required collections exist"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.filename_collection not in collection_names:
                logger.warning(f"Collection not found: {self.filename_collection}")
            
            if self.content_collection not in collection_names:
                logger.warning(f"Collection not found: {self.content_collection}")
                
        except Exception as e:
            logger.error(f"Error verifying collections: {e}")
    
    def upload_filename(
        self,
        filename: str,
        embedding: List[float],
        file_hash: str
    ) -> bool:
        """
        Upload filename to filename collection
        
        Args:
            filename: Filename with extension (e.g., "file.pdf")
            embedding: Embedding vector from filename model
            file_hash: Lightweight hash (xxHash or CRC32)
            
        Returns:
            True if successful
        """
        try:
            # Generate UUID based on filename
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, filename))
            
            # Create point
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "pagecontent": filename,  # Keep extension
                    "source": filename,        # Same as pagecontent
                    "metadata": {
                        "hash": file_hash
                    }
                }
            )
            
            # Upload to Qdrant
            self.client.upsert(
                collection_name=self.filename_collection,
                points=[point]
            )
            
            logger.info(f"Uploaded filename: {filename} (ID: {point_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading filename: {e}")
            return False
    
    def upload_content_chunks(
        self,
        filename: str,
        chunks: List,  # List of Chunk objects
        embeddings: List[List[float]]
    ) -> bool:
        """
        Upload content chunks to content collection
        
        Args:
            filename: Source filename with extension
            chunks: List of Chunk objects
            embeddings: List of embedding vectors from content model
            
        Returns:
            True if successful
        """
        if len(chunks) != len(embeddings):
            logger.error(f"Mismatch: {len(chunks)} chunks, {len(embeddings)} embeddings")
            return False
        
        try:
            points = []
            
            for chunk, embedding in zip(chunks, embeddings):
                if embedding is None:
                    logger.warning(f"Skipping chunk {chunk.chunk_number} - no embedding")
                    continue
                
                # Generate UUID based on filename + chunk number
                point_id = str(uuid.uuid5(
                    uuid.NAMESPACE_DNS,
                    f"{filename}_{chunk.chunk_number}"
                ))
                
                # Create point
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "pagecontent": chunk.text,
                        "metadata": {
                            "filename": filename,  # Keep extension
                            "page_number": chunk.chunk_number,
                            "element_type": chunk.element_type,
                            "md5_hash": chunk.md5_hash
                        }
                    }
                )
                
                points.append(point)
            
            if not points:
                logger.warning("No valid points to upload")
                return False
            
            # Upload to Qdrant in batches
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=self.content_collection,
                    points=batch
                )
                logger.debug(f"Uploaded batch {i // batch_size + 1}: {len(batch)} points")
            
            logger.info(f"Uploaded {len(points)} content chunks for {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading content chunks: {e}")
            return False
    
    def collection_exists(self, collection_name: str) -> bool:
        """
        Check if collection exists
        
        Args:
            collection_name: Collection name
            
        Returns:
            True if exists
        """
        try:
            collections = self.client.get_collections().collections
            return collection_name in [c.name for c in collections]
        except:
            return False
    
    def get_collection_info(self, collection_name: str) -> Optional[dict]:
        """
        Get collection information
        
        Args:
            collection_name: Collection name
            
        Returns:
            Collection info dict or None
        """
        try:
            info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return None
    
    def health_check(self) -> bool:
        """
        Check if Qdrant is healthy
        
        Returns:
            True if healthy
        """
        try:
            self.client.get_collections()
            return True
        except:
            return False


if __name__ == "__main__":
    # Test Qdrant uploader
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    host = os.getenv("QDRANT_HOST", "192.168.254.22")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    
    uploader = QdrantUploader(host=host, port=int(port))
    
    # Health check
    if uploader.health_check():
        print("✅ Qdrant is healthy")
        
        # Get collection info
        filename_info = uploader.get_collection_info(uploader.filename_collection)
        if filename_info:
            print(f"\nFilename collection:")
            print(f"  Points: {filename_info['points_count']}")
            print(f"  Status: {filename_info['status']}")
        
        content_info = uploader.get_collection_info(uploader.content_collection)
        if content_info:
            print(f"\nContent collection:")
            print(f"  Points: {content_info['points_count']}")
            print(f"  Status: {content_info['status']}")
    else:
        print("❌ Qdrant is not reachable")
