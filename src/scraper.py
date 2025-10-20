import requests
from bs4 import BeautifulSoup
import re
import logging
from datetime import datetime
from typing import Optional, Dict, List
import time
import random


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

    def get_verification_token(self) -> Optional[str]:
        try:
            response = self.session.get('https://annarbor.citationportal.com/')
            soup = BeautifulSoup(response.text, 'html.parser')
            token_input = soup.find('input', {'name': '__RequestVerificationToken'})
            return token_input['value'] if token_input else None
        except Exception as e:
            logging.error(f"Error getting verification token: {e}")
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
            # politeness: small random delay per request
            time.sleep(random.uniform(0.4, 1.1))

            response = self.session.post(
                'https://annarbor.citationportal.com/Citation/Search',
                data=search_data,
                timeout=30
            )
            base = self.parse_search_results(response.text, citation_number)
            if base and base.get('more_info_url'):
                details = self.fetch_details_page(base['more_info_url'])
                if details:
                    base.update(details)
            return base
        except Exception as e:
            logging.error(f"Error searching citation {citation_number}: {e}")
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
                return {
                    'citation_number': citation_number,
                    'location': cells[1].get_text(strip=True),
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

    def parse_date(self, date_str: str) -> Optional[datetime]:
        try:
            date_str = re.sub(r'<br\s*/?>', ' ', date_str).strip()
            return datetime.strptime(date_str, '%m/%d/%Y %I:%M %p')
        except Exception:
            return None

    def fetch_details_page(self, url: str) -> Optional[Dict]:
        try:
            time.sleep(random.uniform(0.4, 1.1))
            resp = self.session.get(url, timeout=30)
            if resp.status_code != 200:
                return None
            return self.parse_details_page(resp.text)
        except Exception as e:
            logging.error(f"Error fetching details page {url}: {e}")
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
                if info_key == 'amount_due':
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

        return info


