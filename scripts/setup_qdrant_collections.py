#!/usr/bin/env python3
"""
Flexible Qdrant Collection Setup Script

Creates Qdrant collections based on .env configuration with full customization support.
All settings are read from environment variables with sensible defaults.

Features:
- Fully configurable via .env file
- Supports custom collection names
- Configurable vector dimensions and distance metrics
- Optional text indexing with multiple tokenizer types
- HNSW index tuning
- Validates Ollama embedding dimensions

Usage:
    # Use .env configuration
    python scripts/setup_qdrant_collections.py
    
    # Override specific settings
    python scripts/setup_qdrant_collections.py --host 192.168.254.22 --port 6333
    
    # Dry run (show configuration without creating)
    python scripts/setup_qdrant_collections.py --dry-run
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    TextIndexParams,
    TokenizerType,
    OptimizersConfigDiff,
    HnswConfigDiff
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Distance metric mapping
DISTANCE_METRICS = {
    "Cosine": Distance.COSINE,
    "Euclid": Distance.EUCLID,
    "Dot": Distance.DOT,
    "Manhattan": Distance.MANHATTAN
}

# Tokenizer type mapping
TOKENIZER_TYPES = {
    "word": TokenizerType.WORD,
    "whitespace": TokenizerType.WHITESPACE,
    "prefix": TokenizerType.PREFIX,
    "multilingual": TokenizerType.MULTILINGUAL
}


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean from environment variable"""
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')


def get_env_int(key: str, default: int) -> int:
    """Get integer from environment variable"""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        logger.warning(f"Invalid integer for {key}, using default: {default}")
        return default


def get_env_str(key: str, default: str) -> str:
    """Get string from environment variable"""
    return os.getenv(key, default)


def load_collection_config(prefix: str) -> Dict[str, Any]:
    """
    Load collection configuration from environment variables
    
    Args:
        prefix: Environment variable prefix (e.g., 'QDRANT_FILENAME' or 'QDRANT_CONTENT')
    
    Returns:
        Dictionary with collection configuration
    """
    config = {
        # Vector configuration
        'vector_size': get_env_int(f'{prefix}_VECTOR_SIZE', 384 if 'FILENAME' in prefix else 1024),
        'distance': get_env_str(f'{prefix}_DISTANCE', 'Cosine'),
        
        # Text indexing
        'text_index': get_env_bool(f'{prefix}_TEXT_INDEX', 'FILENAME' in prefix),
        'tokenizer': get_env_str(f'{prefix}_TOKENIZER', 'word'),
        'min_token_len': get_env_int(f'{prefix}_MIN_TOKEN_LEN', 1),
        'max_token_len': get_env_int(f'{prefix}_MAX_TOKEN_LEN', 15),
        'lowercase': get_env_bool(f'{prefix}_LOWERCASE', True),
        
        # HNSW configuration
        'hnsw_m': get_env_int(f'{prefix}_HNSW_M', 16),
        'hnsw_ef_construct': get_env_int(f'{prefix}_HNSW_EF_CONSTRUCT', 100),
        'hnsw_full_scan_threshold': get_env_int(f'{prefix}_HNSW_FULL_SCAN_THRESHOLD', 10000),
        'hnsw_on_disk': get_env_bool(f'{prefix}_HNSW_ON_DISK', False),
    }
    
    return config


