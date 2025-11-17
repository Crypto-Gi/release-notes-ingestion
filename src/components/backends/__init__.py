"""Embedding backend implementations"""

from .ollama_backend import OllamaBackend
from .gemini_backend import GeminiBackend

__all__ = ["OllamaBackend", "GeminiBackend"]
