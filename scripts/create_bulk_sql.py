#!/usr/bin/env python3
"""
Simple bulk import using Supabase MCP
"""
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_bulk_sql():
    """Create one clean bulk INSERT statement"""
    
    with open('citations_export.json', 'r') as f:
        citations = json.load(f)
    
    logger.info(f"Creating bulk SQL for {len(citations)} citations")
    
    # Create VALUES clauses
    values = []
    for c in citations:
        location = c['location'].replace("'", "''")
        more_info_url = c['more_info_url'].replace("'", "''")
        values.append(f"({c['citation_number']}, '{location}', '{c['plate_state']}', '{c['plate_number']}', {c['amount_due']}, '{c['status']}', '{more_info_url}', '{c['scraped_at']}')")
    
    # Create complete SQL
    sql = f"""
INSERT INTO citations 
(citation_number, location, plate_state, plate_number, amount_due, status, more_info_url, scraped_at)
VALUES 
{', '.join(values)}
ON CONFLICT (citation_number) DO UPDATE SET
    location = EXCLUDED.location,
    plate_state = EXCLUDED.plate_state,
    plate_number = EXCLUDED.plate_number,
    amount_due = EXCLUDED.amount_due,
    status = EXCLUDED.status,
    scraped_at = EXCLUDED.scraped_at;

-- Update scraper state
INSERT INTO scraper_state (last_successful_citation) 
VALUES ({max(c['citation_number'] for c in citations)})
ON CONFLICT (id) DO UPDATE SET 
    last_successful_citation = EXCLUDED.last_successful_citation,
    updated_at = NOW();
"""
    
    with open('bulk_import.sql', 'w') as f:
        f.write(sql)
    
    logger.info("✅ Created bulk_import.sql")
    logger.info(f"📊 Total citations: {len(citations)}")
    logger.info(f"🎯 Highest citation: {max(c['citation_number'] for c in citations)}")

if __name__ == "__main__":
    create_bulk_sql()
