#!/usr/bin/env python3
"""
Parking Citation Scraper - Standalone Script
Runs only the scraper without web server. Used by GitHub Actions cron jobs.
"""

import schedule
import time
import logging
import os
import threading
import traceback
from dotenv import load_dotenv
from db_manager import DatabaseManager
from scraper import CitationScraper
from email_notifier import EmailNotifier
from storage_factory import StorageFactory
from geocoder import Geocoder

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
    """Run scraper job with ±100 range from last successful citation"""
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
        
        # Use ±100 range as requested
        start_range = last_citation - 100
        end_range = last_citation + 100
        
        logger.info(f"Processing citations from {start_range} to {end_range} (last successful: {last_citation})")
        
        # Get all existing citation numbers in this range to avoid duplicate processing
        logger.info("Fetching existing citations in range to optimize processing...")
        existing_citations = db_manager.get_existing_citation_numbers_in_range(start_range, end_range)
        logger.info(f"Found {len(existing_citations)} existing citations in range. Will skip these.")
        
        for citation_num in range(start_range, end_range + 1):
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
                    
                    # Geocode address for map display
                    if result.get('location'):
                        try:
                            logger.debug(f"Geocoding address for citation {citation_num}...")
                            geocoder.geocode_and_update_citation(db_manager, citation_num, result['location'])
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
                    
                    # Update last successful citation if this is higher than current
                    if citation_num > last_citation:
                        logger.debug(f"Updating last successful citation to {citation_num}")
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

