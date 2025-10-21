#!/usr/bin/env python3
"""
Export local citations to JSON for Supabase import
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

def export_citations_to_json() -> bool:
    """Export all citations from local database to JSON"""
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
                
                # Export to JSON
                with open('citations_export.json', 'w') as f:
                    json.dump(citations, f, indent=2, default=str)
                
                logger.info(f"Exported {len(citations)} citations to citations_export.json")
                logger.info(f"Citation range: {min(c['citation_number'] for c in citations)} to {max(c['citation_number'] for c in citations)}")
                
                return True
                
    except Exception as e:
        logger.error(f"Failed to export citations: {e}")
        return False

def main():
    """Export citations to JSON"""
    logger.info("Exporting local citations to JSON...")
    
    success = export_citations_to_json()
    
    if success:
        logger.info("Export completed successfully!")
        logger.info("You can now import citations_export.json to Supabase")
    else:
        logger.error("Export failed!")

if __name__ == "__main__":
    main()
