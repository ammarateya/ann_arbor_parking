#!/usr/bin/env python3
"""
Range Discovery Script - Fast Version
Finds active 10k citation ranges that haven't been discovered yet.

Strategy:
1. Check every 500th citation in each 10k range (20 samples per range = 5,580 total)
2. If ANY citation is found in a range (regardless of date), mark it as active
3. If the citation is from after Dec 25th 2025, it's "recently active"

This runs in about 10-15 minutes with 15 workers.
"""

import requests
from bs4 import BeautifulSoup
import concurrent.futures
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import re
import os
import sys

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Output file for discovered ranges
OUTPUT_FILE = "discovered_ranges.txt"

# Lock for thread-safe file writing
file_lock = threading.Lock()
progress_lock = threading.Lock()

# Counters for progress
total_checked = 0
total_hits = 0
total_recent_hits = 0
ranges_completed = 0

# Cutoff date - only log citations issued after this date as "recent"
CUTOFF_DATE = datetime(2025, 12, 25, tzinfo=ZoneInfo('UTC'))

# Sample step - check every Nth citation within each 10k range
SAMPLE_STEP = 500  # 20 samples per 10k range

# Known active ranges (from scraper_only.py) - these will be SKIPPED
KNOWN_RANGES = [
    (10_000_000, 10_020_000),  # AA
    (2_080_000, 2_100_000),    # NC
    (1_000_000, 1_020_000),    # Third
    (2_000_000, 2_080_000),    # Fourth (larger range)
    (1_020_000, 1_030_000),    # Fifth
    (1_030_000, 1_040_000),    # FifthB
    (1_040_000, 1_050_000),    # Sixth
    (1_070_000, 1_080_000),    # Seventh
    (1_120_000, 1_130_000),    # Eighth
    (10_910_000, 10_920_000),  # Ninth
    (2_040_000, 2_060_000),    # Tenth
    (10_310_000, 10_320_000),  # Eleventh
]

def is_in_known_range(citation_num: int) -> bool:
    """Check if a citation number falls within a known range."""
    for start, end in KNOWN_RANGES:
        if start <= citation_num < end:
            return True
    return False

def get_10k_ranges_to_check() -> list:
    """
    Generate list of 10k ranges to check.
    
    We'll check ranges in the following bands:
    - 1,000,000 to 2,000,000 (1M band, 10k increments)
    - 2,000,000 to 3,000,000 (2M band, 10k increments)
    - 10,000,000 to 11,000,000 (10M band, 10k increments)
    
    Skip ranges that are already known/tracked.
    """
    ranges_to_check = []
    
    # 1M to 2M band
    for start in range(1_000_000, 2_000_000, 10_000):
        end = start + 10_000
        overlaps = False
        for known_start, known_end in KNOWN_RANGES:
            if not (end <= known_start or start >= known_end):
                overlaps = True
                break
        if not overlaps:
            ranges_to_check.append((start, end))
    
    # 2M to 3M band
    for start in range(2_000_000, 3_000_000, 10_000):
        end = start + 10_000
        overlaps = False
        for known_start, known_end in KNOWN_RANGES:
            if not (end <= known_start or start >= known_end):
                overlaps = True
                break
        if not overlaps:
            ranges_to_check.append((start, end))
    
    # 10M to 11M band
    for start in range(10_000_000, 11_000_000, 10_000):
        end = start + 10_000
        overlaps = False
        for known_start, known_end in KNOWN_RANGES:
            if not (end <= known_start or start >= known_end):
                overlaps = True
                break
        if not overlaps:
            ranges_to_check.append((start, end))
    
    return ranges_to_check


