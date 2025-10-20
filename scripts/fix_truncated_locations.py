#!/usr/bin/env python3
"""
Fix truncated OCR locations by restoring full street names from scraped data.
"""

import os
import re
import psycopg
from dotenv import load_dotenv


def get_connection():
    """Get database connection."""
    load_dotenv()
    cfg = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'dbname': os.getenv('DB_NAME', 'parking_local'),
        'user': os.getenv('DB_USER', os.getenv('USER')),
        'password': os.getenv('DB_PASSWORD', ''),
        'port': os.getenv('DB_PORT', '5432'),
    }
    return psycopg.connect(**cfg)


def fix_truncated_locations():
    """Fix locations that got truncated to just directional letters."""
    conn = get_connection()
    updated_count = 0
    
    try:
        with conn.cursor() as cur:
            # Get citations with truncated OCR locations
            cur.execute("""
                SELECT citation_number, ocr_location, location 
                FROM citations 
                WHERE (ocr_location ~ '^[0-9]+ [ESNW]$' OR ocr_location ~ '^[0-9]+ [ESNW] [A-Z]')
                   AND location IS NOT NULL
            """)
            
            rows = cur.fetchall()
            print(f"Found {len(rows)} citations with truncated OCR locations to fix")
            
            for citation_num, ocr_location, scraped_location in rows:
                # Use the scraped location as the corrected OCR location
                # since it has the full street name
                corrected_location = scraped_location
                
                if corrected_location != ocr_location:
                    cur.execute("""
                        UPDATE citations 
                        SET ocr_location = %s
                        WHERE citation_number = %s
                    """, (corrected_location, citation_num))
                    
                    print(f"Citation {citation_num}: '{ocr_location}' -> '{corrected_location}'")
                    updated_count += 1
            
            conn.commit()
            print(f"\nSuccessfully updated {updated_count} citations")
            
    except Exception as e:
        print(f"Error during fix: {e}")
        conn.rollback()
    finally:
        conn.close()


def show_sample_after_fix():
    """Show sample of fixed data."""
    conn = get_connection()
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT citation_number, ocr_location, vehicle_model 
                FROM citations 
                WHERE ocr_location IS NOT NULL OR vehicle_model IS NOT NULL
                ORDER BY citation_number DESC 
                LIMIT 10
            """)
            
            rows = cur.fetchall()
            print("\n=== SAMPLE AFTER FIX ===")
            for citation_num, location, model in rows:
                print(f"Citation {citation_num}:")
                if location:
                    print(f"  Location: {location}")
                if model:
                    print(f"  Model: {model}")
                print()
                
    except Exception as e:
        print(f"Error showing sample: {e}")
    finally:
        conn.close()


if __name__ == '__main__':
    print("Starting OCR location fix...")
    fix_truncated_locations()
    show_sample_after_fix()
    print("Fix complete!")


