#!/usr/bin/env python3
"""
Parking Citation Scraper - Cron Job Entry Point

This script runs only the scraper job without the web server.
Used for GitHub Actions cron jobs.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def main():
    """Run the scraper job"""
    try:
        logger.info("=" * 50)
        logger.info("GITHUB ACTIONS SCRAPER STARTING")
        logger.info("=" * 50)
        
        # Import and run the scraper job
        from main_combined import ongoing_scraper_job
        ongoing_scraper_job()
        
        logger.info("=" * 50)
        logger.info("GITHUB ACTIONS SCRAPER COMPLETE")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Scraper failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
