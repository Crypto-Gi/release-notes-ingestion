#!/usr/bin/env python3
"""
Diagnostic script to investigate R2 markdown files
Helps identify why certain directories might not be processed
"""

import sys
import os
from pathlib import Path
from collections import defaultdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from components.config import load_config
from components.r2_client import R2Client
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def diagnose_r2_markdown():
    """Diagnose R2 markdown files and directory structure"""
    
    logger.info("=" * 70)
    logger.info("R2 Markdown Diagnostic Tool")
    logger.info("=" * 70)
    
    # Load config
    config = load_config()
    
    # Initialize R2 client
    r2_client = R2Client(
        endpoint=config.r2.endpoint,
        access_key=config.r2.access_key,
        secret_key=config.r2.secret_key,
        bucket_name=config.r2.bucket_name
    )
    
    logger.info(f"\n📦 Bucket: {config.r2.bucket_name}")
    logger.info(f"📁 Markdown prefix: {config.r2.markdown_prefix}")
    
    # List all files
    logger.info(f"\n🔍 Listing all files under '{config.r2.markdown_prefix}'...")
    all_files = r2_client.list_files(prefix=config.r2.markdown_prefix)
    
    logger.info(f"✅ Found {len(all_files)} total files")
    
    if not all_files:
        logger.warning("⚠️  No files found! Check your R2 configuration.")
        return
    
    # Analyze files
    stats = {
        'total': len(all_files),
        'markdown': 0,
        'other': 0,
        'by_extension': defaultdict(int),
        'by_directory': defaultdict(int),
        'by_depth': defaultdict(int)
    }
    
    markdown_files = []
    other_files = []
    
    for file_info in all_files:
        key = file_info['key']
        
        # Extension analysis
        ext = Path(key).suffix.lower()
        stats['by_extension'][ext if ext else '(no extension)'] += 1
        
        # Directory analysis
        parts = key.split('/')
        depth = len(parts) - 1  # Subtract filename
        stats['by_depth'][depth] += 1
        
        if len(parts) > 2:  # Has subdirectory
            dir_name = parts[1]  # First directory after markdown/
            stats['by_directory'][dir_name] += 1
        
        # Markdown check (case-insensitive)
        if key.lower().endswith('.md'):
            stats['markdown'] += 1
            markdown_files.append(file_info)
        else:
            stats['other'] += 1
            other_files.append(file_info)
    
    # Print results
    logger.info("\n" + "=" * 70)
    logger.info("📊 FILE STATISTICS")
    logger.info("=" * 70)
    
    logger.info(f"\n📄 Total files: {stats['total']}")
    logger.info(f"   ✅ Markdown files (.md): {stats['markdown']}")
    logger.info(f"   ⚠️  Other files: {stats['other']}")
    
    # Extensions
    logger.info(f"\n📝 Files by extension:")
    for ext, count in sorted(stats['by_extension'].items(), key=lambda x: -x[1]):
        logger.info(f"   {ext}: {count} files")
    
    # Directories
    if stats['by_directory']:
        logger.info(f"\n📁 Files by top-level directory:")
        for dir_name, count in sorted(stats['by_directory'].items()):
            logger.info(f"   {dir_name}/: {count} files")
    
    # Depth
    logger.info(f"\n🌳 Files by directory depth:")
    for depth, count in sorted(stats['by_depth'].items()):
        logger.info(f"   Level {depth}: {count} files")
    
    # Show sample files from each directory
    if stats['by_directory']:
        logger.info("\n" + "=" * 70)
        logger.info("📂 SAMPLE FILES BY DIRECTORY")
        logger.info("=" * 70)
        
        samples_by_dir = defaultdict(list)
        for f in markdown_files:
            parts = f['key'].split('/')
            if len(parts) > 2:
                dir_name = parts[1]
                if len(samples_by_dir[dir_name]) < 3:  # Keep first 3
                    samples_by_dir[dir_name].append(f['key'])
        
        for dir_name in sorted(samples_by_dir.keys()):
            logger.info(f"\n📁 {dir_name}/ ({stats['by_directory'][dir_name]} files)")
            for key in samples_by_dir[dir_name]:
                size_kb = [f['size'] for f in markdown_files if f['key'] == key][0] / 1024
                logger.info(f"   - {key} ({size_kb:.1f} KB)")
    
    # Show non-markdown files if any
    if other_files:
        logger.info("\n" + "=" * 70)
        logger.info("⚠️  NON-MARKDOWN FILES (will be skipped)")
        logger.info("=" * 70)
        
        for f in other_files[:10]:  # Show first 10
            logger.info(f"   - {f['key']}")
        
        if len(other_files) > 10:
            logger.info(f"   ... and {len(other_files) - 10} more")
    
    # Check for potential issues
    logger.info("\n" + "=" * 70)
    logger.info("🔍 POTENTIAL ISSUES")
    logger.info("=" * 70)
    
    issues_found = False
    
    # Check for uppercase extensions
    uppercase_md = [f for f in all_files if f['key'].endswith('.MD') or f['key'].endswith('.Md')]
    if uppercase_md:
        issues_found = True
        logger.warning(f"\n⚠️  Found {len(uppercase_md)} files with uppercase .MD extension")
        logger.warning("   These will NOW be processed (case-insensitive filter)")
        for f in uppercase_md[:5]:
            logger.warning(f"   - {f['key']}")
    
    # Check for .markdown extension
    markdown_ext = [f for f in all_files if f['key'].lower().endswith('.markdown')]
    if markdown_ext:
        issues_found = True
        logger.warning(f"\n⚠️  Found {len(markdown_ext)} files with .markdown extension")
        logger.warning("   These will be SKIPPED (only .md is processed)")
        for f in markdown_ext[:5]:
            logger.warning(f"   - {f['key']}")
    
    # Check for empty directories
    if not stats['by_directory']:
        issues_found = True
        logger.warning("\n⚠️  No subdirectories found under markdown/")
        logger.warning("   All files are directly in markdown/ folder")
    
    if not issues_found:
        logger.info("\n✅ No obvious issues found!")
        logger.info("   All files appear to be properly formatted .md files")
    
    # Final summary
    logger.info("\n" + "=" * 70)
    logger.info("📋 SUMMARY")
    logger.info("=" * 70)
    logger.info(f"\n✅ {stats['markdown']} markdown files will be processed")
    logger.info(f"⏭️  {stats['other']} files will be skipped")
    
    if stats['by_directory']:
        logger.info(f"\n📁 Directories with markdown files:")
        for dir_name, count in sorted(stats['by_directory'].items()):
            logger.info(f"   - {dir_name}/: {count} files")
    
    logger.info("\n" + "=" * 70)
    logger.info("Diagnostic complete!")
    logger.info("=" * 70)


if __name__ == "__main__":
    try:
        diagnose_r2_markdown()
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