class QuickChecker:
    """Lightweight citation checker for discovery purposes."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        self._token = None
        self._token_time = 0
    
    def get_verification_token(self) -> str | None:
        # Reuse token for 60 seconds
        if self._token and (time.time() - self._token_time) < 60:
            return self._token
        
        try:
            response = self.session.get('https://annarbor.citationportal.com/', timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            token_input = soup.find('input', {'name': '__RequestVerificationToken'})
            if token_input:
                self._token = token_input['value']
                self._token_time = time.time()
                return self._token
            return None
        except Exception:
            return None
    
    def check_citation(self, citation_number: str) -> dict | None:
        """
        Check if a citation exists and return basic info.
        Returns None if no citation found, otherwise dict with issue_date.
        """
        token = self.get_verification_token()
        if not token:
            return None
        
        search_data = {
            '__RequestVerificationToken': token,
            'Type': 'NumberStrict',
            'Term': citation_number,
            'AdditionalTerm': ''
        }
        
        try:
            response = self.session.post(
                'https://annarbor.citationportal.com/Citation/Search',
                data=search_data,
                timeout=15
            )
            return self.parse_result(response.text, citation_number)
        except Exception:
            return None
    
    def parse_result(self, html: str, citation_number: str) -> dict | None:
        soup = BeautifulSoup(html, 'html.parser')
        
        no_results = soup.find('div', class_='k-grid-norecords-template')
        if no_results and 'No results found' in no_results.text:
            return None
        
        table_rows = soup.find_all('tr', class_='k-table-row k-master-row')
        if table_rows:
            row = table_rows[0]
            cells = row.find_all('td', class_='k-table-td')
            
            if len(cells) >= 9:
                issue_date_str = cells[5].get_text(strip=True)
                issue_date = self.parse_date(issue_date_str)
                
                return {
                    'citation_number': citation_number,
                    'location': cells[1].get_text(strip=True),
                    'issue_date': issue_date,
                    'issue_date_str': issue_date_str,
                    'status': cells[7].get_text(strip=True),
                }
        return None
    
    def parse_date(self, date_str: str) -> datetime | None:
        try:
            date_str = re.sub(r'<br\s*/?>', ' ', date_str).strip()
            naive_local = datetime.strptime(date_str, '%m/%d/%Y %I:%M %p')
            eastern = ZoneInfo('America/Detroit')
            localized = naive_local.replace(tzinfo=eastern)
            return localized.astimezone(ZoneInfo('UTC'))
        except Exception:
            return None


def check_range(range_tuple: tuple) -> tuple[int, int, list]:
    """
    Check a 10k range by sampling every Nth citation.
    Returns (start, end, list_of_hits).
    """
    global total_checked, total_hits, total_recent_hits, ranges_completed
    
    start, end = range_tuple
    checker = QuickChecker()
    hits = []
    
    # Sample every SAMPLE_STEP citation in the range
    for citation_num in range(start, end, SAMPLE_STEP):
        result = checker.check_citation(str(citation_num))
        
        with progress_lock:
            total_checked += 1
        
        if result:
            is_recent = result.get('issue_date') and result['issue_date'] >= CUTOFF_DATE
            hits.append({**result, 'is_recent': is_recent})
            with progress_lock:
                total_hits += 1
                if is_recent:
                    total_recent_hits += 1
                    print(f"RECENT HIT: {citation_num} issued {result['issue_date_str']}")
                else:
                    print(f"OLD HIT: {citation_num} issued {result['issue_date_str']}")
        
        # Minimal delay
        time.sleep(0.01)
    
    with progress_lock:
        ranges_completed += 1
        if ranges_completed % 5 == 0:
            print(f"Progress: {ranges_completed} ranges done, {total_checked} checked, {total_hits} hits ({total_recent_hits} recent)")
    
    return (start, end, hits)


def write_hits_to_file(range_start: int, range_end: int, hits: list, is_recent: bool):
    """Thread-safe write of hits to the output file."""
    with file_lock:
        with open(OUTPUT_FILE, 'a') as f:
            label = "RECENT" if is_recent else "OLD"
            f.write(f"\n### {label} RANGE: {range_start:,} - {range_end:,} ({len(hits)} hits)\n")
            for hit in hits:
                recent_marker = "[RECENT]" if hit.get('is_recent') else "[OLD]"
                f.write(f"  {recent_marker} {hit['citation_number']} | "
                       f"Issued: {hit['issue_date_str']} | Location: {hit['location']} | "
                       f"Status: {hit['status']}\n")


def main():
    global total_checked, total_hits, total_recent_hits, ranges_completed
    
    print("=" * 60)
    print("PARKING CITATION RANGE DISCOVERY - FAST VERSION")
    print(f"Looking for active ranges (highlighting citations since {CUTOFF_DATE.date()})")
    print(f"Sampling every {SAMPLE_STEP}th citation (20 samples per 10k range)")
    print("=" * 60)
    
    # Clear/create output file with header
    with open(OUTPUT_FILE, 'w') as f:
        f.write(f"# Citation Range Discovery Results\n")
        f.write(f"# Run at: {datetime.now().isoformat()}\n")
        f.write(f"# Cutoff date for 'recent': {CUTOFF_DATE.date()}\n")
        f.write(f"# Sample step: every {SAMPLE_STEP}th citation\n")
        f.write("=" * 80 + "\n")
    
    ranges_to_check = get_10k_ranges_to_check()
    total_samples = len(ranges_to_check) * (10_000 // SAMPLE_STEP)
    
    print(f"\nFound {len(ranges_to_check)} ranges to check (excluding known ranges)")
    print(f"Total samples: ~{total_samples:,}")
    
    # Show known ranges being skipped
    print("\nSkipping known ranges:")
    for start, end in KNOWN_RANGES:
        print(f"  - {start:,} to {end:,}")
    
    print(f"\nUsing 15 parallel workers...")
    print()
    
    start_time = time.time()
    recent_ranges = []
    old_ranges = []
    
    # Process ranges with 15 parallel workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        future_to_range = {
            executor.submit(check_range, r): r 
            for r in ranges_to_check
        }
        
        for future in concurrent.futures.as_completed(future_to_range):
            range_tuple = future_to_range[future]
            try:
                range_start, range_end, hits = future.result()
                if hits:
                    has_recent = any(h.get('is_recent') for h in hits)
                    if has_recent:
                        recent_ranges.append((range_start, range_end, hits))
                        print(f"\n*** RECENTLY ACTIVE RANGE: {range_start:,} - {range_end:,} ***\n")
                        write_hits_to_file(range_start, range_end, hits, is_recent=True)
                    else:
                        old_ranges.append((range_start, range_end, hits))
                        write_hits_to_file(range_start, range_end, hits, is_recent=False)
            except Exception as e:
                print(f"Error checking range {range_tuple}: {e}")
    
    elapsed = time.time() - start_time
    
    # Write summary
    with file_lock:
        with open(OUTPUT_FILE, 'a') as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write("# SUMMARY\n")
            f.write(f"# Total ranges checked: {len(ranges_to_check)}\n")
            f.write(f"# Total citations sampled: {total_checked}\n")
            f.write(f"# Total hits: {total_hits} ({total_recent_hits} recent)\n")
            f.write(f"# Elapsed time: {elapsed:.1f} seconds\n")
            
            f.write("\n# RECENTLY ACTIVE RANGES (citations since Dec 25, 2025):\n")
            for start, end, hits in sorted(recent_ranges):
                recent_count = sum(1 for h in hits if h.get('is_recent'))
                f.write(f"  ({start:,}, {end:,}),  # {len(hits)} hits, {recent_count} recent\n")
            
            f.write("\n# OLDER ACTIVE RANGES (no recent citations found in sample):\n")
            for start, end, hits in sorted(old_ranges):
                f.write(f"  ({start:,}, {end:,}),  # {len(hits)} hits\n")
    
    print("\n" + "=" * 60)
    print("DISCOVERY COMPLETE")
    print(f"Elapsed time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"Total citations sampled: {total_checked}")
    print(f"Total hits: {total_hits} ({total_recent_hits} recent)")
    
    print(f"\n=== RECENTLY ACTIVE RANGES ({len(recent_ranges)}) ===")
    for start, end, hits in sorted(recent_ranges):
        recent_count = sum(1 for h in hits if h.get('is_recent'))
        print(f"  ({start:,}, {end:,}),  # {len(hits)} hits, {recent_count} recent")
    
    print(f"\n=== OLDER ACTIVE RANGES ({len(old_ranges)}) ===")
    for start, end, hits in sorted(old_ranges):
        print(f"  ({start:,}, {end:,}),  # {len(hits)} hits")
    
    print(f"\nFull results written to: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
