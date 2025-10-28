import requests
import logging
from typing import Optional, Tuple
import time

logger = logging.getLogger(__name__)


class Geocoder:
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.delay = 2.0  # Be more respectful to the API (2 seconds between requests)
        self.headers = {
            'User-Agent': 'Ann Arbor Parking Citations/1.0 (Educational Research - annarbor.gov citation portal)',
            'Accept': 'application/json'
        }
        
    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Geocode an address and return (latitude, longitude) tuple.
        Tries multiple variations if the first attempt fails.
        
        Args:
            address: Address string to geocode
            
        Returns:
            Tuple of (latitude, longitude) or None if geocoding fails
        """
        if not address:
            return None
        
        # Prepare base address
        if 'Ann Arbor' not in address:
            base_address = f"{address}, Ann Arbor, MI"
        else:
            base_address = address
        
        # Try multiple variations
        variations = [
            base_address,  # Original
            base_address.replace(' St ', ' Ave '),  # Try Ave instead of St
            base_address.replace(' St ', ' St'),  # Try without space before St
            base_address.replace('St ', 'Ave '),  # Try Ave instead of St
        ]
        
        for search_address in variations:
            try:
                # Add delay to respect rate limits
                time.sleep(self.delay)
                
                params = {
                    'q': search_address,
                    'format': 'json',
                    'limit': 1,
                    'addressdetails': 0
                }
                
                response = requests.get(self.base_url, params=params, headers=self.headers, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if data and len(data) > 0:
                    lat = float(data[0]['lat'])
                    lon = float(data[0]['lon'])
                    logger.info(f"Geocoded '{address}' to ({lat}, {lon}) using variation: {search_address}")
                    return (lat, lon)
                
            except Exception as e:
                logger.debug(f"Error geocoding variation '{search_address}': {e}")
                continue
        
        logger.warning(f"No geocoding results for '{address}' after trying {len(variations)} variations")
        return None
    
    def geocode_and_update_citation(self, db_manager, citation_number: int, address: str) -> bool:
        """
        Geocode an address and update the citation in the database.
        
        Args:
            db_manager: DatabaseManager instance
            citation_number: Citation number to update
            address: Address to geocode
            
        Returns:
            True if successful, False otherwise
        """
        coords = self.geocode_address(address)
        
        if not coords:
            return False
            
        try:
            lat, lon = coords
            db_manager.supabase.table('citations').update({
                'latitude': lat,
                'longitude': lon,
                'geocoded_at': 'now()'
            }).eq('citation_number', citation_number).execute()
            
            logger.info(f"Updated citation {citation_number} with coordinates ({lat}, {lon})")
            return True
            
        except Exception as e:
            logger.error(f"Error updating citation {citation_number} with coordinates: {e}")
            return False

