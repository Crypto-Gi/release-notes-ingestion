"""Configuration loader for the ingestion pipeline"""

import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class R2Config(BaseModel):
    """Cloudflare R2 configuration"""
    endpoint: str = Field(..., description="R2 endpoint URL")
    access_key: str = Field(..., description="R2 access key")
    secret_key: str = Field(..., description="R2 secret key")
    bucket_name: str = Field(..., description="R2 bucket name")
    source_prefix: str = Field(default="source/", description="Source files prefix")
    markdown_prefix: str = Field(default="markdown/", description="Markdown files prefix")


class QdrantConfig(BaseModel):
    """Qdrant configuration"""
    host: str = Field(..., description="Qdrant host")
    port: int = Field(default=6333, description="Qdrant port")
    
    # Production support
    use_https: bool = Field(default=False, description="Use HTTPS connection")
    api_key: Optional[str] = Field(default=None, description="API key for authentication")
    
    # Optional: gRPC support for better performance
    grpc_port: Optional[int] = Field(default=None, description="gRPC port (optional)")
    prefer_grpc: bool = Field(default=False, description="Prefer gRPC over HTTP")
    
    # Collection names
    filename_collection: str = Field(
        default="filename-granite-embedding30m",
        description="Filename collection name"
    )
    content_collection: str = Field(
        default="releasenotes-bge-m3",
        description="Content collection name"
    )


class OllamaConfig(BaseModel):
    """Ollama configuration"""
    host: str = Field(..., description="Ollama host")
    port: int = Field(default=11434, description="Ollama port")
    filename_model: str = Field(
        default="granite-embedding:30m",
        description="Filename embedding model"
    )
    content_model: str = Field(
        default="bge-m3",
        description="Content embedding model"
    )
    # Optional embedding parameters (use Ollama defaults if None)
    truncate: Optional[bool] = Field(default=None, description="Truncate input to fit context")
    keep_alive: Optional[str] = Field(default=None, description="Model memory retention duration")
    dimensions: Optional[int] = Field(default=None, description="Override embedding dimensions")


class DoclingConfig(BaseModel):
    """Docling service configuration"""
    base_url: str = Field(..., description="Docling service base URL")
    timeout: int = Field(default=300, description="Request timeout in seconds")
    poll_interval: int = Field(default=2, description="Status poll interval in seconds")


class ChunkingConfig(BaseModel):
    """Chunking configuration"""
    chunk_size_tokens: int = Field(default=500, description="Chunk size in tokens")
    chunk_overlap_tokens: int = Field(default=0, description="Chunk overlap in tokens")


class LogConfig(BaseModel):
    """Logging configuration"""
    log_dir: str = Field(default="logs/", description="Log directory")
    conversion_log: str = Field(default="conversion.json", description="Conversion log filename")
    upload_log: str = Field(default="upload.json", description="Upload log filename")
    failed_log: str = Field(default="failed.json", description="Failed files log filename")


class ProcessingConfig(BaseModel):
    """File processing configuration"""
    skip_extensions: list[str] = Field(
        default_factory=list,
        description="List of file extensions to skip (e.g., ['.DS_Store', '.tmp'])"
    )


class PipelineConfig(BaseModel):
    """Complete pipeline configuration"""
    r2: R2Config
    qdrant: QdrantConfig
    ollama: OllamaConfig
    docling: DoclingConfig
    chunking: ChunkingConfig
    log: LogConfig
    processing: ProcessingConfig


