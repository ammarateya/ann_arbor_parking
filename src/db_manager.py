import os
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Optional, List, Tuple

import psycopg
from psycopg.rows import dict_row
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_config):
        self.db_config = db_config
        self.supabase: Client = None
        self._pg_conn = None
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

    def _get_pg_connection(self):
        """Create (or reuse) a psycopg connection for analytical queries."""
        if self._pg_conn and not self._pg_conn.closed:
            return self._pg_conn
        try:
            self._pg_conn = psycopg.connect(
                host=self.db_config.get('host'),
                dbname=self.db_config.get('database'),
                user=self.db_config.get('user'),
                password=self.db_config.get('password'),
                port=self.db_config.get('port'),
                autocommit=True,
                row_factory=dict_row,
            )
            logger.info("✓ PostgreSQL connection established for analytics")
            return self._pg_conn
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL for analytics: {e}")
            raise

    def get_connection(self):
        """Backwards-compatible accessor for psycopg connection."""
        return self._get_pg_connection()

    def close_connection(self):
        """Close the psycopg connection if open."""
        if self._pg_conn and not self._pg_conn.closed:
            try:
                self._pg_conn.close()
            except Exception:
                pass
            finally:
                self._pg_conn = None

    @staticmethod
    def _to_float(value: Optional[Decimal]) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, Decimal):
            return float(value)
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def get_fun_facts(self, lookback_days: int = 30) -> Dict:
        """
        Return aggregated statistics used by the fun facts UI.
        Uses Supabase to fetch data and performs aggregations in Python.

        Args:
            lookback_days: How far back to query data.
        """
        lookback_days = max(1, min(lookback_days, 180))
        
        facts: Dict = {
            'generated_at': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
            'lookback_days': lookback_days,
            'worst_blocks': [],
            'repeat_offenders': [],
            'spicy_windows': [],
            'ticket_pressure': {'last_24h': 0, 'last_7d': 0, 'avg_amount': 0.0, 'total_revenue': 0.0, 'total_tickets': 0},
            'out_of_state_heat': [],
            'champions': {'worst_plate': None, 'worst_location': None},
            'insights': {'most_expensive': 0.0, 'worst_day': None, 'worst_hour': None},
            'officer_leaderboard': [],
        }

        try:
            from datetime import timedelta
            cutoff_date = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).isoformat()
            
            # Fetch all citations in the time range using Supabase
            citations = []
            page_size = 1000
            offset = 0
            max_iterations = 100  # Safety limit
            
            while offset < max_iterations * page_size:
                result = (
                    self.supabase
                    .table('citations')
                    .select('location,plate_state,plate_number,issue_date,amount_due,officer_name')
                    .gte('issue_date', cutoff_date)
                    .order('issue_date', desc=False)
                    .range(offset, offset + page_size - 1)
                    .execute()
                )
                page_data = result.data if result.data else []
                if not page_data:
                    break
                citations.extend(page_data)
                offset += page_size
                if len(page_data) == 0:
                    break
            
            if not citations:
                return facts
            
            # Calculate cutoff times for ticket pressure
            now = datetime.now(timezone.utc)
            last_24h = (now - timedelta(hours=24)).isoformat()
            last_7d = (now - timedelta(days=7)).isoformat()
            
            # Aggregate in Python
            from collections import defaultdict
            import math
            
            location_counts = defaultdict(lambda: {'count': 0, 'amounts': [], 'last_seen': None})
            plate_counts = defaultdict(lambda: {'count': 0, 'amounts': [], 'last_seen': None, 'state': None})
            time_buckets = defaultdict(int)
            hour_buckets = defaultdict(int)
            day_buckets = defaultdict(int)
            hour_buckets = defaultdict(int)
            day_buckets = defaultdict(int)
            out_of_state_counts = defaultdict(int)
            officer_revenue = defaultdict(float)
            officer_counts = defaultdict(int)
            all_amounts = []
            max_amount = 0.0
            last_24h_count = 0
            last_7d_count = 0
            total_revenue = 0.0
            
            for citation in citations:
                issue_date_str = citation.get('issue_date')
                if not issue_date_str:
                    continue
                    
                try:
                    issue_date = self._parse_timestamp(issue_date_str)
                    if not issue_date:
                        continue
                except:
                    continue
                
                amount = citation.get('amount_due')
                if amount is not None:
                    amount_float = float(amount)
                    all_amounts.append(amount_float)
                    total_revenue += amount_float
                    if amount_float > max_amount:
                        max_amount = amount_float
                
                # Ticket pressure
                if issue_date_str >= last_24h:
                    last_24h_count += 1
                if issue_date_str >= last_7d:
                    last_7d_count += 1
                
                # Worst locations
                location = citation.get('location')
                if location:
                    location_counts[location]['count'] += 1
                    if amount is not None:
                        location_counts[location]['amounts'].append(float(amount))
                    if not location_counts[location]['last_seen'] or issue_date > location_counts[location]['last_seen']:
                        location_counts[location]['last_seen'] = issue_date
                
                # Repeat offenders
                plate_state = citation.get('plate_state')
                plate_number = citation.get('plate_number')
                if plate_state and plate_number:
                    plate_key = f"{plate_state.upper()}|{plate_number}"
                    plate_counts[plate_key]['count'] += 1
                    plate_counts[plate_key]['state'] = plate_state.upper()
                    if amount is not None:
                        plate_counts[plate_key]['amounts'].append(float(amount))
                    if not plate_counts[plate_key]['last_seen'] or issue_date > plate_counts[plate_key]['last_seen']:
                        plate_counts[plate_key]['last_seen'] = issue_date
                    
                    # Out of state
                    if plate_state.upper() != 'MI':
                        out_of_state_counts[plate_state.upper()] += 1

                # Officer stats
                officer_name = citation.get('officer_name')
                if officer_name:
                    officer_name = officer_name.strip()
                    if officer_name:
                        officer_revenue[officer_name] += amount_float
                        officer_counts[officer_name] += 1
                
                # Time buckets (30-minute windows)
                if issue_date:
                    # Round down to nearest 30-minute bucket
                    minute = issue_date.minute
                    bucket_minute = (minute // 30) * 30
                    bucket_start = issue_date.replace(minute=bucket_minute, second=0, microsecond=0)
                    time_buckets[bucket_start.isoformat()] += 1
                    
                    # Hour buckets (for worst hour insight)
                    hour = issue_date.hour
                    hour_buckets[hour] += 1
                    
                    # Day of week buckets (0=Monday, 6=Sunday)
                    day_of_week = issue_date.weekday()
                    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    day_buckets[day_names[day_of_week]] += 1
            
            # Worst blocks
            worst_blocks = sorted(
                [
                    {
                        'location': loc,
                        'citation_count': data['count'],
                        'avg_amount': sum(data['amounts']) / len(data['amounts']) if data['amounts'] else 0.0,
                        'last_seen': data['last_seen'].isoformat() if data['last_seen'] else None,
                    }
                    for loc, data in location_counts.items()
                    if loc and loc.strip()
                ],
                key=lambda x: (x['citation_count'], x['last_seen'] or ''),
                reverse=True
            )[:5]
            facts['worst_blocks'] = worst_blocks
            
            # Repeat offenders
            repeat_offenders = sorted(
                [
                    {
                        'plate_state': data['state'],
                        'plate_number': key.split('|')[1],
                        'citation_count': data['count'],
                        'total_amount': sum(data['amounts']) if data['amounts'] else 0.0,
                        'last_seen': data['last_seen'].isoformat() if data['last_seen'] else None,
                    }
                    for key, data in plate_counts.items()
                    if data['count'] > 1
                ],
                key=lambda x: (x['citation_count'], x['last_seen'] or ''),
                reverse=True
            )[:5]
            facts['repeat_offenders'] = repeat_offenders
            
            # Spicy time windows
            spicy_windows = sorted(
                [
                    {
                        'bucket_start': bucket_start,
                        'bucket_end': (self._parse_timestamp(bucket_start) + timedelta(minutes=30)).isoformat() if self._parse_timestamp(bucket_start) else None,
                        'citation_count': count,
                    }
                    for bucket_start, count in time_buckets.items()
                ],
                key=lambda x: (x['citation_count'], x['bucket_start'] or ''),
                reverse=True
            )[:3]
            facts['spicy_windows'] = spicy_windows
            
            # Champions (worst plate and worst location)
            if worst_blocks:
                facts['champions']['worst_location'] = {
                    'location': worst_blocks[0]['location'],
                    'citation_count': worst_blocks[0]['citation_count'],
                    'avg_amount': worst_blocks[0]['avg_amount'],
                }
            
            if repeat_offenders:
                facts['champions']['worst_plate'] = {
                    'plate_state': repeat_offenders[0]['plate_state'],
                    'plate_number': repeat_offenders[0]['plate_number'],
                    'citation_count': repeat_offenders[0]['citation_count'],
                    'total_amount': repeat_offenders[0]['total_amount'],
                }
            
            # Ticket pressure
            facts['ticket_pressure'] = {
                'last_24h': last_24h_count,
                'last_7d': last_7d_count,
                'avg_amount': sum(all_amounts) / len(all_amounts) if all_amounts else 0.0,
                'total_revenue': total_revenue,
                'total_tickets': len(citations),
            }
            
            # Additional insights
            worst_hour = max(hour_buckets.items(), key=lambda x: x[1]) if hour_buckets else None
            worst_day = max(day_buckets.items(), key=lambda x: x[1]) if day_buckets else None
            
            facts['insights'] = {
                'most_expensive': max_amount,
                'worst_hour': worst_hour[0] if worst_hour else None,
                'worst_hour_count': worst_hour[1] if worst_hour else 0,
                'worst_day': worst_day[0] if worst_day else None,
                'worst_day_count': worst_day[1] if worst_day else 0,
            }
            
            # Out of state heat
            out_of_state_heat = sorted(
                [
                    {
                        'plate_state': state,
                        'citation_count': count,
                    }
                    for state, count in out_of_state_counts.items()
                ],
                key=lambda x: x['citation_count'],
                reverse=True
            )[:3]
            facts['out_of_state_heat'] = out_of_state_heat

            # Officer Leaderboard
            officer_leaderboard = sorted(
                [
                    {
                        'officer_name': name,
                        'revenue': revenue,
                        'citation_count': officer_counts[name]
                    }
                    for name, revenue in officer_revenue.items()
                ],
                key=lambda x: x['revenue'],
                reverse=True
            )[:5]
            facts['officer_leaderboard'] = officer_leaderboard
            
        except Exception as e:
            logger.error(f"Failed to build fun facts: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Return facts with empty lists instead of raising
            return facts

        return facts

    @staticmethod
    def _parse_timestamp(value) -> Optional[datetime]:
        """Parse Supabase timestamp values into timezone-aware datetimes."""
        if not value:
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value
        if isinstance(value, str):
            try:
                clean = value.replace("Z", "+00:00") if value.endswith("Z") else value
                parsed = datetime.fromisoformat(clean)
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=timezone.utc)
                return parsed
            except Exception:
                logger.warning(f"Failed to parse timestamp value '{value}'")
                return None
        logger.warning(f"Unsupported timestamp type: {type(value)}")
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
        """Get the highest citation number currently in the database."""
        try:
            result = (
                self.supabase
                .table('citations')
                .select('citation_number')
                .order('citation_number', desc=True)
                .limit(1)
                .execute()
            )
            if result.data:
                return int(result.data[0]['citation_number'])
            return None
        except Exception as e:
            logger.error(f"Failed to get last successful citation: {e}")
            return None


    def get_existing_citation_numbers_in_range(self, start_range: int, end_range: int) -> set:
        """Get all existing citation numbers in the given range"""
        try:
            # Log the query parameters and their types
            logger.info(f"[DEBUG] get_existing_citation_numbers_in_range called with start={start_range} (type={type(start_range).__name__}), end={end_range} (type={type(end_range).__name__})")
            
            result = self.supabase.table('citations').select('citation_number').gte('citation_number', start_range).lte('citation_number', end_range).execute()
            
            # Log raw result details
            logger.info(f"[DEBUG] Raw result.data length: {len(result.data) if result.data else 0}")
            if result.data:
                # Log sample of what we got back
                sample = result.data[:5]
                logger.info(f"[DEBUG] Sample results (first 5): {sample}")
                sample_types = [(row['citation_number'], type(row['citation_number']).__name__) for row in sample]
                logger.info(f"[DEBUG] Sample types: {sample_types}")
                
                existing_numbers = {row['citation_number'] for row in result.data}
                logger.info(f"Found {len(existing_numbers)} existing citations in range {start_range}-{end_range}")
                return existing_numbers
            else:
                logger.info(f"[DEBUG] No results returned from Supabase for range {start_range}-{end_range}")
            return set()
        except Exception as e:
            logger.error(f"Failed to get existing citation numbers in range: {e}")
            import traceback
            logger.error(f"[DEBUG] Traceback: {traceback.format_exc()}")
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
            # Log the query parameters and their types
            logger.info(f"[DEBUG] get_max_citation_between called with min={min_inclusive} (type={type(min_inclusive).__name__}), max={max_exclusive} (type={type(max_exclusive).__name__})")
            
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
            
            # Log raw result details
            logger.info(f"[DEBUG] Raw result.data: {result.data}")
            if result.data:
                raw_value = result.data[0]['citation_number']
                logger.info(f"[DEBUG] Raw citation_number value: {raw_value} (type={type(raw_value).__name__})")
                return int(result.data[0]['citation_number'])
            else:
                logger.info(f"[DEBUG] No results returned from Supabase for range [{min_inclusive}, {max_exclusive})")
            return None
        except Exception as e:
            logger.error(
                f"Failed to get max citation between {min_inclusive} and {max_exclusive}: {e}"
            )
            import traceback
            logger.error(f"[DEBUG] Traceback: {traceback.format_exc()}")
            return None



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
    def get_officer_stats(self, officer_name: str, officer_badge: str) -> Dict:
        """
        Get statistics for a specific officer (citation count, photo count).
        Returns a dict with 'total_citations' and 'total_photos'.
        """
        stats = {'total_citations': 0, 'total_photos': 0}
        
        # We need at least one identifier
        if not officer_name and not officer_badge:
            return stats
            
        try:
            # Build query
            query = self.supabase.table('citations').select('image_urls', count='exact')
            
            # Filter by badge if available (more precise), otherwise name
            # If both are present, we might want to prioritize badge or match both? 
            # Given the data quality, matching one might be safer. Let's try matching badge if present, else name.
            if officer_badge:
                query = query.eq('officer_badge', officer_badge)
            elif officer_name:
                query = query.eq('officer_name', officer_name)
                
            # Execute count query first for total reviews/citations
            # We want all records, not just a page. But selecting all rows for images might be heavy.
            # Strategy: 
            # 1. Get exact count of citations (reviews)
            # 2. To get photo count, we ideally want to sum the lengths of image_urls arrays.
            #    Doing this client-side (in python) requires fetching all rows.
            #    Let's fetch just the image_urls column for all matching records.
            
            # Fetch all image_urls for this officer
            # Note: If an officer has thousands of tickets, this fetch might be large.
            # But the payload is just the list of lists of URLs.
            # Let's paginate if necessary or just hope limit is high enough? 
            # Supabase default limit is 1000. We better loop or use a stored procedure.
            # For simplicity in this "fun" feature, let's just fetch up to 1000 for now to estimate photos.
            # Or better, we can use the count from step 1 for citations, and sample photos?
            # User asked for "calculate how many photos".
            
            # Let's try a single fetch with a reasonable limit (e.g. 5000)
            result = query.limit(5000).execute()
            
            if result.count is not None:
                stats['total_citations'] = result.count
            
            # Calculate total photos from the returned batch
            photo_count = 0
            if result.data:
                for row in result.data:
                    urls = row.get('image_urls')
                    if urls:
                        if isinstance(urls, list):
                            photo_count += len(urls)
                        elif isinstance(urls, str):
                            # In case it's a JSON string (shouldn't be with python client but safety first)
                            # Actually python client returns parsed JSON usually
                            pass
            
            # If we hit the limit, this is a lower bound, which is fine for "reviews"
            stats['total_photos'] = photo_count
            
            # If we have 0 citations, return 0
            if stats['total_citations'] == 0:
                pass
                
            return stats

        except Exception as e:
            logger.error(f"Failed to get officer stats: {e}")
            return stats

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