#!/usr/bin/env python3
"""
Script to rebuild issue_date timestamps by fetching details pages from more_info_url
and extracting the timestamp from each page.
"""
import os
import sys
import logging
import time
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from supabase import create_client, Client
from src.scraper import CitationScraper
from typing import Optional, List, Dict

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_date_from_details_page(html: str) -> Optional[str]:
    """Extract issue_date from details page HTML"""
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html, 'html.parser')
    info_list = soup.select('.citation-information-box ul.list-unstyled > li')
    
    for li in info_list:
        key_el = li.find('span', class_='key')
        if not key_el:
            continue
        
        key = key_el.get_text(strip=True).rstrip(':')
        value_el = li.find('span', class_='value')
        
        # Look for Issue Date or Date Issued fields
        if key.lower() in ['issue date', 'date issued', 'issued date', 'date']:
            if value_el:
                date_str = value_el.get_text(" ", strip=True)
                # Parse the date using the same logic as scraper
                return parse_date_str(date_str)
    
    return None


def parse_date_str(date_str: str) -> Optional[str]:
    """Parse date string in format 'MM/DD/YYYY HH:MM AM/PM' to UTC ISO format"""
    try:
        # Clean up HTML tags if any
        date_str = re.sub(r'<br\s*/?>', ' ', date_str).strip()
        
        # Try common date formats
        formats = [
            '%m/%d/%Y %I:%M %p',      # 10/29/2025 3:04 PM
            '%m/%d/%Y %I:%M:%S %p',    # 10/29/2025 3:04:00 PM
            '%Y-%m-%d %H:%M:%S',       # 2025-10-29 15:04:00
        ]
        
        naive_local = None
        for fmt in formats:
            try:
                naive_local = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        
        if not naive_local:
            logger.warning(f"Could not parse date format: {date_str}")
            return None
        
        # Localize to America/Detroit (handles EST/EDT automatically)
        eastern = ZoneInfo('America/Detroit')
        localized = naive_local.replace(tzinfo=eastern)
        
        # Convert to UTC and return ISO string
        utc_time = localized.astimezone(ZoneInfo('UTC'))
        return utc_time.isoformat()
    except Exception as e:
        logger.error(f"Error parsing date '{date_str}': {e}")
        return None


def rebuild_timestamps():
    """Main function to rebuild timestamps for all citations"""
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        logger.error("Missing SUPABASE_URL or SUPABASE credentials")
        sys.exit(1)
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Initialize scraper
    scraper = CitationScraper()
    
    # Get all citations with more_info_url (batch processing for large datasets)
    logger.info("Fetching citations with more_info_url...")
    
    # First, get total count
    count_result = supabase.table('citations').select(
        'citation_number', count='exact'
    ).not_.is_('more_info_url', 'null').execute()
    total_count = count_result.count if hasattr(count_result, 'count') else None
    logger.info(f"Total citations with more_info_url: {total_count or 'unknown'}")
    
    all_citations = []
    page_size = 1000  # Supabase max per request
    offset = 0
    
    logger.info(f"Fetching citations in batches of {page_size}...")
    
    while True:
        # Supabase range() is inclusive: range(0, 999) = 1000 items
        # So range(offset, offset + page_size - 1) gets exactly page_size items
        result = supabase.table('citations').select(
            'citation_number,more_info_url,issue_date'
        ).not_.is_('more_info_url', 'null').order('citation_number').range(offset, offset + page_size - 1).execute()
        
        if not result.data or len(result.data) == 0:
            break
        
        all_citations.extend(result.data)
        logger.info(f"Fetched {len(all_citations)} citations so far...")
        
        # Continue to next page
        offset += page_size
        
        # If we got fewer than page_size, we're done
        if len(result.data) < page_size:
            break
        
        # Safety check: if we've fetched more than total, something's wrong
        if total_count and len(all_citations) >= total_count:
            break
    
    logger.info(f"Found {len(all_citations)} citations with more_info_url")
    
    if not all_citations:
        logger.warning("No citations found with more_info_url")
        return
    
    # Process each citation
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for i, citation in enumerate(all_citations, 1):
        citation_number = citation['citation_number']
        more_info_url = citation['more_info_url']
        current_issue_date = citation.get('issue_date')
        
        logger.info(f"[{i}/{len(all_citations)}] Processing citation {citation_number}...")
        
        try:
            # Try to get issue_date by searching for the citation (most reliable method)
            # This uses the search results table which has the date in cells[5]
            issue_date_str = None
            logger.debug(f"Searching for citation {citation_number} to get issue_date...")
            search_result = scraper.search_citation(str(citation_number))
            
            if search_result and search_result.get('issue_date'):
                issue_date_str = search_result['issue_date']
                logger.debug(f"Got issue_date from search: {issue_date_str}")
            else:
                # Fallback: try to extract from details page HTML
                logger.debug(f"Trying to extract from details page HTML...")
                import requests
                resp = scraper.session.get(more_info_url, timeout=30)
                if resp.status_code == 200:
                    issue_date_str = parse_date_from_details_page(resp.text)
                    if issue_date_str:
                        logger.debug(f"Got issue_date from details page: {issue_date_str}")
            
            if not issue_date_str:
                logger.warning(f"Could not extract issue_date for citation {citation_number}")
                skipped_count += 1
                continue
            
            # Update database
            update_result = supabase.table('citations').update({
                'issue_date': issue_date_str
            }).eq('citation_number', citation_number).execute()
            
            if update_result.data:
                logger.info(f"✓ Updated citation {citation_number}: {issue_date_str}")
                updated_count += 1
            else:
                logger.warning(f"Failed to update citation {citation_number}")
                error_count += 1
            
            # Small delay to be polite
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error processing citation {citation_number}: {e}")
            error_count += 1
            continue
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    logger.info(f"Total citations processed: {len(all_citations)}")
    logger.info(f"Successfully updated: {updated_count}")
    logger.info(f"Skipped (no date found): {skipped_count}")
    logger.info(f"Errors: {error_count}")
    logger.info("="*60)


if __name__ == '__main__':
    rebuild_timestamps()

