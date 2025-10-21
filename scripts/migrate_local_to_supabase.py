#!/usr/bin/env python3
"""
Migrate local parking citations to Supabase
"""
import os
import psycopg
import json
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Local database configuration
LOCAL_DB_CONFIG = {
    'host': 'localhost',
    'dbname': 'parking_local',
    'user': os.getenv('USER'),
    'password': '',
    'port': '5432'
}

# Supabase configuration
SUPABASE_CONFIG = {
    'host': 'db.kctfygcpobxjgpivujiy.supabase.co',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'bGhCeH3UXqUPm8Z',
    'port': '5432'
}

def get_local_citations() -> List[Dict]:
    """Export all citations from local database"""
    try:
        with psycopg.connect(**LOCAL_DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        citation_number, location, plate_state, plate_number, vin,
                        issue_date, due_date, status, amount_due, more_info_url,
                        raw_html, issuing_agency, comments, violations, image_urls,
                        scraped_at, created_at,
                        -- OCR fields
                        ocr_location, vehicle_make, vehicle_model, vehicle_color,
                        plate_exp_month, plate_exp_year, district_number, meter_number
                    FROM citations
                    ORDER BY citation_number DESC
                """)
                
                columns = [desc[0] for desc in cur.description]
                citations = []
                
                for row in cur.fetchall():
                    citation = dict(zip(columns, row))
                    
                    # Handle JSON fields that might be lists
                    if citation.get('violations'):
                        if isinstance(citation['violations'], list):
                            citation['violations'] = json.dumps(citation['violations'])
                        elif isinstance(citation['violations'], str):
                            try:
                                json.loads(citation['violations'])  # Validate JSON
                            except:
                                citation['violations'] = json.dumps([citation['violations']])
                    
                    if citation.get('image_urls'):
                        if isinstance(citation['image_urls'], list):
                            citation['image_urls'] = json.dumps(citation['image_urls'])
                        elif isinstance(citation['image_urls'], str):
                            try:
                                json.loads(citation['image_urls'])  # Validate JSON
                            except:
                                citation['image_urls'] = json.dumps([citation['image_urls']])
                    
                    citations.append(citation)
                
                logger.info(f"Found {len(citations)} citations in local database")
                return citations
                
    except Exception as e:
        logger.error(f"Failed to connect to local database: {e}")
        return []

def upload_to_supabase(citations: List[Dict]) -> bool:
    """Upload citations to Supabase"""
    if not citations:
        logger.warning("No citations to upload")
        return False
    
    try:
        with psycopg.connect(**SUPABASE_CONFIG) as conn:
            with conn.cursor() as cur:
                uploaded_count = 0
                
                for citation in citations:
                    try:
                        cur.execute("""
                            INSERT INTO citations 
                            (citation_number, location, plate_state, plate_number, vin, 
                             issue_date, due_date, status, amount_due, more_info_url, raw_html,
                             issuing_agency, comments, violations, image_urls, scraped_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                                scraped_at = EXCLUDED.scraped_at
                        """, (
                            citation['citation_number'],
                            citation['location'],
                            citation['plate_state'],
                            citation['plate_number'],
                            citation['vin'],
                            citation['issue_date'],
                            citation['due_date'],
                            citation['status'],
                            citation['amount_due'],
                            citation['more_info_url'],
                            citation['raw_html'],
                            citation.get('issuing_agency'),
                            citation.get('comments'),
                            citation.get('violations'),
                            citation.get('image_urls'),
                            citation.get('scraped_at')
                        ))
                        uploaded_count += 1
                        
                        if uploaded_count % 50 == 0:
                            logger.info(f"Uploaded {uploaded_count} citations...")
                            
                    except Exception as e:
                        logger.error(f"Failed to upload citation {citation.get('citation_number')}: {e}")
                
                # Update scraper state with highest citation number
                if citations:
                    highest_citation = max(c['citation_number'] for c in citations)
                    cur.execute("""
                        INSERT INTO scraper_state (last_successful_citation) 
                        VALUES (%s)
                        ON CONFLICT (id) DO UPDATE SET 
                            last_successful_citation = EXCLUDED.last_successful_citation,
                            updated_at = NOW()
                    """, (highest_citation,))
                    
                    logger.info(f"Set scraper state to citation {highest_citation}")
                
                conn.commit()
                logger.info(f"Successfully uploaded {uploaded_count} citations to Supabase")
                return True
                
    except Exception as e:
        logger.error(f"Failed to upload to Supabase: {e}")
        return False

def main():
    """Main migration function"""
    logger.info("Starting citation data migration from local to Supabase...")
    
    # Check if Supabase password is set
    if not SUPABASE_CONFIG['password']:
        logger.error("Please set SUPABASE_CONFIG['password'] with your Supabase database password")
        logger.info("You can get this from: https://app.supabase.com/project/kctfygcpobxjgpivujiy/settings/database")
        return
    
    # Export from local database
    citations = get_local_citations()
    
    if not citations:
        logger.warning("No citations found in local database")
        return
    
    logger.info(f"Found {len(citations)} citations to migrate")
    logger.info(f"Citation range: {min(c['citation_number'] for c in citations)} to {max(c['citation_number'] for c in citations)}")
    
    # Upload to Supabase
    success = upload_to_supabase(citations)
    
    if success:
        logger.info("Migration completed successfully!")
        logger.info("Your Supabase database now has all your local citations")
    else:
        logger.error("Migration failed!")

if __name__ == "__main__":
    main()
