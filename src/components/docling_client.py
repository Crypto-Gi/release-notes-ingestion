"""Docling service client for PDF/Word to Markdown conversion"""

import requests
import time
from typing import Optional, Dict
from pathlib import Path
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class DoclingClient:
    """Client for interacting with Docling service"""
    
    def __init__(
        self,
        base_url: str,
        timeout: int = 300,
        poll_interval: int = 2
    ):
        """
        Initialize Docling client
        
        Args:
            base_url: Docling service base URL (e.g., http://docling.mynetwork.ing)
            timeout: Request timeout in seconds
            poll_interval: Status poll interval in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.poll_interval = poll_interval
        
        logger.info(f"Docling client initialized: {base_url}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _post_file(self, file_path: str) -> str:
        """
        Upload file to Docling for conversion
        
        Args:
            file_path: Path to file
            
        Returns:
            Task ID
            
        Raises:
            Exception: If upload fails
        """
        url = f"{self.base_url}/api/convert"
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (Path(file_path).name, f)}
                response = requests.post(
                    url,
                    files=files,
                    timeout=30  # Upload timeout
                )
                response.raise_for_status()
            
            data = response.json()
            task_id = data.get('task_id')
            
            if not task_id:
                raise ValueError("No task_id in response")
            
            logger.info(f"File uploaded to Docling: {file_path} -> task_id: {task_id}")
            return task_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error uploading file to Docling: {e}")
            raise
    
    def _poll_status(self, task_id: str) -> Dict:
        """
        Poll conversion status until complete or timeout
        
        Args:
            task_id: Task ID from upload
            
        Returns:
            Status response
            
        Raises:
            TimeoutError: If conversion times out
            Exception: If conversion fails
        """
        url = f"{self.base_url}/api/status/{task_id}"
        start_time = time.time()
        
        while True:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                status = data.get('status', '').lower()
                
                if status == 'completed':
                    logger.info(f"Conversion completed: {task_id}")
                    return data
                
                elif status == 'failed':
                    error = data.get('error', 'Unknown error')
                    logger.error(f"Conversion failed: {task_id} - {error}")
                    raise Exception(f"Docling conversion failed: {error}")
                
                elif status in ['processing', 'pending', 'queued']:
                    # Check timeout
                    elapsed = time.time() - start_time
                    if elapsed > self.timeout:
                        raise TimeoutError(f"Conversion timeout after {elapsed:.1f}s")
                    
                    # Wait before next poll
                    time.sleep(self.poll_interval)
                    logger.debug(f"Polling status: {task_id} - {status} ({elapsed:.1f}s)")
                
                else:
                    logger.warning(f"Unknown status: {status}")
                    time.sleep(self.poll_interval)
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Error polling status: {e}")
                raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _get_markdown(self, task_id: str) -> str:
        """
        Get markdown content from completed conversion
        
        Args:
            task_id: Task ID
            
        Returns:
            Markdown content as string
            
        Raises:
            Exception: If retrieval fails
        """
        url = f"{self.base_url}/api/result/{task_id}/json"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            markdown_content = data.get('markdown_content')
            
            if not markdown_content:
                raise ValueError("No markdown_content in response")
            
            logger.info(f"Retrieved markdown: {task_id} ({len(markdown_content)} chars)")
            return markdown_content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting markdown: {e}")
            raise
    
    def convert_to_markdown(self, file_path: str) -> Optional[str]:
        """
        Convert PDF/Word file to Markdown
        
        Args:
            file_path: Path to PDF or Word file
            
        Returns:
            Markdown content as string, or None if conversion fails
        """
        try:
            # Step 1: Upload file
            logger.info(f"Converting file: {file_path}")
            task_id = self._post_file(file_path)
            
            # Step 2: Poll status
            self._poll_status(task_id)
            
            # Step 3: Get markdown
            markdown = self._get_markdown(task_id)
            
            logger.info(f"Conversion successful: {file_path}")
            return markdown
            
        except TimeoutError as e:
            logger.error(f"Conversion timeout: {file_path} - {e}")
            return None
            
        except Exception as e:
            logger.error(f"Conversion failed: {file_path} - {e}")
            return None
    
    def convert_from_memory(
        self,
        file_content: bytes,
        filename: str
    ) -> Optional[str]:
        """
        Convert file from memory to Markdown
        
        Args:
            file_content: File content as bytes
            filename: Original filename (for extension detection)
            
        Returns:
            Markdown content as string, or None if conversion fails
        """
        url = f"{self.base_url}/api/convert"
        
        try:
            # Upload from memory
            files = {'file': (filename, file_content)}
            response = requests.post(url, files=files, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            task_id = data.get('task_id')
            
            if not task_id:
                raise ValueError("No task_id in response")
            
            logger.info(f"File uploaded from memory: {filename} -> {task_id}")
            
            # Poll and get markdown
            self._poll_status(task_id)
            markdown = self._get_markdown(task_id)
            
            logger.info(f"Conversion from memory successful: {filename}")
            return markdown
            
        except Exception as e:
            logger.error(f"Conversion from memory failed: {filename} - {e}")
            return None
    
    def health_check(self) -> bool:
        """
        Check if Docling service is healthy
        
        Returns:
            True if service is reachable
        """
        try:
            url = f"{self.base_url}/healthz"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Docling health check failed: {e}")
            return False


if __name__ == "__main__":
    # Test Docling client
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    client = DoclingClient(
        base_url=os.getenv("DOCLING_BASE_URL", "http://docling.mynetwork.ing")
    )
    
    # Health check
    if client.health_check():
        print("✅ Docling service is healthy")
    else:
        print("❌ Docling service is not reachable")
