import os
import logging
import hashlib
from typing import List, Optional, Dict
from datetime import datetime
import requests
from b2sdk.v1 import B2Api, InMemoryAccountInfo
from b2sdk.v1.exception import B2Error

logger = logging.getLogger(__name__)


class BackblazeStorage:
    def __init__(self):
        self.application_key_id = os.getenv('B2_APPLICATION_KEY_ID')
        self.application_key = os.getenv('B2_APPLICATION_KEY')
        self.bucket_name = os.getenv('B2_BUCKET_NAME', 'parking-citations')
        
        self.api = None
        self.bucket = None
        
        if self.application_key_id and self.application_key:
            self._initialize_api()
        else:
            logger.warning("Backblaze B2 credentials not configured")
    
    def _initialize_api(self):
        """Initialize the B2 API connection"""
        try:
            account_info = InMemoryAccountInfo()
            self.api = B2Api(account_info)
            self.api.authorize_account("production", self.application_key_id, self.application_key)
            
            # Get or create bucket
            try:
                self.bucket = self.api.get_bucket_by_name(self.bucket_name)
                logger.info(f"Connected to existing B2 bucket: {self.bucket_name}")
            except B2Error:
                # Create bucket if it doesn't exist
                self.bucket = self.api.create_bucket(self.bucket_name, bucket_type="allPrivate")
                logger.info(f"Created new B2 bucket: {self.bucket_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Backblaze B2 API: {e}")
            self.api = None
            self.bucket = None
    
    def is_configured(self) -> bool:
        """Check if Backblaze B2 is properly configured"""
        return self.api is not None and self.bucket is not None
    
    def upload_image(self, image_url: str, citation_number: int, image_index: int = 0) -> Optional[Dict]:
        """
        Download an image from URL and upload it to Backblaze B2
        
        Args:
            image_url: URL of the image to download
            citation_number: Citation number for organizing files
            image_index: Index of the image for this citation
            
        Returns:
            Dict with upload info or None if failed
        """
        if not self.is_configured():
            logger.warning("Backblaze B2 not configured, skipping image upload")
            return None
        
        try:
            # Download image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Generate filename with citation number and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = self._get_file_extension(image_url, response.headers.get('content-type'))
            filename = f"citations/{citation_number}/{citation_number}_{image_index}_{timestamp}{file_extension}"
            
            # Generate content hash for deduplication
            content_hash = hashlib.sha1(response.content).hexdigest()
            
            # Upload to B2
            file_info = self.bucket.upload_bytes(
                response.content,
                filename,
                content_type=response.headers.get('content-type', 'image/jpeg'),
                file_infos={
                    'citation_number': str(citation_number),
                    'original_url': image_url,
                    'upload_timestamp': timestamp,
                    'content_hash': content_hash
                }
            )
            
            logger.info(f"Uploaded image to B2: {filename}")
            
            return {
                'filename': filename,
                'file_id': file_info.id_,
                'download_url': self._get_download_url(filename),
                'size_bytes': len(response.content),
                'content_type': response.headers.get('content-type'),
                'content_hash': content_hash,
                'upload_timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Failed to upload image {image_url}: {e}")
            return None
    
    def upload_images_for_citation(self, image_urls: List[str], citation_number: int) -> List[Dict]:
        """
        Upload all images for a citation
        
        Args:
            image_urls: List of image URLs
            citation_number: Citation number
            
        Returns:
            List of upload results
        """
        results = []
        
        for i, image_url in enumerate(image_urls):
            result = self.upload_image(image_url, citation_number, i)
            if result:
                results.append(result)
        
        return results
    
    def _get_file_extension(self, url: str, content_type: str) -> str:
        """Determine file extension from URL or content type"""
        # Try to get extension from URL
        if '.' in url:
            ext = url.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                return f'.{ext}'
        
        # Fall back to content type
        if content_type:
            if 'jpeg' in content_type or 'jpg' in content_type:
                return '.jpg'
            elif 'png' in content_type:
                return '.png'
            elif 'gif' in content_type:
                return '.gif'
            elif 'webp' in content_type:
                return '.webp'
        
        # Default to jpg
        return '.jpg'
    
    def _get_download_url(self, filename: str) -> str:
        """Generate a download URL for a file"""
        try:
            download_url = self.api.get_download_url_for_file_name(self.bucket_name, filename)
            return download_url
        except Exception as e:
            logger.error(f"Failed to generate download URL for {filename}: {e}")
            return ""
    
    def delete_image(self, filename: str) -> bool:
        """Delete an image from B2 storage"""
        if not self.is_configured():
            return False
        
        try:
            file_version = self.bucket.get_file_info_by_name(filename)
            self.bucket.delete_file_version(file_version.id_, filename)
            logger.info(f"Deleted image from B2: {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete image {filename}: {e}")
            return False
    
    def list_images_for_citation(self, citation_number: int) -> List[Dict]:
        """List all images stored for a specific citation"""
        if not self.is_configured():
            return []
        
        try:
            prefix = f"citations/{citation_number}/"
            files = list(self.bucket.ls(prefix))
            
            results = []
            for file_info in files:
                results.append({
                    'filename': file_info.file_name,
                    'file_id': file_info.id_,
                    'size_bytes': file_info.size,
                    'upload_timestamp': file_info.upload_timestamp,
                    'download_url': self._get_download_url(file_info.file_name)
                })
            
            return results
        except Exception as e:
            logger.error(f"Failed to list images for citation {citation_number}: {e}")
            return []
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        if not self.is_configured():
            return {}
        
        try:
            files = list(self.bucket.ls())
            total_files = len(files)
            total_size = sum(f.size for f in files)
            
            return {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'bucket_name': self.bucket_name
            }
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {}
