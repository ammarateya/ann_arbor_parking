import psycopg
import json
from typing import Dict, Optional


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


