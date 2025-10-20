#!/usr/bin/env python3
"""
Run OCR enrichment on citations from the highest number we have +1500.
"""

import os
import re
import psycopg
from dotenv import load_dotenv
from ocr_citation_parser import extract_text_from_image, get_last_image_in_dir, parse_citation_data


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


def update_citation_with_ocr(conn, citation_number: int, data: dict):
    """Update citation with OCR data."""
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE citations SET
                vehicle_make = COALESCE(%s, vehicle_make),
                vehicle_model = COALESCE(%s, vehicle_model),
                vehicle_color = COALESCE(%s, vehicle_color),
                plate_exp_month = COALESCE(%s, plate_exp_month),
                plate_exp_year = COALESCE(%s, plate_exp_year),
                district_number = COALESCE(%s, district_number),
                meter_number = COALESCE(%s, meter_number),
                ocr_location = COALESCE(%s, ocr_location),
                comments = COALESCE(%s, comments)
            WHERE citation_number = %s
            """,
            (
                data.get('make'),
                data.get('model'),
                data.get('color'),
                int(data['plate_exp_month']) if data.get('plate_exp_month') else None,
                int(data['plate_exp_year']) if data.get('plate_exp_year') else None,
                int(data['district']) if data.get('district') else None,
                data.get('meter_number'),
                data.get('location'),
                data.get('comments'),
                citation_number,
            ),
        )


def enrich_citations_range(start_citation: int, end_citation: int):
    """Enrich citations in the specified range with OCR data."""
    conn = get_connection()
    processed = 0
    updated = 0
    errors = 0
    
    try:
        print(f"Starting OCR enrichment for citations {start_citation} to {end_citation}")
        
        for citation_num in range(start_citation, end_citation + 1):
            # Check if we have images for this citation
            img_dir = f'images/{citation_num}'
            if not os.path.exists(img_dir):
                continue
            
            last_img = get_last_image_in_dir(img_dir)
            if not last_img:
                continue
            
            try:
                # Extract OCR text
                ocr_text = extract_text_from_image(last_img)
                if not ocr_text:
                    continue
                
                # Parse the OCR data
                parsed_data = parse_citation_data(ocr_text)
                
                # Clean up the location if it exists
                if parsed_data.get('location'):
                    location = parsed_data['location']
                    # Remove noisy tokens
                    location = re.sub(r'\s+(DISTRICT|COMPLAINT|VIOLATION).*$', '', location, flags=re.IGNORECASE)
                    # Add proper spacing
                    location = re.sub(r'(\d)([A-Z])', r'\1 \2', location)
                    location = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', location)
                    parsed_data['location'] = location.strip()
                
                # Update the database
                update_citation_with_ocr(conn, citation_num, parsed_data)
                
                processed += 1
                updated += 1
                
                if processed % 50 == 0:
                    print(f"Processed {processed} citations, updated {updated}")
                    conn.commit()
                
            except Exception as e:
                print(f"Error processing citation {citation_num}: {e}")
                errors += 1
                continue
        
        conn.commit()
        print(f"\nOCR enrichment complete!")
        print(f"Processed: {processed} citations")
        print(f"Updated: {updated} citations")
        print(f"Errors: {errors} citations")
        
    except Exception as e:
        print(f"Error during enrichment: {e}")
        conn.rollback()
    finally:
        conn.close()


def show_sample_results():
    """Show sample of enriched data."""
    conn = get_connection()
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT citation_number, ocr_location, vehicle_make, vehicle_model, vehicle_color
                FROM citations 
                WHERE ocr_location IS NOT NULL 
                   OR vehicle_make IS NOT NULL 
                   OR vehicle_model IS NOT NULL
                ORDER BY citation_number DESC 
                LIMIT 10
            """)
            
            rows = cur.fetchall()
            print("\n=== SAMPLE ENRICHED DATA ===")
            for citation_num, location, make, model, color in rows:
                print(f"Citation {citation_num}:")
                if location:
                    print(f"  Location: {location}")
                if make or model or color:
                    print(f"  Vehicle: {make} {model} [{color}]")
                print()
                
    except Exception as e:
        print(f"Error showing sample: {e}")
    finally:
        conn.close()


if __name__ == '__main__':
    # Get the highest citation number and add 1500
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(citation_number) FROM citations")
            max_citation = cur.fetchone()[0]
            start_citation = max_citation
            end_citation = max_citation + 1500
            
            print(f"Starting from citation {start_citation}, going to {end_citation}")
    finally:
        conn.close()
    
    enrich_citations_range(start_citation, end_citation)
    show_sample_results()
