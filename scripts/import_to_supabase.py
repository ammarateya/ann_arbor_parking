#!/usr/bin/env python3
"""
Simple Data Import Script for Supabase
This script can import citations from various sources
"""

import os
import json
import psycopg
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_CONFIG = {
    'host': 'db.kctfygcpobxjgpivujiy.supabase.co',
    'database': 'postgres',
    'user': 'postgres',
    'password': '',  # Set this with your Supabase password
    'port': '5432',
}

def import_from_json(filename: str) -> bool:
    """Import citations from JSON file"""
    try:
        with open(filename, 'r') as f:
            citations = json.load(f)
        
        logger.info(f"Loaded {len(citations)} citations from {filename}")
        return upload_to_supabase(citations)
        
    except Exception as e:
        logger.error(f"Failed to load JSON file: {e}")
        return False

def import_sample_data() -> bool:
    """Import some sample citations to test the system"""
    sample_citations = [
        {
            'citation_number': 10516370,
            'location': 'Main St & State St',
            'plate_state': 'MI',
            'plate_number': 'ABC123',
            'vin': None,
            'issue_date': '2024-01-15 10:30:00',
            'due_date': '2024-02-15',
            'status': 'Open',
            'amount_due': 25.00,
            'more_info_url': 'https://example.com/citation/10516370',
            'raw_html': '<html>Sample citation data</html>',
            'issuing_agency': 'Ann Arbor Police',
            'comments': 'Sample citation for testing',
            'violations': ['Parking in No Parking Zone'],
            'image_urls': ['https://example.com/image1.jpg'],
            'scraped_at': '2024-01-15 10:35:00'
        },
        {
            'citation_number': 10516369,
            'location': 'Liberty St & Division St',
            'plate_state': 'MI',
            'plate_number': 'XYZ789',
            'vin': None,
            'issue_date': '2024-01-15 11:15:00',
            'due_date': '2024-02-15',
            'status': 'Open',
            'amount_due': 15.00,
            'more_info_url': 'https://example.com/citation/10516369',
            'raw_html': '<html>Sample citation data 2</html>',
            'issuing_agency': 'Ann Arbor Police',
            'comments': 'Another sample citation',
            'violations': ['Expired Meter'],
            'image_urls': ['https://example.com/image2.jpg'],
            'scraped_at': '2024-01-15 11:20:00'
        }
    ]
    
    logger.info("Importing sample data...")
    return upload_to_supabase(sample_citations)

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
    """Main import function"""
    logger.info("Starting citation data import...")
    
    # Check if Supabase password is set
    if not SUPABASE_CONFIG['password']:
        logger.error("Please set SUPABASE_CONFIG['password'] with your Supabase database password")
        logger.info("You can get this from: https://app.supabase.com/project/kctfygcpobxjgpivujiy/settings/database")
        return
    
    # Try to import from JSON file first
    if os.path.exists('citations_export.json'):
        logger.info("Found citations_export.json, importing...")
        success = import_from_json('citations_export.json')
    else:
        logger.info("No JSON file found, importing sample data...")
        success = import_sample_data()
    
    if success:
        logger.info("Import completed successfully!")
    else:
        logger.error("Import failed!")

if __name__ == "__main__":
    main()
