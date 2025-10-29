#!/usr/bin/env python3
"""
Rebuild timestamps using ONLY the stored more_info_url for each citation.
- Fetch details page per citation
- Parse issue_date/due_date in local Eastern (America/Detroit), convert to UTC ISO
- Update DB; no search step used
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
    if not local_str:
        return None
    local_str = local_str.strip()
    # Already ISO? try fast path
    try:
        dt = datetime.fromisoformat(local_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=DETROIT_TZ)
        return dt.astimezone(UTC_TZ).isoformat()
    except Exception:
        pass
    fmts: List[str] = [
        '%m/%d/%Y %I:%M %p',
        '%m/%d/%Y %I:%M:%S %p',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
    ]
    for fmt in fmts:
        try:
            naive = datetime.strptime(local_str, fmt)
            eastern_dt = naive.replace(tzinfo=DETROIT_TZ)
            return eastern_dt.astimezone(UTC_TZ).isoformat()
        except Exception:
            continue
    return None


def main():
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    if not supabase_url or not supabase_key:
        logger.error('Missing SUPABASE_URL or key')
        sys.exit(1)
    supabase = create_client(supabase_url, supabase_key)

    logger.info('Fetching all citations with more_info_url...')
    rows: List[Dict] = []
    page_size = 1000
    offset = 0
    while True:
        res = supabase.table('citations').select('citation_number,more_info_url').not_.is_('more_info_url', 'null').order('citation_number').range(offset, offset + page_size - 1).execute()
        batch = res.data or []
        if not batch:
            break
        rows.extend(batch)
        offset += page_size
        if len(batch) < page_size:
            break
    logger.info(f'Found {len(rows)} citations with more_info_url')

    scraper = CitationScraper()

    updated = 0
    skipped = 0
    errors = 0

    for i, row in enumerate(rows, start=1):
        citation_number = row['citation_number']
        url = row.get('more_info_url')
        if i % 25 == 0:
            logger.info(f'Progress {i}/{len(rows)} updated={updated} skipped={skipped} errors={errors}')
        if not url:
            skipped += 1
            continue
        try:
            # Fetch details page directly
            details = scraper.fetch_details_page(url) or {}
            issue_raw = details.get('issue_date') or details.get('issued_date')
            due_raw = details.get('due_date')

            issue_iso = to_utc_iso_from_local_eastern(issue_raw) if issue_raw else None
            due_iso = to_utc_iso_from_local_eastern(due_raw) if due_raw else None

            if not issue_iso and not due_iso:
                skipped += 1
                continue

            payload: Dict[str, object] = {}
            if issue_iso:
                payload['issue_date'] = issue_iso
            if due_iso:
                payload['due_date'] = due_iso

            supabase.table('citations').update(payload).eq('citation_number', citation_number).execute()
            updated += 1
            time.sleep(0.4)
        except Exception as e:
            errors += 1
            logger.error(f'{citation_number}: {e}')
            continue

    logger.info('\n' + '='*60)
    logger.info('SUMMARY')
    logger.info('='*60)
    logger.info(f'Total: {len(rows)} | Updated: {updated} | Skipped: {skipped} | Errors: {errors}')


if __name__ == '__main__':
    main()
