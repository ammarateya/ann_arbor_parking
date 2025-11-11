import os
import json
import logging
from typing import Dict, Optional, List, Tuple
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
            
            # Log the configuration (with masked key for security)
            logger.info(f"Supabase URL: {supabase_url}")
            if supabase_key:
                masked_key = supabase_key[:8] + "..." + supabase_key[-4:] if len(supabase_key) > 12 else "***"
                logger.info(f"Supabase Key: {masked_key}")
            else:
                logger.warning("Supabase Key: NOT SET")
            
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

    def batch_insert_citations(self, citations: List[Dict]) -> Dict:
        """
        Insert multiple citations in a single batch operation.
        
        Args:
            citations: List of citation dictionaries to insert
            
        Returns:
            Dict with 'success_count' and 'failed_count' keys
            
        Note: If batch insert fails, falls back to individual inserts.
        """
        if not citations:
            return {'success_count': 0, 'failed_count': 0, 'errors': []}
        
        try:
            # Attempt batch insert
            result = self.supabase.table('citations').insert(citations).execute()
            success_count = len(citations)
            citation_numbers = [c.get('citation_number', 'unknown') for c in citations]
            logger.info(f"Batch inserted {success_count} citations: {citation_numbers[0] if citation_numbers else 'none'} to {citation_numbers[-1] if citation_numbers else 'none'}")
            return {
                'success_count': success_count,
                'failed_count': 0,
                'errors': []
            }
        except Exception as e:
            # If batch insert fails, fall back to individual inserts
            logger.warning(f"Batch insert failed for {len(citations)} citations, falling back to individual inserts: {e}")
            success_count = 0
            failed_count = 0
            errors = []
            
            for citation in citations:
                try:
                    self.save_citation(citation)
                    success_count += 1
                except Exception as individual_error:
                    failed_count += 1
                    citation_num = citation.get('citation_number', 'unknown')
                    error_msg = f"Failed to save citation {citation_num}: {individual_error}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            return {
                'success_count': success_count,
                'failed_count': failed_count,
                'errors': errors
            }

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

    def get_existing_citation_numbers_in_range(self, start_range: int, end_range: int) -> set:
        """Get all existing citation numbers in the given range"""
        try:
            result = self.supabase.table('citations').select('citation_number').gte('citation_number', start_range).lte('citation_number', end_range).execute()
            if result.data:
                existing_numbers = {row['citation_number'] for row in result.data}
                logger.info(f"Found {len(existing_numbers)} existing citations in range {start_range}-{end_range}")
                return existing_numbers
            return set()
        except Exception as e:
            logger.error(f"Failed to get existing citation numbers in range: {e}")
            return set()

    def get_max_citation_below(self, threshold: int) -> Optional[int]:
        """Return the maximum citation_number strictly below the given threshold."""
        try:
            result = (
                self.supabase
                .table('citations')
                .select('citation_number')
                .lt('citation_number', threshold)
                .order('citation_number', desc=True)
                .limit(1)
                .execute()
            )
            if result.data:
                return int(result.data[0]['citation_number'])
            return None
        except Exception as e:
            logger.error(f"Failed to get max citation below {threshold}: {e}")
            return None

    def get_max_citation_at_or_above(self, threshold: int) -> Optional[int]:
        """Return the maximum citation_number at or above the given threshold."""
        try:
            result = (
                self.supabase
                .table('citations')
                .select('citation_number')
                .gte('citation_number', threshold)
                .order('citation_number', desc=True)
                .limit(1)
                .execute()
            )
            if result.data:
                return int(result.data[0]['citation_number'])
            return None
        except Exception as e:
            logger.error(f"Failed to get max citation at or above {threshold}: {e}")
            return None

    def get_max_citation_between(self, min_inclusive: int, max_exclusive: int) -> Optional[int]:
        """Return the maximum citation_number in [min_inclusive, max_exclusive)."""
        try:
            result = (
                self.supabase
                .table('citations')
                .select('citation_number')
                .gte('citation_number', min_inclusive)
                .lt('citation_number', max_exclusive)
                .order('citation_number', desc=True)
                .limit(1)
                .execute()
            )
            if result.data:
                return int(result.data[0]['citation_number'])
            return None
        except Exception as e:
            logger.error(
                f"Failed to get max citation between {min_inclusive} and {max_exclusive}: {e}"
            )
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

    # Subscriptions
    def add_subscription(self, plate_state: str, plate_number: str, email: str) -> Dict:
        """Create or upsert a subscription for the given plate and email."""
        if not email:
            raise ValueError("email is required")
        try:
            payload = {
                'plate_state': plate_state.upper(),
                'plate_number': plate_number,
                'email': email,
                'is_active': True,
            }
            # Check if subscription already exists
            existing = (
                self.supabase
                .table('subscriptions')
                .select('*')
                .eq('plate_state', plate_state.upper())
                .eq('plate_number', plate_number)
                .eq('email', email)
                .execute()
            )
            
            if existing.data and len(existing.data) > 0:
                # Update existing subscription
                result = (
                    self.supabase
                    .table('subscriptions')
                    .update(payload)
                    .eq('id', existing.data[0]['id'])
                    .execute()
                )
            else:
                # Insert new subscription
                result = (
                    self.supabase
                    .table('subscriptions')
                    .insert(payload)
                    .execute()
                )
            return {'status': 'success', 'data': result.data}
        except Exception as e:
            logger.error(f"Failed to add subscription: {e}")
            raise

    def deactivate_subscription(self, plate_state: str, plate_number: str, email: str) -> Dict:
        """Deactivate a subscription matching the plate and email."""
        if not email:
            raise ValueError("email is required")
        try:
            result = (
                self.supabase
                .table('subscriptions')
                .update({'is_active': False})
                .eq('plate_state', plate_state.upper())
                .eq('plate_number', plate_number)
                .eq('email', email)
                .eq('is_active', True)
                .execute()
            )
            return {'status': 'success', 'data': result.data}
        except Exception as e:
            logger.error(f"Failed to deactivate subscription: {e}")
            raise

    def find_active_subscriptions_for_plate(self, plate_state: str, plate_number: str) -> List[Dict]:
        """Return active subscriptions for a given plate."""
        try:
            result = (
                self.supabase
                .table('subscriptions')
                .select('*')
                .eq('plate_state', plate_state.upper())
                .eq('plate_number', plate_number)
                .eq('is_active', True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to find subscriptions for plate {plate_state} {plate_number}: {e}")
            return []

    def add_location_subscription(self, center_lat: float, center_lon: float, radius_m: float, email: str) -> Dict:
        """Create a location-based subscription."""
        if not email:
            raise ValueError("email is required")
        if radius_m <= 0 or radius_m > 100000:
            raise ValueError("radius_m must be between 1 and 100000 meters")
        try:
            payload = {
                'sub_type': 'location',
                'center_lat': center_lat,
                'center_lon': center_lon,
                'radius_m': radius_m,
                'email': email,
                'is_active': True,
            }
            result = self.supabase.table('subscriptions').insert(payload).execute()
            return {'status': 'success', 'data': result.data}
        except Exception as e:
            logger.error(f"Failed to add location subscription: {e}")
            raise

    def deactivate_location_subscription(self, center_lat: float, center_lon: float, radius_m: float, email: str) -> Dict:
        """Deactivate location-based subscriptions matching provided params and email."""
        if not email:
            raise ValueError("email is required")
        try:
            result = (
                self.supabase
                .table('subscriptions')
                .update({'is_active': False})
                .eq('sub_type', 'location')
                .eq('center_lat', center_lat)
                .eq('center_lon', center_lon)
                .eq('radius_m', radius_m)
                .eq('email', email)
                .eq('is_active', True)
                .execute()
            )
            return {'status': 'success', 'data': result.data}
        except Exception as e:
            logger.error(f"Failed to deactivate location subscription: {e}")
            raise

    def find_active_location_subscriptions_for_point(self, lat: float, lon: float) -> List[Dict]:
        """Return active location subscriptions whose radius covers the provided point.

        Note: We filter coarse candidates in SQL-like fashion in app by reading subs of type 'location',
        then apply precise haversine distance here.
        """
        try:
            result = (
                self.supabase
                .table('subscriptions')
                .select('*')
                .eq('sub_type', 'location')
                .eq('is_active', True)
                .not_.is_('center_lat', 'null')
                .not_.is_('center_lon', 'null')
                .not_.is_('radius_m', 'null')
                .execute()
            )
            subs = result.data or []
        except Exception as e:
            logger.error(f"Failed to load location subscriptions: {e}")
            return []

        import math
        def haversine_m(lat1, lon1, lat2, lon2):
            R = 6371000.0
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
            return 2 * R * math.asin(math.sqrt(a))

        matched = []
        for s in subs:
            try:
                d = haversine_m(lat, lon, float(s['center_lat']), float(s['center_lon']))
                if d <= float(s['radius_m']):
                    matched.append(s)
            except Exception:
                continue
        return matched

    def get_cached_coords_for_location(self, location: str) -> Optional[Tuple[float, float]]:
        """Return (lat, lon) for a location if any citation has already been geocoded.

        This is used to avoid repeated geocoding requests for identical location strings.
        """
        try:
            result = (
                self.supabase
                .table('citations')
                .select('latitude,longitude')
                .eq('location', location)
                .not_.is_('latitude', 'null')
                .not_.is_('longitude', 'null')
                .limit(1)
                .execute()
            )
            if result.data:
                row = result.data[0]
                lat = row.get('latitude')
                lon = row.get('longitude')
                if lat is not None and lon is not None:
                    return float(lat), float(lon)
            return None
        except Exception as e:
            logger.error(f"Failed to check cached coords for location '{location}': {e}")
            return None