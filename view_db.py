#!/usr/bin/env python3
"""
Pretty database viewer for citation data
"""
import os
import psycopg
from tabulate import tabulate
import json

def get_connection():
    cfg = {
        'host': 'localhost',
        'dbname': 'parking_local',
        'user': os.getenv('USER'),
        'password': '',
        'port': '5432'
    }
    return psycopg.connect(**cfg)

def show_summary():
    """Show database summary statistics"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Total stats
            cur.execute("""
                SELECT 
                    count(*) as total_citations,
                    sum(amount_due) as total_fines,
                    count(CASE WHEN image_urls IS NOT NULL AND jsonb_array_length(image_urls) > 0 THEN 1 END) as with_images
                FROM citations
            """)
            total, fines, images = cur.fetchone()
            
            print("📊 DATABASE SUMMARY")
            print("=" * 50)
            print(f"Total Citations: {total:,}")
            print(f"Total Fine Amount: ${fines:,.2f}")
            print(f"Citations with Images: {images:,}")
            print()

def show_recent_citations(limit=10):
    """Show recent citations"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    citation_number,
                    COALESCE(ocr_location, location) as location,
                    plate_state,
                    plate_number,
                    COALESCE(vehicle_make, '') as make,
                    COALESCE(vehicle_model, '') as model,
                    COALESCE(vehicle_color, '') as color,
                    plate_exp_month,
                    plate_exp_year,
                    district_number,
                    meter_number,
                    amount_due,
                    status,
                    created_at::date as scraped_date
                FROM citations 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (limit,))
            
            headers = [
                "Citation #", "Location", "State", "Plate",
                "Make", "Model", "Color", "Exp Mo", "Exp Yr",
                "District", "Meter", "Amount", "Status", "Date"
            ]
            rows = cur.fetchall()
            
            print("🚗 RECENT CITATIONS")
            print("=" * 80)
            print(tabulate(rows, headers=headers, tablefmt="grid"))
            print()

def show_by_state():
    """Show citations by state"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    plate_state,
                    count(*) as citations,
                    sum(amount_due) as total_fines
                FROM citations 
                GROUP BY plate_state 
                ORDER BY citations DESC 
                LIMIT 15
            """)
            
            headers = ["State", "Citations", "Total Fines"]
            rows = cur.fetchall()
            
            print("🗺️  CITATIONS BY STATE")
            print("=" * 50)
            print(tabulate(rows, headers=headers, tablefmt="grid"))
            print()

def show_by_location():
    """Show top locations"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    location,
                    count(*) as citations,
                    sum(amount_due) as total_fines
                FROM citations 
                GROUP BY location 
                ORDER BY citations DESC 
                LIMIT 10
            """)
            
            headers = ["Location", "Citations", "Total Fines"]
            rows = cur.fetchall()
            
            print("📍 TOP LOCATIONS")
            print("=" * 60)
            print(tabulate(rows, headers=headers, tablefmt="grid"))
            print()

def show_top_vehicles():
    """Top vehicle makes and models from OCR"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT vehicle_make, vehicle_model, count(*) as cnt
                FROM citations
                WHERE vehicle_make IS NOT NULL AND vehicle_model IS NOT NULL
                GROUP BY vehicle_make, vehicle_model
                ORDER BY cnt DESC
                LIMIT 10
            """)
            headers = ["Make", "Model", "Citations"]
            rows = cur.fetchall()
            print("🚙 TOP VEHICLES")
            print("=" * 50)
            print(tabulate(rows, headers=headers, tablefmt="grid"))
            print()

def show_sample_with_details():
    """Show a sample citation with full details"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    citation_number,
                    COALESCE(ocr_location, location) as location,
                    plate_state,
                    plate_number,
                    amount_due,
                    issuing_agency,
                    comments,
                    violations,
                    image_urls,
                    vehicle_make,
                    vehicle_model,
                    vehicle_color,
                    plate_exp_month,
                    plate_exp_year,
                    district_number,
                    meter_number
                FROM citations 
                WHERE vehicle_make IS NOT NULL OR comments IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 1
            """)
            
            row = cur.fetchone()
            if row:
                (citation_num, location, plate_state, plate_number, amount, agency, comments,
                 violations, image_urls, v_make, v_model, v_color, exp_mo, exp_yr, district, meter) = row
                
                print("📋 SAMPLE CITATION DETAILS")
                print("=" * 60)
                print(f"Citation #: {citation_num}")
                print(f"Location: {location}")
                print(f"Plate: {plate_number} ({plate_state})")
                print(f"Amount: ${amount}")
                print(f"Agency: {agency}")
                if v_make or v_model or v_color:
                    print(f"Vehicle: {v_make} {v_model} [{v_color}]")
                if exp_mo or exp_yr:
                    print(f"Plate Exp: {exp_mo}/{exp_yr}")
                if district or meter:
                    print(f"District/Meter: {district}/{meter}")
                print(f"Comments: {comments}")
                if violations:
                    print(f"Violations: {json.loads(violations)}")
                if image_urls:
                    urls = json.loads(image_urls)
                    print(f"Images: {len(urls)} photos")
                print()

def main():
    try:
        show_summary()
        show_recent_citations()
        show_by_state()
        show_by_location()
        show_top_vehicles()
        show_sample_with_details()
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure PostgreSQL is running and the database exists.")

if __name__ == "__main__":
    main()
