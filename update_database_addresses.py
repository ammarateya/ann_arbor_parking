#!/usr/bin/env python3
"""
Database Update Script for OCR Addresses

This script updates the Supabase database with clean addresses extracted from OCR.
It processes all citations that have images and updates their location field.
"""

import os
import sys
import logging
import json
from typing import List, Dict, Optional
from datetime import datetime

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseAddressUpdater:
    def __init__(self):
        """Initialize the database updater"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        logger.info("✓ Supabase client initialized")
    
    def get_all_citations_with_images(self) -> List[Dict]:
        """Get all citations that have images stored"""
        try:
            # Get all citations with images (no limit)
            response = self.supabase.from_('citations').select('*').not_.is_('image_urls', 'null').execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error getting citations with images: {e}")
            return []
    
    def update_citation_address(self, citation_number: int, new_address: str) -> bool:
        """Update a single citation's address"""
        try:
            response = self.supabase.table('citations').update({
                'location': new_address,
                'updated_at': datetime.now().isoformat()
            }).eq('citation_number', citation_number).execute()
            
            if response.data:
                logger.info(f"✓ Updated citation {citation_number}: {new_address}")
                return True
            else:
                logger.error(f"✗ Failed to update citation {citation_number}")
                return False
        except Exception as e:
            logger.error(f"Error updating citation {citation_number}: {e}")
            return False
    
    def load_ocr_results(self, results_file: str) -> Dict[int, str]:
        """Load OCR results from JSON file"""
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)
            
            # Create mapping of citation_number -> extracted_address
            address_map = {}
            for result in results:
                if result['status'] == 'success' and result['extracted_address']:
                    citation_number = result['citation_number']
                    address_map[citation_number] = result['extracted_address']
            
            logger.info(f"Loaded {len(address_map)} successful OCR results from {results_file}")
            return address_map
        except Exception as e:
            logger.error(f"Error loading OCR results: {e}")
            return {}
    
    def update_database_from_ocr_results(self, results_file: str, dry_run: bool = True):
        """Update database with OCR results"""
        logger.info(f"Starting database update from OCR results...")
        logger.info(f"Dry run mode: {dry_run}")
        
        # Load OCR results
        address_map = self.load_ocr_results(results_file)
        if not address_map:
            logger.error("No OCR results to process")
            return
        
        # Get all citations with images
        citations = self.get_all_citations_with_images()
        logger.info(f"Found {len(citations)} citations with images")
        
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for citation in citations:
            citation_number = citation['citation_number']
            current_location = citation.get('location', '')
            
            if citation_number in address_map:
                new_address = address_map[citation_number]
                
                if current_location != new_address:
                    logger.info(f"Citation {citation_number}: '{current_location}' -> '{new_address}'")
                    
                    if not dry_run:
                        success = self.update_citation_address(citation_number, new_address)
                        if success:
                            updated_count += 1
                        else:
                            error_count += 1
                    else:
                        updated_count += 1
                else:
                    logger.info(f"Citation {citation_number}: No change needed")
                    skipped_count += 1
            else:
                logger.warning(f"Citation {citation_number}: No OCR result available")
                skipped_count += 1
        
        logger.info("=" * 60)
        logger.info("DATABASE UPDATE SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total citations processed: {len(citations)}")
        logger.info(f"Citations to update: {updated_count}")
        logger.info(f"Citations skipped: {skipped_count}")
        logger.info(f"Errors: {error_count}")
        
        if dry_run:
            logger.info("DRY RUN COMPLETE - No changes made to database")
            logger.info("Run with dry_run=False to apply changes")
        else:
            logger.info("DATABASE UPDATE COMPLETE")


def main():
    """Main function"""
    try:
        updater = DatabaseAddressUpdater()
        
        # Find the most recent OCR results file
        import glob
        ocr_files = glob.glob("ocr_results_*.json")
        if not ocr_files:
            logger.error("No OCR results files found. Run ocr_address_extractor.py first.")
            return
        
        # Use the most recent file
        latest_file = max(ocr_files)
        logger.info(f"Using OCR results file: {latest_file}")
        
        # Apply changes directly
        logger.info("Applying OCR address updates to database...")
        updater.update_database_from_ocr_results(latest_file, dry_run=False)
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    main()
