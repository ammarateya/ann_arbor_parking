#!/usr/bin/env python3
"""
Restore full addresses by re-running OCR on images and extracting complete location data.
"""

import os
import re
import psycopg
from dotenv import load_dotenv
from ocr_citation_parser import extract_text_from_image, get_last_image_in_dir


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


def restore_full_addresses():
    """Restore full addresses by re-running OCR on images."""
    conn = get_connection()
    updated_count = 0
    
    try:
        with conn.cursor() as cur:
            # Get all citations that have OCR locations but might be missing house numbers
            cur.execute("""
                SELECT citation_number, ocr_location 
                FROM citations 
                WHERE ocr_location IS NOT NULL
                ORDER BY citation_number DESC
                LIMIT 50
            """)
            
            rows = cur.fetchall()
            print(f"Processing {len(rows)} citations to restore full addresses")
            
            for citation_num, current_ocr_location in rows:
                # Get the last image for this citation
                img_path = get_last_image_in_dir(f'images/{citation_num}')
                if not img_path:
                    print(f"No image found for citation {citation_num}")
                    continue
                
                # Extract OCR text
                ocr_text = extract_text_from_image(img_path)
                if not ocr_text:
                    print(f"No OCR text for citation {citation_num}")
                    continue
                
                # Extract location from OCR text
                location_match = re.search(r'LOCATION\s*:\s*([A-Z0-9\s]+?)(?:\s+DISTRICT|\s+COMPLAINT|\s+VIOLATION|$)', ocr_text, re.IGNORECASE)
                if location_match:
                    full_location = location_match.group(1).strip()
                    
                    # Add proper spacing to the address
                    formatted_location = re.sub(r'(\d)([A-Z])', r'\1 \2', full_location)
                    formatted_location = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', formatted_location)
                    
                    if formatted_location != current_ocr_location:
                        cur.execute("""
                            UPDATE citations 
                            SET ocr_location = %s
                            WHERE citation_number = %s
                        """, (formatted_location, citation_num))
                        
                        print(f"Citation {citation_num}: '{current_ocr_location}' -> '{formatted_location}'")
                        updated_count += 1
            
            conn.commit()
            print(f"\nSuccessfully updated {updated_count} citations")
            
    except Exception as e:
        print(f"Error during restoration: {e}")
        conn.rollback()
    finally:
        conn.close()


def show_sample_after_restoration():
    """Show sample of restored data."""
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
            print("\n=== SAMPLE AFTER RESTORATION ===")
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
    print("Starting full address restoration...")
    restore_full_addresses()
    show_sample_after_restoration()
    print("Restoration complete!")

