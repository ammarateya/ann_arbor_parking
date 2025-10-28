#!/usr/bin/env python3
"""
Utility script to geocode citations in the database that don't have coordinates yet.

Usage:
    python geocode_citations.py
"""

import os
import sys
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from db_manager import DatabaseManager
from geocoder import Geocoder

def main():
    """Geocode citations that don't have coordinates"""
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
    
    # Get all citations that have a location but no coordinates
    print("Fetching citations without coordinates...")
    result = db_manager.supabase.table('citations').select('*').not_.is_('location', 'null').is_('latitude', 'null').execute()
    
    citations = result.data if result.data else []
    
    print(f"Found {len(citations)} citations to geocode")
    
    if not citations:
        print("No citations need geocoding!")
        return
    
    success_count = 0
    fail_count = 0
    
    for i, citation in enumerate(citations):
        citation_number = citation['citation_number']
        address = citation.get('location')
        
        if not address:
            print(f"[{i+1}/{len(citations)}] Skipping citation {citation_number} - no address")
            continue
        
        print(f"[{i+1}/{len(citations)}] Geocoding citation {citation_number}: {address}")
        
        if geocoder.geocode_and_update_citation(db_manager, citation_number, address):
            success_count += 1
            print(f"  ✓ Success")
        else:
            fail_count += 1
            print(f"  ✗ Failed")
    
    print(f"\nGeocoding complete!")
    print(f"  Success: {success_count}")
    print(f"  Failed: {fail_count}")
    print(f"  Total: {len(citations)}")

if __name__ == '__main__':
    main()

