#!/usr/bin/env python3
"""
Fix remaining OCR data formatting issues in the database.
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


def fix_messy_addresses():
    """Fix addresses that still have messy formatting."""
    conn = get_connection()
    updated_count = 0
    
    try:
        with conn.cursor() as cur:
            # Get citations with messy addresses
            cur.execute("""
                SELECT citation_number, ocr_location 
                FROM citations 
                WHERE ocr_location LIKE '%D IS TR IC T%' 
                   OR ocr_location LIKE '%C OM PL AI NT%'
                   OR ocr_location LIKE '%V IO LA TI ON%'
            """)
            
            rows = cur.fetchall()
            print(f"Found {len(rows)} citations with messy addresses to fix")
            
            for citation_num, ocr_location in rows:
                # Clean up the messy formatting
                cleaned = ocr_location
                
                # Remove the messy DISTRICT/COMPLAINT/VIOLATION parts
                cleaned = re.sub(r'\s+D\s+I\s+S\s+T\s+R\s+I\s+C\s+T.*$', '', cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r'\s+C\s+O\s+M\s+P\s+L\s+A\s+I\s+N\s+T.*$', '', cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r'\s+V\s+I\s+O\s+L\s+A\s+T\s+I\s+O\s+N.*$', '', cleaned, flags=re.IGNORECASE)
                
                # Clean up any remaining messy spacing
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                
                if cleaned != ocr_location:
                    cur.execute("""
                        UPDATE citations 
                        SET ocr_location = %s
                        WHERE citation_number = %s
                    """, (cleaned, citation_num))
                    
                    print(f"Citation {citation_num}: '{ocr_location}' -> '{cleaned}'")
                    updated_count += 1
            
            conn.commit()
            print(f"\nSuccessfully updated {updated_count} citations")
            
    except Exception as e:
        print(f"Error during cleanup: {e}")
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
    print("Starting OCR data fix...")
    fix_messy_addresses()
    show_sample_after_fix()
    print("Fix complete!")


