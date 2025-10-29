#!/usr/bin/env python3
"""
Parking Citation Scraper - Standalone Script
Runs only the scraper without web server. Used by GitHub Actions cron jobs.
"""

import schedule
import time
import logging
import os
import sys
import threading
import traceback
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from db_manager import DatabaseManager
from scraper import CitationScraper
from email_notifier import EmailNotifier
from storage_factory import StorageFactory
from geocoder import Geocoder
from nonstandard import resolve_alias

# Configure verbose logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables from a .env file if present
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': os.getenv('DB_PORT', '5432'),
}

def ongoing_scraper_job():
    """Run scraper job across two seeds with configurable ± range.

    Seeds:
      - Ann Arbor seed: AA_BASE_SEED env var (defaults to last successful citation)
      - North Campus seed: NC_BASE_SEED env var (defaults to 2081673)

    Range size:
      - SCRAPE_RANGE_SIZE env var (defaults to 200)
    """
    logger.info("Starting ongoing scraper job...")
    
    try:
        logger.info("Initializing components...")
        scraper = CitationScraper()
        logger.info("✓ CitationScraper initialized")
        
        db_manager = DatabaseManager(DB_CONFIG)
        logger.info("✓ DatabaseManager initialized")
        
        email_notifier = EmailNotifier()
        logger.info("✓ EmailNotifier initialized")
        
        cloud_storage = StorageFactory.create_storage_service()
        logger.info(f"✓ Cloud storage initialized: {cloud_storage is not None}")
        
        geocoder = Geocoder()
        logger.info("✓ Geocoder initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return
    
    successful_citations = []
    errors = []
    total_processed = 0
    images_uploaded = 0
    
    try:
        logger.info("Getting last successful citation...")
        last_citation = db_manager.get_last_successful_citation()
        if not last_citation:
            logger.error("No last successful citation found.")
            return 

        logger.info(f"Last successful citation: {last_citation}")

        # Configure seeds and range size from environment
        try:
            aa_seed = int(os.getenv('AA_BASE_SEED', str(last_citation)))
        except ValueError:
            aa_seed = last_citation
        try:
            nc_seed = int(os.getenv('NC_BASE_SEED', '2081673'))
        except ValueError:
            nc_seed = 2081673
        try:
            range_size = int(os.getenv('SCRAPE_RANGE_SIZE', '200'))
        except ValueError:
            range_size = 200

        aa_range = (aa_seed - range_size, aa_seed + range_size)
        nc_range = (nc_seed - range_size, nc_seed + range_size)
        ranges = [aa_range, nc_range]

        overall_start = min(start for start, _ in ranges)
        overall_end = max(end for _, end in ranges)

        logger.info(
            f"Processing dual ranges: AA[{aa_range[0]}..{aa_range[1]}], NC[{nc_range[0]}..{nc_range[1]}] "
            f"(overall {overall_start}..{overall_end})"
        )

        # Fetch existing citations once for the overall span; we'll filter per-target when iterating
        logger.info("Fetching existing citations in overall range to optimize processing...")
        existing_citations = db_manager.get_existing_citation_numbers_in_range(overall_start, overall_end)
        logger.info(f"Found {len(existing_citations)} existing citations in overall range. Will skip these.")

        # Build unique target list covering both ranges
        target_numbers = []
        for start_range, end_range in ranges:
            target_numbers.extend(range(start_range, end_range + 1))
        target_numbers = sorted(set(target_numbers))

        for citation_num in target_numbers:
            # Skip if citation already exists in database
            if citation_num in existing_citations:
                logger.debug(f"Skipping citation {citation_num} - already exists in database")
                continue
                
            try:
                logger.debug(f"Processing citation {citation_num}...")
                result = scraper.search_citation(str(citation_num))
                total_processed += 1
                
                if result:
                    logger.debug(f"Found citation {citation_num}, saving to database...")
                    db_manager.save_citation(result)
                    successful_citations.append(result)
                    
                    # Geocode address for map display with caching and nonstandard resolution
                    if result.get('location'):
                        location_str = result['location']
                        try:
                            # 1) DB cache: reuse coords if location was already geocoded before
                            cached = db_manager.get_cached_coords_for_location(location_str)
                            if cached:
                                lat, lon = cached
                                db_manager.supabase.table('citations').update({
                                    'latitude': lat,
                                    'longitude': lon,
                                    'geocoded_at': 'now()'
                                }).eq('citation_number', citation_num).execute()
                                logger.debug(f"✓ Reused cached coords for {citation_num} -> ({lat}, {lon})")
                            else:
                                # 2) Nonstandard alias mapping: coords or mapped address
                                mapped_address, coords = resolve_alias(location_str)
                                if coords:
                                    lat, lon = coords
                                    db_manager.supabase.table('citations').update({
                                        'latitude': lat,
                                        'longitude': lon,
                                        'geocoded_at': 'now()'
                                    }).eq('citation_number', citation_num).execute()
                                    logger.debug(f"✓ Applied nonstandard coords for {citation_num} -> ({lat}, {lon})")
                                elif mapped_address:
                                    geocoder.geocode_and_update_citation(db_manager, citation_num, mapped_address)
                                    logger.debug(f"✓ Geocoded via nonstandard mapping for {citation_num} -> '{mapped_address}'")
                                else:
                                    # 3) Fallback: geocode the raw location string
                                    geocoder.geocode_and_update_citation(db_manager, citation_num, location_str)
                                    logger.debug(f"✓ Geocoded citation {citation_num}")
                        except Exception as e:
                            logger.warning(f"Failed to geocode citation {citation_num}: {e}")
                    
                    # Upload images to cloud storage if available
                    if result.get('image_urls') and cloud_storage and cloud_storage.is_configured():
                        try:
                            logger.debug(f"Uploading images for citation {citation_num}...")
                            uploaded_images = cloud_storage.upload_images_for_citation(
                                result['image_urls'], 
                                citation_num
                            )
                            
                            # Save cloud storage image metadata to database
                            for image_data in uploaded_images:
                                image_data['original_url'] = result['image_urls'][uploaded_images.index(image_data)]
                                db_manager.save_b2_image(citation_num, image_data)
                                images_uploaded += 1
                            
                            logger.info(f"Uploaded {len(uploaded_images)} images for citation {citation_num}")
                            
                        except Exception as e:
                            logger.error(f"Failed to upload images for citation {citation_num}: {e}")
                            logger.error(f"Traceback: {traceback.format_exc()}")
                    
                    # Update last successful citation only for AA range, not NC
                    if aa_range[0] <= citation_num <= aa_range[1] and citation_num > last_citation:
                        logger.debug(f"Updating last successful citation (AA) to {citation_num}")
                        db_manager.update_last_successful_citation(citation_num)
                        last_citation = citation_num
                    
                    logger.info(f"✓ Found and saved citation {citation_num}")
                else:
                    logger.debug(f"No results for citation {citation_num}")
                    
            except Exception as e:
                error_msg = f"Error processing citation {citation_num}: {str(e)}"
                logger.error(error_msg)
                logger.error(f"Traceback: {traceback.format_exc()}")
                errors.append(error_msg)
            
            # Small delay between requests to be respectful
            time.sleep(1)
            
    except Exception as e:
        error_msg = f"Critical error in scraper job: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        errors.append(error_msg)
    
    finally:
        logger.info("Scraper job finishing up...")
        # Send email notification
        if successful_citations or errors:
            try:
                logger.info("Sending email notification...")
                email_notifier.send_notification(successful_citations, total_processed, errors, images_uploaded)
                logger.info("✓ Email notification sent")
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
        
        skipped_count = len(existing_citations)
        logger.info(f"Scraper job completed. Processed: {total_processed}, Found: {len(successful_citations)}, Skipped (existing): {skipped_count}, Images uploaded: {images_uploaded}, Errors: {len(errors)}")


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("PARKING CITATION SCRAPER - GITHUB ACTIONS")
    logger.info("=" * 50)
    ongoing_scraper_job()
    logger.info("=" * 50)
    logger.info("✓ SCRAPER RUN COMPLETE")
    logger.info("=" * 50)

