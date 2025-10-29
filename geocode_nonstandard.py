#!/usr/bin/env python3
"""
Geocode citations with nonstandard, non-geocodable location aliases using mappings in nonstandard.md.

Usage:
    python geocode_nonstandard.py
"""

import os
import re
import sys
from typing import Dict, Tuple, Optional
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from db_manager import DatabaseManager
from geocoder import Geocoder

NONSTANDARD_FILE = os.path.join(os.path.dirname(__file__), 'nonstandard.md')


def parse_nonstandard_file(path: str) -> Tuple[Dict[str, str], Dict[str, Tuple[float, float]]]:
    """Parse nonstandard.md into alias->address and alias->(lat, lon) maps."""
    alias_to_address: Dict[str, str] = {}
    alias_to_coords: Dict[str, Tuple[float, float]] = {}

    if not os.path.exists(path):
        raise FileNotFoundError(f"nonstandard file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            # Expected formats:
            #   "Alias: 123 Main St, Ann Arbor, MI 48104"
            #   "Alias: 42.292306, -83.717500"
            if ':' not in line:
                continue
            alias, rhs = line.split(':', 1)
            alias = alias.strip()
            rhs = rhs.strip()

            # Try coordinates first
            m = re.match(r'^(-?\d+(?:\.\d+)?)[ ,]+(-?\d+(?:\.\d+)?)$', rhs)
            if m:
                lat = float(m.group(1))
                lon = float(m.group(2))
                alias_to_coords[alias] = (lat, lon)
                continue

            # Otherwise treat as address string
            if rhs:
                alias_to_address[alias] = rhs

    return alias_to_address, alias_to_coords


def update_citation_coords(db_manager: DatabaseManager, citation_number: int, lat: float, lon: float) -> None:
    db_manager.supabase.table('citations').update({
        'latitude': lat,
        'longitude': lon,
        'geocoded_at': 'now()'
    }).eq('citation_number', citation_number).execute()


def main() -> None:
    load_dotenv()

    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'postgres'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'port': os.getenv('DB_PORT', '5432'),
    }

    db_manager = DatabaseManager(db_config)
    geocoder = Geocoder()

    alias_to_address, alias_to_coords = parse_nonstandard_file(NONSTANDARD_FILE)

    aliases = sorted(set(list(alias_to_address.keys()) + list(alias_to_coords.keys())))
    if not aliases:
        print("No aliases found in nonstandard.md")
        return

    print(f"Found {len(aliases)} aliases in nonstandard.md")

    # Fetch citations whose location exactly matches any alias and is missing coordinates
    print("Querying citations with nonstandard locations and missing coords...")
    # Supabase python client doesn't support eq any-of natively in a single call; loop aliases
    total_checked = 0
    total_updated = 0

    for alias in aliases:
        result = db_manager.supabase.table('citations').select('*') \
            .eq('location', alias) \
            .is_('latitude', 'null') \
            .is_('longitude', 'null') \
            .execute()

        citations = result.data or []
        if not citations:
            continue

        print(f"Alias '{alias}': {len(citations)} pending updates")

        for citation in citations:
            total_checked += 1
            citation_number = citation['citation_number']

            # If we have explicit coords mapping, use it
            if alias in alias_to_coords:
                lat, lon = alias_to_coords[alias]
                try:
                    update_citation_coords(db_manager, citation_number, lat, lon)
                    total_updated += 1
                    print(f"  ✓ {citation_number} updated with coords ({lat}, {lon})")
                except Exception as e:
                    print(f"  ✗ {citation_number} failed to update coords: {e}")
                continue

            # If we have an address mapping, geocode that address
            mapped_address: Optional[str] = alias_to_address.get(alias)
            if mapped_address:
                try:
                    ok = geocoder.geocode_and_update_citation(db_manager, citation_number, mapped_address)
                    if ok:
                        total_updated += 1
                        print(f"  ✓ {citation_number} geocoded via '{mapped_address}'")
                    else:
                        print(f"  ✗ {citation_number} geocoding failed for '{mapped_address}'")
                except Exception as e:
                    print(f"  ✗ {citation_number} error geocoding '{mapped_address}': {e}")
            else:
                print(f"  ✗ {citation_number} alias has no mapping")

    print("\nDone.")
    print(f"Checked: {total_checked}")
    print(f"Updated: {total_updated}")


if __name__ == '__main__':
    main()
