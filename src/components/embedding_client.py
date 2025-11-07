"""Ollama embedding client for generating vector embeddings"""

import requests
from typing import List, Optional
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

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
        dimensions: Optional[int] = None
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
        """
        self.base_url = f"http://{host}:{port}"
        self.filename_model = filename_model
        self.content_model = content_model
        self.truncate = truncate
        self.keep_alive = keep_alive
        self.dimensions = dimensions
        
        logger.info(f"Embedding client initialized: {self.base_url}")
        logger.info(f"  Filename model: {filename_model}")
        logger.info(f"  Content model: {content_model}")
        if truncate is not None:
            logger.info(f"  Truncate: {truncate}")
        if keep_alive is not None:
            logger.info(f"  Keep alive: {keep_alive}")
        if dimensions is not None:
            logger.info(f"  Dimensions override: {dimensions}")
    
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
        url = f"{self.base_url}/api/embed"
        
        try:
            # Build request payload with only specified parameters
            payload = {
                "model": model,
                "input": text
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
            # New API returns embeddings array, get first one
            embeddings = data.get('embeddings', [])
            
            if not embeddings or len(embeddings) == 0:
                raise ValueError("No embeddings in response")
            
            embedding = embeddings[0]
            logger.debug(f"Generated embedding: {len(embedding)}D vector")
            return embedding
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def generate_filename_embedding(self, filename: str) -> Optional[List[float]]:
        """
        Generate embedding for filename
        
        Args:
            filename: Filename to embed
            
        Returns:
            Embedding vector (dimensions depend on model), or None if error
        """
        try:
            embedding = self._generate_embedding(filename, self.filename_model)
            
            if embedding:
                logger.debug(f"Generated filename embedding: {len(embedding)}D vector")
            
            logger.info(f"Generated filename embedding: {filename}")
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
