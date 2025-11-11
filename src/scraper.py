import requests
from bs4 import BeautifulSoup
import re
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Dict, List
import time
import random
from PIL import Image
import io

logger = logging.getLogger(__name__)


class CitationScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1'
        })

    def normalize_location(self, location: str) -> str:
        """Normalize location strings - replace Tappan St with Tappan Ave"""
        if not location:
            return location
        # Replace "Tappan St" with "Tappan Ave" (case-insensitive)
        location = re.sub(r'\bTappan\s+St\b', 'Tappan Ave', location, flags=re.IGNORECASE)
        location = re.sub(r'\bTappan\s+Street\b', 'Tappan Ave', location, flags=re.IGNORECASE)
        return location

    def get_verification_token(self) -> Optional[str]:
        try:
            start = time.time()
            response = self.session.get('https://annarbor.citationportal.com/', timeout=30)
            elapsed = (time.time() - start) * 1000
            logger.debug(f"GET / (token) status={response.status_code} elapsed_ms={elapsed:.0f}")
            soup = BeautifulSoup(response.text, 'html.parser')
            token_input = soup.find('input', {'name': '__RequestVerificationToken'})
            return token_input['value'] if token_input else None
        except Exception as e:
            logger.error(f"Error getting verification token: {e}")
            return None

    def search_citation(self, citation_number: str) -> Optional[Dict]:
        token = self.get_verification_token()
        if not token:
            return None

        search_data = {
            '__RequestVerificationToken': token,
            'Type': 'NumberStrict',
            'Term': citation_number,
            'AdditionalTerm': ''
        }

        try:
            # minimal delay for politeness
            delay = random.uniform(0.01, 0.05)
            logger.debug(f"POST /Citation/Search delay_s={delay:.3f} citation={citation_number}")
            time.sleep(delay)

            start = time.time()
            response = self.session.post(
                'https://annarbor.citationportal.com/Citation/Search',
                data=search_data,
                timeout=30
            )
            elapsed = (time.time() - start) * 1000
            logger.debug(f"POST /Citation/Search status={response.status_code} elapsed_ms={elapsed:.0f} citation={citation_number}")
            base = self.parse_search_results(response.text, citation_number)
            if base and base.get('more_info_url'):
                details = self.fetch_details_page(base['more_info_url'])
                if details:
                    base.update(details)
            return base
        except Exception as e:
            logger.error(f"Error searching citation {citation_number}: {e}")
            return None

    def parse_search_results(self, html: str, citation_number: str) -> Optional[Dict]:
        soup = BeautifulSoup(html, 'html.parser')

        no_results = soup.find('div', class_='k-grid-norecords-template')
        if no_results and 'No results found' in no_results.text:
            return None

        table_rows = soup.find_all('tr', class_='k-table-row k-master-row')
        if table_rows:
            row = table_rows[0]
            cells = row.find_all('td', class_='k-table-td')

            if len(cells) >= 9:
                more_info_url = self.extract_more_info_url_from_row(row)
                location = self.normalize_location(cells[1].get_text(strip=True))
                return {
                    'citation_number': citation_number,
                    'location': location,
                    'plate_state': cells[2].get_text(strip=True),
                    'plate_number': cells[3].get_text(strip=True),
                    'vin': cells[4].get_text(strip=True),
                    'issue_date': self.parse_date(cells[5].get_text(strip=True)),
                    'due_date': self.parse_date(cells[6].get_text(strip=True)),
                    'status': cells[7].get_text(strip=True),
                    'amount_due': self.extract_amount(cells[8].get_text()),
                    'more_info_url': more_info_url,
                    'raw_html': html
                }
        return None

    def extract_amount(self, text: str) -> Optional[float]:
        match = re.search(r'\$(\d+\.?\d*)', text)
        return float(match.group(1)) if match else None

    def extract_more_info_url_from_row(self, row) -> Optional[str]:
        # Prefer the explicit More Info button cell
        more_info = row.find('a', href=True, string=re.compile(r"More Info", re.I))
        if more_info and more_info.get('href'):
            return f"https://annarbor.citationportal.com{more_info['href']}"
        # Fallback to the first cell anchor around citation number
        first_link = row.find('td').find('a', href=True) if row.find('td') else None
        if first_link and first_link.get('href'):
            return f"https://annarbor.citationportal.com{first_link['href']}"
        return None

    def parse_date(self, date_str: str) -> Optional[str]:
        try:
            date_str = re.sub(r'<br\s*/?>', ' ', date_str).strip()
            # Parse naive local time (portal shows Eastern local time)
            naive_local = datetime.strptime(date_str, '%m/%d/%Y %I:%M %p')
            # Localize to America/Detroit (handles EST/EDT automatically)
            eastern = ZoneInfo('America/Detroit')
            localized = naive_local.replace(tzinfo=eastern)
            # Convert to UTC and return ISO string (e.g., 2025-10-29T15:04:05+00:00)
            utc_time = localized.astimezone(ZoneInfo('UTC'))
            return utc_time.isoformat()
        except Exception:
            return None

    def fetch_details_page(self, url: str) -> Optional[Dict]:
        try:
            # minimal delay for politeness
            delay = random.uniform(0.01, 0.05)
            logger.debug(f"GET details delay_s={delay:.3f} url={url}")
            time.sleep(delay)
            start = time.time()
            resp = self.session.get(url, timeout=30)
            elapsed = (time.time() - start) * 1000
            logger.debug(f"GET details status={resp.status_code} elapsed_ms={elapsed:.0f} url={url}")
            if resp.status_code != 200:
                return None
            return self.parse_details_page(resp.text)
        except Exception as e:
            logger.error(f"Error fetching details page {url}: {e}")
            return None

    def parse_details_page(self, html: str) -> Optional[Dict]:
        soup = BeautifulSoup(html, 'html.parser')
        info = {}
        info_list = soup.select('.citation-information-box ul.list-unstyled > li')
        for li in info_list:
            key_el = li.find('span', class_='key')
            if not key_el:
                # Violation code block comes as <li><span class="key">Violation Code:</span><ul>...</ul></li>
                continue
            key = key_el.get_text(strip=True).rstrip(':')
            value_el = li.find('span', class_='value')
            if key.lower().startswith('violation'):
                violations: List[str] = []
                for vli in li.select('ul.value li'):
                    violations.append(vli.get_text(" ", strip=True))
                info['violations'] = violations
            elif key.lower() == 'comments':
                val = value_el.get_text(" ", strip=True) if value_el else ''
                info['comments'] = val
            elif value_el:
                info_key = key.lower().replace(' ', '_')
                text_val = value_el.get_text(" ", strip=True)
                
                # Skip 'plate' field to avoid conflicts with plate_state and plate_number
                if info_key == 'plate':
                    logging.debug(f"Skipping 'plate' field to avoid schema conflict")
                    continue
                
                # Parse date fields (issue_date, due_date) to UTC instead of storing raw string
                if info_key in ['issue_date', 'due_date', 'issued_date']:
                    parsed_date = self.parse_date(text_val)
                    if parsed_date:
                        info[info_key] = parsed_date
                    else:
                        # If parsing fails, still store the raw value
                        info[info_key] = text_val
                elif info_key == 'amount_due':
                    info[info_key] = self.extract_amount(text_val)
                else:
                    info[info_key] = text_val

        # Images
        image_urls: List[str] = []
        for a in soup.select('#imageLinks a[href]'):
            href = a.get('href')
            if href and href.startswith('/'):
                image_urls.append(f"https://annarbor.citationportal.com{href}")
        if image_urls:
            info['image_urls'] = image_urls
            
            # Extract clean address from receipt image (last image)
            try:
                clean_address = self.extract_address_from_receipt(image_urls[-1])
                if clean_address:
                    clean_address = self.normalize_location(clean_address)
                    info['location'] = clean_address
                    logger.info(f"Extracted clean address from OCR: {clean_address}")
            except Exception as e:
                logger.warning(f"Failed to extract address from receipt image: {e}")

        return info
    
    def extract_address_from_receipt(self, image_url: str) -> Optional[str]:
        """Extract clean address from receipt image using OCR"""
        try:
            # Check if pytesseract is available
            try:
                import pytesseract
            except ImportError:
                logging.debug("Tesseract not available, skipping OCR")
                return None
            
            # Download image
            response = self.session.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Preprocess image
            image = Image.open(io.BytesIO(response.content))
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Crop to LOCATION region - targeting the middle-left area of receipt
            # Based on typical receipt layout, LOCATION is in the middle portion, left side
            original_width = image.width
            original_height = image.height
            
            # Crop to approximately the middle section (20%-70% from top) and left 70% to capture long addresses
            crop_left = 0
            crop_top = int(original_height * 0.2)  # Start from 20% down
            crop_right = int(original_width * 0.7)  # End at 70% width (increased from 60% for longer streets)
            crop_bottom = int(original_height * 0.7)  # End at 70% from top
            
            # Create cropped image
            cropped_image = image.crop((crop_left, crop_top, crop_right, crop_bottom))
            
            # Resize if too small for better OCR accuracy
            if cropped_image.width < 800 or cropped_image.height < 600:
                ratio = max(800 / cropped_image.width, 600 / cropped_image.height)
                new_width = int(cropped_image.width * ratio)
                new_height = int(cropped_image.height * ratio)
                cropped_image = cropped_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Extract text with OCR on cropped region
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(cropped_image, config=custom_config)
            
            # Find the LOCATION line specifically
            location_line = None
            for line in text.split('\n'):
                if 'LOCATION' in line.upper():
                    location_line = line
                    break
            
            # Extract address from text (or just the LOCATION line if found)
            return self.parse_address_from_ocr(location_line if location_line else text)
            
        except Exception as e:
            logger.debug(f"Error extracting address from receipt: {e}")
            return None
    
    def parse_address_from_ocr(self, text: str) -> Optional[str]:
        """Parse address from OCR text"""
        if not text:
            return None
        
        # Look for LOCATION patterns - handle both "LOCATION:" and "LOCATION" formats
        location_patterns = [
            # Pattern: LOCATION: 800 S Forest Ave (with direction)
            r'LOCATION:\s*(\d+)\s*([NSEW])\s+([A-Za-z\s]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Ct|Court|Pl|Place|Way|Cir|Circle))',
            # Pattern: LOCATION: 1100 Prospect St (without direction)
            r'LOCATION:\s*(\d+)\s+([A-Za-z\s]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Ct|Court|Pl|Place|Way|Cir|Circle))',
            # Pattern without colon: LOCATION800SForestAve
            r'LOCATION(\d+)([NSEW])([A-Za-z]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Ct|Court|Pl|Place|Way|Cir|Circle))',
            # Pattern without colon and direction: LOCATION1100ProspectSt
            r'LOCATION(\d+)([A-Za-z]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Ct|Court|Pl|Place|Way|Cir|Circle))',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 3:
                    # Pattern with direction
                    number, direction, street = match.groups()
                    formatted_street = self.add_spaces_before_capitals(street.strip())
                    # Clean up the address - remove newlines and extra whitespace
                    address = f"{number} {direction} {formatted_street}"
                    address = re.sub(r'\s+', ' ', address).strip()
                    # Take only the first line (before any newline)
                    address = address.split('\n')[0].strip()
                    return address
                elif len(match.groups()) == 2:
                    # Pattern without direction
                    number, street = match.groups()
                    formatted_street = self.add_spaces_before_capitals(street.strip())
                    # Clean up the address - remove newlines and extra whitespace
                    address = f"{number} {formatted_street}"
                    address = re.sub(r'\s+', ' ', address).strip()
                    # Take only the first line (before any newline)
                    address = address.split('\n')[0].strip()
                    return address
        
        return None
    
    def add_spaces_before_capitals(self, text: str) -> str:
        """Add spaces before capital letters for better readability"""
        if not text:
            return text
        
        # Special handling for directional indicators (N, S, E, W)
        directional_pattern = r'^([NSEW])([A-Z][a-z]+.*)$'
        match = re.match(directional_pattern, text)
        if match:
            direction = match.group(1)
            street_part = match.group(2)
            formatted_street = self.add_spaces_before_capitals(street_part)
            return f"{direction} {formatted_street}"
        
        # Regular case: add space before capital letters
        result = text[0]
        for i in range(1, len(text)):
            char = text[i]
            if char.isupper() and text[i-1].islower():
                result += ' ' + char
            else:
                result += char
        
        return result