def load_config(env_file: Optional[str] = None) -> PipelineConfig:
    """
    Load configuration from environment variables
    
    Args:
        env_file: Optional path to .env file
        
    Returns:
        PipelineConfig: Complete pipeline configuration
        
    Raises:
        ValueError: If required environment variables are missing
    """
    # Load environment variables
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()
    
    # R2 Configuration
    r2_config = R2Config(
        endpoint=os.getenv("R2_ENDPOINT", ""),
        access_key=os.getenv("R2_ACCESS_KEY", ""),
        secret_key=os.getenv("R2_SECRET_KEY", ""),
        bucket_name=os.getenv("R2_BUCKET_NAME", ""),
        source_prefix=os.getenv("R2_SOURCE_PREFIX", "source/"),
        markdown_prefix=os.getenv("R2_MARKDOWN_PREFIX", "markdown/")
    )
    
    # Qdrant Configuration
    qdrant_config = QdrantConfig(
        host=os.getenv("QDRANT_HOST", ""),
        port=int(os.getenv("QDRANT_PORT", "6333")),
        use_https=os.getenv("QDRANT_USE_HTTPS", "false").lower() == "true",
        api_key=os.getenv("QDRANT_API_KEY") or None,
        grpc_port=int(os.getenv("QDRANT_GRPC_PORT")) if os.getenv("QDRANT_GRPC_PORT") else None,
        prefer_grpc=os.getenv("QDRANT_PREFER_GRPC", "false").lower() == "true",
        filename_collection=os.getenv("QDRANT_FILENAME_COLLECTION", "filename-granite-embedding30m"),
        content_collection=os.getenv("QDRANT_CONTENT_COLLECTION", "releasenotes-bge-m3")
    )
    
    # Ollama Configuration
    # Helper to parse optional bool from env
    def get_optional_bool(key: str) -> Optional[bool]:
        value = os.getenv(key, "").strip().lower()
        if value in ('true', '1', 'yes'):
            return True
        elif value in ('false', '0', 'no'):
            return False
        return None
    
    # Helper to parse optional int from env
    def get_optional_int(key: str) -> Optional[int]:
        value = os.getenv(key, "").strip()
        if value:
            try:
                return int(value)
            except ValueError:
                return None
        return None
    
    ollama_config = OllamaConfig(
        host=os.getenv("OLLAMA_HOST", ""),
        port=int(os.getenv("OLLAMA_PORT", "11434")),
        filename_model=os.getenv("OLLAMA_FILENAME_MODEL", "granite-embedding:30m"),
        content_model=os.getenv("OLLAMA_CONTENT_MODEL", "bge-m3"),
        truncate=get_optional_bool("OLLAMA_TRUNCATE"),
        keep_alive=os.getenv("OLLAMA_KEEP_ALIVE") or None,
        dimensions=get_optional_int("OLLAMA_DIMENSIONS")
    )
    
    # Docling Configuration
    docling_config = DoclingConfig(
        base_url=os.getenv("DOCLING_BASE_URL", ""),
        timeout=int(os.getenv("DOCLING_TIMEOUT", "300")),
        poll_interval=int(os.getenv("DOCLING_POLL_INTERVAL", "2"))
    )
    
    # Chunking Configuration
    chunking_config = ChunkingConfig(
        chunk_size_tokens=int(os.getenv("CHUNK_SIZE_TOKENS", "500")),
        chunk_overlap_tokens=int(os.getenv("CHUNK_OVERLAP_TOKENS", "0"))
    )
    
    # Log Configuration
    log_config = LogConfig(
        log_dir=os.getenv("LOG_DIR", "logs/"),
        conversion_log=os.getenv("CONVERSION_LOG", "conversion.json"),
        upload_log=os.getenv("UPLOAD_LOG", "upload.json"),
        failed_log=os.getenv("FAILED_LOG", "failed.json")
    )
    
    # Processing Configuration
    skip_extensions_str = os.getenv("SKIP_EXTENSIONS", "")
    skip_extensions = [ext.strip() for ext in skip_extensions_str.split(",") if ext.strip()]
    processing_config = ProcessingConfig(
        skip_extensions=skip_extensions
    )
    
    return PipelineConfig(
        r2=r2_config,
        qdrant=qdrant_config,
        ollama=ollama_config,
        docling=docling_config,
        chunking=chunking_config,
        log=log_config,
        processing=processing_config
    )


if __name__ == "__main__":
    # Test configuration loading
    config = load_config()
    print("Configuration loaded successfully:")
    print(f"R2 Bucket: {config.r2.bucket_name}")
    print(f"Qdrant Host: {config.qdrant.host}:{config.qdrant.port}")
    print(f"Ollama Host: {config.ollama.host}:{config.ollama.port}")
    print(f"Docling URL: {config.docling.base_url}")
