#!/usr/bin/env python3
"""
Fix existing timestamps in the database that were stored as Eastern time instead of UTC.
Adds 4 hours for EDT or 5 hours for EST to convert them to proper UTC values.
"""
import os
import sys
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)




def fix_timestamps():
    """Fix all issue_date timestamps that were stored as Eastern time instead of UTC"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        logger.error("Missing SUPABASE_URL or SUPABASE credentials")
        sys.exit(1)
    
    supabase = create_client(supabase_url, supabase_key)
    
    logger.info("Fetching all citations with issue_date...")
    
    # Get all citations with issue_date
    all_citations = []
    page_size = 1000
    offset = 0
    
    logger.info(f"Fetching citations in batches of {page_size}...")
    
    while True:
        result = supabase.table('citations').select(
            'citation_number,issue_date'
        ).not_.is_('issue_date', 'null').order('citation_number').range(offset, offset + page_size - 1).execute()
        
        if not result.data or len(result.data) == 0:
            break
        
        all_citations.extend(result.data)
        logger.info(f"Fetched {len(all_citations)} citations so far...")
        
        # Continue to next page
        offset += page_size
        
        # If we got fewer than page_size, we're done
        if len(result.data) < page_size:
            break
    
    logger.info(f"Found {len(all_citations)} citations with issue_date")
    
    if not all_citations:
        logger.warning("No citations found with issue_date")
        return
    
    # Fix each timestamp
    updated_count = 0
    error_count = 0
    
    for i, citation in enumerate(all_citations, 1):
        citation_number = citation['citation_number']
        issue_date_str = citation['issue_date']
        
        if i % 100 == 0:
            logger.info(f"[{i}/{len(all_citations)}] Processing...")
        
        try:
            # Parse current timestamp (stored as if UTC, but actually Eastern time)
            current_dt = datetime.fromisoformat(issue_date_str.replace('Z', '+00:00'))
            
            # Remove timezone info to get naive datetime (the stored value)
            naive_dt = current_dt.replace(tzinfo=None)
            
            # Treat this naive datetime as Eastern local time
            eastern = ZoneInfo('America/Detroit')
            eastern_dt = naive_dt.replace(tzinfo=eastern)
            
            # Convert to UTC (this adds the proper offset automatically based on DST)
            fixed_utc = eastern_dt.astimezone(ZoneInfo('UTC'))
            
            fixed_iso = fixed_utc.isoformat()
            
            # Update database
            update_result = supabase.table('citations').update({
                'issue_date': fixed_iso
            }).eq('citation_number', citation_number).execute()
            
            if update_result.data:
                updated_count += 1
            else:
                logger.warning(f"Failed to update citation {citation_number}")
                error_count += 1
                
        except Exception as e:
            logger.error(f"Error processing citation {citation_number}: {e}")
            error_count += 1
            continue
    
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    logger.info(f"Total citations processed: {len(all_citations)}")
    logger.info(f"Successfully updated: {updated_count}")
    logger.info(f"Errors: {error_count}")
    logger.info("="*60)


if __name__ == '__main__':
    fix_timestamps()

