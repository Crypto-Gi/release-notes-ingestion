"""Ollama embedding backend implementation"""

import requests
import logging
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from ..embedding_backend import EmbeddingBackend

logger = logging.getLogger(__name__)


class OllamaBackend(EmbeddingBackend):
    """Ollama embedding backend using local Ollama server"""
    
    def __init__(
        self,
        host: str,
        port: int = 11434,
        truncate: Optional[bool] = None,
        keep_alive: Optional[str] = None,
        dimensions: Optional[int] = None,
        batch_size: int = 100
    ):
        """
        Initialize Ollama backend
        
        Args:
            host: Ollama server host
            port: Ollama server port
            truncate: Truncate input to fit context (default: Ollama default=true)
            keep_alive: How long to keep model in memory (default: Ollama default=5m)
            dimensions: Override embedding dimensions (default: model's native dimensions)
        """
        self.base_url = f"http://{host}:{port}"
        self.truncate = truncate
        self.keep_alive = keep_alive
        self.dimensions = dimensions
        self.batch_size = batch_size
        
        logger.info(f"Ollama backend initialized: {self.base_url}")
        if truncate is not None:
            logger.info(f"  Truncate: {truncate}")
        if keep_alive is not None:
            logger.info(f"  Keep alive: {keep_alive}")
        if dimensions is not None:
            logger.info(f"  Dimensions override: {dimensions}")
        logger.info(f"  Batch size: {batch_size}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate_embedding(
        self,
        text: str,
        model: str
    ) -> Optional[List[float]]:
        """
        Generate embedding for text using Ollama
        
        Args:
            text: Text to embed
            model: Ollama model name
            
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
    
    def generate_batch_embeddings(
        self,
        texts: List[str],
        model: str
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts using native batch API
        
        Ollama's /api/embed endpoint supports batch processing by passing
        an array of strings in the 'input' field.
        
        Args:
            texts: List of texts to embed
            model: Ollama model name
            
        Returns:
            List of embedding vectors (same length as input)
        """
        logger.info(f"Generating batch embeddings for {len(texts)} texts (native batch, batch_size={self.batch_size})")
        
        all_embeddings = []
        
        # Process in chunks of batch_size
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
            
            logger.debug(f"Processing batch {batch_num}/{total_batches} ({len(batch_texts)} texts)")
            
            try:
                # Use /api/embed endpoint with array input for native batch support
                url = f"{self.base_url}/api/embed"
                
                payload = {
                    "model": model,
                    "input": batch_texts  # Pass array of texts
                }
                
                # Add optional parameters
                if self.truncate is not None:
                    payload["truncate"] = self.truncate
                if self.keep_alive is not None:
                    payload["keep_alive"] = self.keep_alive
                if self.dimensions is not None:
                    payload["dimensions"] = self.dimensions
                
                response = requests.post(url, json=payload, timeout=60)
                response.raise_for_status()
                
                data = response.json()
                batch_embeddings = data.get('embeddings', [])
                
                if len(batch_embeddings) != len(batch_texts):
                    raise ValueError(
                        f"Batch {batch_num}: Expected {len(batch_texts)} embeddings, got {len(batch_embeddings)}"
                    )
                
                all_embeddings.extend(batch_embeddings)
                
                if batch_num % 5 == 0 or batch_num == total_batches:
                    logger.info(f"Processed {len(all_embeddings)}/{len(texts)} embeddings")
                    
            except Exception as e:
                logger.error(f"Batch {batch_num} failed: {e}")
                # Fallback to sequential for this batch
                logger.warning(f"Falling back to sequential for batch {batch_num}")
                for text in batch_texts:
                    try:
                        emb = self.generate_embedding(text, model)
                        all_embeddings.append(emb)
                    except Exception as seq_error:
                        logger.error(f"Sequential embedding failed: {seq_error}")
                        all_embeddings.append(None)
        
        logger.info(f"Batch embedding complete: {len(all_embeddings)} vectors")
        return all_embeddings
    
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
    
    def get_model_dimensions(self, model: str) -> int:
        """
        Get embedding dimensions for Ollama model
        
        Args:
            model: Model name
            
        Returns:
            Number of dimensions (uses override if set, otherwise model default)
        """
        if self.dimensions:
            return self.dimensions
        
        # Default dimensions for known models
        if "granite-embedding:30m" in model:
            return 384
        elif "bge-m3" in model:
            return 1024
        else:
            # Try to infer from model response
            logger.warning(f"Unknown model dimensions for {model}, defaulting to 768")
            return 768
    
    def list_models(self) -> List[str]:
        """
        List available Ollama models
        
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
