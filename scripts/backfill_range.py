import os
import json
import time
import logging
from dotenv import load_dotenv
from scraper import CitationScraper
from db_manager import DatabaseManager
from image_downloader import download_images


logging.basicConfig(level=logging.INFO)
load_dotenv()


DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': os.getenv('DB_PORT', '5432'),
}


def backfill(start_num: int, end_num: int):
    scraper = CitationScraper()
    db = DatabaseManager(DB_CONFIG)
    step = 1 if end_num >= start_num else -1
    count_saved = 0
    for citation in range(start_num, end_num + step, step):
        logging.info(f"Processing {citation}")
        data = scraper.search_citation(str(citation))
        if not data:
            continue
        # Download images locally
        local_images = download_images(data.get('image_urls') or [], str(citation))
        if local_images:
            # Replace image_urls with local paths list in a parallel key
            data['local_image_paths'] = [p for (_, p) in local_images]
        try:
            db.save_citation(data)
            db.update_last_successful_citation(citation)
            count_saved += 1
        except Exception as e:
            logging.exception(f"DB save failed for {citation}: {e}")
        time.sleep(1)
    logging.info(f"Done. Saved {count_saved} records.")


if __name__ == '__main__':
    s = int(os.getenv('RANGE_START', '10515150'))
    e = int(os.getenv('RANGE_END', '10516869'))
    backfill(s, e)


