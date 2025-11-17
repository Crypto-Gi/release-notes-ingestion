"""Google Gemini embedding backend implementation"""

import logging
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from ..embedding_backend import EmbeddingBackend

logger = logging.getLogger(__name__)


class GeminiBackend(EmbeddingBackend):
    """Google Gemini embedding backend using official API"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-embedding-001",
        task_type: str = "RETRIEVAL_DOCUMENT",
        output_dimensionality: Optional[int] = None,
        batch_size: int = 100
    ):
        """
        Initialize Gemini backend
        
        Args:
            api_key: Google API key for Gemini
            model: Gemini model name (default: gemini-embedding-001)
            task_type: Task type for embeddings (RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY, 
                      SEMANTIC_SIMILARITY, CLASSIFICATION, CLUSTERING, QUESTION_ANSWERING,
                      FACT_VERIFICATION, CODE_RETRIEVAL_QUERY)
            output_dimensionality: Custom dimensions (256-768 for gemini-embedding-001, 
                                  default: 768)
            batch_size: Number of texts to send in a single API call (default: 100)
        """
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai package is required for Gemini backend. "
                "Install with: pip install google-generativeai"
            )
        
        self.genai = genai
        # Configure API key
        genai.configure(api_key=api_key)
        self.model = model
        self.task_type = task_type
        self.output_dimensionality = output_dimensionality or 768
        self.batch_size = batch_size
        
        logger.info(f"Gemini backend initialized")
        logger.info(f"  Model: {model}")
        logger.info(f"  Task type: {task_type}")
        logger.info(f"  Dimensions: {self.output_dimensionality}")
        logger.info(f"  Batch size: {self.batch_size}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate_embedding(
        self,
        text: str,
        model: str = None
    ) -> Optional[List[float]]:
        """
        Generate single embedding using Gemini API
        
        Args:
            text: Text to embed
            model: Model name (uses self.model if None)
            
        Returns:
            Embedding vector as list of floats, or None if error
        """
        try:
            result = self.genai.embed_content(
                model=model or self.model,
                content=text,
                task_type=self.task_type,
                output_dimensionality=self.output_dimensionality
            )
            
            # Extract embedding from response
            embedding = result['embedding']
            
            # Convert to list if needed
            if hasattr(embedding, 'tolist'):
                embedding = embedding.tolist()
            elif not isinstance(embedding, list):
                embedding = list(embedding)
            
            logger.debug(f"Generated embedding: {len(embedding)}D vector")
            return embedding
            
        except Exception as e:
            logger.error(f"Gemini embedding error: {e}")
            raise
    
    def generate_batch_embeddings(
        self,
        texts: List[str],
        model: str = None
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts using native batch API
        
        This uses Gemini's native batch support - single API call for all texts.
        Much more efficient than sequential calls.
        
        Args:
            texts: List of texts to embed
            model: Model name (uses self.model if None)
            
        Returns:
            List of embedding vectors (same length as input)
        """
        try:
            logger.info(f"Generating batch embeddings for {len(texts)} texts (native batch, batch_size={self.batch_size})")
            
            all_embeddings = []
            
            # Process in chunks of batch_size
            for i in range(0, len(texts), self.batch_size):
                batch_texts = texts[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
                
                logger.debug(f"Processing batch {batch_num}/{total_batches} ({len(batch_texts)} texts)")
                
                # Native batch: single API call with list of texts
                result = self.genai.embed_content(
                    model=model or self.model,
                    content=batch_texts,  # Pass batch
                    task_type=self.task_type,
                    output_dimensionality=self.output_dimensionality
                )
                
                # Extract embeddings for this batch
                embeddings_data = result.get('embedding', [])
                if not embeddings_data or len(embeddings_data) != len(batch_texts):
                    raise ValueError(
                        f"Batch {batch_num}: Expected {len(batch_texts)} embeddings, got {len(embeddings_data) if embeddings_data else 0}"
                    )
                
                for emb in embeddings_data:
                    # Convert to list if needed
                    if hasattr(emb, 'tolist'):
                        all_embeddings.append(emb.tolist())
                    elif isinstance(emb, list):
                        all_embeddings.append(emb)
                    else:
                        all_embeddings.append(list(emb))
                
                if batch_num % 5 == 0 or batch_num == total_batches:
                    logger.info(f"Processed {len(all_embeddings)}/{len(texts)} embeddings")
            
            logger.info(f"Batch embedding complete: {len(all_embeddings)} vectors")
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Gemini batch embedding error: {e}")
            logger.warning("Falling back to sequential embedding generation")
            
            # Fallback to sequential if batch fails
            embeddings = []
            for i, text in enumerate(texts):
                try:
                    emb = self.generate_embedding(text, model)
                    embeddings.append(emb)
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"Generated {i + 1}/{len(texts)} embeddings (fallback)")
                except Exception as seq_error:
                    logger.error(f"Failed to embed text {i}: {seq_error}")
                    embeddings.append(None)
            
            return embeddings
    
    def health_check(self) -> bool:
        """
        Check if Gemini API is accessible
        
        Returns:
            True if service is available
        """
        try:
            # Try a simple embedding request
            test_embedding = self.generate_embedding("test", self.model)
            return test_embedding is not None and len(test_embedding) > 0
        except Exception as e:
            logger.error(f"Gemini health check failed: {e}")
            return False
    
    def get_model_dimensions(self, model: str) -> int:
        """
        Get embedding dimensions for Gemini model
        
        Args:
            model: Model name
            
        Returns:
            Number of dimensions (uses configured output_dimensionality)
        """
        return self.output_dimensionality
