import os
import logging
import hashlib
import requests
from typing import List, Optional, Dict, Tuple
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from image_compressor import ImageCompressor

logger = logging.getLogger(__name__)


class CloudflareR2Storage:
    """Cloudflare R2 storage service with image compression"""
    
    def __init__(self):
        self.access_key_id = (os.getenv('R2_ACCESS_KEY_ID') or '').strip()
        self.secret_access_key = (os.getenv('R2_SECRET_ACCESS_KEY') or '').strip()
        self.bucket_name = os.getenv('R2_BUCKET_NAME', 'parking-citations')
        self.account_id = (os.getenv('R2_ACCOUNT_ID') or '').strip()
        self.public_url = os.getenv('R2_PUBLIC_URL')  # Custom domain or R2.dev URL
        
        self.s3_client = None
        self.compressor = ImageCompressor()
        
        # Guard against accidental newlines in credentials (which cause invalid header errors)
        for key_name, key_val in [('R2_ACCESS_KEY_ID', self.access_key_id), ('R2_SECRET_ACCESS_KEY', self.secret_access_key), ('R2_ACCOUNT_ID', self.account_id)]:
            if '\n' in key_val or '\r' in key_val:
                logger.error(f"Environment variable {key_name} contains newline characters; trimming may be required.")

        if self.access_key_id and self.secret_access_key and self.account_id:
            self._initialize_client()
        else:
            logger.warning("Cloudflare R2 credentials not configured")
    
    def _initialize_client(self):
        """Initialize the S3-compatible R2 client"""
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=f'https://{self.account_id}.r2.cloudflarestorage.com',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name='auto'
            )
            
            # Test connection
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Connected to Cloudflare R2 bucket: {self.bucket_name}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                # Bucket doesn't exist, create it
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created new R2 bucket: {self.bucket_name}")
                except Exception as create_error:
                    logger.error(f"Failed to create R2 bucket: {create_error}")
                    self.s3_client = None
            else:
                logger.error(f"Failed to initialize R2 client: {e}")
                self.s3_client = None
        except Exception as e:
            logger.error(f"Failed to initialize R2 client: {e}")
            self.s3_client = None
    
    def is_configured(self) -> bool:
        """Check if R2 is properly configured"""
        return self.s3_client is not None
    
    def upload_image(self, image_url: str, citation_number: int, image_index: int = 0) -> Optional[Dict]:
        """
        Download, compress, and upload an image to Cloudflare R2
        """
        if not self.is_configured():
            logger.warning("Cloudflare R2 not configured, skipping image upload")
            return None
        
        try:
            # Download image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Compress image
            compressed_data, compression_metadata = self.compressor.compress_image(
                response.content, image_url
            )
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"citations/{citation_number}/{citation_number}_{image_index}_{timestamp}.jpg"
            
            # Generate content hash
            content_hash = hashlib.sha1(compressed_data).hexdigest()
            
            # Upload to R2
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=compressed_data,
                ContentType='image/jpeg',
                Metadata={
                    'citation_number': str(citation_number),
                    'original_url': image_url,
                    'upload_timestamp': timestamp,
                    'content_hash': content_hash,
                    'compression_ratio': str(compression_metadata.get('compression_ratio', 0)),
                    'original_size': str(compression_metadata.get('original_size', 0)),
                    'compressed_size': str(compression_metadata.get('compressed_size', 0))
                }
            )
            
            # Generate public URL
            if self.public_url:
                download_url = f"{self.public_url}/{filename}"
            else:
                download_url = f"https://{self.bucket_name}.{self.account_id}.r2.cloudflarestorage.com/{filename}"
            
            logger.info(f"Uploaded compressed image to R2: {filename}")
            
            return {
                'filename': filename,
                'file_id': filename,  # R2 uses filename as ID
                'download_url': download_url,
                'size_bytes': len(compressed_data),
                'content_type': 'image/jpeg',
                'content_hash': content_hash,
                'upload_timestamp': timestamp,
                'compression_metadata': compression_metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to upload compressed image to R2 {image_url}: {e}")
            return None
    
    def upload_images_for_citation(self, image_urls: List[str], citation_number: int) -> List[Dict]:
        """Upload all images for a citation"""
        results = []
        
        for i, image_url in enumerate(image_urls):
            result = self.upload_image(image_url, citation_number, i)
            if result:
                results.append(result)
        
        return results
    
    def get_storage_stats(self) -> Dict:
        """Get R2 storage statistics"""
        if not self.is_configured():
            return {}
        
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            total_files = response.get('KeyCount', 0)
            total_size = sum(obj.get('Size', 0) for obj in response.get('Contents', []))
            
            return {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'bucket_name': self.bucket_name,
                'service': 'cloudflare_r2'
            }
        except Exception as e:
            logger.error(f"Failed to get R2 storage stats: {e}")
            return {}


class GoogleCloudStorage:
    """Google Cloud Storage service with image compression"""
    
    def __init__(self):
        self.bucket_name = os.getenv('GCS_BUCKET_NAME', 'parking-citations')
        self.credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        self.storage_client = None
        self.compressor = ImageCompressor()
        
        if self.credentials_path and os.path.exists(self.credentials_path):
            self._initialize_client()
        else:
            logger.warning("Google Cloud Storage credentials not configured")
    
    def _initialize_client(self):
        """Initialize the GCS client"""
        try:
            from google.cloud import storage
            self.storage_client = storage.Client()
            
            # Test connection
            bucket = self.storage_client.bucket(self.bucket_name)
            if not bucket.exists():
                bucket = self.storage_client.create_bucket(self.bucket_name)
                logger.info(f"Created new GCS bucket: {self.bucket_name}")
            else:
                logger.info(f"Connected to GCS bucket: {self.bucket_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            self.storage_client = None
    
    def is_configured(self) -> bool:
        """Check if GCS is properly configured"""
        return self.storage_client is not None
    
    def upload_image(self, image_url: str, citation_number: int, image_index: int = 0) -> Optional[Dict]:
        """Upload compressed image to Google Cloud Storage"""
        if not self.is_configured():
            logger.warning("Google Cloud Storage not configured, skipping image upload")
            return None
        
        try:
            from google.cloud import storage
            
            # Download and compress image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            compressed_data, compression_metadata = self.compressor.compress_image(
                response.content, image_url
            )
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"citations/{citation_number}/{citation_number}_{image_index}_{timestamp}.jpg"
            
            # Upload to GCS
            bucket = self.storage_client.bucket(self.bucket_name)
            blob = bucket.blob(filename)
            
            blob.upload_from_string(
                compressed_data,
                content_type='image/jpeg'
            )
            
            # Set metadata
            blob.metadata = {
                'citation_number': str(citation_number),
                'original_url': image_url,
                'upload_timestamp': timestamp,
                'compression_ratio': str(compression_metadata.get('compression_ratio', 0)),
                'original_size': str(compression_metadata.get('original_size', 0)),
                'compressed_size': str(compression_metadata.get('compressed_size', 0))
            }
            blob.patch()
            
            logger.info(f"Uploaded compressed image to GCS: {filename}")
            
            return {
                'filename': filename,
                'file_id': blob.id,
                'download_url': blob.public_url,
                'size_bytes': len(compressed_data),
                'content_type': 'image/jpeg',
                'upload_timestamp': timestamp,
                'compression_metadata': compression_metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to upload compressed image to GCS {image_url}: {e}")
            return None
