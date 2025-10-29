import logging
from typing import Dict
import requests


class WebhookNotifier:
    def __init__(self, timeout_seconds: int = 10):
        self.timeout_seconds = timeout_seconds

    def send_ticket_alert(self, webhook_url: str, citation: Dict) -> bool:
        """POST a JSON payload to a subscriber webhook URL about a new citation."""
        payload = {
            'type': 'parking_ticket_alert',
            'citation_number': citation.get('citation_number'),
            'plate_state': citation.get('plate_state'),
            'plate_number': citation.get('plate_number'),
            'issue_date': citation.get('issue_date'),
            'amount_due': citation.get('amount_due'),
            'location': citation.get('location'),
            'more_info_url': citation.get('more_info_url'),
        }
        try:
            resp = requests.post(
                webhook_url,
                json=payload,
                timeout=self.timeout_seconds,
                headers={'Content-Type': 'application/json', 'User-Agent': 'parking-scraper/notifications'}
            )
            if 200 <= resp.status_code < 300:
                logging.info(f"Webhook delivered to {webhook_url} status={resp.status_code}")
                return True
            logging.warning(f"Webhook to {webhook_url} failed status={resp.status_code} body={resp.text[:200]}")
            return False
        except Exception as e:
            logging.error(f"Failed to deliver webhook to {webhook_url}: {e}")
            return False


