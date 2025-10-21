#!/usr/bin/env python3
"""
Export local citations to CSV for easy import via Supabase UI
"""
import os
import csv
import json
import psycopg
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOCAL_DB_CONFIG = {
    'host': 'localhost',
    'dbname': 'parking_local',
    'user': os.getenv('USER'),
    'password': '',
    'port': '5432'
}

CSV_PATH = 'citations_export.csv'

COLUMNS = [
    'citation_number',
    'location',
    'plate_state',
    'plate_number',
    'vin',
    'issue_date',
    'due_date',
    'status',
    'amount_due',
    'more_info_url',
    'issuing_agency',
    'comments',
    'violations',  # JSON as string
    'image_urls',  # JSON as string
    'scraped_at'
]

def coerce_json(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value, str):
        # If already a JSON-like string, return as-is
        try:
            json.loads(value)
            return value
        except Exception:
            return json.dumps(value)
    return json.dumps(value)

def export_to_csv() -> None:
    with psycopg.connect(**LOCAL_DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT citation_number, location, plate_state, plate_number, vin,
                       issue_date, due_date, status, amount_due, more_info_url,
                       issuing_agency, comments, violations, image_urls, scraped_at
                FROM citations
                ORDER BY citation_number ASC
                """
            )
            rows = cur.fetchall()
            logger.info(f"Exporting {len(rows)} rows to {CSV_PATH}")
            
            with open(CSV_PATH, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=COLUMNS)
                writer.writeheader()
                
                for row in rows:
                    record = dict(zip(COLUMNS, row))
                    # Coerce JSON columns to strings
                    record['violations'] = coerce_json(record.get('violations'))
                    record['image_urls'] = coerce_json(record.get('image_urls'))
                    
                    # Convert None to empty string for CSV
                    for k, v in record.items():
                        if v is None:
                            record[k] = ''
                    
                    writer.writerow(record)
    logger.info(f"CSV written: {CSV_PATH}")

if __name__ == '__main__':
    export_to_csv()