def validate_ollama_dimensions(
    client: QdrantClient,
    model_name: str,
    expected_dims: int,
    ollama_host: str,
    ollama_port: int
) -> bool:
    """
    Validate that Ollama model produces embeddings with expected dimensions
    
    Args:
        client: Qdrant client (not used, but kept for consistency)
        model_name: Ollama model name
        expected_dims: Expected embedding dimensions
        ollama_host: Ollama server host
        ollama_port: Ollama server port
    
    Returns:
        True if dimensions match, False otherwise
    """
    try:
        import requests
        
        # Test embedding generation
        response = requests.post(
            f"http://{ollama_host}:{ollama_port}/api/embed",
            json={
                "model": model_name,
                "input": "test"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'embeddings' in data and len(data['embeddings']) > 0:
                actual_dims = len(data['embeddings'][0])
                
                if actual_dims == expected_dims:
                    logger.info(f"✅ Model '{model_name}' produces {actual_dims}D embeddings (matches expected {expected_dims}D)")
                    return True
                else:
                    logger.error(f"❌ Model '{model_name}' produces {actual_dims}D embeddings, but collection expects {expected_dims}D!")
                    logger.error(f"   Update QDRANT_*_VECTOR_SIZE in .env to {actual_dims} or use a different model")
                    return False
        else:
            logger.warning(f"⚠️  Could not validate model '{model_name}': HTTP {response.status_code}")
            logger.warning(f"   Proceeding anyway, but verify manually that model produces {expected_dims}D embeddings")
            return True
            
    except Exception as e:
        logger.warning(f"⚠️  Could not validate model '{model_name}': {e}")
        logger.warning(f"   Proceeding anyway, but verify manually that model produces {expected_dims}D embeddings")
        return True


def create_collection(
    client: QdrantClient,
    collection_name: str,
    config: Dict[str, Any],
    shard_number: int,
    replication_factor: int,
    write_consistency_factor: int,
    on_disk_payload: bool
) -> bool:
    """
    Create a Qdrant collection with specified configuration
    
    Args:
        client: Qdrant client
        collection_name: Name of the collection
        config: Collection configuration dictionary
        shard_number: Number of shards
        replication_factor: Replication factor
        write_consistency_factor: Write consistency factor
        on_disk_payload: Store payload on disk
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if collection exists
        collections = client.get_collections().collections
        if any(c.name == collection_name for c in collections):
            logger.info(f"✅ Collection '{collection_name}' already exists")
            return True
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Creating collection: {collection_name}")
        logger.info(f"{'='*60}")
        
        # Validate distance metric
        distance_str = config['distance']
        if distance_str not in DISTANCE_METRICS:
            logger.error(f"❌ Invalid distance metric: {distance_str}")
            logger.error(f"   Valid options: {', '.join(DISTANCE_METRICS.keys())}")
            return False
        
        distance = DISTANCE_METRICS[distance_str]
        
        # Log configuration
        logger.info(f"Vector Configuration:")
        logger.info(f"  Size: {config['vector_size']}D")
        logger.info(f"  Distance: {distance_str}")
        logger.info(f"  Shards: {shard_number}")
        logger.info(f"  Replication: {replication_factor}")
        logger.info(f"  On-disk payload: {on_disk_payload}")
        
        logger.info(f"\nHNSW Configuration:")
        logger.info(f"  M: {config['hnsw_m']}")
        logger.info(f"  EF Construct: {config['hnsw_ef_construct']}")
        logger.info(f"  Full Scan Threshold: {config['hnsw_full_scan_threshold']}")
        logger.info(f"  On-disk: {config['hnsw_on_disk']}")
        
        # Create collection with vector configuration
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=config['vector_size'],
                distance=distance,
                on_disk=config['hnsw_on_disk']
            ),
            shard_number=shard_number,
            replication_factor=replication_factor,
            write_consistency_factor=write_consistency_factor,
            on_disk_payload=on_disk_payload,
            hnsw_config=HnswConfigDiff(
                m=config['hnsw_m'],
                ef_construct=config['hnsw_ef_construct'],
                full_scan_threshold=config['hnsw_full_scan_threshold'],
                on_disk=config['hnsw_on_disk']
            ),
            optimizers_config=OptimizersConfigDiff(
                default_segment_number=2
            )
        )
        
        logger.info(f"✅ Collection '{collection_name}' created")
        
        # Add text indexing if enabled
        if config['text_index']:
            logger.info(f"\nText Indexing Configuration:")
            logger.info(f"  Enabled: true")
            logger.info(f"  Tokenizer: {config['tokenizer']}")
            logger.info(f"  Token length: {config['min_token_len']}-{config['max_token_len']}")
            logger.info(f"  Lowercase: {config['lowercase']}")
            
            # Validate tokenizer
            tokenizer_str = config['tokenizer']
            if tokenizer_str not in TOKENIZER_TYPES:
                logger.error(f"❌ Invalid tokenizer: {tokenizer_str}")
                logger.error(f"   Valid options: {', '.join(TOKENIZER_TYPES.keys())}")
                return False
            
            tokenizer = TOKENIZER_TYPES[tokenizer_str]
            
            # Add text index to pagecontent field
            logger.info(f"\nAdding text index to 'pagecontent' field...")
            client.create_payload_index(
                collection_name=collection_name,
                field_name="pagecontent",
                field_schema=TextIndexParams(
                    type="text",
                    tokenizer=tokenizer,
                    min_token_len=config['min_token_len'],
                    max_token_len=config['max_token_len'],
                    lowercase=config['lowercase']
                )
            )
            logger.info(f"✅ Text index added to 'pagecontent' field")
            
            # Add text index to metadata.filename field
            logger.info(f"Adding text index to 'metadata.filename' field...")
            client.create_payload_index(
                collection_name=collection_name,
                field_name="metadata.filename",
                field_schema=TextIndexParams(
                    type="text",
                    tokenizer=tokenizer,
                    min_token_len=config['min_token_len'],
                    max_token_len=config['max_token_len'],
                    lowercase=config['lowercase']
                )
            )
            logger.info(f"✅ Text index added to 'metadata.filename' field")
        else:
            logger.info(f"\nText Indexing: disabled (pure vector search)")
        
        logger.info(f"\n🎉 Collection '{collection_name}' setup complete!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating collection '{collection_name}': {e}")
        return False


def verify_collection(
    client: QdrantClient,
    collection_name: str,
    expected_config: Dict[str, Any]
) -> bool:
    """Verify collection configuration"""
    try:
        info = client.get_collection(collection_name)
        
        logger.info(f"\n📊 {collection_name}:")
        logger.info(f"  Vector size: {info.config.params.vectors.size}")
        logger.info(f"  Distance: {info.config.params.vectors.distance}")
        logger.info(f"  Points: {info.points_count}")
        logger.info(f"  Status: {info.status}")
        
        # Verify vector size
        if info.config.params.vectors.size != expected_config['vector_size']:
            logger.error(f"  ❌ Wrong vector size! Expected {expected_config['vector_size']}, got {info.config.params.vectors.size}")
            return False
        
        logger.info(f"  ✅ Configuration verified")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verifying collection '{collection_name}': {e}")
        return False


def main():
    """Main setup function"""
    # Load environment variables
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="Setup Qdrant collections with flexible configuration from .env"
    )
    parser.add_argument(
        "--host",
        default=get_env_str("QDRANT_HOST", "192.168.254.22"),
        help="Qdrant host (default: from QDRANT_HOST env or 192.168.254.22)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=get_env_int("QDRANT_PORT", 6333),
        help="Qdrant port (default: from QDRANT_PORT env or 6333)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show configuration without creating collections"
    )
    parser.add_argument(
        "--validate-ollama",
        action="store_true",
        help="Validate Ollama model dimensions before creating collections"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    filename_collection = get_env_str("QDRANT_FILENAME_COLLECTION", "filename-granite-embedding30m")
    content_collection = get_env_str("QDRANT_CONTENT_COLLECTION", "releasenotes-bge-m3")
    
    filename_config = load_collection_config("QDRANT_FILENAME")
    content_config = load_collection_config("QDRANT_CONTENT")
    
    # General settings
    shard_number = get_env_int("QDRANT_SHARD_NUMBER", 1)
    replication_factor = get_env_int("QDRANT_REPLICATION_FACTOR", 1)
    write_consistency_factor = get_env_int("QDRANT_WRITE_CONSISTENCY_FACTOR", 1)
    on_disk_payload = get_env_bool("QDRANT_ON_DISK_PAYLOAD", True)
    
    # Ollama configuration
    ollama_host = get_env_str("OLLAMA_HOST", "192.168.254.22")
    ollama_port = get_env_int("OLLAMA_PORT", 11434)
    ollama_filename_model = get_env_str("OLLAMA_FILENAME_MODEL", "granite-embedding:30m")
    ollama_content_model = get_env_str("OLLAMA_CONTENT_MODEL", "bge-m3")
    
    # Display configuration
    logger.info("="*60)
    logger.info("QDRANT COLLECTION SETUP")
    logger.info("="*60)
    logger.info(f"Qdrant Server: {args.host}:{args.port}")
    logger.info(f"Ollama Server: {ollama_host}:{ollama_port}")
    logger.info(f"\nFilename Collection: {filename_collection}")
    logger.info(f"  Model: {ollama_filename_model}")
    logger.info(f"  Dimensions: {filename_config['vector_size']}D")
    logger.info(f"  Distance: {filename_config['distance']}")
    logger.info(f"  Text Index: {filename_config['text_index']}")
    if filename_config['text_index']:
        logger.info(f"  Tokenizer: {filename_config['tokenizer']}")
    
    logger.info(f"\nContent Collection: {content_collection}")
    logger.info(f"  Model: {ollama_content_model}")
    logger.info(f"  Dimensions: {content_config['vector_size']}D")
    logger.info(f"  Distance: {content_config['distance']}")
    logger.info(f"  Text Index: {content_config['text_index']}")
    
    logger.info(f"\nGeneral Settings:")
    logger.info(f"  Shards: {shard_number}")
    logger.info(f"  Replication: {replication_factor}")
    logger.info(f"  Write Consistency: {write_consistency_factor}")
    logger.info(f"  On-disk Payload: {on_disk_payload}")
    logger.info("="*60 + "\n")
    
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No collections will be created")
        logger.info("\nConfiguration loaded successfully!")
        logger.info("Remove --dry-run flag to create collections")
        return 0
    
    try:
        # Connect to Qdrant (support both dev and production)
        logger.info("Connecting to Qdrant...")
        
        # Check for production settings
        use_https = os.getenv("QDRANT_USE_HTTPS", "false").lower() == "true"
        api_key = os.getenv("QDRANT_API_KEY")
        
        if use_https or api_key:
            # Production mode: Use URL with HTTPS and API key
            protocol = "https" if use_https else "http"
            url = f"{protocol}://{args.host}:{args.port}"
            logger.info(f"  Mode: PRODUCTION ({protocol.upper()})")
            if api_key:
                logger.info("  Authentication: API Key enabled")
            client = QdrantClient(url=url, api_key=api_key)
        else:
            # Development mode: Simple host + port
            logger.info("  Mode: DEVELOPMENT (HTTP)")
            client = QdrantClient(host=args.host, port=args.port)
        
        # Test connection
        collections = client.get_collections()
        logger.info(f"✅ Connected! Found {len(collections.collections)} existing collections\n")
        
        # Validate Ollama dimensions if requested
        if args.validate_ollama:
            logger.info("Validating Ollama model dimensions...\n")
            
            filename_valid = validate_ollama_dimensions(
                client, ollama_filename_model, filename_config['vector_size'],
                ollama_host, ollama_port
            )
            
            content_valid = validate_ollama_dimensions(
                client, ollama_content_model, content_config['vector_size'],
                ollama_host, ollama_port
            )
            
            if not (filename_valid and content_valid):
                logger.error("\n❌ Ollama model dimension validation failed!")
                logger.error("Fix the dimension mismatch in .env before proceeding")
                return 1
            
            logger.info("\n✅ All Ollama models validated successfully!\n")
        
        # Create filename collection
        success1 = create_collection(
            client, filename_collection, filename_config,
            shard_number, replication_factor, write_consistency_factor, on_disk_payload
        )
        
        # Create content collection
        success2 = create_collection(
            client, content_collection, content_config,
            shard_number, replication_factor, write_consistency_factor, on_disk_payload
        )
        
        # Verify collections
        if success1 and success2:
            logger.info("\n" + "="*60)
            logger.info("VERIFYING COLLECTIONS")
            logger.info("="*60)
            
            verify1 = verify_collection(client, filename_collection, filename_config)
            verify2 = verify_collection(client, content_collection, content_config)
            
            if verify1 and verify2:
                logger.info("\n" + "="*60)
                logger.info("🎉 SETUP COMPLETE!")
                logger.info("="*60)
                logger.info("\nYou can now run the ingestion pipeline:")
                logger.info("  python src/pipeline.py")
                logger.info("\nOr start the API server:")
                logger.info("  python api/main.py")
                logger.info("\nOr use Docker:")
                logger.info("  docker-compose up -d")
                return 0
        
        logger.error("\n❌ Setup failed! Check errors above.")
        return 1
            
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
