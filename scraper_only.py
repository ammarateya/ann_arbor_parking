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
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from db_manager import DatabaseManager
from scraper import CitationScraper
from email_notifier import EmailNotifier
from storage_factory import StorageFactory
from geocoder import Geocoder
from nonstandard import resolve_alias
from webhook_notifier import WebhookNotifier

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
    """Run scraper job across multiple ranges with configurable ± range.

    Ranges:
      - AA (Ann Arbor): [10,000,000, 20,000,000) - auto-updates from DB max (legacy large window)
      - NC (North Campus): [2,080,000, 3,000,000) - auto-updates from DB max
      - Third: [1,000,000, 2,000,000) - auto-updates from DB max
      - Fourth: [2,000,000, 2,080,000) - auto-updates from DB max
      - Fifth: Center 1,027,117 - uses 1.02M-1.03M window to find max, scrapes 50 in either direction
      - Sixth: Center 1,048,162 - uses 1.04M-1.05M window to find max, scrapes 50 in either direction
      - Seventh: Center 1,072,744 - uses 1.07M-1.08M window to find max, scrapes 50 in either direction
      - Eighth: Center 1,123,252 - uses 1.12M-1.13M window to find max, scrapes 50 in either direction
      - Ninth: Center 10,913,791 - uses 10.91M-10.92M window to find max, scrapes 50 in either direction

    Range size:
      - SCRAPE_RANGE_SIZE env var (defaults to 50 for all ranges)
      - All ranges scrape 50 citations in either direction (100 total per range)
      - New ranges use 10k windows (1.02M-1.03M, 1.04M-1.05M, 10.91M-10.92M, etc.) to find max citation for center updates
    
    Note: Range 1039342 (ends at 1039399) should be run locally once up to 1039400.
          This is a one-time historical backfill, not added as a recurring range.
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

        try:
            last_citation_seen_at = db_manager.get_last_citation_seen_at()
            last_no_citation_email_sent_at = db_manager.get_last_no_citation_email_sent_at()
            if last_citation_seen_at:
                logger.info(f"Last citation seen at: {last_citation_seen_at.isoformat()}")
            if last_no_citation_email_sent_at:
                logger.info(f"Last no-citation email sent at: {last_no_citation_email_sent_at.isoformat()}")
        except Exception as state_error:
            logger.warning(f"Unable to load historical scraper state timestamps: {state_error}")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return
    
    successful_citations = []
    errors = []
    total_processed = 0
    images_uploaded = 0
    skipped_existing = 0
    last_citation_seen_at = None
    last_no_citation_email_sent_at = None
    latest_citation_number = None
    latest_citation_seen_at = None
    
    # Global batch buffer for citations to be inserted
    citation_batch = []
    
    def flush_citation_batch() -> None:
        """Flush all citations in the batch to the database"""
        nonlocal citation_batch, errors
        if not citation_batch:
            return
        
        try:
            batch_result = db_manager.batch_insert_citations(citation_batch)
            if batch_result.get('failed_count', 0) > 0:
                errors.extend(batch_result.get('errors', []))
            logger.info(f"Batch inserted {batch_result.get('success_count', 0)} citations, {batch_result.get('failed_count', 0)} failed")
        except Exception as e:
            logger.error(f"Error flushing citation batch: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Add batch citations to errors
            for citation in citation_batch:
                errors.append(f"Failed to save citation {citation.get('citation_number', 'unknown')}: {e}")
        finally:
            citation_batch = []
    
    try:
        logger.info("Getting last successful citation...")
        last_citation = db_manager.get_last_successful_citation()
        if not last_citation:
            logger.error("No last successful citation found.")
            return 

        logger.info(f"Last successful citation: {last_citation}")

        # Determine dynamic bases from DB using leading-digit bands
        # NC (starts with 2,080,000+): [2,080,000, 3,000,000)
        nc_db_max = db_manager.get_max_citation_between(2_080_000, 3_000_000)
        # AA (starts with 1): [10,000,000, 20,000,000)
        aa_db_max = db_manager.get_max_citation_between(10_000_000, 20_000_000)
        # Third range (starts with 1): [1,000,000, 2,000,000)
        third_db_max = db_manager.get_max_citation_between(1_000_000, 2_000_000)
        # Fourth range (starts from 2025645): [2,000,000, 2,080,000)
        fourth_db_max = db_manager.get_max_citation_between(2_000_000, 2_080_000)
        
        # New range centers discovered from citation_hits.txt analysis
        # These are separate ranges within the [1,000,000, 2,000,000) band
        # Each range uses a 10k window (based on million boundaries) to find max citation for center updates
        # But scraping still uses the standard range_size (50) in either direction
        fifth_db_max = db_manager.get_max_citation_between(1_020_000, 1_030_000)  # 1.02M to 1.03M
        sixth_db_max = db_manager.get_max_citation_between(1_040_000, 1_050_000)  # 1.04M to 1.05M
        seventh_db_max = db_manager.get_max_citation_between(1_070_000, 1_080_000)  # 1.07M to 1.08M
        eighth_db_max = db_manager.get_max_citation_between(1_120_000, 1_130_000)  # 1.12M to 1.13M
        # Ninth range: AA range split into 10k windows (10.91M-10.92M window)
        ninth_db_max = db_manager.get_max_citation_between(10_910_000, 10_920_000)  # 10.91M to 10.92M
        
        logger.info(f"NC DB max [2,080,000..3,000,000): {nc_db_max}")
        logger.info(f"AA DB max [10,000,000..20,000,000): {aa_db_max}")
        logger.info(f"Third range DB max [1,000,000..2,000,000): {third_db_max}")
        logger.info(f"Fourth range DB max [2,000,000..2,080,000): {fourth_db_max}")
        logger.info(f"Fifth range DB max [1,020,000..1,030,000): {fifth_db_max}")
        logger.info(f"Sixth range DB max [1,040,000..1,050,000): {sixth_db_max}")
        logger.info(f"Seventh range DB max [1,070,000..1,080,000): {seventh_db_max}")
        logger.info(f"Eighth range DB max [1,120,000..1,130,000): {eighth_db_max}")
        logger.info(f"Ninth range DB max [10,910,000..10,920,000): {ninth_db_max}")

        # Configure range size from environment
        # All ranges use the same scraping range size (50 in either direction = 100 total)
        try:
            range_size = int(os.getenv('SCRAPE_RANGE_SIZE', '50'))
        except ValueError:
            range_size = 50

        # Center ranges on DB maxima directly (no env seeds)
        aa_center = aa_db_max if aa_db_max is not None else last_citation
        nc_center = nc_db_max if nc_db_max is not None else 2081673
        third_center = third_db_max if third_db_max is not None else 1123108
        fourth_center = fourth_db_max if fourth_db_max is not None else 2025645
        
        # New range centers - use discovered centers if DB max found, otherwise use fixed centers
        # The 10k window is only used to find the max; scraping uses standard range_size
        fifth_center = fifth_db_max if fifth_db_max is not None else 1_027_117
        sixth_center = sixth_db_max if sixth_db_max is not None else 1_048_162
        seventh_center = seventh_db_max if seventh_db_max is not None else 1_072_744
        eighth_center = eighth_db_max if eighth_db_max is not None else 1_123_252
        ninth_center = ninth_db_max if ninth_db_max is not None else 10_913_791

        # All ranges use the same scraping range size (50 in either direction)
        aa_range = (aa_center - range_size, aa_center + range_size)
        nc_range = (nc_center - range_size, nc_center + range_size)
        third_range = (third_center - range_size, third_center + range_size)
        fourth_range = (fourth_center - range_size, fourth_center + range_size)
        fifth_range = (fifth_center - range_size, fifth_center + range_size)
        sixth_range = (sixth_center - range_size, sixth_center + range_size)
        seventh_range = (seventh_center - range_size, seventh_center + range_size)
        eighth_range = (eighth_center - range_size, eighth_center + range_size)
        ninth_range = (ninth_center - range_size, ninth_center + range_size)
        
        ranges = [aa_range, nc_range, third_range, fourth_range, fifth_range, sixth_range, seventh_range, eighth_range, ninth_range]

        overall_start = min(start for start, _ in ranges)
        overall_end = max(end for _, end in ranges)

        logger.info(
            f"Processing nine ranges: "
            f"AA[{aa_range[0]}..{aa_range[1]}], "
            f"NC[{nc_range[0]}..{nc_range[1]}], "
            f"Third[{third_range[0]}..{third_range[1]}], "
            f"Fourth[{fourth_range[0]}..{fourth_range[1]}], "
            f"Fifth[{fifth_range[0]}..{fifth_range[1]}], "
            f"Sixth[{sixth_range[0]}..{sixth_range[1]}], "
            f"Seventh[{seventh_range[0]}..{seventh_range[1]}], "
            f"Eighth[{eighth_range[0]}..{eighth_range[1]}], "
            f"Ninth[{ninth_range[0]}..{ninth_range[1]}] "
            f"(overall {overall_start}..{overall_end})"
        )

        # Add a GitHub Actions title and initial summary
        write_github_actions_summary(
            body_lines=[
                f"AA range: {aa_range[0]}..{aa_range[1]}",
                f"NC range: {nc_range[0]}..{nc_range[1]}",
                f"Third range: {third_range[0]}..{third_range[1]}",
                f"Fourth range: {fourth_range[0]}..{fourth_range[1]}",
                f"Fifth range: {fifth_range[0]}..{fifth_range[1]}",
                f"Sixth range: {sixth_range[0]}..{sixth_range[1]}",
                f"Seventh range: {seventh_range[0]}..{seventh_range[1]}",
                f"Eighth range: {eighth_range[0]}..{eighth_range[1]}",
                f"Ninth range: {ninth_range[0]}..{ninth_range[1]}",
                f"Overall: {overall_start}..{overall_end}",
            ]
        )

        def process_range(label: str, start_range: int, end_range: int, update_last_successful: bool) -> None:
            nonlocal last_citation, total_processed, images_uploaded, skipped_existing, aa_db_max, nc_db_max, third_db_max, fourth_db_max, fifth_db_max, sixth_db_max, seventh_db_max, eighth_db_max, ninth_db_max, citation_batch, latest_citation_number, latest_citation_seen_at
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
                        logger.debug(f"Found citation {citation_num}, adding to batch...")
                        
                        # Geocode address BEFORE adding to batch so coordinates are included in the insert
                        # This fixes the issue where geocoding tried to update citations that didn't exist yet
                        if result.get('location'):
                            location_str = result['location']
                            try:
                                # 1) DB cache: reuse coords if location was already geocoded before
                                cached = db_manager.get_cached_coords_for_location(location_str)
                                if cached:
                                    lat, lon = cached
                                    result['latitude'] = lat
                                    result['longitude'] = lon
                                    result['geocoded_at'] = datetime.now(timezone.utc).isoformat()
                                    logger.debug(f"✓ Reused cached coords for {citation_num} -> ({lat}, {lon})")
                                else:
                                    # 2) Nonstandard alias mapping: coords or mapped address
                                    mapped_address, coords = resolve_alias(location_str)
                                    if coords:
                                        lat, lon = coords
                                        result['latitude'] = lat
                                        result['longitude'] = lon
                                        result['geocoded_at'] = datetime.now(timezone.utc).isoformat()
                                        logger.debug(f"✓ Applied nonstandard coords for {citation_num} -> ({lat}, {lon})")
                                    elif mapped_address:
                                        # Geocode the mapped address
                                        geocoded_coords = geocoder.geocode_address(mapped_address)
                                        if geocoded_coords:
                                            lat, lon = geocoded_coords
                                            result['latitude'] = lat
                                            result['longitude'] = lon
                                            result['geocoded_at'] = datetime.now(timezone.utc).isoformat()
                                            logger.debug(f"✓ Geocoded via nonstandard mapping for {citation_num} -> '{mapped_address}'")
                                    else:
                                        # 3) Fallback: geocode the raw location string
                                        geocoded_coords = geocoder.geocode_address(location_str)
                                        if geocoded_coords:
                                            lat, lon = geocoded_coords
                                            result['latitude'] = lat
                                            result['longitude'] = lon
                                            result['geocoded_at'] = datetime.now(timezone.utc).isoformat()
                                            logger.debug(f"✓ Geocoded citation {citation_num}")
                            except Exception as e:
                                logger.warning(f"Failed to geocode citation {citation_num}: {e}")
                        
                        # Add to batch - will be inserted all at once per range (with coordinates if geocoded)
                        citation_batch.append(result)
                        successful_citations.append(result)
                        try:
                            citation_value = int(result.get('citation_number'))
                            if latest_citation_number is None or citation_value > latest_citation_number:
                                latest_citation_number = citation_value
                        except (TypeError, ValueError):
                            pass
                        latest_citation_seen_at = datetime.now(timezone.utc)

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
                        except Exception as e:
                            logger.error(f"Failed notifying location subscribers for {citation_num}: {e}")

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

                        # Update range bases in-memory during processing (optimization for current run)
                        # All ranges auto-derive from DB at start of next run; this is just for efficiency
                        if label == "AA" and 10_000_000 <= citation_num < 20_000_000:
                            if aa_db_max is None or citation_num > aa_db_max:
                                aa_db_max = citation_num
                        elif label == "NC" and 2_080_000 <= citation_num < 3_000_000:
                            if nc_db_max is None or citation_num > nc_db_max:
                                nc_db_max = citation_num
                        elif label == "Third" and 1_000_000 <= citation_num < 2_000_000:
                            if third_db_max is None or citation_num > third_db_max:
                                third_db_max = citation_num
                        elif label == "Fourth" and 2_000_000 <= citation_num < 2_080_000:
                            if fourth_db_max is None or citation_num > fourth_db_max:
                                fourth_db_max = citation_num
                        elif label == "Fifth" and 1_020_000 <= citation_num < 1_030_000:
                            if fifth_db_max is None or citation_num > fifth_db_max:
                                fifth_db_max = citation_num
                        elif label == "Sixth" and 1_040_000 <= citation_num < 1_050_000:
                            if sixth_db_max is None or citation_num > sixth_db_max:
                                sixth_db_max = citation_num
                        elif label == "Seventh" and 1_070_000 <= citation_num < 1_080_000:
                            if seventh_db_max is None or citation_num > seventh_db_max:
                                seventh_db_max = citation_num
                        elif label == "Eighth" and 1_120_000 <= citation_num < 1_130_000:
                            if eighth_db_max is None or citation_num > eighth_db_max:
                                eighth_db_max = citation_num
                        elif label == "Ninth" and 10_910_000 <= citation_num < 10_920_000:
                            if ninth_db_max is None or citation_num > ninth_db_max:
                                ninth_db_max = citation_num

                        logger.info(f"✓ [{label}] Found citation {citation_num} (added to batch)")
                    else:
                        logger.debug(f"[{label}] No results for citation {citation_num}")

                except Exception as e:
                    error_msg = f"Error processing citation {citation_num}: {str(e)}"
                    logger.error(error_msg)
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    errors.append(error_msg)

                # Minimal delay between requests (only after we made a request)
                time.sleep(0.01)
            
            # Flush all citations collected for this range
            if citation_batch:
                logger.info(f"Flushing {len(citation_batch)} citations for {label} range...")
                flush_citation_batch()
                
                # Post-batch geocoding: geocode any citations that failed to geocode during initial pass
                # This handles cases where geocoding failed or was skipped
                logger.info(f"Post-batch geocoding for {label} range...")
                for citation in citation_batch:
                    citation_num = citation.get('citation_number')
                    location_str = citation.get('location')
                    # Only geocode if we have a location but no coordinates
                    if location_str and not citation.get('latitude') and not citation.get('longitude'):
                        try:
                            # Try cached coords first
                            cached = db_manager.get_cached_coords_for_location(location_str)
                            if cached:
                                lat, lon = cached
                                db_manager.supabase.table('citations').update({
                                    'latitude': lat,
                                    'longitude': lon,
                                    'geocoded_at': 'now()'
                                }).eq('citation_number', citation_num).execute()
                                logger.debug(f"✓ Post-batch: Reused cached coords for {citation_num}")
                                continue
                            
                            # Try nonstandard alias
                            mapped_address, coords = resolve_alias(location_str)
                            if coords:
                                lat, lon = coords
                                db_manager.supabase.table('citations').update({
                                    'latitude': lat,
                                    'longitude': lon,
                                    'geocoded_at': 'now()'
                                }).eq('citation_number', citation_num).execute()
                                logger.debug(f"✓ Post-batch: Applied nonstandard coords for {citation_num}")
                                continue
                            
                            # Geocode the address
                            if mapped_address:
                                geocoder.geocode_and_update_citation(db_manager, citation_num, mapped_address)
                            else:
                                geocoder.geocode_and_update_citation(db_manager, citation_num, location_str)
                            logger.debug(f"✓ Post-batch: Geocoded citation {citation_num}")
                        except Exception as e:
                            logger.warning(f"Post-batch geocoding failed for citation {citation_num}: {e}")

        # Explicitly run all ranges sequentially, isolating failures
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

        try:
            process_range("Third", third_range[0], third_range[1], update_last_successful=False)
        except Exception as e:
            logger.error(f"Third range processing failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

        try:
            process_range("Fourth", fourth_range[0], fourth_range[1], update_last_successful=False)
        except Exception as e:
            logger.error(f"Fourth range processing failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

        try:
            process_range("Fifth", fifth_range[0], fifth_range[1], update_last_successful=False)
        except Exception as e:
            logger.error(f"Fifth range processing failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

        try:
            process_range("Sixth", sixth_range[0], sixth_range[1], update_last_successful=False)
        except Exception as e:
            logger.error(f"Sixth range processing failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

        try:
            process_range("Seventh", seventh_range[0], seventh_range[1], update_last_successful=False)
        except Exception as e:
            logger.error(f"Seventh range processing failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

        try:
            process_range("Eighth", eighth_range[0], eighth_range[1], update_last_successful=False)
        except Exception as e:
            logger.error(f"Eighth range processing failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

        try:
            process_range("Ninth", ninth_range[0], ninth_range[1], update_last_successful=False)
        except Exception as e:
            logger.error(f"Ninth range processing failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
    except Exception as e:
        error_msg = f"Critical error in scraper job: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        errors.append(error_msg)
    
    finally:
        logger.info("Scraper job finishing up...")
        # Flush any remaining citations in batch before finishing
        if citation_batch:
            logger.info(f"Flushing final batch of {len(citation_batch)} citations...")
            try:
                flush_citation_batch()
            except Exception as e:
                logger.error(f"Error flushing final citation batch: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
        
        now_utc = datetime.now(timezone.utc)
        found_count = len(successful_citations)
        errors_count = len(errors)

        if found_count > 0:
            try:
                db_manager.record_citation_activity(
                    latest_citation_number,
                    latest_citation_seen_at or now_utc,
                )
                last_citation_seen_at = latest_citation_seen_at or now_utc
                last_no_citation_email_sent_at = None
            except Exception as e:
                logger.error(f"Failed to record citation activity: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")

        found_count = len(successful_citations)
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

