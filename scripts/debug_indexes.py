#!/usr/bin/env python3
"""
Debug script to see what Qdrant returns for collection info and payload indexes
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from components.config import load_config
from qdrant_client import QdrantClient

# Load configuration
config = load_config()

print(f"Connecting to Qdrant...")

# Use proper connection based on configuration
if config.qdrant.use_https:
    url = f"https://{config.qdrant.host}:{config.qdrant.port}"
else:
    url = f"http://{config.qdrant.host}:{config.qdrant.port}"

client = QdrantClient(
    url=url,
    api_key=config.qdrant.api_key if config.qdrant.api_key else None,
    check_compatibility=False
)

print(f"Connected to: {url}")

# Check both collections
for collection_name in [config.qdrant.filename_collection, config.qdrant.content_collection]:
    try:
        info = client.get_collection(collection_name)
        print(f"\n{'='*80}")
        print(f"=== {collection_name} ===")
        print(f"{'='*80}")
        
        print(f"Points: {info.points_count}")
        print(f"Vector Size: {info.config.params.vectors.size}D")
        print(f"Distance Metric: {info.config.params.vectors.distance}")
        print(f"Status: {info.status}")
        
        # Access payload schema correctly
        if hasattr(info, 'payload_schema') and info.payload_schema:
            print(f"\n📋 Payload Indexes ({len(info.payload_schema)}):")
            for field_name, field_schema in info.payload_schema.items():
                print(f"  {field_name}:")
                print(f"    Type: {field_schema.data_type}")
                if hasattr(field_schema, 'params') and field_schema.params:
                    print(f"    Params: {field_schema.params}")
                if hasattr(field_schema, 'points'):
                    print(f"    Points: {field_schema.points}")
        else:
            print("\n📋 No payload indexes configured")
            
    except Exception as e:
        print(f"❌ Error with {collection_name}: {e}")

print(f"\n✅ Debug complete!")
