"""Semantic chunking for markdown content"""

from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken
import logging
import re

logger = logging.getLogger(__name__)


class Chunk:
    """Represents a text chunk with metadata"""
    
    def __init__(
        self,
        text: str,
        filename: str,
        chunk_number: int,
        element_type: str,
        md5_hash: str
    ):
        self.text = text
        self.filename = filename
        self.chunk_number = chunk_number
        self.element_type = element_type
        self.md5_hash = md5_hash
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for Qdrant upload"""
        return {
            "text": self.text,
            "metadata": {
                "filename": self.filename,
                "page_number": self.chunk_number,
                "element_type": self.element_type,
                "md5_hash": self.md5_hash
            }
        }


class SemanticChunker:
    """Semantic chunking of markdown content"""
    
    def __init__(
        self,
        chunk_size_tokens: int = 500,
        chunk_overlap_tokens: int = 0
    ):
        """
        Initialize semantic chunker
        
        Args:
            chunk_size_tokens: Target chunk size in tokens
            chunk_overlap_tokens: Overlap between chunks in tokens
        """
        self.chunk_size_tokens = chunk_size_tokens
        self.chunk_overlap_tokens = chunk_overlap_tokens
        
        # Initialize tokenizer for token counting
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Initialize text splitter
        # Approximate: 1 token ≈ 4 characters
        chunk_size_chars = chunk_size_tokens * 4
        chunk_overlap_chars = chunk_overlap_tokens * 4
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size_chars,
            chunk_overlap=chunk_overlap_chars,
            length_function=self._count_tokens,
            separators=[
                "\n\n\n",  # Multiple blank lines
                "\n\n",    # Paragraph breaks
                "\n",      # Line breaks
                ". ",      # Sentences
                " ",       # Words
                ""         # Characters
            ]
        )
        
        logger.info(f"Chunker initialized: {chunk_size_tokens} tokens, {chunk_overlap_tokens} overlap")
    
    def _count_tokens(self, text: str) -> int:
        """
        Count tokens in text
        
        Args:
            text: Text to count
            
        Returns:
            Number of tokens
        """
        return len(self.tokenizer.encode(text))
    
    def _detect_element_type(self, text: str) -> str:
        """
        Detect element type from markdown syntax
        
        Args:
            text: Chunk text
            
        Returns:
            Element type: Text, Table, Image, List, Code
        """
        # Check for table (markdown table syntax)
        if '|' in text and ('---' in text or '|-' in text):
            return "Table"
        
        # Check for image (markdown image syntax)
        if re.search(r'!\[.*?\]\(.*?\)', text):
            return "Image"
        
        # Check for code block
        if '```' in text or text.strip().startswith('    '):
            return "Code"
        
        # Check for list (markdown list syntax)
        if re.search(r'^[\s]*[-*+]\s', text, re.MULTILINE) or \
           re.search(r'^[\s]*\d+\.\s', text, re.MULTILINE):
            return "List"
        
        # Default to text
        return "Text"
    
    def chunk_markdown(
        self,
        markdown_content: str,
        filename: str,
        file_hasher
    ) -> List[Chunk]:
        """
        Chunk markdown content semantically
        
        Args:
            markdown_content: Markdown content as string
            filename: Source filename (with extension for metadata)
            file_hasher: FileHasher instance for generating hashes
            
        Returns:
            List of Chunk objects
        """
        try:
            # Split text into chunks
            text_chunks = self.text_splitter.split_text(markdown_content)
            
            chunks = []
            for i, text in enumerate(text_chunks, start=1):
                # Detect element type
                element_type = self._detect_element_type(text)
                
                # Generate hash for chunk content
                chunk_hash = file_hasher.hash_text(text)
                
                # Create chunk object
                chunk = Chunk(
                    text=text,
                    filename=filename,
                    chunk_number=i,
                    element_type=element_type,
                    md5_hash=chunk_hash
                )
                
                chunks.append(chunk)
            
            logger.info(f"Created {len(chunks)} chunks from {filename}")
            
            # Log chunk statistics
            token_counts = [self._count_tokens(c.text) for c in chunks]
            avg_tokens = sum(token_counts) / len(token_counts) if token_counts else 0
            logger.debug(f"Chunk stats - Avg tokens: {avg_tokens:.1f}, Min: {min(token_counts) if token_counts else 0}, Max: {max(token_counts) if token_counts else 0}")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking markdown: {e}")
            return []
    
    def get_chunk_stats(self, chunks: List[Chunk]) -> Dict:
        """
        Get statistics about chunks
        
        Args:
            chunks: List of chunks
            
        Returns:
            Dictionary with statistics
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_tokens": 0,
                "min_tokens": 0,
                "max_tokens": 0,
                "element_types": {}
            }
        
        token_counts = [self._count_tokens(c.text) for c in chunks]
        element_types = {}
        
        for chunk in chunks:
            element_types[chunk.element_type] = element_types.get(chunk.element_type, 0) + 1
        
        return {
            "total_chunks": len(chunks),
            "avg_tokens": sum(token_counts) / len(token_counts),
            "min_tokens": min(token_counts),
            "max_tokens": max(token_counts),
            "element_types": element_types
        }


if __name__ == "__main__":
    # Test chunker
    from file_hasher import FileHasher
    
    test_markdown = """
# Test Document

This is a test paragraph with some content.

## Section 1

Here's a list:
- Item 1
- Item 2
- Item 3

## Section 2

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |

Some more text here.

```python
def example():
    return "code"
```
"""
    
    chunker = SemanticChunker(chunk_size_tokens=100, chunk_overlap_tokens=0)
    hasher = FileHasher()
    
    chunks = chunker.chunk_markdown(test_markdown, "test.pdf", hasher)
    
    print(f"Created {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"\nChunk {chunk.chunk_number} ({chunk.element_type}):")
        print(f"  Tokens: {chunker._count_tokens(chunk.text)}")
        print(f"  Hash: {chunk.md5_hash[:16]}...")
        print(f"  Preview: {chunk.text[:100]}...")
    
    stats = chunker.get_chunk_stats(chunks)
    print(f"\nStats: {stats}")
