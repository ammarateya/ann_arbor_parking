#!/usr/bin/env python3
"""
Import all citations to Supabase using direct SQL
This script will be run manually to import all 532 citations
"""
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_import_sql():
    """Generate SQL to import all citations"""
    
    with open('citations_export.json', 'r') as f:
        citations = json.load(f)
    
    logger.info(f"Generating SQL for {len(citations)} citations")
    
    # Create SQL file
    with open('import_all_citations.sql', 'w') as f:
        f.write("-- Import all citations to Supabase\n")
        f.write("-- Generated from local database export\n\n")
        
        for i, citation in enumerate(citations):
            # Escape single quotes in strings
            def escape_sql_string(s):
                if s is None:
                    return 'NULL'
                return "'" + str(s).replace("'", "''") + "'"
            
            sql = f"""
INSERT INTO citations 
(citation_number, location, plate_state, plate_number, vin, 
 issue_date, due_date, status, amount_due, more_info_url, raw_html,
 issuing_agency, comments, violations, image_urls, scraped_at)
VALUES 
({citation['citation_number']}, 
 {escape_sql_string(citation['location'])}, 
 {escape_sql_string(citation['plate_state'])}, 
 {escape_sql_string(citation['plate_number'])}, 
 {escape_sql_string(citation['vin'])}, 
 {escape_sql_string(citation['issue_date'])}, 
 {escape_sql_string(citation['due_date'])}, 
 {escape_sql_string(citation['status'])}, 
 {citation['amount_due']}, 
 {escape_sql_string(citation['more_info_url'])}, 
 {escape_sql_string(citation['raw_html'])}, 
 {escape_sql_string(citation['issuing_agency'])}, 
 {escape_sql_string(citation['comments'])}, 
 {escape_sql_string(citation['violations'])}, 
 {escape_sql_string(citation['image_urls'])}, 
 {escape_sql_string(citation['scraped_at'])})
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
    scraped_at = EXCLUDED.scraped_at;

"""
            f.write(sql)
            
            if (i + 1) % 50 == 0:
                logger.info(f"Generated SQL for {i + 1} citations...")
        
        # Update scraper state
        highest_citation = max(c['citation_number'] for c in citations)
        f.write(f"""
-- Update scraper state
INSERT INTO scraper_state (last_successful_citation) 
VALUES ({highest_citation})
ON CONFLICT (id) DO UPDATE SET 
    last_successful_citation = EXCLUDED.last_successful_citation,
    updated_at = NOW();
""")
    
    logger.info(f"Generated import_all_citations.sql with {len(citations)} citations")
    logger.info(f"Highest citation: {highest_citation}")

if __name__ == "__main__":
    generate_import_sql()
