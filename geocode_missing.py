#!/usr/bin/env python3
"""
Utility script to geocode citations that were scraped after a specific timestamp
but don't have coordinates yet.

Usage:
    python geocode_missing.py
"""

import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from db_manager import DatabaseManager
from geocoder import Geocoder
from nonstandard import resolve_alias

def main():
    """Geocode citations scraped after 2025-11-12 15:20:04.855189+00 that don't have coordinates"""
    load_dotenv()
    
    # The timestamp from which geocoding stopped working
    cutoff_timestamp = datetime.fromisoformat('2025-11-12T15:20:04.855189+00:00')
    
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'postgres'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'port': os.getenv('DB_PORT', '5432'),
    }
    
    db_manager = DatabaseManager(db_config)
    geocoder = Geocoder()
    
    # Get all citations that:
    # 1. Have a location
    # 2. Don't have coordinates (latitude is null)
    # 3. Were scraped at or after the cutoff timestamp
    print(f"Fetching citations scraped after {cutoff_timestamp.isoformat()} without coordinates...")
    
    try:
        # Query for citations without coordinates, with location, scraped after cutoff
        result = (
            db_manager.supabase
            .table('citations')
            .select('citation_number,location,scraped_at')
            .not_.is_('location', 'null')
            .is_('latitude', 'null')
            .gte('scraped_at', cutoff_timestamp.isoformat())
            .execute()
        )
        
        citations = result.data if result.data else []
        print(f"Found {len(citations)} citations to geocode")
        
        if not citations:
            print("No citations need geocoding!")
            return
        
        success_count = 0
        fail_count = 0
        cached_count = 0
        nonstandard_count = 0
        
        for i, citation in enumerate(citations):
            citation_number = citation['citation_number']
            address = citation.get('location')
            scraped_at = citation.get('scraped_at')
            
            if not address:
                print(f"[{i+1}/{len(citations)}] Skipping citation {citation_number} - no address")
                continue
            
            print(f"[{i+1}/{len(citations)}] Geocoding citation {citation_number}: {address}")
            
            # Try to use cached coordinates first
            cached = db_manager.get_cached_coords_for_location(address)
            if cached:
                lat, lon = cached
                try:
                    db_manager.supabase.table('citations').update({
                        'latitude': lat,
                        'longitude': lon,
                        'geocoded_at': 'now()'
                    }).eq('citation_number', citation_number).execute()
                    cached_count += 1
                    print(f"  ✓ Success (cached)")
                    continue
                except Exception as e:
                    print(f"  ✗ Failed to update with cached coords: {e}")
            
            # Try nonstandard alias resolution
            mapped_address, coords = resolve_alias(address)
            if coords:
                lat, lon = coords
                try:
                    db_manager.supabase.table('citations').update({
                        'latitude': lat,
                        'longitude': lon,
                        'geocoded_at': 'now()'
                    }).eq('citation_number', citation_number).execute()
                    nonstandard_count += 1
                    print(f"  ✓ Success (nonstandard)")
                    continue
                except Exception as e:
                    print(f"  ✗ Failed to update with nonstandard coords: {e}")
            elif mapped_address:
                if geocoder.geocode_and_update_citation(db_manager, citation_number, mapped_address):
                    nonstandard_count += 1
                    print(f"  ✓ Success (nonstandard mapping)")
                    continue
            
            # Fallback: geocode the raw location string
            if geocoder.geocode_and_update_citation(db_manager, citation_number, address):
                success_count += 1
                print(f"  ✓ Success")
            else:
                fail_count += 1
                print(f"  ✗ Failed")
        
        print(f"\nGeocoding complete!")
        print(f"  Success (geocoded): {success_count}")
        print(f"  Success (cached): {cached_count}")
        print(f"  Success (nonstandard): {nonstandard_count}")
        print(f"  Failed: {fail_count}")
        print(f"  Total: {len(citations)}")
        
    except Exception as e:
        print(f"Error fetching citations: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

