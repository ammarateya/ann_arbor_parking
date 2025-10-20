import psycopg
import json
from typing import Dict, Optional, List


class DatabaseManager:
    def __init__(self, db_config):
        self.db_config = db_config

    def get_connection(self):
        cfg = dict(self.db_config)
        # psycopg expects 'dbname' instead of 'database'
        if 'database' in cfg and 'dbname' not in cfg:
            cfg['dbname'] = cfg.pop('database')
        return psycopg.connect(**cfg)

    def save_citation(self, citation_data: Dict):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                query = """
                INSERT INTO citations 
                (citation_number, location, plate_state, plate_number, vin, 
                 issue_date, due_date, status, amount_due, more_info_url, raw_html,
                 issuing_agency, comments, violations, image_urls)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (citation_number) DO UPDATE SET
                    location = EXCLUDED.location,
                    plate_state = EXCLUDED.plate_state,
                    plate_number = EXCLUDED.plate_number,
                    vin = EXCLUDED.vin,
                    issue_date = EXCLUDED.issue_date,
                    due_date = EXCLUDED.due_date,
                    status = EXCLUDED.status,
                    amount_due = EXCLUDED.amount_due,
                    more_info_url = EXCLUDED.more_info_url,
                    raw_html = EXCLUDED.raw_html,
                    issuing_agency = EXCLUDED.issuing_agency,
                    comments = EXCLUDED.comments,
                    violations = EXCLUDED.violations,
                    image_urls = EXCLUDED.image_urls,
                    scraped_at = NOW()
                """
                cur.execute(query, (
                    citation_data['citation_number'],
                    citation_data['location'],
                    citation_data['plate_state'],
                    citation_data['plate_number'],
                    citation_data['vin'],
                    citation_data['issue_date'],
                    citation_data['due_date'],
                    citation_data['status'],
                    citation_data['amount_due'],
                    citation_data['more_info_url'],
                    citation_data['raw_html'],
                    citation_data.get('issuing_agency'),
                    citation_data.get('comments'),
                    json.dumps(citation_data.get('violations')) if citation_data.get('violations') is not None else None,
                    json.dumps(citation_data.get('image_urls')) if citation_data.get('image_urls') is not None else None,
                ))

    def get_last_successful_citation(self) -> Optional[int]:
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT last_successful_citation FROM scraper_state ORDER BY updated_at DESC LIMIT 1")
                result = cur.fetchone()
                return result[0] if result else None

    def update_last_successful_citation(self, citation_number: int):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO scraper_state (last_successful_citation) 
                    VALUES (%s)
                    ON CONFLICT (id) DO UPDATE SET 
                        last_successful_citation = EXCLUDED.last_successful_citation,
                        updated_at = NOW()
                """, (citation_number,))

    def log_scrape_attempt(self, citation_number: str, found_results: bool, error_message: str = None):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO scrape_logs (search_term, found_results, error_message)
                    VALUES (%s, %s, %s)
                """, (citation_number, found_results, error_message))

    def save_b2_image(self, citation_number: int, image_data: Dict):
        """Save Backblaze B2 image metadata to database"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO citation_images_b2 
                    (citation_number, original_url, b2_filename, b2_file_id, b2_download_url,
                     file_size_bytes, content_type, content_hash, upload_timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (b2_file_id) DO NOTHING
                """, (
                    citation_number,
                    image_data.get('original_url'),
                    image_data.get('filename'),
                    image_data.get('file_id'),
                    image_data.get('download_url'),
                    image_data.get('size_bytes'),
                    image_data.get('content_type'),
                    image_data.get('content_hash'),
                    image_data.get('upload_timestamp')
                ))

    def get_b2_images_for_citation(self, citation_number: int) -> List[Dict]:
        """Get all B2 stored images for a citation"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, original_url, b2_filename, b2_file_id, b2_download_url,
                           file_size_bytes, content_type, content_hash, upload_timestamp
                    FROM citation_images_b2 
                    WHERE citation_number = %s
                    ORDER BY upload_timestamp
                """, (citation_number,))
                
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]

    def get_citations_with_images(self, limit: int = 100) -> List[Dict]:
        """Get citations that have images stored in B2"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT c.citation_number, c.location, c.issue_date, c.amount_due,
                           COUNT(b2.id) as image_count
                    FROM citations c
                    JOIN citation_images_b2 b2 ON c.citation_number = b2.citation_number
                    GROUP BY c.citation_number, c.location, c.issue_date, c.amount_due
                    ORDER BY c.issue_date DESC
                    LIMIT %s
                """, (limit,))
                
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]

    def get_storage_stats(self) -> Dict:
        """Get B2 storage statistics"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Total images
                cur.execute("SELECT COUNT(*) FROM citation_images_b2")
                total_images = cur.fetchone()[0]
                
                # Total storage used
                cur.execute("SELECT SUM(file_size_bytes) FROM citation_images_b2")
                total_bytes = cur.fetchone()[0] or 0
                
                # Citations with images
                cur.execute("SELECT COUNT(DISTINCT citation_number) FROM citation_images_b2")
                citations_with_images = cur.fetchone()[0]
                
                return {
                    'total_images': total_images,
                    'total_bytes': total_bytes,
                    'total_mb': round(total_bytes / (1024 * 1024), 2),
                    'citations_with_images': citations_with_images
                }


