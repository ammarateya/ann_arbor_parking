import os
import logging
from typing import Optional
from backblaze_storage import BackblazeStorage
from image_compressor import OptimizedBackblazeStorage
from cloud_storage import CloudflareR2Storage, GoogleCloudStorage

logger = logging.getLogger(__name__)


class StorageFactory:
    """Factory to create the appropriate storage service based on configuration"""
    
    @staticmethod
    def create_storage_service():
        """
        Create storage service based on STORAGE_PROVIDER environment variable
        
        Returns:
            Storage service instance or None if not configured
        """
        provider = os.getenv('STORAGE_PROVIDER', 'cloudflare_r2').lower()
        
        if provider == 'backblaze_b2':
            logger.info("Using Backblaze B2 storage with compression")
            return OptimizedBackblazeStorage()
        
        elif provider == 'cloudflare_r2':
            logger.info("Using Cloudflare R2 storage with compression")
            return CloudflareR2Storage()
        
        elif provider == 'google_cloud':
            logger.info("Using Google Cloud Storage with compression")
            return GoogleCloudStorage()
        
        else:
            logger.warning(f"Unknown storage provider: {provider}")
            return None
    
    @staticmethod
    def get_storage_info():
        """Get information about available storage providers"""
        return {
            'backblaze_b2': {
                'name': 'Backblaze B2',
                'free_tier': '10GB storage',
                'pros': ['Simple setup', 'Good performance'],
                'cons': ['Limited free tier', 'Egress fees'],
                'best_for': 'Small projects'
            },
            'cloudflare_r2': {
                'name': 'Cloudflare R2',
                'free_tier': '10GB storage + 1M requests/month',
                'pros': ['No egress fees', 'S3-compatible', 'Good free tier'],
                'cons': ['Newer service'],
                'best_for': 'Production apps (RECOMMENDED)'
            },
            'google_cloud': {
                'name': 'Google Cloud Storage',
                'free_tier': '$300 student credits (~1.5TB)',
                'pros': ['Large free tier for students', 'Reliable', 'Good integration'],
                'cons': ['Requires .edu email', 'Complex setup'],
                'best_for': 'Students with credits'
            }
        }
