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
from web_server import app

# Configure verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log') if os.path.exists('/tmp') else logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from a .env file if present
load_dotenv()

# Log startup information
logger.info("=" * 50)
logger.info("PARKING CITATION SCRAPER STARTING UP")
logger.info("=" * 50)
logger.info(f"Python version: {os.sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Environment variables loaded: {bool(os.getenv('DB_HOST'))}")

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'port': os.getenv('DB_PORT', '5432'),
}

# Log database configuration (without password)
logger.info(f"Database config: host={DB_CONFIG['host']}, db={DB_CONFIG['database']}, user={DB_CONFIG['user']}, port={DB_CONFIG['port']}")
logger.info(f"Database password configured: {bool(DB_CONFIG['password'])}")

# Log storage configuration
storage_provider = os.getenv('STORAGE_PROVIDER', 'cloudflare_r2')
logger.info(f"Storage provider: {storage_provider}")
logger.info(f"R2 credentials configured: {bool(os.getenv('R2_ACCESS_KEY_ID'))}")
logger.info(f"Email configured: {bool(os.getenv('EMAIL_PASSWORD'))}")


def initial_database_build(start_citation=10516370, end_citation=10515150):
    scraper = CitationScraper()
    db_manager = DatabaseManager(DB_CONFIG)
    for citation_num in range(start_citation, end_citation - 1, -1):
        logging.info(f"Processing citation: {citation_num}")
        result = scraper.search_citation(str(citation_num))
        if result:
            db_manager.save_citation(result)
            db_manager.update_last_successful_citation(citation_num)
            logging.info(f"Saved citation {citation_num}")
        time.sleep(3)


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
        
        for citation_num in range(start_range, end_range + 1):
            try:
                logger.debug(f"Processing citation {citation_num}...")
                result = scraper.search_citation(str(citation_num))
                total_processed += 1
                
                if result:
                    logger.debug(f"Found citation {citation_num}, saving to database...")
                    db_manager.save_citation(result)
                    successful_citations.append(result)
                    
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
                                db_manager.save_b2_image(citation_num, image_data)  # Keep same method name for compatibility
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
        
        logger.info(f"Scraper job completed. Processed: {total_processed}, Found: {len(successful_citations)}, Images uploaded: {images_uploaded}, Errors: {len(errors)}")


def scrape_job():
    logger.info("Starting scrape job")
    ongoing_scraper_job()
    logger.info("Scrape job complete")


def run_scraper():
    """Run the scraper scheduler in a separate thread"""
    logger.info("Starting scraper scheduler thread...")
    
    # Schedule scraping job every 10 minutes
    schedule.every(10).minutes.do(scrape_job)
    
    logger.info("✓ Parking Citation Scraper started. Running every 10 minutes.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        logger.error(f"Scraper thread error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("MAIN APPLICATION STARTING")
    logger.info("=" * 50)
    
    try:
        # Test database connection first
        logger.info("Testing database connection...")
        db_manager = DatabaseManager(DB_CONFIG)
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                logger.info(f"✓ Database connection successful: {result}")
        
        # Test storage connection
        logger.info("Testing storage connection...")
        cloud_storage = StorageFactory.create_storage_service()
        if cloud_storage:
            logger.info(f"✓ Storage service created: {type(cloud_storage).__name__}")
            logger.info(f"✓ Storage configured: {cloud_storage.is_configured()}")
        else:
            logger.warning("⚠ Storage service not available")
        
        # Test email configuration
        logger.info("Testing email configuration...")
        email_notifier = EmailNotifier()
        logger.info(f"✓ Email notifier created")
        
        logger.info("All components initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error("Application will exit due to initialization failure")
        exit(1)
    
    try:
        # Start scraper in a separate thread
        logger.info("Starting scraper thread...")
        scraper_thread = threading.Thread(target=run_scraper, daemon=True)
        scraper_thread.start()
        logger.info("✓ Scraper thread started")
        
        # Start web server
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"Starting web server on port {port}...")
        logger.info("=" * 50)
        logger.info("APPLICATION STARTUP COMPLETE - READY TO SERVE")
        logger.info("=" * 50)
        
        app.run(host='0.0.0.0', port=port)
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        exit(1)
