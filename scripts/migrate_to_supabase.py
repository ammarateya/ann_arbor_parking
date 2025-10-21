#!/usr/bin/env python3
"""
Data Migration Script: Export local citations to Supabase
This script helps migrate your local citation data to Supabase
"""

import os
import json
import psycopg
from typing import List, Dict, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Local database configuration (update these)
LOCAL_DB_CONFIG = {
    'host': 'localhost',
    'database': 'parking_citations',  # Update this
    'user': 'postgres',  # Update this
    'password': '',  # Update this
    'port': '5432',
}

# Supabase configuration
SUPABASE_CONFIG = {
    'host': 'db.kctfygcpobxjgpivujiy.supabase.co',
    'database': 'postgres',
    'user': 'postgres',
    'password': '',  # You'll need to set this
    'port': '5432',
}

def get_local_citations() -> List[Dict]:
    """Export citations from local database"""
    try:
        with psycopg.connect(**LOCAL_DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT citation_number, location, plate_state, plate_number, vin,
                           issue_date, due_date, status, amount_due, more_info_url,
                           raw_html, issuing_agency, comments, violations, image_urls,
                           scraped_at
                    FROM citations
                    ORDER BY citation_number DESC
                """)
                
                columns = [desc[0] for desc in cur.description]
                citations = []
                
                for row in cur.fetchall():
                    citation = dict(zip(columns, row))
                    # Convert any JSON fields
                    if citation.get('violations'):
                        if isinstance(citation['violations'], str):
                            citation['violations'] = json.loads(citation['violations'])
                    if citation.get('image_urls'):
                        if isinstance(citation['image_urls'], str):
                            citation['image_urls'] = json.loads(citation['image_urls'])
                    
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
                            json.dumps(citation.get('violations')) if citation.get('violations') else None,
                            json.dumps(citation.get('image_urls')) if citation.get('image_urls') else None,
                            citation.get('scraped_at')
                        ))
                        uploaded_count += 1
                        
                        if uploaded_count % 100 == 0:
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

def export_to_json(citations: List[Dict], filename: str = "citations_export.json"):
    """Export citations to JSON file as backup"""
    try:
        with open(filename, 'w') as f:
            json.dump(citations, f, indent=2, default=str)
        logger.info(f"Exported {len(citations)} citations to {filename}")
    except Exception as e:
        logger.error(f"Failed to export to JSON: {e}")

def main():
    """Main migration function"""
    logger.info("Starting citation data migration...")
    
    # Check if Supabase password is set
    if not SUPABASE_CONFIG['password']:
        logger.error("Please set SUPABASE_CONFIG['password'] with your Supabase database password")
        return
    
    # Export from local database
    citations = get_local_citations()
    
    if not citations:
        logger.warning("No citations found in local database")
        return
    
    # Export to JSON as backup
    export_to_json(citations)
    
    # Upload to Supabase
    success = upload_to_supabase(citations)
    
    if success:
        logger.info("Migration completed successfully!")
    else:
        logger.error("Migration failed!")

if __name__ == "__main__":
    main()
