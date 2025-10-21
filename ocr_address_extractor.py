#!/usr/bin/env python3
"""
OCR Address Extraction Script

This script processes existing citations in the Supabase database and extracts
clean street addresses from receipt images using OCR. It focuses on the last
image in the citation_images array (the receipt image).
"""

import os
import sys
import logging
import requests
import json
from typing import List, Dict, Optional, Tuple
from PIL import Image
import io
import re
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

class OCRAddressExtractor:
    def __init__(self):
        """Initialize the OCR address extractor"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        logger.info("✓ Supabase client initialized")
        
        # Try to import OCR libraries
        self.tesseract_available = False
        try:
            import pytesseract
            self.tesseract_available = True
            logger.info("✓ Tesseract OCR available")
        except ImportError:
            logger.warning("⚠ Tesseract OCR not available - install pytesseract for OCR functionality")
    
    def get_citations_with_images(self, limit: int = 10) -> List[Dict]:
        """Get citations that have images stored"""
        try:
            response = self.supabase.from_('citations').select('*').not_.is_('image_urls', 'null').limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error getting citations with images: {e}")
            return []
    
    def get_all_citations_with_images(self) -> List[Dict]:
        """Get ALL citations that have images stored (no limit)"""
        try:
            response = self.supabase.from_('citations').select('*').not_.is_('image_urls', 'null').execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error getting all citations with images: {e}")
            return []
    
    def get_receipt_image_url(self, citation: Dict) -> Optional[str]:
        """Get the receipt image URL (last image in the array)"""
        try:
            image_urls = citation.get('image_urls', [])
            if not image_urls or not isinstance(image_urls, list):
                return None
            
            # Get the last image (receipt image)
            receipt_url = image_urls[-1] if image_urls else None
            return receipt_url
        except Exception as e:
            logger.error(f"Error getting receipt image URL: {e}")
            return None
    
    def download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Error downloading image from {url}: {e}")
            return None
    
    def preprocess_image(self, image_data: bytes) -> Image.Image:
        """Preprocess image for better OCR results"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too small (OCR works better on larger images)
            if image.width < 800 or image.height < 600:
                # Calculate new size maintaining aspect ratio
                ratio = max(800 / image.width, 600 / image.height)
                new_width = int(image.width * ratio)
                new_height = int(image.height * ratio)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            return image
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            raise
    
    def extract_text_with_ocr(self, image: Image.Image) -> str:
        """Extract text from image using OCR"""
        if not self.tesseract_available:
            logger.warning("Tesseract not available, skipping OCR")
            return ""
        
        try:
            import pytesseract
            
            # Use Tesseract to extract text
            # Configure for better address recognition
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,- '
            text = pytesseract.image_to_string(image, config=custom_config)
            
            return text.strip()
        except Exception as e:
            logger.error(f"Error during OCR: {e}")
            return ""
    
    def extract_address_from_text(self, text: str) -> Optional[str]:
        """Extract street address from OCR text using pattern matching"""
        if not text:
            return None
        
        # Look for LOCATION pattern first (most common in these citations)
        location_pattern = r'LOCATION(\d+)([A-Za-z]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Ct|Court|Pl|Place|Way|Cir|Circle))'
        location_match = re.search(location_pattern, text, re.IGNORECASE)
        if location_match:
            number = location_match.group(1)
            street = location_match.group(2)
            # Add spaces before capital letters for better readability
            formatted_street = self.add_spaces_before_capitals(street)
            return f"{number} {formatted_street}"
        
        # Common address patterns (updated for OCR spacing issues)
        address_patterns = [
            # Pattern 1: "1300SUniversityAve" (no spaces)
            r'\b(\d+)([A-Za-z]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Ct|Court|Pl|Place|Way|Cir|Circle))\b',
            
            # Pattern 2: "123 N Main St" (with direction)
            r'\b(\d+)\s+[NSEW]\s+[A-Za-z\s]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Ct|Court|Pl|Place|Way|Cir|Circle)\b',
            
            # Pattern 3: "123 North Main St" (with full direction)
            r'\b(\d+)\s+(?:North|South|East|West)\s+[A-Za-z\s]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Ct|Court|Pl|Place|Way|Cir|Circle)\b',
            
            # Pattern 4: More flexible - any number followed by street name
            r'\b(\d+)\s+[A-Za-z][A-Za-z\s]{2,30}(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Ct|Court|Pl|Place|Way|Cir|Circle)\b'
        ]
        
        # Try each pattern
        for pattern in address_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Return the first match, cleaned up
                if isinstance(matches[0], tuple):
                    number, street = matches[0]
                    # Add spaces before capital letters for better readability
                    formatted_street = self.add_spaces_before_capitals(street)
                    address = f"{number} {formatted_street}".strip()
                else:
                    address = matches[0].strip()
                # Clean up extra whitespace
                address = re.sub(r'\s+', ' ', address)
                return address
        
        return None
    
    def add_spaces_before_capitals(self, text: str) -> str:
        """Add spaces before capital letters for better readability"""
        if not text:
            return text
        
        # Special handling for directional indicators followed by street names
        # Pattern: "SUniversity" -> "S University", "EDivision" -> "E Division"
        directional_pattern = r'^([NSEW])([A-Z][a-z]+.*)$'
        match = re.match(directional_pattern, text)
        if match:
            direction = match.group(1)
            street_part = match.group(2)
            # Add spaces before capitals in the street part
            formatted_street = self.add_spaces_before_capitals(street_part)
            return f"{direction} {formatted_street}"
        
        # Regular case: Add space before capital letters (except the first character)
        result = text[0]  # Keep first character as is
        for i in range(1, len(text)):
            char = text[i]
            if char.isupper() and text[i-1].islower():
                result += ' ' + char
            else:
                result += char
        
        return result
    
    def process_citation(self, citation: Dict) -> Dict:
        """Process a single citation to extract clean address"""
        citation_number = citation.get('citation_number')
        current_location = citation.get('location', '')
        
        logger.info(f"Processing citation {citation_number}")
        logger.info(f"Current location: {current_location}")
        
        # Get receipt image URL
        receipt_url = self.get_receipt_image_url(citation)
        if not receipt_url:
            logger.warning(f"No receipt image URL for citation {citation_number}")
            return {
                'citation_number': citation_number,
                'original_location': current_location,
                'extracted_address': None,
                'ocr_text': '',
                'status': 'no_image'
            }
        
        logger.info(f"Receipt image URL: {receipt_url}")
        
        # Download image
        image_data = self.download_image(receipt_url)
        if not image_data:
            logger.warning(f"Failed to download image for citation {citation_number}")
            return {
                'citation_number': citation_number,
                'original_location': current_location,
                'extracted_address': None,
                'ocr_text': '',
                'status': 'download_failed'
            }
        
        try:
            # Preprocess image
            image = self.preprocess_image(image_data)
            logger.info(f"Image preprocessed: {image.size}")
            
            # Extract text with OCR
            ocr_text = self.extract_text_with_ocr(image)
            logger.info(f"OCR text length: {len(ocr_text)}")
            
            # Extract address from text
            extracted_address = self.extract_address_from_text(ocr_text)
            
            status = 'success' if extracted_address else 'no_address_found'
            
            result = {
                'citation_number': citation_number,
                'original_location': current_location,
                'extracted_address': extracted_address,
                'ocr_text': ocr_text[:500],  # Truncate for display
                'status': status
            }
            
            logger.info(f"Extracted address: {extracted_address}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing citation {citation_number}: {e}")
            return {
                'citation_number': citation_number,
                'original_location': current_location,
                'extracted_address': None,
                'ocr_text': '',
                'status': 'processing_error',
                'error': str(e)
            }
    
    def run_ocr_analysis(self, limit: int = None) -> List[Dict]:
        """Run OCR analysis on citations"""
        if limit:
            logger.info(f"Starting OCR analysis on up to {limit} citations...")
        else:
            logger.info(f"Starting OCR analysis on ALL citations with images...")
        
        # Get citations with images
        if limit:
            citations = self.get_citations_with_images(limit)
        else:
            citations = self.get_all_citations_with_images()
        logger.info(f"Found {len(citations)} citations with images")
        
        results = []
        for citation in citations:
            result = self.process_citation(citation)
            results.append(result)
            logger.info(f"Processed citation {result['citation_number']}: {result['status']}")
        
        return results
    
    def display_results(self, results: List[Dict]):
        """Display OCR results in a readable format"""
        print("\n" + "="*80)
        print("OCR ADDRESS EXTRACTION RESULTS")
        print("="*80)
        
        success_count = 0
        for result in results:
            print(f"\nCitation #{result['citation_number']}")
            print(f"Status: {result['status']}")
            print(f"Original: {result['original_location']}")
            print(f"Extracted: {result['extracted_address'] or 'None'}")
            
            if result['ocr_text']:
                print(f"OCR Text (first 200 chars): {result['ocr_text'][:200]}...")
            
            if result['status'] == 'success':
                success_count += 1
        
        print(f"\n" + "="*80)
        print(f"SUMMARY: {success_count}/{len(results)} citations had addresses extracted")
        print("="*80)


def main():
    """Main function"""
    try:
        extractor = OCRAddressExtractor()
        
        # Run OCR analysis on ALL citations (no limit)
        results = extractor.run_ocr_analysis(limit=None)
        
        # Display results
        extractor.display_results(results)
        
        # Save results to file for review
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"ocr_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to: {results_file}")
        print("\nReview the results above. If you approve, run the update script to write to database.")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    main()
