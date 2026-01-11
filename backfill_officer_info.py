#!/usr/bin/env python3
"""
Officer Info Backfill Script

Backfill officer_badge, officer_name, and officer_beat for existing citations
by OCR-processing their receipt images (last image in image_urls).

Usage:
    python backfill_officer_info.py [--limit N] [--dry-run] [--batch-size N]
"""

import os
import sys
import logging
import argparse
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

from db_manager import DatabaseManager
from scraper import CitationScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Reduce verbosity for noisy third-party libraries
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': os.getenv('DB_PORT', '5432'),
}


def get_citations_without_officer_info(db_manager: DatabaseManager, limit: int = 100, offset: int = 0) -> List[Dict]:
    """Get citations that have images but no officer info.
    
    If the officer_badge column doesn't exist yet, falls back to getting
    all citations with images.
    """
    try:
        # First, try to query with officer_badge filter (column exists)
        try:
            result = (
                db_manager.supabase
                .table('citations')
                .select('citation_number,image_urls')
                .not_.is_('image_urls', 'null')
                .is_('officer_badge', 'null')
                .order('citation_number', desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
        except Exception as col_err:
            # If the column doesn't exist, fall back to getting all citations with images
            if '42703' in str(col_err) or 'does not exist' in str(col_err):
                logger.warning("officer_badge column not found - please run the migration first!")
                logger.warning("Run: docs/migration_add_officer_info.sql in Supabase SQL Editor")
                # Fall back to getting all citations with images
                result = (
                    db_manager.supabase
                    .table('citations')
                    .select('citation_number,image_urls')
                    .not_.is_('image_urls', 'null')
                    .order('citation_number', desc=True)
                    .range(offset, offset + limit - 1)
                    .execute()
                )
            else:
                raise col_err
        
        citations = result.data or []
        # Filter to only include citations that have at least one image URL
        citations_with_images = [
            c for c in citations 
            if c.get('image_urls') and isinstance(c['image_urls'], list) and len(c['image_urls']) > 0
        ]
        return citations_with_images
    except Exception as e:
        logger.error(f"Failed to query citations: {e}")
        return []


def update_officer_info(db_manager: DatabaseManager, citation_number: int, officer_info: Dict) -> bool:
    """Update a citation with officer info."""
    try:
        update_data = {}
        if officer_info.get('officer_badge'):
            update_data['officer_badge'] = officer_info['officer_badge']
        if officer_info.get('officer_name'):
            update_data['officer_name'] = officer_info['officer_name']
        if officer_info.get('officer_beat'):
            update_data['officer_beat'] = officer_info['officer_beat']
        
        if not update_data:
            return False
        
        # Add timestamp for when we extracted this info
        update_data['officer_info_extracted_at'] = datetime.now(timezone.utc).isoformat()
        
        db_manager.supabase.table('citations').update(update_data).eq('citation_number', citation_number).execute()
        return True
    except Exception as e:
        logger.error(f"Failed to update citation {citation_number}: {e}")
        return False


def backfill_officer_info(
    limit: int = 0,
    batch_size: int = 100,
    dry_run: bool = False,
    delay_between_requests: float = 0.1
):
    """Main backfill function."""
    logger.info("=" * 60)
    logger.info("OFFICER INFO BACKFILL")
    logger.info("=" * 60)
    
    if dry_run:
        logger.info("DRY RUN MODE - no database updates will be made")
    
    # Initialize components
    db_manager = DatabaseManager(DB_CONFIG)
    scraper = CitationScraper()
    
    total_processed = 0
    total_updated = 0
    total_skipped = 0
    total_errors = 0
    offset = 0
    
    while True:
        # Get batch of citations
        citations = get_citations_without_officer_info(db_manager, batch_size, offset)
        
        if not citations:
            logger.info(f"No more citations to process (offset={offset})")
            break
        
        logger.info(f"Processing batch of {len(citations)} citations (offset={offset})")
        
        for citation in citations:
            citation_number = citation['citation_number']
            image_urls = citation['image_urls']
            
            # Get the receipt image (last image in the list)
            receipt_url = image_urls[-1] if image_urls else None
            
            if not receipt_url:
                logger.debug(f"No receipt URL for citation {citation_number}")
                total_skipped += 1
                continue
            
            try:
                # Extract officer info
                officer_info = scraper.extract_officer_info_from_receipt(receipt_url)
                
                if officer_info.get('officer_badge') or officer_info.get('officer_name'):
                    if dry_run:
                        logger.info(f"[DRY RUN] Would update citation {citation_number}: {officer_info}")
                    else:
                        success = update_officer_info(db_manager, citation_number, officer_info)
                        if success:
                            logger.info(f"✓ Updated citation {citation_number}: badge={officer_info.get('officer_badge')}, name={officer_info.get('officer_name')}, beat={officer_info.get('officer_beat')}")
                            total_updated += 1
                        else:
                            total_errors += 1
                else:
                    logger.debug(f"No officer info found for citation {citation_number}")
                    total_skipped += 1
                
                total_processed += 1
                
                # Check limit
                if limit > 0 and total_processed >= limit:
                    logger.info(f"Reached limit of {limit} citations")
                    break
                
                # Delay between requests
                time.sleep(delay_between_requests)
                
            except Exception as e:
                logger.error(f"Error processing citation {citation_number}: {e}")
                total_errors += 1
        
        # Check if we should stop
        if limit > 0 and total_processed >= limit:
            break
        
        offset += batch_size
        
        # Safety break if we've processed too many
        if offset > 100000:
            logger.warning("Safety limit reached (100k citations)")
            break
    
    # Summary
    logger.info("=" * 60)
    logger.info("BACKFILL SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total processed: {total_processed}")
    logger.info(f"Total updated:   {total_updated}")
    logger.info(f"Total skipped:   {total_skipped}")
    logger.info(f"Total errors:    {total_errors}")
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Backfill officer info from receipt images')
    parser.add_argument('--limit', type=int, default=0, help='Maximum number of citations to process (0 = unlimited)')
    parser.add_argument('--batch-size', type=int, default=100, help='Number of citations per batch')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without updating database')
    parser.add_argument('--delay', type=float, default=0.1, help='Delay between requests in seconds')
    
    args = parser.parse_args()
    
    backfill_officer_info(
        limit=args.limit,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        delay_between_requests=args.delay
    )


if __name__ == '__main__':
    main()
