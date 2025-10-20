import os
import re
import json
from pathlib import Path
from typing import Dict
import psycopg
from dotenv import load_dotenv
from ocr_citation_parser import extract_text_from_image, parse_citation_data, get_last_image_in_dir


def get_connection():
    load_dotenv()
    cfg = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'dbname': os.getenv('DB_NAME', 'parking_local'),
        'user': os.getenv('DB_USER', os.getenv('USER')),
        'password': os.getenv('DB_PASSWORD', ''),
        'port': os.getenv('DB_PORT', '5432'),
    }
    return psycopg.connect(**cfg)


def update_citation_with_ocr(conn, citation_number: int, data: Dict):
    with conn.cursor() as cur:
        cur.execute(
            """
            update citations set
              vehicle_make = coalesce(%s, vehicle_make),
              vehicle_model = coalesce(%s, vehicle_model),
              vehicle_color = coalesce(%s, vehicle_color),
              plate_exp_month = coalesce(%s, plate_exp_month),
              plate_exp_year = coalesce(%s, plate_exp_year),
              district_number = coalesce(%s, district_number),
              meter_number = coalesce(%s, meter_number),
              ocr_location = coalesce(%s, ocr_location),
              comments = coalesce(%s, comments)
            where citation_number = %s
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


def enrich_all_last_images():
    images_root = Path('images')
    if not images_root.exists():
        print('images directory not found')
        return
    conn = get_connection()
    updated = 0
    try:
        for d in sorted(p for p in images_root.iterdir() if p.is_dir()):
            citation = int(d.name)
            last_img = get_last_image_in_dir(str(d))
            if not last_img:
                continue
            txt = extract_text_from_image(last_img)
            parsed = parse_citation_data(txt)
            update_citation_with_ocr(conn, citation, parsed)
            updated += 1
        conn.commit()
        print(json.dumps({'updated_citations': updated}))
    finally:
        conn.close()


if __name__ == '__main__':
    enrich_all_last_images()


