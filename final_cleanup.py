#!/usr/bin/env python3
"""
Final cleanup of OCR data - remove all messy DISTRICT/COMPLAINT/VIOLATION parts.
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


def final_cleanup():
    """Remove all messy DISTRICT/COMPLAINT/VIOLATION parts from addresses."""
    conn = get_connection()
    updated_count = 0
    
    try:
        with conn.cursor() as cur:
            # Get all citations with OCR locations
            cur.execute("""
                SELECT citation_number, ocr_location 
                FROM citations 
                WHERE ocr_location IS NOT NULL
            """)
            
            rows = cur.fetchall()
            print(f"Found {len(rows)} citations with OCR locations to clean")
            
            for citation_num, ocr_location in rows:
                # Clean up the messy formatting - remove everything after the street name
                cleaned = ocr_location
                
                # Remove everything that looks like DISTRICT, COMPLAINT, VIOLATION, METER info
                # Keep only the street address part
                cleaned = re.sub(r'\s+D.*$', '', cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r'\s+C.*$', '', cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r'\s+V.*$', '', cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r'\s+M.*$', '', cleaned, flags=re.IGNORECASE)
                
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


def show_sample_after_final_cleanup():
    """Show sample of final cleaned data."""
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
            print("\n=== SAMPLE AFTER FINAL CLEANUP ===")
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
    print("Starting final OCR data cleanup...")
    final_cleanup()
    show_sample_after_final_cleanup()
    print("Final cleanup complete!")


