#!/usr/bin/env python3
"""
Range Discovery Script - Gentle Version
Checks citation ranges with longer delays to be nice to the server.

Features:
- 2-5 second delay between each request (random)
- Single-threaded to avoid overwhelming the server
- Resume capability: tracks progress in a checkpoint file
- Samples every 500th citation (same as fast version)

Usage:
  python3 discover_ranges_gentle.py           # Start fresh
  python3 discover_ranges_gentle.py --resume  # Resume from checkpoint
"""

import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import re
import os
import sys
import json
import random
import argparse

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Output files
OUTPUT_FILE = "discovered_ranges_gentle.txt"
CHECKPOINT_FILE = "discover_checkpoint.json"

# Cutoff date - only log citations issued after this date as "recent"
CUTOFF_DATE = datetime(2025, 12, 25, tzinfo=ZoneInfo('UTC'))

# Sample step - check every Nth citation within each 10k range
SAMPLE_STEP = 500  # 20 samples per 10k range

# Delay between requests (seconds)
MIN_DELAY = 2.0
MAX_DELAY = 5.0

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


def get_10k_ranges_to_check() -> list:
    """Generate list of 10k ranges to check, excluding known ranges."""
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


class GentleChecker:
    """Lightweight citation checker with longer delays."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        self._token = None
        self._token_time = 0
        self.consecutive_failures = 0
    
    def get_verification_token(self) -> str | None:
        # Reuse token for 60 seconds
        if self._token and (time.time() - self._token_time) < 60:
            return self._token
        
        try:
            response = self.session.get('https://annarbor.citationportal.com/', timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            token_input = soup.find('input', {'name': '__RequestVerificationToken'})
            if token_input:
                self._token = token_input['value']
                self._token_time = time.time()
                self.consecutive_failures = 0
                return self._token
            return None
        except Exception as e:
            self.consecutive_failures += 1
            print(f"  Token error ({self.consecutive_failures}): {e}")
            return None
    
    def check_citation(self, citation_number: str) -> dict | None:
        """Check if a citation exists and return basic info."""
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
                timeout=30
            )
            self.consecutive_failures = 0
            return self.parse_result(response.text, citation_number)
        except Exception as e:
            self.consecutive_failures += 1
            print(f"  Search error ({self.consecutive_failures}): {e}")
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


def load_checkpoint() -> dict:
    """Load checkpoint if it exists."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {
        'completed_ranges': [],
        'total_checked': 0,
        'total_hits': 0,
        'total_recent_hits': 0,
        'recent_ranges': [],
        'old_ranges': [],
    }


def save_checkpoint(data: dict):
    """Save checkpoint to file."""
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def write_hit_to_file(hit: dict, range_start: int, range_end: int):
    """Append a single hit to the output file."""
    with open(OUTPUT_FILE, 'a') as f:
        recent_marker = "[RECENT]" if hit.get('is_recent') else "[OLD]"
        f.write(f"  {recent_marker} {hit['citation_number']} | "
               f"Issued: {hit['issue_date_str']} | Location: {hit['location']} | "
               f"Status: {hit['status']} | Range: {range_start:,}-{range_end:,}\n")


