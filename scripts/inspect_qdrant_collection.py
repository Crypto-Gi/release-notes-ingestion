#!/usr/bin/env python3
"""
Inspect Qdrant Collection

This script inspects Qdrant collections to see:
- Collection configuration (vector size, distance metric)
- Sample points with payloads
- Vector dimensions
- Metadata structure
- Index configuration

Use this to verify what model dimensions are actually stored.
"""

import sys
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from components.config import load_config
from qdrant_client import QdrantClient
from qdrant_client.http import models

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def inspect_collection(client: QdrantClient, collection_name: str, sample_size: int = 3):
    """
    Inspect a Qdrant collection
    
    Args:
        client: QdrantClient instance
        collection_name: Name of collection to inspect
        sample_size: Number of sample points to retrieve
    """
    try:
        logger.info(f"\n{'='*70}")
        logger.info(f"Inspecting Collection: {collection_name}")
        logger.info(f"{'='*70}")
        
        # Get collection info
        collection_info = client.get_collection(collection_name)
        
        # Display basic info
        logger.info(f"\n📊 Collection Statistics:")
        logger.info(f"  Points Count: {collection_info.points_count}")
        vectors_count = collection_info.vectors_count if collection_info.vectors_count is not None else 0
        indexed_vectors = collection_info.indexed_vectors_count if collection_info.indexed_vectors_count is not None else 0
        logger.info(f"  Vectors Count: {vectors_count}")
        logger.info(f"  Indexed Vectors: {indexed_vectors}")
        logger.info(f"  Status: {collection_info.status}")
        
        # Display vector configuration
        logger.info(f"\n🔢 Vector Configuration:")
        vector_config = collection_info.config.params.vectors
        
        if isinstance(vector_config, dict):
            # Named vectors
            for name, config in vector_config.items():
                logger.info(f"  Vector '{name}':")
                logger.info(f"    Size: {config.size}D")
                logger.info(f"    Distance: {config.distance}")
        else:
            # Single vector
            logger.info(f"  Size: {vector_config.size}D")
            logger.info(f"  Distance: {vector_config.distance}")
        
        # Display HNSW configuration
        if collection_info.config.hnsw_config:
            logger.info(f"\n🔗 HNSW Index Configuration:")
            hnsw = collection_info.config.hnsw_config
            logger.info(f"  M (connections): {hnsw.m}")
            logger.info(f"  EF Construct: {hnsw.ef_construct}")
            logger.info(f"  Full Scan Threshold: {hnsw.full_scan_threshold}")
            logger.info(f"  On Disk: {hnsw.on_disk}")
        
        # Display payload schema
        if collection_info.payload_schema:
            logger.info(f"\n📋 Payload Schema:")
            for field_name, field_info in collection_info.payload_schema.items():
                logger.info(f"  {field_name}: {field_info}")
        
        # Get sample points
        logger.info(f"\n🔍 Sample Points (showing {sample_size}):")
        
        scroll_result = client.scroll(
            collection_name=collection_name,
            limit=sample_size,
            with_payload=True,
            with_vectors=True
        )
        
        points, _ = scroll_result
        
        if not points:
            logger.warning("  No points found in collection")
            return
        
        for i, point in enumerate(points, 1):
            logger.info(f"\n  --- Point {i} ---")
            logger.info(f"  ID: {point.id}")
            
            # Check vector dimensions
            if isinstance(point.vector, dict):
                # Named vectors
                for name, vector in point.vector.items():
                    logger.info(f"  Vector '{name}' Dimensions: {len(vector)}D")
            else:
                # Single vector
                logger.info(f"  Vector Dimensions: {len(point.vector)}D")
                logger.info(f"  First 5 values: {point.vector[:5]}")
            
            # Display payload
            if point.payload:
                logger.info(f"  Payload:")
                for key, value in point.payload.items():
                    if key == "pagecontent" and len(str(value)) > 100:
                        # Truncate long content
                        logger.info(f"    {key}: {str(value)[:100]}...")
                    else:
                        logger.info(f"    {key}: {value}")
        
        # Check for specific metadata fields
        logger.info(f"\n🔎 Checking Metadata Fields:")
        
        # Try to find a point with metadata
        scroll_result = client.scroll(
            collection_name=collection_name,
            limit=1,
            with_payload=True
        )
        
        if scroll_result[0]:
            sample_point = scroll_result[0][0]
            payload = sample_point.payload
            
            # Check for common fields
            fields_to_check = ["metadata", "filename", "md5_hash", "page_number", "element_type"]
            
            for field in fields_to_check:
                if field in payload:
                    logger.info(f"  ✅ {field}: Present")
                    if field == "metadata" and isinstance(payload[field], dict):
                        logger.info(f"     Metadata keys: {list(payload[field].keys())}")
                else:
                    logger.info(f"  ❌ {field}: Not found")
        
        # Display indexes
        logger.info(f"\n🗂️  Payload Indexes:")
        
        # Get collection info again to check indexes
        collection_info = client.get_collection(collection_name)
        
        if hasattr(collection_info.config, 'payload_schema') and collection_info.config.payload_schema:
            for field_name, field_info in collection_info.config.payload_schema.items():
                logger.info(f"  {field_name}:")
                logger.info(f"    Type: {field_info.data_type if hasattr(field_info, 'data_type') else 'N/A'}")
                logger.info(f"    Indexed: {field_info.is_indexed if hasattr(field_info, 'is_indexed') else 'N/A'}")
        else:
            logger.info("  No payload indexes configured")
        
        logger.info(f"\n{'='*70}\n")
        
    except Exception as e:
        logger.error(f"Error inspecting collection '{collection_name}': {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main inspection function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Inspect Qdrant collections to see stored data"
    )
    parser.add_argument(
        "--collection",
        type=str,
        help="Specific collection to inspect (default: inspect both)"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=3,
        help="Number of sample points to show (default: 3)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all collections"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Initialize Qdrant client
    logger.info("Connecting to Qdrant...")
    
    if config.qdrant.use_https:
        url = f"https://{config.qdrant.host}:{config.qdrant.port}"
    else:
        url = f"http://{config.qdrant.host}:{config.qdrant.port}"
    
    client = QdrantClient(
        url=url,
        api_key=config.qdrant.api_key if config.qdrant.api_key else None,
        timeout=30
    )
    
    logger.info(f"Connected to: {url}")
    
    # Get all collections
    if args.all:
        logger.info("\n📚 All Collections:")
        collections = client.get_collections()
        for collection in collections.collections:
            logger.info(f"  - {collection.name}")
        logger.info("")
    
    # Inspect specific collection or both default collections
    if args.collection:
        inspect_collection(client, args.collection, args.samples)
    else:
        # Inspect both default collections
        inspect_collection(client, config.qdrant.filename_collection, args.samples)
        inspect_collection(client, config.qdrant.content_collection, args.samples)
    
    logger.info("✅ Inspection complete!")


if __name__ == "__main__":
    main()
