#!/usr/bin/env python3
"""
Advanced Interactive Payload Index Creator for Qdrant Collections

This script provides comprehensive indexing options for Qdrant collections:
- All 8 index types: Keyword, Integer, Float, Bool, Geo, DateTime, UUID, Text
- Advanced options: is_tenant, is_principal, on_disk, phrase_matching, stopwords
- Detailed explanations for each option
- Interactive configuration

Usage:
    python scripts/create_payload_indexes_advanced.py
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
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Index type information
INDEX_TYPES = {
    'keyword': {
        'name': 'Keyword Index',
        'description': 'For exact string matching (IDs, hashes, filenames, categories)',
        'python_types': ['str'],
        'options': ['is_tenant', 'on_disk'],
        'use_cases': [
            'Exact match filters (filename="doc.pdf")',
            'Multi-value filters with is_tenant (all chunks from file X)',
            'Category/tag filtering'
        ]
    },
    'integer': {
        'name': 'Integer Index',
        'description': 'For whole number fields (counts, page numbers, IDs)',
        'python_types': ['int'],
        'options': ['is_principal', 'on_disk'],
        'use_cases': [
            'Range queries (page_number >= 10)',
            'Exact matches (status_code=200)',
            'Sorting by numeric fields'
        ]
    },
    'float': {
        'name': 'Float Index',
        'description': 'For decimal number fields (scores, ratings, prices)',
        'python_types': ['float'],
        'options': ['is_principal', 'on_disk'],
        'use_cases': [
            'Range queries (price < 100.0)',
            'Threshold filtering (confidence >= 0.8)',
            'Numeric comparisons'
        ]
    },
    'bool': {
        'name': 'Boolean Index',
        'description': 'For true/false fields (flags, status)',
        'python_types': ['bool'],
        'options': ['on_disk'],
        'use_cases': [
            'Binary filters (is_processed=true)',
            'Status flags (is_active=false)',
            'Feature toggles'
        ]
    },
    'geo': {
        'name': 'Geo Index',
        'description': 'For geographic coordinates (lat/lon)',
        'python_types': ['dict'],
        'options': ['on_disk'],
        'use_cases': [
            'Location-based search (within radius)',
            'Proximity filtering',
            'Geographic boundaries'
        ],
        'format': '{"lon": 52.52, "lat": 13.40}'
    },
    'datetime': {
        'name': 'DateTime Index',
        'description': 'For timestamp fields (created_at, updated_at)',
        'python_types': ['str'],
        'options': ['on_disk'],
        'use_cases': [
            'Time range queries (created_at > "2024-01-01")',
            'Chronological filtering',
            'Date-based sorting'
        ],
        'format': 'RFC 3339: "2024-01-15T10:30:00Z"'
    },
    'uuid': {
        'name': 'UUID Index',
        'description': 'For UUID fields (v1.11.0+) - optimized for UUIDs',
        'python_types': ['str'],
        'options': ['on_disk'],
        'use_cases': [
            'UUID exact matching (faster than keyword)',
            'Reference IDs',
            'Unique identifiers'
        ],
        'format': '"550e8400-e29b-41d4-a716-446655440000"'
    },
    'text': {
        'name': 'Text Index',
        'description': 'For full-text search (content, descriptions)',
        'python_types': ['str'],
        'options': ['tokenizer', 'min_token_len', 'max_token_len', 'lowercase', 'phrase_matching', 'on_disk'],
        'use_cases': [
            'Full-text search',
            'Keyword search in content',
            'Phrase matching ("exact phrase")'
        ]
    }
}

# Option descriptions
OPTIONS_INFO = {
    'is_tenant': {
        'name': 'Tenant Optimization',
        'description': 'Optimizes for filtering by this field (multi-value queries)',
        'when_to_use': 'When field has many unique values and is frequently filtered',
        'example': 'filename field with 1000s of different files',
        'applies_to': ['keyword', 'integer']
    },
    'is_principal': {
        'name': 'Principal Index',
        'description': 'Optimizes for range queries and sorting',
        'when_to_use': 'When field is used for range queries or sorting',
        'example': 'timestamp or page_number for chronological/sequential access',
        'applies_to': ['integer', 'float']
    },
    'on_disk': {
        'name': 'On-Disk Storage',
        'description': 'Stores index on disk instead of RAM (saves memory)',
        'when_to_use': 'For large indexes or when RAM is limited',
        'example': 'Large collections with memory constraints',
        'applies_to': ['keyword', 'integer', 'float', 'bool', 'geo', 'datetime', 'uuid', 'text']
    },
    'phrase_matching': {
        'name': 'Phrase Matching',
        'description': 'Enables exact phrase search (e.g., "machine learning")',
        'when_to_use': 'When users need to search for exact phrases',
        'example': 'Search for "release notes" as exact phrase',
        'applies_to': ['text']
    }
}


def print_section_header(title: str):
    """Print a formatted section header"""
    print(f"\n{'=' * 80}")
    print(f"{title}")
    print(f"{'=' * 80}")


def print_index_type_info(index_type: str):
    """Print detailed information about an index type"""
    info = INDEX_TYPES[index_type]
    print(f"\n📋 {info['name']}")
    print(f"   {info['description']}")
    print(f"\n   Use Cases:")
    for use_case in info['use_cases']:
        print(f"     • {use_case}")
    
    if 'format' in info:
        print(f"\n   Format: {info['format']}")
    
    if info['options']:
        print(f"\n   Available Options: {', '.join(info['options'])}")


def print_option_info(option: str):
    """Print detailed information about an option"""
    if option not in OPTIONS_INFO:
        return
    
    info = OPTIONS_INFO[option]
    print(f"\n   ℹ️  {info['name']}")
    print(f"      {info['description']}")
    print(f"      When to use: {info['when_to_use']}")
    print(f"      Example: {info['example']}")


def detect_field_type(field_value: Any, field_type_str: str) -> str:
    """Detect appropriate index type based on field value and Python type"""
    # Check for geo format
    if isinstance(field_value, dict) and 'lon' in field_value and 'lat' in field_value:
        return 'geo'
    
    # Check for UUID format
    if isinstance(field_value, str) and len(field_value) == 36 and field_value.count('-') == 4:
        return 'uuid'
    
    # Check for datetime format (RFC 3339)
    if isinstance(field_value, str) and ('T' in field_value or 'Z' in field_value):
        # Simple heuristic for datetime
        if any(char in field_value for char in [':', '-', 'T', 'Z']):
            return 'datetime'
    
    # Map Python types to index types
    type_mapping = {
        'int': 'integer',
        'float': 'float',
        'bool': 'bool',
        'str': 'keyword'  # Default for strings
    }
    
    return type_mapping.get(field_type_str, 'keyword')


def get_sample_payload(client: QdrantClient, collection_name: str) -> dict:
    """Get a sample payload from collection to analyze structure"""
    try:
        info = client.get_collection(collection_name)
        if info.points_count == 0:
            return {}
        
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
        
        if isinstance(value, dict) and not ('lon' in value and 'lat' in value):
            # Recurse into nested dictionaries (except geo coordinates)
            fields.extend(extract_metadata_fields(value, field_path))
        else:
            # Leaf node - add field with type and suggested index
            field_type = type(value).__name__
            suggested_index = detect_field_type(value, field_type)
            
            fields.append({
                'path': field_path,
                'type': field_type,
                'suggested_index': suggested_index,
                'sample': str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
            })
    
    return fields


def select_index_type(field: dict) -> Optional[str]:
    """Interactive index type selection"""
    print(f"\n{'─' * 80}")
    print(f"Field: {field['path']}")
    print(f"Type: {field['type']}")
    print(f"Sample: {field['sample']}")
    print(f"{'─' * 80}")
    
    # Get compatible index types
    compatible_types = [
        idx_type for idx_type, info in INDEX_TYPES.items()
        if field['type'] in info['python_types']
    ]
    
    if not compatible_types:
        compatible_types = ['keyword']  # Fallback
    
    # Show suggested index type
    suggested = field['suggested_index']
    print(f"\n💡 Suggested Index Type: {INDEX_TYPES[suggested]['name']}")
    print(f"   {INDEX_TYPES[suggested]['description']}")
    
    # Show all compatible options
    print(f"\nAvailable Index Types:")
    for idx, idx_type in enumerate(compatible_types, 1):
        marker = "⭐" if idx_type == suggested else "  "
        print(f"  {marker} {idx}. {INDEX_TYPES[idx_type]['name']}")
        print(f"      {INDEX_TYPES[idx_type]['description']}")
    
    print(f"\n  0. Skip this field")
    
    while True:
        choice = input(f"\nSelect index type (0-{len(compatible_types)}) [default: 1]: ").strip()
        
        if not choice:
            choice = '1'
        
        if choice == '0':
            return None
        
        try:
            idx = int(choice)
            if 1 <= idx <= len(compatible_types):
                return compatible_types[idx - 1]
        except ValueError:
            pass
        
        print(f"❌ Invalid choice. Please enter 0-{len(compatible_types)}")


def configure_index_options(index_type: str, field_path: str) -> dict:
    """Interactive configuration of index options"""
    options = {}
    available_options = INDEX_TYPES[index_type]['options']
    
    if not available_options:
        return options
    
    print(f"\n📝 Configure Index Options for {index_type}:")
    
    # Special handling for text index
    if index_type == 'text':
        print(f"\n   Text Index Configuration:")
        
        # Tokenizer
        print(f"\n   Tokenizer options:")
        print(f"     1. word (default) - Split by word boundaries")
        print(f"     2. whitespace - Split by whitespace only")
        print(f"     3. prefix - Enable prefix search")
        print(f"     4. multilingual - Support multiple languages")
        
        tokenizer_choice = input(f"   Select tokenizer (1-4) [default: 1]: ").strip() or '1'
        tokenizers = ['word', 'whitespace', 'prefix', 'multilingual']
        options['tokenizer'] = tokenizers[int(tokenizer_choice) - 1] if tokenizer_choice in ['1','2','3','4'] else 'word'
        
        # Token length
        options['min_token_len'] = int(input(f"   Min token length [default: 2]: ").strip() or '2')
        options['max_token_len'] = int(input(f"   Max token length [default: 15]: ").strip() or '15')
        
        # Lowercase
        lowercase = input(f"   Convert to lowercase? (y/n) [default: y]: ").strip().lower()
        options['lowercase'] = lowercase != 'n'
        
        # Phrase matching
        print_option_info('phrase_matching')
        phrase = input(f"   Enable phrase matching? (y/n) [default: n]: ").strip().lower()
        options['phrase_matching'] = phrase == 'y'
        
        # On disk
        on_disk = input(f"   Store on disk? (y/n) [default: n]: ").strip().lower()
        options['on_disk'] = on_disk == 'y'
        
        return options
    
    # For other index types
    for option in available_options:
        if option not in OPTIONS_INFO:
            continue
        
        print_option_info(option)
        
        # Special handling for specific options
        if option == 'is_tenant' and 'filename' in field_path.lower():
            response = input(f"   Enable {option}? (y/n) [recommended: y]: ").strip().lower()
            options[option] = response != 'n'
        elif option == 'is_principal':
            response = input(f"   Enable {option}? (y/n) [default: n]: ").strip().lower()
            options[option] = response == 'y'
        elif option == 'on_disk':
            response = input(f"   Enable {option}? (y/n) [default: n]: ").strip().lower()
            options[option] = response == 'y'
    
    return options


def create_index(
    client: QdrantClient,
    collection_name: str,
    field_path: str,
    index_type: str,
    options: dict
) -> bool:
    """Create a payload index with specified configuration"""
    try:
        logger.info(f"\nCreating {index_type} index on '{field_path}'...")
        
        # Build field schema based on index type
        if index_type == 'keyword':
            field_schema = models.KeywordIndexParams(
                type="keyword",
                is_tenant=options.get('is_tenant', False),
                on_disk=options.get('on_disk', False)
            )
        elif index_type == 'integer':
            field_schema = models.IntegerIndexParams(
                type="integer",
                is_principal=options.get('is_principal', False),
                on_disk=options.get('on_disk', False)
            )
        elif index_type == 'float':
            field_schema = models.FloatIndexParams(
                type="float",
                is_principal=options.get('is_principal', False),
                on_disk=options.get('on_disk', False)
            )
        elif index_type == 'bool':
            field_schema = models.BoolIndexParams(
                type="bool",
                on_disk=options.get('on_disk', False)
            )
        elif index_type == 'geo':
            field_schema = models.GeoIndexParams(
                type="geo",
                on_disk=options.get('on_disk', False)
            )
        elif index_type == 'datetime':
            field_schema = models.DatetimeIndexParams(
                type="datetime",
                on_disk=options.get('on_disk', False)
            )
        elif index_type == 'uuid':
            field_schema = models.UuidIndexParams(
                type="uuid",
                on_disk=options.get('on_disk', False)
            )
        elif index_type == 'text':
            tokenizer_map = {
                'word': models.TokenizerType.WORD,
                'whitespace': models.TokenizerType.WHITESPACE,
                'prefix': models.TokenizerType.PREFIX,
                'multilingual': models.TokenizerType.MULTILINGUAL
            }
            field_schema = models.TextIndexParams(
                type="text",
                tokenizer=tokenizer_map.get(options.get('tokenizer', 'word'), models.TokenizerType.WORD),
                min_token_len=options.get('min_token_len', 2),
                max_token_len=options.get('max_token_len', 15),
                lowercase=options.get('lowercase', True),
                on_disk=options.get('on_disk', False)
            )
            if options.get('phrase_matching'):
                field_schema.phrase_matching = True
        else:
            logger.error(f"Unsupported index type: {index_type}")
            return False
        
        # Create the index
        client.create_payload_index(
            collection_name=collection_name,
            field_name=field_path,
            field_schema=field_schema
        )
        
        # Show configuration summary
        logger.info(f"✅ Index created successfully!")
        logger.info(f"   Type: {index_type}")
        if options:
            logger.info(f"   Options: {', '.join(f'{k}={v}' for k, v in options.items())}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating index: {e}")
        return False


def process_single_field(client: QdrantClient, collection_name: str, fields: list, existing_indexes: dict) -> bool:
    """Process a single field selection and indexing"""
    # Display available fields
    print(f"\nAvailable Fields:")
    print("─" * 80)
    for idx, field in enumerate(fields, 1):
        suggested = INDEX_TYPES[field['suggested_index']]['name']
        
        # Check if field already has an index
        if field.get('has_index', False):
            # Show with indicator that it's already indexed
            print(f"  {idx}. {field['path']:<30} ({field['type']:<10}) → {suggested} ✓ (indexed)")
        else:
            print(f"  {idx}. {field['path']:<30} ({field['type']:<10}) → {suggested}")
    print("─" * 80)
    print(f"  0. Go back to collection selection")
    
    # Ask user to select a field
    while True:
        choice = input(f"\nSelect a field to index (0-{len(fields)}): ").strip()
        
        if choice == '0':
            return False  # Go back to collection selection
        
        try:
            field_idx = int(choice)
            if 1 <= field_idx <= len(fields):
                field = fields[field_idx - 1]
                break
        except ValueError:
            pass
        
        print(f"❌ Invalid choice. Please enter 0-{len(fields)}")
    
    # Select index type
    index_type = select_index_type(field)
    
    if not index_type:
        print(f"⏭️  Skipping {field['path']}")
        return True  # Continue with same collection
    
    # Show detailed info about selected index type
    print_index_type_info(index_type)
    
    # Configure options
    options = configure_index_options(index_type, field['path'])
    
    # Create index
    if create_index(client, collection_name, field['path'], index_type, options):
        print(f"\n✅ Index created successfully for {field['path']}")
    else:
        print(f"\n❌ Failed to create index for {field['path']}")
    
    return True  # Continue with same collection


def get_existing_indexes(client: QdrantClient, collection_name: str) -> dict:
    """Get existing payload indexes for a collection"""
    try:
        # Get collection info which includes payload indexes
        info = client.get_collection(collection_name)
        
        # The payload_schema is directly in info, not in info.config.params
        # Structure: info.payload_schema
        if not hasattr(info, 'payload_schema'):
            return {}
        
        payload_schema = info.payload_schema
        
        if not payload_schema:
            return {}
        
        indexes = {}
        
        # Iterate through the payload schema dictionary
        for field_name, field_schema in payload_schema.items():
            # field_schema has: data_type, params, points
            
            # Get the schema type (keyword, integer, text, etc.)
            if hasattr(field_schema, 'data_type'):
                schema_type = str(field_schema.data_type)
            else:
                schema_type = str(field_schema)
            
            # Extract the actual type name
            # e.g., "PayloadSchemaType.KEYWORD" -> "keyword" or just "text"
            if '.' in schema_type:
                schema_type = schema_type.split('.')[-1].lower()
            
            # Get the field parameters if available
            options = {}
            
            # Check for various index parameters
            if hasattr(field_schema, 'params') and field_schema.params:
                params = field_schema.params
                
                # Extract common options
                if hasattr(params, 'is_tenant'):
                    options['is_tenant'] = params.is_tenant
                if hasattr(params, 'is_principal'):
                    options['is_principal'] = params.is_principal
                if hasattr(params, 'on_disk'):
                    options['on_disk'] = params.on_disk
                
                # For text indexes
                if hasattr(params, 'tokenizer'):
                    tokenizer_str = str(params.tokenizer)
                    # Handle both "TokenizerType.WORD" and "word" formats
                    if '.' in tokenizer_str:
                        options['tokenizer'] = tokenizer_str.split('.')[-1].lower()
                    else:
                        options['tokenizer'] = tokenizer_str.lower()
                
                if hasattr(params, 'min_token_len'):
                    options['min_token_len'] = params.min_token_len
                if hasattr(params, 'max_token_len'):
                    options['max_token_len'] = params.max_token_len
                if hasattr(params, 'lowercase'):
                    options['lowercase'] = params.lowercase
            
            indexes[field_name] = {
                'type': schema_type,
                'options': options
            }
        
        return indexes
        
    except Exception as e:
        logger.warning(f"Could not retrieve existing indexes: {e}")
        logger.debug(f"Full error: {e}", exc_info=True)
        return {}


def create_manual_index(client: QdrantClient, collection_name: str, existing_indexes: Dict):
    """Create an index manually by specifying field name and type"""
    print(f"\n{'=' * 80}")
    print("MANUAL INDEX CREATION")
    print("=" * 80)
    
    # Get field name
    print("\nEnter the field name to index:")
    print("  Examples:")
    print("    - metadata.md5_hash")
    print("    - metadata.filename")
    print("    - metadata.page_number")
    print("    - pagecontent")
    
    field_name = input("\nField name: ").strip()
    
    if not field_name:
        logger.error("❌ Field name cannot be empty")
        return
    
    # Check if already indexed
    if field_name in existing_indexes:
        logger.warning(f"⚠️  Field '{field_name}' already has an index: {existing_indexes[field_name]['type']}")
        choice = input("Overwrite? (y/n) [n]: ").strip().lower()
        if choice != 'y':
            return
    
    # Select index type
    print(f"\n{'─' * 80}")
    print("SELECT INDEX TYPE:")
    print("─" * 80)
    print("  1. Keyword   - Exact string matching (IDs, hashes, filenames)")
    print("  2. Integer   - Whole numbers (counts, page numbers)")
    print("  3. Float     - Decimal numbers (scores, ratings)")
    print("  4. Bool      - True/false values")
    print("  5. DateTime  - Timestamps")
    print("  6. Text      - Full-text search")
    print("  0. Cancel")
    
    type_choice = input("\nSelect type (0-6): ").strip()
    
    type_map = {
        '1': ('keyword', models.PayloadSchemaType.KEYWORD),
        '2': ('integer', models.PayloadSchemaType.INTEGER),
        '3': ('float', models.PayloadSchemaType.FLOAT),
        '4': ('bool', models.PayloadSchemaType.BOOL),
        '5': ('datetime', models.PayloadSchemaType.DATETIME),
        '6': ('text', None)  # Text requires special handling
    }
    
    if type_choice == '0':
        return
    
    if type_choice not in type_map:
        logger.error("❌ Invalid choice")
        return
    
    type_name, schema_type = type_map[type_choice]
    
    # Create the index
    try:
        print(f"\n🔄 Creating {type_name} index for '{field_name}'...")
        
        if type_choice == '6':  # Text index
            # Text index requires TextIndexParams
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=models.TextIndexParams(
                    type="text",
                    tokenizer=models.TokenizerType.WORD,
                    min_token_len=1,
                    max_token_len=15,
                    lowercase=True
                ),
                wait=True
            )
        else:
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=schema_type,
                wait=True
            )
        
        logger.info(f"✅ Index created successfully!")
        logger.info(f"   Field: {field_name}")
        logger.info(f"   Type: {type_name}")
        
    except Exception as e:
        logger.error(f"❌ Failed to create index: {e}")


def process_collection(client: QdrantClient, collection_name: str, collection_label: str, all_collections: list):
    """Process a single collection"""
    print_section_header(f"{collection_label} Collection: {collection_name}")
    
    # Check if collection exists
    if not any(c.name == collection_name for c in all_collections):
        logger.warning(f"⚠️  Collection '{collection_name}' not found.")
        input("\nPress Enter to continue...")
        return
    
    # Get collection info
    info = client.get_collection(collection_name)
    print(f"\nCollection Info:")
    print(f"  Points: {info.points_count:,}")
    print(f"  Vector Size: {info.config.params.vectors.size}D")
    print(f"  Distance Metric: {info.config.params.vectors.distance}")
    
    # Show existing indexes
    existing_indexes = get_existing_indexes(client, collection_name)
    if existing_indexes:
        print(f"\n📋 Existing Payload Indexes:")
        print("─" * 80)
        for field_name, index_info in existing_indexes.items():
            index_type = index_info['type']
            options = index_info['options']
            
            # Format options nicely
            if options:
                # For text indexes, show tokenizer info prominently
                if index_type == 'text' and 'tokenizer' in options:
                    opts_parts = [f"tokenizer={options['tokenizer']}"]
                    if 'min_token_len' in options:
                        opts_parts.append(f"min={options['min_token_len']}")
                    if 'max_token_len' in options:
                        opts_parts.append(f"max={options['max_token_len']}")
                    if 'lowercase' in options:
                        opts_parts.append(f"lowercase={options['lowercase']}")
                    opts_str = ", ".join(opts_parts)
                else:
                    opts_str = ", ".join(f"{k}={v}" for k, v in options.items())
                
                print(f"  ✓ {field_name:<30} → {index_type:<10} ({opts_str})")
            else:
                print(f"  ✓ {field_name:<30} → {index_type}")
        print("─" * 80)
    else:
        print(f"\n📋 Existing Payload Indexes: None")
    
    # Check if collection is empty
    if info.points_count == 0:
        logger.warning(f"⚠️  Collection is empty. You can still create indexes for future data.")
        
        # Allow manual index creation for empty collections
        print(f"\n{'─' * 80}")
        print("OPTIONS:")
        print("  1. Create index manually (specify field name and type)")
        print("  0. Go back")
        
        choice = input(f"\nSelect option (0-1): ").strip()
        
        if choice == '1':
            create_manual_index(client, collection_name, existing_indexes)
        
        return
    
    # Get sample payload and extract fields
    logger.info("\nAnalyzing payload structure...")
    sample_payload = get_sample_payload(client, collection_name)
    
    if not sample_payload:
        logger.warning(f"⚠️  Could not get sample payload.")
        
        # Allow manual index creation even without sample
        print(f"\n{'─' * 80}")
        print("OPTIONS:")
        print("  1. Create index manually (specify field name and type)")
        print("  0. Go back")
        
        choice = input(f"\nSelect option (0-1): ").strip()
        
        if choice == '1':
            create_manual_index(client, collection_name, existing_indexes)
        
        return
    
    fields = extract_metadata_fields(sample_payload)
    
    # Update field suggestions with actual existing indexes
    for field in fields:
        field_path = field['path']
        if field_path in existing_indexes:
            # Override suggestion with actual index type
            actual_type = existing_indexes[field_path]['type']
            # Map type to index type key
            type_map = {
                'keyword': 'keyword',
                'integer': 'integer',
                'float': 'float',
                'bool': 'bool',
                'geo': 'geo',
                'datetime': 'datetime',
                'uuid': 'uuid',
                'text': 'text'
            }
            if actual_type in type_map:
                field['suggested_index'] = type_map[actual_type]
                field['has_index'] = True
            else:
                field['has_index'] = False
        else:
            field['has_index'] = False
    
    # Process fields one by one
    while True:
        continue_collection = process_single_field(client, collection_name, fields, existing_indexes)
        
        if not continue_collection:
            # User chose to go back to collection selection
            break
        
        # Refresh existing indexes after each field
        existing_indexes = get_existing_indexes(client, collection_name)
        
        # Update field suggestions again
        for field in fields:
            field_path = field['path']
            if field_path in existing_indexes:
                actual_type = existing_indexes[field_path]['type']
                type_map = {
                    'keyword': 'keyword',
                    'integer': 'integer',
                    'float': 'float',
                    'bool': 'bool',
                    'geo': 'geo',
                    'datetime': 'datetime',
                    'uuid': 'uuid',
                    'text': 'text'
                }
                if actual_type in type_map:
                    field['suggested_index'] = type_map[actual_type]
                    field['has_index'] = True
            else:
                field['has_index'] = False
        
        # Ask if user wants to index another field in this collection
        print(f"\n{'─' * 80}")
        choice = input(f"Index another field in '{collection_name}'? (y/n) [y]: ").strip().lower()
        
        if choice == 'n':
            break


def main():
    """Main interactive function"""
    load_dotenv()
    
    # Get connection details
    qdrant_host = os.getenv("QDRANT_HOST", "192.168.254.22")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    qdrant_use_https = os.getenv("QDRANT_USE_HTTPS", "false").lower() == "true"
    qdrant_use_grpc = os.getenv("QDRANT_USE_GRPC", "false").lower() == "true"
    
    filename_collection = os.getenv("QDRANT_FILENAME_COLLECTION", "filenames")
    content_collection = os.getenv("QDRANT_CONTENT_COLLECTION", "content")
    
    print_section_header("QDRANT ADVANCED PAYLOAD INDEX CREATOR")
    print(f"\nQdrant Server: {qdrant_host}:{qdrant_port}")
    print(f"Filename Collection: {filename_collection}")
    print(f"Content Collection: {content_collection}")
    
    # Connect to Qdrant
    try:
        logger.info("\nConnecting to Qdrant...")
        
        # Determine connection mode based on .env settings
        # Production mode: HTTPS enabled OR API key present OR cloud.qdrant.io hostname
        is_production = qdrant_use_https or qdrant_api_key or 'cloud.qdrant.io' in qdrant_host
        
        if is_production:
            # Production mode: Use URL with protocol from .env settings
            if qdrant_use_grpc:
                protocol = 'grpc'
            elif qdrant_use_https:
                protocol = 'https'
            else:
                # Default to HTTPS if API key is present
                protocol = 'https'
            
            url = f"{protocol}://{qdrant_host}:{qdrant_port}"
            logger.info(f"  Mode: PRODUCTION ({protocol.upper()})")
            if qdrant_api_key:
                logger.info("  Authentication: API Key enabled")
            client = QdrantClient(url=url, api_key=qdrant_api_key)
        else:
            # Development mode: Simple HTTP connection
            logger.info("  Mode: DEVELOPMENT (HTTP)")
            client = QdrantClient(host=qdrant_host, port=qdrant_port)
        
        collections = client.get_collections()
        logger.info(f"✅ Connected! Found {len(collections.collections)} collections\n")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Qdrant: {e}")
        return 1
    
    # Available collections
    collections_map = {
        '1': (filename_collection, "Filename"),
        '2': (content_collection, "Content")
    }
    
    # Main loop: collection selection
    while True:
        print("=" * 80)
        print("SELECT COLLECTION TO INDEX")
        print("=" * 80)
        print(f"\n  1. {filename_collection} (Filename Collection)")
        print(f"  2. {content_collection} (Content Collection)")
        print(f"  0. Exit")
        
        choice = input(f"\nSelect collection (0-2): ").strip()
        
        if choice == '0':
            print("\n" + "=" * 80)
            print("🎉 INDEX CREATION SESSION COMPLETE!")
            print("=" * 80)
            break
        
        if choice in collections_map:
            collection_name, collection_label = collections_map[choice]
            process_collection(client, collection_name, collection_label, collections.collections)
        else:
            print(f"❌ Invalid choice. Please enter 0-2")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
