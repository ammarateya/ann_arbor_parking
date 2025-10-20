#!/usr/bin/env python3
"""
Clean up existing OCR data in the database by removing noisy tokens and formatting addresses.
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


def format_address(address: str) -> str:
    """
    Format address by adding spaces between numbers and letters.
    Example: 1300EAnnSt -> 1300 E Ann St
    """
    if not address:
        return address
    
    # Remove noisy tokens first
    cleaned = re.sub(r'\s+(DISTRICT|COMPLAINT|VIOLATION).*$', '', address, flags=re.IGNORECASE)
    
    # Add spaces between numbers and letters
    formatted = re.sub(r'(\d)([A-Z])', r'\1 \2', cleaned)
    
    # Add spaces between consecutive capital letters, but be more careful
    # Only add spaces between letters that are part of street names
    formatted = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', formatted)
    
    return formatted.strip()


def clean_model(model: str) -> str:
    """Remove trailing COLOR token from model."""
    if not model:
        return model
    
    # Remove trailing COLOR token
    cleaned = re.sub(r'\s+COLOR\s*$', '', model, flags=re.IGNORECASE)
    return cleaned.strip()


def cleanup_ocr_data():
    """Clean up existing OCR data in the database."""
    conn = get_connection()
    updated_count = 0
    
    try:
        with conn.cursor() as cur:
            # Get all citations with OCR data
            cur.execute("""
                SELECT citation_number, ocr_location, vehicle_model 
                FROM citations 
                WHERE ocr_location IS NOT NULL OR vehicle_model IS NOT NULL
            """)
            
            rows = cur.fetchall()
            print(f"Found {len(rows)} citations with OCR data to clean up")
            
            for citation_num, ocr_location, vehicle_model in rows:
                updates = {}
                
                # Clean up location
                if ocr_location:
                    cleaned_location = format_address(ocr_location)
                    if cleaned_location != ocr_location:
                        updates['ocr_location'] = cleaned_location
                        print(f"Citation {citation_num}: '{ocr_location}' -> '{cleaned_location}'")
                
                # Clean up model
                if vehicle_model:
                    cleaned_model = clean_model(vehicle_model)
                    if cleaned_model != vehicle_model:
                        updates['vehicle_model'] = cleaned_model
                        print(f"Citation {citation_num}: Model '{vehicle_model}' -> '{cleaned_model}'")
                
                # Update database if there are changes
                if updates:
                    set_clauses = []
                    values = []
                    for field, value in updates.items():
                        set_clauses.append(f"{field} = %s")
                        values.append(value)
                    
                    values.append(citation_num)
                    
                    update_query = f"""
                        UPDATE citations 
                        SET {', '.join(set_clauses)}
                        WHERE citation_number = %s
                    """
                    
                    cur.execute(update_query, values)
                    updated_count += 1
            
            conn.commit()
            print(f"\nSuccessfully updated {updated_count} citations")
            
    except Exception as e:
        print(f"Error during cleanup: {e}")
        conn.rollback()
    finally:
        conn.close()


def show_sample_after_cleanup():
    """Show sample of cleaned data."""
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
            print("\n=== SAMPLE AFTER CLEANUP ===")
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
    print("Starting OCR data cleanup...")
    cleanup_ocr_data()
    show_sample_after_cleanup()
    print("Cleanup complete!")