def main():
    parser = argparse.ArgumentParser(description='Gentle range discovery')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    args = parser.parse_args()
    
    print("=" * 60)
    print("PARKING CITATION RANGE DISCOVERY - GENTLE VERSION")
    print(f"Sampling every {SAMPLE_STEP}th citation")
    print(f"Delay between requests: {MIN_DELAY}-{MAX_DELAY} seconds")
    print(f"Looking for ranges with citations since {CUTOFF_DATE.date()}")
    print("=" * 60)
    
    # Load or initialize checkpoint
    checkpoint = load_checkpoint() if args.resume else {
        'completed_ranges': [],
        'total_checked': 0,
        'total_hits': 0,
        'total_recent_hits': 0,
        'recent_ranges': [],
        'old_ranges': [],
    }
    
    if args.resume and checkpoint['completed_ranges']:
        print(f"\nResuming from checkpoint:")
        print(f"  Completed ranges: {len(checkpoint['completed_ranges'])}")
        print(f"  Total checked: {checkpoint['total_checked']}")
        print(f"  Hits: {checkpoint['total_hits']} ({checkpoint['total_recent_hits']} recent)")
    else:
        # Create/clear output file with header
        with open(OUTPUT_FILE, 'w') as f:
            f.write(f"# Citation Range Discovery Results - GENTLE\n")
            f.write(f"# Run at: {datetime.now().isoformat()}\n")
            f.write(f"# Cutoff date for 'recent': {CUTOFF_DATE.date()}\n")
            f.write(f"# Sample step: every {SAMPLE_STEP}th citation\n")
            f.write("=" * 80 + "\n")
    
    all_ranges = get_10k_ranges_to_check()
    completed_set = set(tuple(r) for r in checkpoint['completed_ranges'])
    ranges_to_check = [r for r in all_ranges if tuple(r) not in completed_set]
    
    print(f"\nTotal ranges: {len(all_ranges)}")
    print(f"Already done: {len(checkpoint['completed_ranges'])}")
    print(f"Remaining: {len(ranges_to_check)}")
    
    samples_per_range = 10_000 // SAMPLE_STEP
    remaining_samples = len(ranges_to_check) * samples_per_range
    avg_delay = (MIN_DELAY + MAX_DELAY) / 2
    est_minutes = (remaining_samples * avg_delay) / 60
    
    print(f"Estimated time remaining: ~{est_minutes:.0f} minutes ({est_minutes/60:.1f} hours)")
    print("\nSkipping known ranges:")
    for start, end in KNOWN_RANGES:
        print(f"  - {start:,} to {end:,}")
    
    print(f"\nStarting in 3 seconds...")
    time.sleep(3)
    
    checker = GentleChecker()
    start_time = time.time()
    
    try:
        for range_idx, (range_start, range_end) in enumerate(ranges_to_check):
            print(f"\n[{range_idx + 1}/{len(ranges_to_check)}] Checking range {range_start:,} - {range_end:,}")
            
            hits = []
            for citation_num in range(range_start, range_end, SAMPLE_STEP):
                # Wait with random delay
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                time.sleep(delay)
                
                # Check if site is down (too many consecutive failures)
                if checker.consecutive_failures >= 5:
                    print(f"\n*** Site appears to be down ({checker.consecutive_failures} failures). Saving checkpoint and exiting. ***")
                    save_checkpoint(checkpoint)
                    print(f"Checkpoint saved. Run with --resume to continue.")
                    return
                
                result = checker.check_citation(str(citation_num))
                checkpoint['total_checked'] += 1
                
                if result:
                    is_recent = result.get('issue_date') and result['issue_date'] >= CUTOFF_DATE
                    result['is_recent'] = is_recent
                    hits.append(result)
                    checkpoint['total_hits'] += 1
                    
                    if is_recent:
                        checkpoint['total_recent_hits'] += 1
                        print(f"  RECENT HIT: {citation_num} issued {result['issue_date_str']}")
                    else:
                        print(f"  OLD HIT: {citation_num} issued {result['issue_date_str']}")
                    
                    write_hit_to_file(result, range_start, range_end)
                else:
                    # Print progress dot every 5 checks
                    if checkpoint['total_checked'] % 5 == 0:
                        print(".", end="", flush=True)
            
            # Mark range as complete
            checkpoint['completed_ranges'].append([range_start, range_end])
            
            if hits:
                has_recent = any(h.get('is_recent') for h in hits)
                if has_recent:
                    checkpoint['recent_ranges'].append([range_start, range_end, len(hits)])
                    print(f"\n  *** RECENTLY ACTIVE RANGE ***")
                else:
                    checkpoint['old_ranges'].append([range_start, range_end, len(hits)])
            
            # Save checkpoint after each range
            save_checkpoint(checkpoint)
            
            elapsed = time.time() - start_time
            remaining = len(ranges_to_check) - range_idx - 1
            if range_idx > 0:
                per_range = elapsed / (range_idx + 1)
                est_remaining = remaining * per_range
                print(f"\n  Range done. Progress: {checkpoint['total_hits']} hits, ~{est_remaining/60:.0f} min remaining")
            
    except KeyboardInterrupt:
        print("\n\n*** Interrupted by user. Saving checkpoint... ***")
        save_checkpoint(checkpoint)
        print(f"Checkpoint saved. Run with --resume to continue.")
        return
    
    elapsed = time.time() - start_time
    
    # Write final summary
    with open(OUTPUT_FILE, 'a') as f:
        f.write("\n" + "=" * 80 + "\n")
        f.write("# SUMMARY\n")
        f.write(f"# Total ranges checked: {len(checkpoint['completed_ranges'])}\n")
        f.write(f"# Total citations sampled: {checkpoint['total_checked']}\n")
        f.write(f"# Total hits: {checkpoint['total_hits']} ({checkpoint['total_recent_hits']} recent)\n")
        f.write(f"# Elapsed time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)\n")
        
        f.write("\n# RECENTLY ACTIVE RANGES:\n")
        for start, end, hits in sorted(checkpoint['recent_ranges']):
            f.write(f"  ({start:,}, {end:,}),  # {hits} hits\n")
        
        f.write("\n# OLDER ACTIVE RANGES:\n")
        for start, end, hits in sorted(checkpoint['old_ranges']):
            f.write(f"  ({start:,}, {end:,}),  # {hits} hits\n")
    
    print("\n" + "=" * 60)
    print("DISCOVERY COMPLETE")
    print(f"Elapsed time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"Total citations sampled: {checkpoint['total_checked']}")
    print(f"Total hits: {checkpoint['total_hits']} ({checkpoint['total_recent_hits']} recent)")
    print(f"\nFull results written to: {OUTPUT_FILE}")
    
    # Clean up checkpoint file on successful completion
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        print("Checkpoint file removed (completed successfully)")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
