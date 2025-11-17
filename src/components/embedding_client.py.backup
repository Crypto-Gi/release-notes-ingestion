"""Ollama embedding client for generating vector embeddings"""

import requests
from typing import List, Optional, TYPE_CHECKING
import logging
import time
from tenacity import retry, stop_after_attempt, wait_exponential

if TYPE_CHECKING:
    from .log_manager import LogManager
    from .file_hasher import FileHasher

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """Client for generating embeddings via Ollama"""
    
    def __init__(
        self,
        host: str,
        port: int = 11434,
        filename_model: str = "granite-embedding:30m",
        content_model: str = "bge-m3",
        truncate: Optional[bool] = None,
        keep_alive: Optional[str] = None,
        dimensions: Optional[int] = None,
        log_manager: Optional["LogManager"] = None,
        enable_deduplication: bool = True,
        enable_logging: bool = True
    ):
        """
        Initialize embedding client
        
        Args:
            host: Ollama host
            port: Ollama port
            filename_model: Model for filename embeddings
            content_model: Model for content embeddings
            truncate: Truncate input to fit context (default: Ollama default=true)
            keep_alive: How long to keep model in memory (default: Ollama default=5m)
            dimensions: Override embedding dimensions (default: model's native dimensions)
            log_manager: LogManager instance for Phase 3 logging (optional)
            enable_deduplication: Enable deduplication checks (default: True)
            enable_logging: Enable Phase 3 logging (default: True)
        """
        self.base_url = f"http://{host}:{port}"
        self.filename_model = filename_model
        self.content_model = content_model
        self.truncate = truncate
        self.keep_alive = keep_alive
        self.dimensions = dimensions
        
        # Phase 3: Logging and deduplication
        self.log_manager = log_manager
        self.enable_deduplication = enable_deduplication
        self.enable_logging = enable_logging
        
        logger.info(f"Embedding client initialized: {self.base_url}")
        logger.info(f"  Filename model: {filename_model}")
        logger.info(f"  Content model: {content_model}")
        if truncate is not None:
            logger.info(f"  Truncate: {truncate}")
        if keep_alive is not None:
            logger.info(f"  Keep alive: {keep_alive}")
        if dimensions is not None:
            logger.info(f"  Dimensions override: {dimensions}")
        if log_manager:
            logger.info(f"  Phase 3 logging: enabled")
            logger.info(f"  Deduplication: {'enabled' if enable_deduplication else 'disabled'}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _generate_embedding(
        self,
        text: str,
        model: str
    ) -> Optional[List[float]]:
        """
        Generate embedding for text using specified model
        
        Args:
            text: Text to embed
            model: Model name
            
        Returns:
            Embedding vector as list of floats, or None if error
        """
        # Try old API endpoint first (/api/embed), fallback to new (/api/embeddings)
        # Old endpoint is more reliable across Ollama versions
        endpoints = ["/api/embed", "/api/embeddings"]
        
        for endpoint in endpoints:
            url = f"{self.base_url}{endpoint}"
            logger.debug(f"Trying endpoint: {endpoint}")
            
            try:
                # Build request payload based on endpoint
                if endpoint == "/api/embed":
                    # New API format
                    payload = {
                        "model": model,
                        "input": text
                    }
                else:
                    # Old API format (/api/embeddings)
                    payload = {
                        "model": model,
                        "prompt": text
                    }
                
                # Add optional parameters only if specified
                if self.truncate is not None:
                    payload["truncate"] = self.truncate
                
                if self.keep_alive is not None:
                    payload["keep_alive"] = self.keep_alive
                
                if self.dimensions is not None:
                    payload["dimensions"] = self.dimensions
                
                response = requests.post(
                    url,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                # Handle both API response formats:
                # - Old API: {"embeddings": [[...]]}  (plural, nested array)
                # - New API: {"embedding": [...]}     (singular, flat array)
                embedding = data.get('embedding')  # Try new format first
                if embedding is None:
                    # Fall back to old format
                    embeddings = data.get('embeddings', [])
                    if not embeddings or len(embeddings) == 0:
                        raise ValueError("No embeddings in response")
                    embedding = embeddings[0]
                
                if not embedding or len(embedding) == 0:
                    raise ValueError("Empty embedding vector in response")
                
                logger.debug(f"Generated embedding: {len(embedding)}D vector using {endpoint}")
                return embedding
                
            except requests.exceptions.HTTPError as e:
                # If 404, try next endpoint
                if e.response.status_code == 404 and endpoint != endpoints[-1]:
                    logger.debug(f"Endpoint {endpoint} not found, trying next...")
                    continue
                logger.error(f"Error generating embedding: {e}")
                raise
            except requests.exceptions.RequestException as e:
                logger.error(f"Error generating embedding: {e}")
                raise
    
    def generate_filename_embedding(
        self,
        filename: str,
        file_content: Optional[bytes] = None,
        collection_name: Optional[str] = None,
        log_to_phase3: bool = False
    ) -> Optional[List[float]]:
        """
        Generate embedding for filename
        
        Args:
            filename: Filename to embed
            file_content: Optional file content for Phase 3 logging (for hash calculation)
            collection_name: Optional collection name for Phase 3 logging
            log_to_phase3: Enable Phase 3 logging (requires file_content and collection_name)
            
        Returns:
            Embedding vector (dimensions depend on model), or None if error
        """
        try:
            import time
            start_time = time.time()
            
            embedding = self._generate_embedding(filename, self.filename_model)
            
            if embedding:
                logger.debug(f"Generated filename embedding: {len(embedding)}D vector")
            
            logger.info(f"Generated filename embedding: {filename}")
            
            # Phase 3: Log filename embedding if enabled
            if log_to_phase3 and self.enable_logging and self.log_manager and file_content and collection_name:
                from .file_hasher import FileHasher
                file_hash = FileHasher.hash_file_lightweight(file_content)
                embedding_time = time.time() - start_time
                
                self.log_manager.log_embedding_success(
                    filename=filename,
                    md5_hash=file_hash,
                    collection_name=collection_name,
                    chunks_created=1,  # Filename is 1 "chunk"
                    embedding_time=embedding_time,
                    model_name=self.filename_model
                )
                logger.debug(f"✅ Logged filename embedding to Phase 3: {filename}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate filename embedding: {e}")
            return None
    
    def generate_content_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for content chunk
        
        Args:
            text: Content text to embed
            
        Returns:
            Embedding vector (dimensions depend on model), or None if error
        """
        try:
            embedding = self._generate_embedding(text, self.content_model)
            
            if embedding:
                logger.debug(f"Generated content embedding: {len(embedding)}D vector")
            
            logger.debug(f"Generated content embedding: {len(text)} chars")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate content embedding: {e}")
            return None
    
    def generate_batch_embeddings(
        self,
        texts: List[str],
        model_type: str = "content"
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            model_type: "filename" or "content"
            
        Returns:
            List of embedding vectors (same length as input)
        """
        embeddings = []
        
        for i, text in enumerate(texts):
            if model_type == "filename":
                emb = self.generate_filename_embedding(text)
            else:
                emb = self.generate_content_embedding(text)
            
            embeddings.append(emb)
            
            if (i + 1) % 10 == 0:
                logger.info(f"Generated {i + 1}/{len(texts)} embeddings")
        
        logger.info(f"Batch embedding complete: {len(embeddings)} vectors")
        return embeddings
    
    # ============================================
    # Phase 3: Enhanced Batch Embedding with Deduplication
    # ============================================
    
    def generate_batch_embeddings_with_dedup(
        self,
        filename: str,
        file_content: bytes,
        chunks: List[str],
        collection_name: str,
        model_type: str = "content",
        qdrant_client = None,
        force_reprocess: bool = False
    ) -> Optional[List[Optional[List[float]]]]:
        """
        Generate embeddings for chunks with deduplication and logging
        
        Args:
            filename: Name of the source file
            file_content: Raw file content for hashing
            chunks: List of text chunks to embed
            collection_name: Target Qdrant collection
            model_type: "filename" or "content"
            qdrant_client: QdrantClient instance for deduplication check (optional)
            force_reprocess: Skip deduplication checks (default: False)
            
        Returns:
            List of embedding vectors, or None if skipped due to deduplication
        """
        from .file_hasher import FileHasher
        
        # Calculate xxHash for deduplication
        file_hash = FileHasher.hash_file_lightweight(file_content)
        
        # Phase 3: Deduplication check
        if self.enable_deduplication and not force_reprocess and self.log_manager:
            # Check 1: Embedding log (check by collection to avoid false positives)
            if self.log_manager.check_embedding_exists(file_hash, collection_name):
                logger.info(f"⏭️  Skipping {filename} - already embedded in '{collection_name}' (log)")
                
                if self.enable_logging:
                    self.log_manager.log_skipped_file(
                        filename=filename,
                        md5_hash=file_hash,
                        skip_reason="already_embedded",
                        found_in="log_file",
                        collection_name=collection_name
                    )
                
                return None
            
            # Check 2: Qdrant collection
            if qdrant_client and self.log_manager.check_qdrant_exists(
                qdrant_client, collection_name, file_hash
            ):
                logger.info(f"⏭️  Skipping {filename} - already in Qdrant")
                
                if self.enable_logging:
                    self.log_manager.log_skipped_file(
                        filename=filename,
                        md5_hash=file_hash,
                        skip_reason="already_in_qdrant",
                        found_in="qdrant_collection",
                        collection_name=collection_name
                    )
                
                return None
        
        # Generate embeddings
        logger.info(f"🔄 Generating embeddings for {filename} ({len(chunks)} chunks)")
        start_time = time.time()
        
        embeddings = self.generate_batch_embeddings(chunks, model_type)
        
        embedding_time = time.time() - start_time
        
        # Phase 3: Log embedding success
        if self.enable_logging and self.log_manager:
            model_name = self.content_model if model_type == "content" else self.filename_model
            
            self.log_manager.log_embedding_success(
                filename=filename,
                md5_hash=file_hash,
                collection_name=collection_name,
                chunks_created=len(chunks),
                embedding_time=embedding_time,
                model_name=model_name
            )
        
        logger.info(f"✅ Generated {len(embeddings)} embeddings in {embedding_time:.2f}s")
        return embeddings
    
    def health_check(self) -> bool:
        """
        Check if Ollama service is healthy
        
        Returns:
            True if service is reachable
        """
        try:
            url = f"{self.base_url}/api/tags"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> List[str]:
        """
        List available models
        
        Returns:
            List of model names
        """
        try:
            url = f"{self.base_url}/api/tags"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            
            logger.info(f"Available models: {models}")
            return models
            
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []


if __name__ == "__main__":
    # Test embedding client
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    host = os.getenv("OLLAMA_HOST", "192.168.254.22")
    port = int(os.getenv("OLLAMA_PORT", "11434"))
    
    client = EmbeddingClient(host=host, port=int(port))
    
    # Health check
    if client.health_check():
        print("✅ Ollama service is healthy")
        
        # List models
        models = client.list_models()
        print(f"Available models: {models}")
        
        # Test filename embedding
        filename_emb = client.generate_filename_embedding("test_file.pdf")
        if filename_emb:
            print(f"✅ Filename embedding: {len(filename_emb)}D")
        
        # Test content embedding
        content_emb = client.generate_content_embedding("This is test content")
        if content_emb:
            print(f"✅ Content embedding: {len(content_emb)}D")
    else:
        print("❌ Ollama service is not reachable")
