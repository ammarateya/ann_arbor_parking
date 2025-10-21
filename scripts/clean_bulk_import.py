#!/usr/bin/env python3
"""
Clean bulk import to Supabase using psycopg
"""
import json
import psycopg
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase config
SUPABASE_CONFIG = {
    'host': 'db.kctfygcpobxjgpivujiy.supabase.co',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'bGhCeH3UXqUPm8Z',
    'port': '5432'
}

def bulk_import_citations():
    """Import all citations in one go"""
    
    # Load citations
    with open('citations_export.json', 'r') as f:
        citations = json.load(f)
    
    logger.info(f"Importing {len(citations)} citations...")
    
    try:
        with psycopg.connect(**SUPABASE_CONFIG) as conn:
            with conn.cursor() as cur:
                # Bulk insert
                cur.executemany("""
                    INSERT INTO citations 
                    (citation_number, location, plate_state, plate_number, amount_due, status, more_info_url, scraped_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (citation_number) DO UPDATE SET
                        location = EXCLUDED.location,
                        plate_state = EXCLUDED.plate_state,
                        plate_number = EXCLUDED.plate_number,
                        amount_due = EXCLUDED.amount_due,
                        status = EXCLUDED.status,
                        scraped_at = EXCLUDED.scraped_at
                """, [
                    (
                        c['citation_number'],
                        c['location'],
                        c['plate_state'],
                        c['plate_number'],
                        c['amount_due'],
                        c['status'],
                        c['more_info_url'],
                        c['scraped_at']
                    ) for c in citations
                ])
                
                # Update scraper state
                highest = max(c['citation_number'] for c in citations)
                cur.execute("""
                    INSERT INTO scraper_state (last_successful_citation) 
                    VALUES (%s)
                    ON CONFLICT (id) DO UPDATE SET 
                        last_successful_citation = EXCLUDED.last_successful_citation,
                        updated_at = NOW()
                """, (highest,))
                
                conn.commit()
                
        logger.info(f"✅ Successfully imported {len(citations)} citations!")
        logger.info(f"🎯 Highest citation: {highest}")
        
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")

if __name__ == "__main__":
    bulk_import_citations()
