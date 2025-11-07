"""Markdown storage manager for R2"""

from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class MarkdownStorage:
    """Manages markdown file storage in R2 with mirrored directory structure"""
    
    def __init__(
        self,
        r2_client,
        source_prefix: str = "source/",
        markdown_prefix: str = "markdown/"
    ):
        """
        Initialize markdown storage
        
        Args:
            r2_client: R2Client instance
            source_prefix: Source files prefix in R2
            markdown_prefix: Markdown files prefix in R2
        """
        self.r2_client = r2_client
        self.source_prefix = source_prefix.rstrip('/') + '/'
        self.markdown_prefix = markdown_prefix.rstrip('/') + '/'
        
        logger.info(f"Markdown storage initialized: {source_prefix} -> {markdown_prefix}")
    
    def transform_path(self, source_key: str) -> str:
        """
        Transform source path to markdown path
        
        Maintains directory structure:
        source/orchestrator/release1/file.pdf -> markdown/orchestrator/release1/file.md
        
        Args:
            source_key: Source file key in R2
            
        Returns:
            Markdown file key in R2
        """
        # Remove source prefix
        if source_key.startswith(self.source_prefix):
            relative_path = source_key[len(self.source_prefix):]
        else:
            relative_path = source_key
        
        # Change extension to .md
        path = Path(relative_path)
        markdown_filename = path.stem + '.md'
        markdown_path = str(path.parent / markdown_filename)
        
        # Add markdown prefix
        markdown_key = self.markdown_prefix + markdown_path
        
        logger.debug(f"Path transform: {source_key} -> {markdown_key}")
        return markdown_key
    
    def upload_markdown(
        self,
        source_key: str,
        markdown_content: str
    ) -> bool:
        """
        Upload markdown content to R2
        
        Args:
            source_key: Original source file key
            markdown_content: Markdown content as string
            
        Returns:
            True if successful
        """
        try:
            # Transform path
            markdown_key = self.transform_path(source_key)
            
            # Upload to R2
            success = self.r2_client.upload_from_memory(
                content=markdown_content.encode('utf-8'),
                object_key=markdown_key,
                extra_args={'ContentType': 'text/markdown'}
            )
            
            if success:
                logger.info(f"Uploaded markdown: {markdown_key}")
            else:
                logger.error(f"Failed to upload markdown: {markdown_key}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error uploading markdown: {e}")
            return False
    
    def markdown_exists(self, source_key: str) -> bool:
        """
        Check if markdown file already exists in R2
        
        Args:
            source_key: Original source file key
            
        Returns:
            True if markdown exists
        """
        markdown_key = self.transform_path(source_key)
        return self.r2_client.file_exists(markdown_key)
    
    def get_markdown(self, source_key: str) -> Optional[str]:
        """
        Download markdown content from R2
        
        Args:
            source_key: Original source file key
            
        Returns:
            Markdown content as string, or None if not found
        """
        try:
            markdown_key = self.transform_path(source_key)
            content = self.r2_client.download_file_to_memory(markdown_key)
            
            if content:
                return content.decode('utf-8')
            return None
            
        except Exception as e:
            logger.error(f"Error getting markdown: {e}")
            return None
    
    def get_markdown_key(self, source_key: str) -> str:
        """
        Get markdown key for a source key
        
        Args:
            source_key: Source file key
            
        Returns:
            Markdown file key
        """
        return self.transform_path(source_key)


if __name__ == "__main__":
    # Test path transformation
    storage = MarkdownStorage(None)
    
    test_cases = [
        "source/orchestrator/release1/file.pdf",
        "source/ecos/release2/notes.docx",
        "source/srx/file.pdf"
    ]
    
    print("Path transformations:")
    for source in test_cases:
        markdown = storage.transform_path(source)
        print(f"  {source}")
        print(f"  -> {markdown}\n")
