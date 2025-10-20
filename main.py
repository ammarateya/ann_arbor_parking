import schedule
import time
import logging
import os
from dotenv import load_dotenv
from db_manager import DatabaseManager
from scraper import CitationScraper
from email_notifier import EmailNotifier


logging.basicConfig(level=logging.INFO)
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
    scraper = CitationScraper()
    db_manager = DatabaseManager(DB_CONFIG)
    email_notifier = EmailNotifier()
    
    successful_citations = []
    errors = []
    total_processed = 0
    
    try:
        last_citation = db_manager.get_last_successful_citation()
        if not last_citation:
            logger.error("No last successful citation found.")
            return
        
        # Use ±100 range as requested
        start_range = last_citation - 100
        end_range = last_citation + 100
        
        logger.info(f"Processing citations from {start_range} to {end_range} (last successful: {last_citation})")
        
        for citation_num in range(start_range, end_range + 1):
            try:
                result = scraper.search_citation(str(citation_num))
                total_processed += 1
                
                if result:
                    db_manager.save_citation(result)
                    successful_citations.append(result)
                    
                    # Update last successful citation if this is higher than current
                    if citation_num > last_citation:
                        db_manager.update_last_successful_citation(citation_num)
                        last_citation = citation_num
                    
                    logger.info(f"Found citation {citation_num}")
                else:
                    logger.debug(f"No results for citation {citation_num}")
                    
            except Exception as e:
                error_msg = f"Error processing citation {citation_num}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
            
            # Small delay between requests to be respectful
            time.sleep(1)
            
    except Exception as e:
        error_msg = f"Critical error in scraper job: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
    
    finally:
        # Send email notification
        if successful_citations or errors:
            email_notifier.send_notification(successful_citations, total_processed, errors)
        
        logger.info(f"Scraper job completed. Processed: {total_processed}, Found: {len(successful_citations)}, Errors: {len(errors)}")


def scrape_job():
    logger.info("Starting scrape job")
    ongoing_scraper_job()
    logger.info("Scrape job complete")


if __name__ == "__main__":
    # To run initial build once, uncomment below
    # initial_database_build()

    # Schedule scraping job every 10 minutes
    schedule.every(10).minutes.do(scrape_job)
    
    logger.info("Parking Citation Scraper started. Running every 10 minutes.")
    logger.info("Press Ctrl+C to stop.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Scraper stopped by user")


