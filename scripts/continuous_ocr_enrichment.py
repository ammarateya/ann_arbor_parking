#!/usr/bin/env python3
"""
Continuously monitor for new citations and run OCR enrichment on them.
"""

import os
import time
import psycopg
from dotenv import load_dotenv
from ocr_citation_parser import extract_text_from_image, get_last_image_in_dir, parse_citation_data
import re


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


def get_unprocessed_citations():
    """Get citations that have images but no OCR data."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT citation_number 
                FROM citations 
                WHERE vehicle_make IS NULL 
                  AND vehicle_model IS NULL 
                  AND ocr_location IS NULL
                ORDER BY citation_number DESC
                LIMIT 50
            """)
            return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


def process_citation(citation_num):
    """Process a single citation with OCR."""
    img_dir = f'images/{citation_num}'
    if not os.path.exists(img_dir):
        return False
    
    last_img = get_last_image_in_dir(img_dir)
    if not last_img:
        return False
    
    try:
        # Extract OCR text
        ocr_text = extract_text_from_image(last_img)
        if not ocr_text:
            return False
        
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
        conn = get_connection()
        try:
            update_citation_with_ocr(conn, citation_num, parsed_data)
            conn.commit()
            print(f"✅ Processed citation {citation_num}: {parsed_data.get('location', 'N/A')} - {parsed_data.get('make', 'N/A')} {parsed_data.get('model', 'N/A')}")
            return True
        finally:
            conn.close()
        
    except Exception as e:
        print(f"❌ Error processing citation {citation_num}: {e}")
        return False


def continuous_ocr_enrichment():
    """Continuously monitor and process new citations."""
    print("🔄 Starting continuous OCR enrichment...")
    print("Press Ctrl+C to stop")
    
    processed_count = 0
    
    try:
        while True:
            # Get unprocessed citations
            unprocessed = get_unprocessed_citations()
            
            if not unprocessed:
                print("⏳ No unprocessed citations found, waiting...")
                time.sleep(30)
                continue
            
            print(f"📋 Found {len(unprocessed)} unprocessed citations")
            
            # Process each citation
            for citation_num in unprocessed:
                if process_citation(citation_num):
                    processed_count += 1
                
                # Small delay between processing
                time.sleep(1)
            
            print(f"📊 Total processed: {processed_count}")
            print("⏳ Waiting 30 seconds before next check...")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print(f"\n🛑 Stopped. Total citations processed: {processed_count}")


if __name__ == '__main__':
    continuous_ocr_enrichment()
