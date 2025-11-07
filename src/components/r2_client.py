"""Cloudflare R2 client for S3-compatible operations"""

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError
from typing import List, Dict, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class R2Client:
    """Client for interacting with Cloudflare R2 (S3-compatible)"""
    
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str
    ):
        """
        Initialize R2 client
        
        Args:
            endpoint: R2 endpoint URL
            access_key: R2 access key
            secret_key: R2 secret key
            bucket_name: R2 bucket name
        """
        self.bucket_name = bucket_name
        self.client = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        
        # Transfer configuration for large files
        self.transfer_config = TransferConfig(
            multipart_threshold=1024 * 25,  # 25MB
            max_concurrency=10,
            multipart_chunksize=1024 * 25,
            use_threads=True
        )
        
        logger.info(f"R2 client initialized for bucket: {bucket_name}")
    
    def list_files(
        self,
        prefix: str = "",
        recursive: bool = True
    ) -> List[Dict[str, any]]:
        """
        List files in R2 bucket
        
        Args:
            prefix: Prefix to filter files (e.g., "source/")
            recursive: If True, list all files recursively
            
        Returns:
            List of file metadata dictionaries with keys:
            - key: Full object key
            - size: File size in bytes
            - last_modified: Last modification timestamp
            - etag: ETag of the object
        """
        try:
            files = []
            paginator = self.client.get_paginator('list_objects_v2')
            
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            for page in page_iterator:
                if 'Contents' not in page:
                    continue
                    
                for obj in page['Contents']:
                    # Skip directories (keys ending with /)
                    if obj['Key'].endswith('/'):
                        continue
                    
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'etag': obj['ETag'].strip('"')
                    })
            
            logger.info(f"Listed {len(files)} files with prefix: {prefix}")
            return files
            
        except ClientError as e:
            logger.error(f"Error listing files: {e}")
            raise
    
    def download_file(
        self,
        object_key: str,
        local_path: str
    ) -> bool:
        """
        Download file from R2 to local path
        
        Args:
            object_key: R2 object key
            local_path: Local file path to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create parent directories if they don't exist
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.client.download_file(
                self.bucket_name,
                object_key,
                local_path,
                Config=self.transfer_config
            )
            
            logger.info(f"Downloaded: {object_key} -> {local_path}")
            return True
            
        except ClientError as e:
            logger.error(f"Error downloading {object_key}: {e}")
            return False
    
    def download_file_to_memory(self, object_key: str) -> Optional[bytes]:
        """
        Download file from R2 to memory
        
        Args:
            object_key: R2 object key
            
        Returns:
            File content as bytes, or None if error
        """
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            content = response['Body'].read()
            logger.info(f"Downloaded to memory: {object_key} ({len(content)} bytes)")
            return content
            
        except ClientError as e:
            logger.error(f"Error downloading {object_key} to memory: {e}")
            return None
    
    def upload_file(
        self,
        local_path: str,
        object_key: str,
        extra_args: Optional[Dict] = None
    ) -> bool:
        """
        Upload file from local path to R2
        
        Args:
            local_path: Local file path
            object_key: R2 object key
            extra_args: Optional extra arguments (e.g., ACL, metadata)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.upload_file(
                local_path,
                self.bucket_name,
                object_key,
                Config=self.transfer_config,
                ExtraArgs=extra_args or {}
            )
            
            logger.info(f"Uploaded: {local_path} -> {object_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error uploading {local_path}: {e}")
            return False
    
    def upload_from_memory(
        self,
        content: bytes,
        object_key: str,
        extra_args: Optional[Dict] = None
    ) -> bool:
        """
        Upload content from memory to R2
        
        Args:
            content: File content as bytes
            object_key: R2 object key
            extra_args: Optional extra arguments
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=content,
                **(extra_args or {})
            )
            
            logger.info(f"Uploaded from memory: {object_key} ({len(content)} bytes)")
            return True
            
        except ClientError as e:
            logger.error(f"Error uploading to {object_key}: {e}")
            return False
    
    def file_exists(self, object_key: str) -> bool:
        """
        Check if file exists in R2
        
        Args:
            object_key: R2 object key
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return True
        except ClientError:
            return False
    
    def get_file_metadata(self, object_key: str) -> Optional[Dict]:
        """
        Get file metadata from R2
        
        Args:
            object_key: R2 object key
            
        Returns:
            Metadata dictionary or None if error
        """
        try:
            response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'etag': response['ETag'].strip('"'),
                'content_type': response.get('ContentType', '')
            }
        except ClientError as e:
            logger.error(f"Error getting metadata for {object_key}: {e}")
            return None


if __name__ == "__main__":
    # Test R2 client
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    client = R2Client(
        endpoint=os.getenv("R2_ENDPOINT"),
        access_key=os.getenv("R2_ACCESS_KEY"),
        secret_key=os.getenv("R2_SECRET_KEY"),
        bucket_name=os.getenv("R2_BUCKET_NAME")
    )
    
    # List files in source directory
    files = client.list_files(prefix="source/")
    print(f"Found {len(files)} files in source/")
    for f in files[:5]:  # Show first 5
        print(f"  - {f['key']} ({f['size']} bytes)")
