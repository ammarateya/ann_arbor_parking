#!/usr/bin/env python3
"""
Rebuild timestamps for ALL citations by re-scraping authoritative data and
storing issue_date and due_date as UTC ISO strings.
- Uses search results (primary source) and details page (fallback)
- Parses Eastern local time (America/Detroit) and converts to UTC
- Retries transient failures and logs a concise summary
"""
import os
import sys
import time
import logging
from typing import Optional, Dict, List
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from supabase import create_client

# Local imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from scraper import CitationScraper  # noqa: E402

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DETROIT_TZ = ZoneInfo('America/Detroit')
UTC_TZ = ZoneInfo('UTC')


def to_utc_iso_from_local_eastern(local_str: str) -> Optional[str]:
    """Parse various local Eastern formats and return UTC ISO string."""
    if not local_str:
        return None
    local_str = local_str.strip()
    fmts: List[str] = [
        '%m/%d/%Y %I:%M %p',         # 10/29/2025 10:47 AM
        '%m/%d/%Y %I:%M:%S %p',      # 10/29/2025 10:47:00 AM
        '%Y-%m-%d %H:%M:%S',         # 2025-10-29 10:47:00
        '%Y-%m-%dT%H:%M:%S%z',       # 2025-10-29T14:47:00+00:00 (already tz)
        '%Y-%m-%dT%H:%M:%S',         # 2025-10-29T10:47:00 (naive)
    ]
    # If already ISO with offset, pass through
    try:
        dt = datetime.fromisoformat(local_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            # Treat naive ISO as Eastern
            dt = dt.replace(tzinfo=DETROIT_TZ)
        return dt.astimezone(UTC_TZ).isoformat()
    except Exception:
        pass
    for fmt in fmts:
        try:
            dt_naive = datetime.strptime(local_str, fmt)
            # Treat parsed time as Eastern local
            eastern_dt = dt_naive.replace(tzinfo=DETROIT_TZ)
            return eastern_dt.astimezone(UTC_TZ).isoformat()
        except Exception:
            continue
    return None


def merge_dates(base: Dict, details: Dict) -> Dict:
    """Merge and normalize issue_date and due_date to UTC ISO strings."""
    result = dict(base or {})
    for src in (base or {}), (details or {}):
        for key in ('issue_date', 'due_date', 'issued_date'):
            if key in src and src[key]:
                iso = to_utc_iso_from_local_eastern(src[key])
                if iso:
                    # Normalize key names: prefer 'issue_date' and 'due_date'
                    normalized_key = 'issue_date' if key in ('issue_date', 'issued_date') else 'due_date'
                    result[normalized_key] = iso
    return result


def fetch_authoritative(scraper: CitationScraper, citation_number: int) -> Optional[Dict]:
    """Fetch citation data with retries; prefer search results, then details."""
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            base = scraper.search_citation(str(citation_number))
            if not base:
                raise RuntimeError('No search result')
            # search_citation already fetches details and merges, but we still enforce UTC normalization
            details = {}
            if base.get('more_info_url'):
                details = scraper.fetch_details_page(base['more_info_url']) or {}
            merged = merge_dates(base, details)
            return merged
        except Exception as e:
            wait = 1.0 * attempt
            logger.warning(f"{citation_number}: attempt {attempt} failed: {e}; retrying in {wait:.1f}s")
            time.sleep(wait)
    logger.error(f"{citation_number}: failed after {max_retries} attempts")
    return None


def main():
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    if not supabase_url or not supabase_key:
        logger.error('Missing SUPABASE_URL or key')
        sys.exit(1)
    supabase = create_client(supabase_url, supabase_key)

    # Get ALL citation numbers
    logger.info('Fetching all citation numbers...')
    all_rows: List[Dict] = []
    page_size = 1000
    offset = 0
    while True:
        res = supabase.table('citations').select('citation_number,more_info_url').order('citation_number').range(offset, offset + page_size - 1).execute()
        batch = res.data or []
        if not batch:
            break
        all_rows.extend(batch)
        offset += page_size
        if len(batch) < page_size:
            break
    logger.info(f"Found {len(all_rows)} citations")

    scraper = CitationScraper()

    updated = 0
    skipped = 0
    errors = 0

    for idx, row in enumerate(all_rows, start=1):
        citation_number = row['citation_number']
        if idx % 25 == 0:
            logger.info(f"Progress: {idx}/{len(all_rows)} updated={updated} skipped={skipped} errors={errors}")
        try:
            data = fetch_authoritative(scraper, citation_number)
            if not data:
                skipped += 1
                continue
            issue_iso = data.get('issue_date')
            due_iso = data.get('due_date')
            if not issue_iso and not due_iso:
                skipped += 1
                continue
            update_payload: Dict[str, object] = {}
            if issue_iso:
                update_payload['issue_date'] = issue_iso
            if due_iso:
                update_payload['due_date'] = due_iso
            # Only update when we have something to set
            if update_payload:
                supabase.table('citations').update(update_payload).eq('citation_number', citation_number).execute()
                updated += 1
            # politeness
            time.sleep(0.4)
        except Exception as e:
            errors += 1
            logger.error(f"{citation_number}: error {e}")
            continue

    logger.info('\n' + '=' * 60)
    logger.info('SUMMARY')
    logger.info('=' * 60)
    logger.info(f"Total: {len(all_rows)} | Updated: {updated} | Skipped: {skipped} | Errors: {errors}")


if __name__ == '__main__':
    main()
