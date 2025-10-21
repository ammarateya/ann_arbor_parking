#!/usr/bin/env python3
"""
Complete Citation Migration Script for Supabase
This script will import all 532 citations from your local database to Supabase
"""
import json
import logging
import time
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_citations() -> List[Dict]:
    """Load citations from JSON export"""
    with open('citations_export.json', 'r') as f:
        citations = json.load(f)
    logger.info(f"Loaded {len(citations)} citations from JSON")
    return citations

def create_bulk_insert_sql(citations: List[Dict], batch_size: int = 50) -> List[str]:
    """Create bulk INSERT SQL statements"""
    
    sql_batches = []
    
    for i in range(0, len(citations), batch_size):
        batch = citations[i:i + batch_size]
        
        # Create VALUES clause
        values_clauses = []
        for citation in batch:
            values_clause = f"""({citation['citation_number']}, 
 '{citation['location'].replace("'", "''")}', 
 '{citation['plate_state']}', 
 '{citation['plate_number']}', 
 {citation['amount_due']}, 
 '{citation['status']}', 
 '{citation['more_info_url'].replace("'", "''")}', 
 '{citation['scraped_at']}')"""
            values_clauses.append(values_clause)
        
        # Create complete INSERT statement
        sql = f"""
INSERT INTO citations 
(citation_number, location, plate_state, plate_number, amount_due, status, more_info_url, scraped_at)
VALUES 
{', '.join(values_clauses)}
ON CONFLICT (citation_number) DO UPDATE SET
    location = EXCLUDED.location,
    plate_state = EXCLUDED.plate_state,
    plate_number = EXCLUDED.plate_number,
    amount_due = EXCLUDED.amount_due,
    status = EXCLUDED.status,
    scraped_at = EXCLUDED.scraped_at;
"""
        sql_batches.append(sql)
    
    return sql_batches

def main():
    """Main migration function"""
    logger.info("🚀 Starting complete citation migration to Supabase...")
    
    # Load citations
    citations = load_citations()
    
    # Create bulk insert statements
    sql_batches = create_bulk_insert_sql(citations, batch_size=50)
    
    logger.info(f"Created {len(sql_batches)} SQL batches")
    
    # Save SQL batches to files
    for i, sql_batch in enumerate(sql_batches, 1):
        filename = f'bulk_import_batch_{i:02d}.sql'
        with open(filename, 'w') as f:
            f.write(f"-- Bulk import batch {i}: citations {(i-1)*50 + 1} to {min(i*50, len(citations))}\n")
            f.write(sql_batch)
        logger.info(f"Created {filename}")
    
    # Update scraper state
    highest_citation = max(c['citation_number'] for c in citations)
    scraper_state_sql = f"""
-- Update scraper state
INSERT INTO scraper_state (last_successful_citation) 
VALUES ({highest_citation})
ON CONFLICT (id) DO UPDATE SET 
    last_successful_citation = EXCLUDED.last_successful_citation,
    updated_at = NOW();
"""
    
    with open('update_scraper_state.sql', 'w') as f:
        f.write(scraper_state_sql)
    
    logger.info(f"✅ Migration preparation complete!")
    logger.info(f"📊 Total citations: {len(citations)}")
    logger.info(f"🔢 Citation range: {min(c['citation_number'] for c in citations)} to {highest_citation}")
    logger.info(f"📁 Created {len(sql_batches)} bulk import files")
    logger.info(f"🎯 Highest citation: {highest_citation}")
    
    logger.info("\n📋 Next steps:")
    logger.info("1. Run each bulk_import_batch_XX.sql file using Supabase MCP")
    logger.info("2. Run update_scraper_state.sql to set the scraper state")
    logger.info("3. Verify the migration with: SELECT COUNT(*) FROM citations;")

if __name__ == "__main__":
    main()
