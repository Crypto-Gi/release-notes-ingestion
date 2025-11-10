#!/usr/bin/env python3
"""
Interactive Payload Index Creator for Qdrant Collections

This script:
1. Reads collection names from .env
2. Connects to Qdrant and analyzes existing data
3. Shows available metadata fields for each collection
4. Lets you interactively choose which fields to index
5. Creates the selected indexes

Usage:
    python scripts/create_payload_indexes.py
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client import models
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_sample_payload(client: QdrantClient, collection_name: str) -> dict:
    """Get a sample payload from collection to analyze structure"""
    try:
        info = client.get_collection(collection_name)
        if info.points_count == 0:
            return {}
        
        # Get a sample point
        points = client.scroll(
            collection_name=collection_name,
            limit=1,
            with_payload=True,
            with_vectors=False
        )[0]
        
        if points:
            return points[0].payload
        return {}
    except Exception as e:
        logger.error(f"Error getting sample payload: {e}")
        return {}


def extract_metadata_fields(payload: dict, prefix: str = "") -> list:
    """Recursively extract all field paths from payload"""
    fields = []
    
    for key, value in payload.items():
        field_path = f"{prefix}.{key}" if prefix else key
        
        if isinstance(value, dict):
            # Recurse into nested dictionaries
            fields.extend(extract_metadata_fields(value, field_path))
        else:
            # Leaf node - add field with type
            field_type = type(value).__name__
            fields.append({
                'path': field_path,
                'type': field_type,
                'sample': str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
            })
    
    return fields


def get_index_type_for_field(field_type: str) -> str:
    """Determine appropriate index type based on field type"""
    if field_type in ['int', 'float']:
        return 'integer'
    elif field_type == 'str':
        return 'keyword'
    elif field_type == 'bool':
        return 'keyword'
    else:
        return 'keyword'


def create_index(
    client: QdrantClient,
    collection_name: str,
    field_path: str,
    field_type: str,
    is_tenant: bool = False
) -> bool:
    """Create a payload index for a field"""
    try:
        index_type = get_index_type_for_field(field_type)
        
        logger.info(f"\nCreating {index_type} index on '{field_path}'...")
        
        if index_type == 'keyword':
            field_schema = models.KeywordIndexParams(
                type="keyword",
                is_tenant=is_tenant
            )
        elif index_type == 'integer':
            field_schema = models.IntegerIndexParams(
                type="integer"
            )
        else:
            logger.error(f"Unsupported index type: {index_type}")
            return False
        
        client.create_payload_index(
            collection_name=collection_name,
            field_name=field_path,
            field_schema=field_schema
        )
        
        logger.info(f"✅ Index created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating index: {e}")
        return False


def main():
    """Main interactive function"""
    # Load environment
    load_dotenv()
    
    # Get Qdrant connection details
    qdrant_host = os.getenv("QDRANT_HOST", "192.168.254.22")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    
    # Get collection names from .env
    filename_collection = os.getenv("QDRANT_FILENAME_COLLECTION", "filenames")
    content_collection = os.getenv("QDRANT_CONTENT_COLLECTION", "content")
    
    print("=" * 80)
    print("QDRANT PAYLOAD INDEX CREATOR")
    print("=" * 80)
    print(f"\nQdrant Server: {qdrant_host}:{qdrant_port}")
    print(f"Filename Collection: {filename_collection}")
    print(f"Content Collection: {content_collection}")
    print("=" * 80)
    
    # Connect to Qdrant
    try:
        logger.info("\nConnecting to Qdrant...")
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        collections = client.get_collections()
        logger.info(f"✅ Connected! Found {len(collections.collections)} collections\n")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Qdrant: {e}")
        return 1
    
    # Process each collection
    collections_to_process = [
        (filename_collection, "Filename"),
        (content_collection, "Content")
    ]
    
    for collection_name, collection_label in collections_to_process:
        print("\n" + "=" * 80)
        print(f"{collection_label} Collection: {collection_name}")
        print("=" * 80)
        
        # Check if collection exists
        if not any(c.name == collection_name for c in collections.collections):
            logger.warning(f"⚠️  Collection '{collection_name}' not found. Skipping...")
            continue
        
        # Get collection info
        info = client.get_collection(collection_name)
        print(f"\nCollection Info:")
        print(f"  Points: {info.points_count:,}")
        print(f"  Vector Size: {info.config.params.vectors.size}D")
        
        if info.points_count == 0:
            logger.warning(f"⚠️  Collection is empty. Skipping...")
            continue
        
        # Get sample payload and extract fields
        logger.info("\nAnalyzing payload structure...")
        sample_payload = get_sample_payload(client, collection_name)
        
        if not sample_payload:
            logger.warning(f"⚠️  Could not get sample payload. Skipping...")
            continue
        
        fields = extract_metadata_fields(sample_payload)
        
        # Display available fields
        print(f"\nAvailable Fields for Indexing:")
        print("-" * 80)
        for idx, field in enumerate(fields, 1):
            print(f"  {idx}. {field['path']:<30} ({field['type']:<10}) Sample: {field['sample']}")
        print("-" * 80)
        
        # Ask user which fields to index
        print(f"\nSelect fields to index (comma-separated numbers, or 'skip' to skip this collection):")
        print(f"Example: 1,3,5  or  skip")
        
        user_input = input(f"\nYour selection for {collection_name}: ").strip().lower()
        
        if user_input == 'skip':
            logger.info(f"Skipping {collection_name}")
            continue
        
        if not user_input:
            logger.info(f"No fields selected for {collection_name}")
            continue
        
        # Parse selections
        try:
            selections = [int(x.strip()) for x in user_input.split(',')]
        except ValueError:
            logger.error(f"❌ Invalid input. Please enter comma-separated numbers.")
            continue
        
        # Validate selections
        valid_selections = [s for s in selections if 1 <= s <= len(fields)]
        if not valid_selections:
            logger.error(f"❌ No valid selections.")
            continue
        
        # Ask about tenant optimization for filename field
        is_tenant = False
        selected_fields = [fields[s-1] for s in valid_selections]
        
        # Check if metadata.filename is selected
        if any(f['path'] == 'metadata.filename' for f in selected_fields):
            print(f"\n⚠️  You selected 'metadata.filename'")
            print(f"   Enable tenant optimization (is_tenant=True)?")
            print(f"   This optimizes for queries filtering by filename (recommended for multi-file queries)")
            tenant_input = input(f"   Enable tenant optimization? (y/n): ").strip().lower()
            is_tenant = tenant_input in ['y', 'yes']
        
        # Create indexes
        print(f"\n{'=' * 80}")
        print(f"Creating Indexes for {collection_name}")
        print(f"{'=' * 80}")
        
        success_count = 0
        for selection in valid_selections:
            field = fields[selection - 1]
            
            # Check if this is metadata.filename and apply tenant optimization
            use_tenant = is_tenant and field['path'] == 'metadata.filename'
            
            if create_index(
                client,
                collection_name,
                field['path'],
                field['type'],
                is_tenant=use_tenant
            ):
                success_count += 1
        
        print(f"\n✅ Created {success_count}/{len(valid_selections)} indexes for {collection_name}")
    
    print("\n" + "=" * 80)
    print("🎉 INDEX CREATION COMPLETE!")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
