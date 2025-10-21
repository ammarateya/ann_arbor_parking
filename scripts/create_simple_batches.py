#!/usr/bin/env python3
"""
Simple batch import of citations to Supabase
"""
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_simple_import_batches():
    """Create simple SQL batches for import"""
    
    with open('citations_export.json', 'r') as f:
        citations = json.load(f)
    
    logger.info(f"Creating import batches for {len(citations)} citations")
    
    # Create batches of 10 citations each
    batch_size = 10
    batch_num = 1
    
    for i in range(0, len(citations), batch_size):
        batch = citations[i:i + batch_size]
        
        filename = f'import_batch_{batch_num:03d}.sql'
        
        with open(filename, 'w') as f:
            f.write(f"-- Import batch {batch_num}: citations {i+1} to {min(i+batch_size, len(citations))}\n\n")
            
            for citation in batch:
                # Simple insert without complex escaping
                sql = f"""
INSERT INTO citations 
(citation_number, location, plate_state, plate_number, amount_due, status, more_info_url, scraped_at)
VALUES 
({citation['citation_number']}, 
 '{citation['location'].replace("'", "''")}', 
 '{citation['plate_state']}', 
 '{citation['plate_number']}', 
 {citation['amount_due']}, 
 '{citation['status']}', 
 '{citation['more_info_url'].replace("'", "''")}', 
 '{citation['scraped_at']}')
ON CONFLICT (citation_number) DO UPDATE SET
    location = EXCLUDED.location,
    plate_state = EXCLUDED.plate_state,
    plate_number = EXCLUDED.plate_number,
    amount_due = EXCLUDED.amount_due,
    status = EXCLUDED.status,
    scraped_at = EXCLUDED.scraped_at;

"""
                f.write(sql)
        
        logger.info(f"Created {filename} with {len(batch)} citations")
        batch_num += 1
    
    logger.info(f"Created {batch_num - 1} batch files")

if __name__ == "__main__":
    create_simple_import_batches()
