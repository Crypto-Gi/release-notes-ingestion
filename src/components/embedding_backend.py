"""Abstract base class for embedding backends"""

from abc import ABC, abstractmethod
from typing import List, Optional


class EmbeddingBackend(ABC):
    """Abstract base class for embedding backends (Ollama, Gemini, etc.)"""
    
    @abstractmethod
    def generate_embedding(self, text: str, model: str) -> Optional[List[float]]:
        """
        Generate single embedding for text
        
        Args:
            text: Text to embed
            model: Model name to use
            
        Returns:
            Embedding vector as list of floats, or None if error
        """
        pass
    
    @abstractmethod
    def generate_batch_embeddings(
        self,
        texts: List[str],
        model: str
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            model: Model name to use
            
        Returns:
            List of embedding vectors (same length as input)
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if backend service is healthy and reachable
        
        Returns:
            True if service is available
        """
        pass
    
    @abstractmethod
    def get_model_dimensions(self, model: str) -> int:
        """
        Get embedding dimensions for a specific model
        
        Args:
            model: Model name
            
        Returns:
            Number of dimensions in embedding vector
        """
        pass
