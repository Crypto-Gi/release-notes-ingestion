#!/usr/bin/env python3
"""
Debug script to see what Qdrant returns for collection info and payload indexes
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from qdrant_client import QdrantClient
import json

load_dotenv()

# Get connection details
qdrant_host = os.getenv("QDRANT_HOST", "192.168.254.22")
qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
content_collection = os.getenv("QDRANT_CONTENT_COLLECTION", "content")

print(f"Connecting to Qdrant at {qdrant_host}:{qdrant_port}")
print(f"Collection: {content_collection}\n")

# Connect
client = QdrantClient(host=qdrant_host, port=qdrant_port)

# Get collection info
info = client.get_collection(content_collection)

print("=" * 80)
print("COLLECTION INFO STRUCTURE")
print("=" * 80)

# Print the full structure
print(f"\ninfo type: {type(info)}")
print(f"info.config type: {type(info.config)}")
print(f"info.config.params type: {type(info.config.params)}")

# Check for payload_schema
if hasattr(info.config.params, 'payload_schema'):
    print(f"\n✅ payload_schema exists!")
    print(f"payload_schema type: {type(info.config.params.payload_schema)}")
    
    payload_schema = info.config.params.payload_schema
    
    if payload_schema:
        print(f"\nNumber of indexed fields: {len(payload_schema)}")
        print("\n" + "=" * 80)
        print("INDEXED FIELDS")
        print("=" * 80)
        
        for field_name, field_schema in payload_schema.items():
            print(f"\n📋 Field: {field_name}")
            print(f"   Type: {type(field_schema)}")
            print(f"   Attributes: {dir(field_schema)}")
            
            # Try to get data_type
            if hasattr(field_schema, 'data_type'):
                print(f"   data_type: {field_schema.data_type}")
            
            # Try to get params
            if hasattr(field_schema, 'params'):
                print(f"   params: {field_schema.params}")
                if field_schema.params:
                    print(f"   params type: {type(field_schema.params)}")
                    print(f"   params attributes: {dir(field_schema.params)}")
            
            # Try to get points
            if hasattr(field_schema, 'points'):
                print(f"   points: {field_schema.points}")
            
            print(f"   Full repr: {repr(field_schema)}")
    else:
        print("\n⚠️  payload_schema is empty")
else:
    print("\n❌ payload_schema does NOT exist!")
    print(f"Available attributes: {dir(info.config.params)}")

print("\n" + "=" * 80)
print("RAW JSON (if available)")
print("=" * 80)

# Try to convert to dict
try:
    info_dict = info.dict()
    print(json.dumps(info_dict, indent=2, default=str))
except Exception as e:
    print(f"Could not convert to JSON: {e}")
