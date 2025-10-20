import os
import logging
import hashlib
import requests
from typing import List, Optional, Dict, Tuple
from PIL import Image
import io
from datetime import datetime
from backblaze_storage import BackblazeStorage

logger = logging.getLogger(__name__)


class ImageCompressor:
    def __init__(self):
        self.max_width = int(os.getenv('IMAGE_MAX_WIDTH', '1200'))
        self.max_height = int(os.getenv('IMAGE_MAX_HEIGHT', '1200'))
        self.quality = int(os.getenv('IMAGE_QUALITY', '85'))
        self.format = os.getenv('IMAGE_FORMAT', 'JPEG')
        
    def compress_image(self, image_data: bytes, original_url: str) -> Tuple[bytes, Dict]:
        """
        Compress an image to reduce file size while maintaining quality
        
        Args:
            image_data: Raw image bytes
            original_url: Original image URL for metadata
            
        Returns:
            Tuple of (compressed_bytes, metadata_dict)
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_data))
            original_format = image.format
            original_size = len(image_data)
            
            # Convert to RGB if necessary (for JPEG)
            if self.format == 'JPEG' and image.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparent images
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large
            if image.width > self.max_width or image.height > self.max_height:
                image.thumbnail((self.max_width, self.max_height), Image.Resampling.LANCZOS)
            
            # Compress
            output = io.BytesIO()
            image.save(output, format=self.format, quality=self.quality, optimize=True)
            compressed_data = output.getvalue()
            compressed_size = len(compressed_data)
            
            # Calculate compression ratio
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            metadata = {
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': round(compression_ratio, 2),
                'original_format': original_format,
                'final_format': self.format,
                'original_dimensions': f"{image.width}x{image.height}",
                'final_dimensions': f"{image.width}x{image.height}",
                'quality': self.quality
            }
            
            logger.info(f"Compressed image: {original_size} → {compressed_size} bytes ({compression_ratio:.1f}% reduction)")
            
            return compressed_data, metadata
            
        except Exception as e:
            logger.error(f"Failed to compress image: {e}")
            return image_data, {'error': str(e)}


class OptimizedBackblazeStorage(BackblazeStorage):
    """Enhanced Backblaze storage with image compression"""
    
    def __init__(self):
        super().__init__()
        self.compressor = ImageCompressor()
    
    def upload_image(self, image_url: str, citation_number: int, image_index: int = 0) -> Optional[Dict]:
        """
        Download, compress, and upload an image to Backblaze B2
        """
        if not self.is_configured():
            logger.warning("Backblaze B2 not configured, skipping image upload")
            return None
        
        try:
            # Download image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Compress image
            compressed_data, compression_metadata = self.compressor.compress_image(
                response.content, image_url
            )
            
            # Generate filename with citation number and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = '.jpg'  # Always use .jpg for compressed images
            filename = f"citations/{citation_number}/{citation_number}_{image_index}_{timestamp}{file_extension}"
            
            # Generate content hash for deduplication
            content_hash = hashlib.sha1(compressed_data).hexdigest()
            
            # Upload to B2
            file_info = self.bucket.upload_bytes(
                compressed_data,
                filename,
                content_type='image/jpeg',
                file_infos={
                    'citation_number': str(citation_number),
                    'original_url': image_url,
                    'upload_timestamp': timestamp,
                    'content_hash': content_hash,
                    'compression_ratio': str(compression_metadata.get('compression_ratio', 0)),
                    'original_size': str(compression_metadata.get('original_size', 0)),
                    'compressed_size': str(compression_metadata.get('compressed_size', 0))
                }
            )
            
            logger.info(f"Uploaded compressed image to B2: {filename}")
            
            return {
                'filename': filename,
                'file_id': file_info.id_,
                'download_url': self._get_download_url(filename),
                'size_bytes': len(compressed_data),
                'content_type': 'image/jpeg',
                'content_hash': content_hash,
                'upload_timestamp': timestamp,
                'compression_metadata': compression_metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to upload compressed image {image_url}: {e}")
            return None
