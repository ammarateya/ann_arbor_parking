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
from webhook_notifier import WebhookNotifier
from storage_factory import StorageFactory
from geocoder import Geocoder
from nonstandard import resolve_alias

# Configure logging (configurable via LOG_LEVEL)
# Default to INFO to avoid overly verbose logs
log_level_name = os.getenv('LOG_LEVEL', 'INFO').upper()
numeric_level = getattr(logging, log_level_name, logging.INFO)
logging.basicConfig(
    level=numeric_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Reduce verbosity for noisy third-party libraries
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('botocore').setLevel(logging.WARNING)
logging.getLogger('boto3').setLevel(logging.WARNING)

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

def write_github_actions_summary(title: str = "Parking Citation Scraper", body_lines: list[str] | None = None) -> None:
    """If running inside GitHub Actions, write a markdown summary and a titled notice.

    This improves visibility by adding a nice title and compact stats to the run summary.
    """
    try:
        summary_path = os.getenv('GITHUB_STEP_SUMMARY')
        if summary_path:
            with open(summary_path, 'a', encoding='utf-8') as f:
                f.write(f"\n## {title}\n\n")
                if body_lines:
                    for line in body_lines:
                        f.write(f"- {line}\n")
                f.write("\n")
        # Emit a titled notice in the logs for quick visibility
        print(f"::notice title={title}::Run started")
    except Exception:
        # Never fail the job because summary writing failed
        pass

def ongoing_scraper_job():
    """Run scraper job across two seeds with configurable ± range.

    Seeds:
      - Ann Arbor seed: AA_BASE_SEED env var (defaults to last successful citation)
      - North Campus seed: NC_BASE_SEED env var (defaults to 2081673)

    Range size:
      - SCRAPE_RANGE_SIZE env var (defaults to 50)
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
        webhook_notifier = WebhookNotifier()
        logger.info("✓ WebhookNotifier initialized")
        
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
    skipped_existing = 0
    
    try:
        logger.info("Getting last successful citation...")
        last_citation = db_manager.get_last_successful_citation()
        if not last_citation:
            logger.error("No last successful citation found.")
            return 

        logger.info(f"Last successful citation: {last_citation}")

        # Determine dynamic bases from DB with thresholds
        aa_db_max = db_manager.get_max_citation_below(2_000_000)
        nc_db_max = db_manager.get_max_citation_at_or_above(2_000_000)
        logger.info(f"AA DB max <2,000,000: {aa_db_max}")
        logger.info(f"NC DB max ≥2,000,000: {nc_db_max}")

        # Configure seeds and range size from environment
        try:
            aa_seed_env = os.getenv('AA_BASE_SEED')
            aa_seed = int(aa_seed_env) if aa_seed_env else (aa_db_max if aa_db_max is not None else last_citation)
        except ValueError:
            aa_seed = aa_db_max if aa_db_max is not None else last_citation
        try:
            nc_seed_env = os.getenv('NC_BASE_SEED')
            nc_seed = int(nc_seed_env) if nc_seed_env else (nc_db_max if nc_db_max is not None else 2081673)
        except ValueError:
            nc_seed = nc_db_max if nc_db_max is not None else 2081673
        try:
            range_size = int(os.getenv('SCRAPE_RANGE_SIZE', '50'))
        except ValueError:
            range_size = 50

        aa_range = (aa_seed - range_size, aa_seed + range_size)
        nc_range = (nc_seed - range_size, nc_seed + range_size)
        ranges = [aa_range, nc_range]

        overall_start = min(start for start, _ in ranges)
        overall_end = max(end for _, end in ranges)

        logger.info(
            f"Processing dual ranges: AA[{aa_range[0]}..{aa_range[1]}], NC[{nc_range[0]}..{nc_range[1]}] "
            f"(overall {overall_start}..{overall_end})"
        )

        # Add a GitHub Actions title and initial summary
        write_github_actions_summary(
            body_lines=[
                f"AA range: {aa_range[0]}..{aa_range[1]}",
                f"NC range: {nc_range[0]}..{nc_range[1]}",
                f"Overall: {overall_start}..{overall_end}",
            ]
        )

        def process_range(label: str, start_range: int, end_range: int, update_last_successful: bool) -> None:
            nonlocal last_citation, total_processed, images_uploaded, skipped_existing, aa_db_max
            logger.info(f"Fetching existing citations for {label} range {start_range}-{end_range}...")
            existing_citations = db_manager.get_existing_citation_numbers_in_range(start_range, end_range)
            logger.info(f"Found {len(existing_citations)} existing citations in {label} range. Will skip these.")
            if existing_citations:
                # Log a small sample to confirm values are as expected
                sample = sorted(list(existing_citations))[:10]
                logger.debug(f"Sample existing citations in {label}: {sample}")

            total_in_range = (end_range - start_range) + 1
            for idx, citation_num in enumerate(range(start_range, end_range + 1), start=1):
                # Skip if citation already exists in database
                if citation_num in existing_citations:
                    logger.debug(f"Skipping citation {citation_num} - already exists in database")
                    skipped_existing += 1
                    # No network request made here, so do not sleep
                    if idx % 25 == 0:
                        logger.info(f"[{label}] Progress: {idx}/{total_in_range} in range; skipped so far: {skipped_existing}")
                    continue

                try:
                    logger.debug(f"Processing citation {citation_num}...")
                    result = scraper.search_citation(str(citation_num))
                    total_processed += 1

                    if result:
                        logger.debug(f"Found citation {citation_num}, saving to database...")
                        db_manager.save_citation(result)
                        successful_citations.append(result)

                        # Notify subscribers for matching plate
                        try:
                            subs = db_manager.find_active_subscriptions_for_plate(
                                result.get('plate_state', ''),
                                result.get('plate_number', '')
                            )
                            if subs:
                                logger.info(f"Found {len(subs)} subscriber(s) for {result.get('plate_state')} {result.get('plate_number')}")
                            for sub in subs:
                                if sub.get('email'):
                                    email_notifier.send_ticket_alert(
                                        sub['email'],
                                        result,
                                        context={
                                            'type': 'plate',
                                            'plate_state': result.get('plate_state'),
                                            'plate_number': result.get('plate_number'),
                                        },
                                    )
                                if sub.get('webhook_url'):
                                    webhook_notifier.send_ticket_alert(sub['webhook_url'], result)
                        except Exception as e:
                            logger.error(f"Failed notifying subscribers for {citation_num}: {e}")

                        # Notify subscribers for matching location
                        try:
                            if result.get('latitude') and result.get('longitude'):
                                lat = float(result.get('latitude'))
                                lon = float(result.get('longitude'))
                                loc_subs = db_manager.find_active_location_subscriptions_for_point(lat, lon)
                                if loc_subs:
                                    logger.info(f"Found {len(loc_subs)} location subscriber(s) for citation {citation_num}")
                                for sub in loc_subs:
                                    if sub.get('email'):
                                        email_notifier.send_ticket_alert(
                                            sub['email'],
                                            result,
                                            context={
                                                'type': 'location',
                                                'center_lat': sub.get('center_lat'),
                                                'center_lon': sub.get('center_lon'),
                                                'radius_m': sub.get('radius_m'),
                                            },
                                        )
                                    if sub.get('webhook_url'):
                                        webhook_notifier.send_ticket_alert(sub['webhook_url'], result)
                        except Exception as e:
                            logger.error(f"Failed notifying location subscribers for {citation_num}: {e}")

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
                        # TEMPORARILY COMMENTED OUT - Cloudflare image saving disabled
                        # if result.get('image_urls') and cloud_storage and cloud_storage.is_configured():
                        #     try:
                        #         logger.debug(f"Uploading images for citation {citation_num}...")
                        #         uploaded_images = cloud_storage.upload_images_for_citation(
                        #             result['image_urls'],
                        #             citation_num
                        #         )

                        #         # Save cloud storage image metadata to database
                        #         for image_data in uploaded_images:
                        #             image_data['original_url'] = result['image_urls'][uploaded_images.index(image_data)]
                        #             db_manager.save_b2_image(citation_num, image_data)
                        #             images_uploaded += 1

                        #         logger.info(f"Uploaded {len(uploaded_images)} images for citation {citation_num}")

                        #     except Exception as e:
                        #         logger.error(f"Failed to upload images for citation {citation_num}: {e}")
                        #         logger.error(f"Traceback: {traceback.format_exc()}")

                        # Update AA base only when under 2,000,000; NC base auto-derives from DB next run
                        if label == "AA" and citation_num < 2_000_000:
                            if aa_db_max is None or citation_num > aa_db_max:
                                aa_db_max = citation_num

                        logger.info(f"✓ [{label}] Found and saved citation {citation_num}")
                    else:
                        logger.debug(f"[{label}] No results for citation {citation_num}")

                except Exception as e:
                    error_msg = f"Error processing citation {citation_num}: {str(e)}"
                    logger.error(error_msg)
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    errors.append(error_msg)

                # Small delay between requests to be respectful (only after we made a request)
                time.sleep(1)

        # Explicitly run AA, then NC sequentially, isolating failures
        try:
            process_range("AA", aa_range[0], aa_range[1], update_last_successful=True)
        except Exception as e:
            logger.error(f"AA range processing failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

        try:
            process_range("NC", nc_range[0], nc_range[1], update_last_successful=False)
        except Exception as e:
            logger.error(f"NC range processing failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
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
        
        found_count = len(successful_citations)
        errors_count = len(errors)
        logger.info(f"Scraper job completed. Processed: {total_processed}, Found: {found_count}, Skipped (existing): {skipped_existing}, Images uploaded: {images_uploaded}, Errors: {errors_count}")

        # Append final stats to GitHub Actions step summary
        write_github_actions_summary(
            body_lines=[
                f"Processed: {total_processed}",
                f"Found: {found_count}",
                f"Skipped (existing): {skipped_existing}",
                f"Images uploaded: {images_uploaded}",
                f"Errors: {errors_count}",
            ]
        )


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("PARKING CITATION SCRAPER - GITHUB ACTIONS")
    logger.info("=" * 50)
    ongoing_scraper_job()
    logger.info("=" * 50)
    logger.info("✓ SCRAPER RUN COMPLETE")
    logger.info("=" * 50)

