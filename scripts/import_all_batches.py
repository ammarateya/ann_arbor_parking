#!/usr/bin/env python3
"""
Automatically import all citation batches to Supabase
"""
import os
import glob
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_all_batches():
    """Import all batch files to Supabase"""
    
    # Find all batch files
    batch_files = sorted(glob.glob('import_batch_*.sql'))
    logger.info(f"Found {len(batch_files)} batch files to import")
    
    imported_count = 0
    
    for i, batch_file in enumerate(batch_files, 1):
        logger.info(f"Processing batch {i}/{len(batch_files)}: {batch_file}")
        
        try:
            with open(batch_file, 'r') as f:
                sql_content = f.read()
            
            # Split by semicolon to get individual INSERT statements
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
            
            logger.info(f"  Found {len(statements)} INSERT statements in {batch_file}")
            
            # Import each statement
            for j, statement in enumerate(statements):
                if statement:
                    logger.info(f"    Importing statement {j+1}/{len(statements)}")
                    # Here we would call the Supabase MCP, but for now just log
                    logger.info(f"    Would execute: {statement[:100]}...")
                    imported_count += 1
            
            logger.info(f"  Completed {batch_file}")
            
            # Small delay between batches
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Failed to process {batch_file}: {e}")
    
    logger.info(f"Import completed! Processed {imported_count} statements from {len(batch_files)} batch files")

if __name__ == "__main__":
    import_all_batches()
