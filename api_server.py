#!/usr/bin/env python3
"""
Parking Citation API - Web Server Only

This script runs only the web server API without the scraper.
The scraper runs via GitHub Actions cron jobs.
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
    """Run the web server API only"""
    try:
        logger.info("=" * 50)
        logger.info("PARKING CITATION API STARTING")
        logger.info("=" * 50)
        logger.info("Note: Scraper runs via GitHub Actions cron jobs")
        logger.info("=" * 50)
        
        # Import and run the web server
        from web_server import app
        
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"Starting API server on port {port}")
        
        app.run(host='0.0.0.0', port=port)
        
    except Exception as e:
        logger.error(f"API server failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
