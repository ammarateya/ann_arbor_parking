import os
import json
import logging
from typing import Dict, Optional, List
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_config):
        self.db_config = db_config
        self.supabase: Client = None
        self._initialize_supabase()

    def _initialize_supabase(self):
        """Initialize Supabase client using environment variables"""
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')
            
            if not supabase_url or not supabase_key:
                logger.error("Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
                raise ValueError("Supabase credentials not configured")
            
            self.supabase = create_client(supabase_url, supabase_key)
            logger.info("✓ Supabase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise

    def get_connection(self):
        """Legacy method for compatibility - returns None since we use Supabase client directly"""
        logger.warning("get_connection() called - using Supabase client instead of direct psycopg connection")
        return None

    def save_citation(self, citation_data: Dict):
        """Save citation data to Supabase"""
        try:
            result = self.supabase.table('citations').insert(citation_data).execute()
            logger.info(f"Saved citation {citation_data.get('citation_number', 'unknown')}")
            return result
        except Exception as e:
            logger.error(f"Failed to save citation: {e}")
            raise

    def get_last_successful_citation(self) -> Optional[int]:
        """Get the last successfully scraped citation number"""
        try:
            result = self.supabase.table('scraper_state').select('last_successful_citation').execute()
            if result.data:
                return result.data[0]['last_successful_citation']
            return None
        except Exception as e:
            logger.error(f"Failed to get last successful citation: {e}")
            return None

    def update_last_successful_citation(self, citation_number: int):
        """Update the last successfully scraped citation number"""
        try:
            result = self.supabase.table('scraper_state').upsert({
                'id': 1,
                'last_successful_citation': citation_number
            }).execute()
            logger.info(f"Updated last successful citation to {citation_number}")
            return result
        except Exception as e:
            logger.error(f"Failed to update last successful citation: {e}")
            raise

    def log_scrape_attempt(self, citation_number: int, success: bool, error_message: str = None):
        """Log a scrape attempt"""
        try:
            log_data = {
                'citation_number': citation_number,
                'success': success,
                'error_message': error_message,
                'timestamp': 'now()'
            }
            result = self.supabase.table('scrape_logs').insert(log_data).execute()
            return result
        except Exception as e:
            logger.error(f"Failed to log scrape attempt: {e}")
            # Don't raise - logging failures shouldn't break the main flow

    def save_b2_image(self, citation_number: int, image_data: Dict):
        """Save image metadata to database (kept same method name for compatibility)"""
        try:
            image_record = {
                'citation_number': citation_number,
                'filename': image_data.get('filename'),
                'file_id': image_data.get('file_id'),
                'download_url': image_data.get('download_url'),
                'size_bytes': image_data.get('size_bytes'),
                'content_type': image_data.get('content_type'),
                'content_hash': image_data.get('content_hash'),
                'upload_timestamp': image_data.get('upload_timestamp'),
                'original_url': image_data.get('original_url')
            }
            result = self.supabase.table('citation_images').insert(image_record).execute()
            logger.info(f"Saved image metadata for citation {citation_number}")
            return result
        except Exception as e:
            logger.error(f"Failed to save image metadata: {e}")
            raise

    def get_b2_images_for_citation(self, citation_number: int) -> List[Dict]:
        """Get all image records for a citation"""
        try:
            result = self.supabase.table('citation_images').select('*').eq('citation_number', citation_number).execute()
            return result.data
        except Exception as e:
            logger.error(f"Failed to get images for citation {citation_number}: {e}")
            return []

    def get_citations_with_images(self) -> List[Dict]:
        """Get all citations that have associated images"""
        try:
            result = self.supabase.table('citations').select('citation_number').in_('citation_number', 
                self.supabase.table('citation_images').select('citation_number').execute().data
            ).execute()
            return result.data
        except Exception as e:
            logger.error(f"Failed to get citations with images: {e}")
            return []

    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        try:
            # Get total images count
            images_result = self.supabase.table('citation_images').select('size_bytes', count='exact').execute()
            total_images = images_result.count
            
            # Get total size
            size_result = self.supabase.table('citation_images').select('size_bytes').execute()
            total_size_bytes = sum(img['size_bytes'] for img in size_result.data if img['size_bytes'])
            total_size_mb = total_size_bytes / (1024 * 1024)
            
            # Get citations with images count
            citations_with_images = len(set(img['citation_number'] for img in size_result.data))
            
            return {
                'total_images': total_images,
                'total_mb': round(total_size_mb, 2),
                'citations_with_images': citations_with_images
            }
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {'total_images': 0, 'total_mb': 0, 'citations_with_images': 0}