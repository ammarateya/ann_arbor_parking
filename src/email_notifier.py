import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
import os
from datetime import datetime
import pytz
import base64
from email.message import EmailMessage

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
except Exception:
    Credentials = None
    build = None


class EmailNotifier:
    def __init__(self):
        self.smtp_host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('EMAIL_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.notification_email = os.getenv('NOTIFICATION_EMAIL', 'ammarat@umich.edu')
        # Gmail API fallback config
        self.gmail_token_file = os.getenv('GMAIL_TOKEN_FILE', 'gmail_token.json')
        self.gmail_from_email = os.getenv('FROM_EMAIL', self.email_user or 'no-reply@example.com')
        
    def send_notification(self, successful_citations: List[Dict], total_processed: int, errors: List[str] = None, images_uploaded: int = 0):
        """Send email notification about scraper run results"""
        if not self.email_user or not self.email_password:
            logging.warning("Email credentials not configured, skipping notification")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = self.notification_email
            # Format time in Detroit timezone with human-readable format
            detroit_tz = pytz.timezone('America/Detroit')
            detroit_time = datetime.now(detroit_tz)
            # Format as human-readable time (e.g., "Jan 15, 2024 at 3:45 PM")
            subject_time_str = detroit_time.strftime('%b %d, %Y at %I:%M %p')
            msg['Subject'] = f"Parking Citation Scraper Report - {subject_time_str}"
            
            # Create email body
            body = self._create_email_body(successful_citations, total_processed, errors, images_uploaded)
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
                
            logging.info(f"Notification email sent to {self.notification_email}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send notification email: {e}")
            return False
    
    def _create_email_body(self, successful_citations: List[Dict], total_processed: int, errors: List[str] = None, images_uploaded: int = 0) -> str:
        """Create HTML email body with scraper results"""
        # Format time in Detroit timezone
        detroit_tz = pytz.timezone('America/Detroit')
        detroit_time = datetime.now(detroit_tz)
        # Format as human-readable time (e.g., "Jan 15, 2024 at 3:45 PM")
        run_time_str = detroit_time.strftime('%B %d, %Y at %I:%M %p')
        
        html = f"""
        <html>
        <body>
            <h2>Parking Citation Scraper Report</h2>
            <p><strong>Run Time:</strong> {run_time_str}</p>
            <p><strong>Total Citations Processed:</strong> {total_processed}</p>
            <p><strong>Successful Citations Found:</strong> {len(successful_citations)}</p>
            <p><strong>Images Uploaded to B2:</strong> {images_uploaded}</p>
        """
        
        if successful_citations:
            html += """
            <h3>Successfully Found Citations:</h3>
            <table border="1" style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f2f2f2;">
                    <th>Citation Number</th>
                    <th>Location</th>
                    <th>Plate</th>
                    <th>Issue Date</th>
                    <th>Amount Due</th>
                    <th>More Info URL</th>
                </tr>
            """
            
            for citation in successful_citations:
                html += f"""
                <tr>
                    <td>{citation.get('citation_number', 'N/A')}</td>
                    <td>{citation.get('location', 'N/A')}</td>
                    <td>{citation.get('plate_state', 'N/A')} {citation.get('plate_number', 'N/A')}</td>
                    <td>{citation.get('issue_date', 'N/A')}</td>
                    <td>${citation.get('amount_due', 'N/A')}</td>
                    <td><a href="{citation.get('more_info_url', '#')}">View Details</a></td>
                </tr>
                """
            
            html += "</table>"
        
        if errors:
            html += f"""
            <h3>Errors Encountered:</h3>
            <ul>
            """
            for error in errors:
                html += f"<li>{error}</li>"
            html += "</ul>"
        
        html += """
            <p><em>This is an automated report from the Parking Citation Scraper.</em></p>
        </body>
        </html>
        """
        
        return html

    def send_ticket_alert(self, to_email: str, citation: Dict, context: Dict | None = None) -> bool:
        """Send a single ticket alert to a subscriber.

        context may include:
          - type: 'plate' | 'location'
          - plate_state, plate_number (for type='plate')
          - center_lat, center_lon, radius_m (for type='location')
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.gmail_from_email if not (self.email_user and self.email_password) else self.email_user
            msg['To'] = to_email
            subject_citation = citation.get('citation_number', 'New Citation')
            subject_prefix = "Parking Ticket Alert"
            if context and context.get('type') == 'plate':
                subject_prefix = "Plate Alert"
            elif context and context.get('type') == 'location':
                subject_prefix = "Location Alert"
            msg['Subject'] = f"{subject_prefix}: Citation {subject_citation}"

            details_url = citation.get('more_info_url', '#')
            amount_due = citation.get('amount_due')
            amount_str = f"${amount_due}" if amount_due is not None else "Unknown"
            plate = f"{citation.get('plate_state','')} {citation.get('plate_number','')}".strip()
            issue_date = citation.get('issue_date', 'Unknown')
            location = citation.get('location', 'Unknown')

            header_line = "Your vehicle may have received a parking ticket"
            if context and context.get('type') == 'plate':
                header_line = f"You subscribed for plate {plate}. We just found a matching ticket."
            elif context and context.get('type') == 'location':
                clat = context.get('center_lat')
                clon = context.get('center_lon')
                rad = context.get('radius_m')
                header_line = f"You subscribed for a {rad} m radius around ({clat}, {clon}). A citation appeared in that area."

            body = f"""
            <html>
            <body>
                <h2>{header_line}</h2>
                <ul>
                    <li><strong>Plate</strong>: {plate}</li>
                    <li><strong>Citation</strong>: {subject_citation}</li>
                    <li><strong>Issued</strong>: {issue_date}</li>
                    <li><strong>Amount Due</strong>: {amount_str}</li>
                    <li><strong>Location</strong>: {location}</li>
                </ul>
                <p><a href="{details_url}">View details</a></p>
                <p style="color:#666">You're receiving this because you subscribed on the ticket map.</p>
            </body>
            </html>
            """
            msg.attach(MIMEText(body, 'html'))

            # Prefer SMTP if configured
            if self.email_user and self.email_password:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.email_user, self.email_password)
                    server.send_message(msg)
                logging.info(f"Sent ticket alert via SMTP to {to_email}")
                return True

            # Gmail API fallback if token and libs present
            if Credentials and build and os.path.exists(self.gmail_token_file):
                try:
                    creds = Credentials.from_authorized_user_file(
                        self.gmail_token_file,
                        scopes=['https://www.googleapis.com/auth/gmail.send']
                    )
                    service = build('gmail', 'v1', credentials=creds)
                    em = EmailMessage()
                    em['To'] = to_email
                    em['From'] = self.gmail_from_email
                    em['Subject'] = msg['Subject']
                    # reuse HTML body
                    html_body = msg.get_payload()[0].get_payload()
                    em.set_content('This email requires HTML')
                    em.add_alternative(html_body, subtype='html')

                    raw = base64.urlsafe_b64encode(em.as_bytes()).decode()
                    service.users().messages().send(userId='me', body={'raw': raw}).execute()
                    logging.info(f"Sent ticket alert via Gmail API to {to_email}")
                    return True
                except Exception as ge:
                    logging.error(f"Gmail API send failed: {ge}")
                    return False

            logging.warning("No SMTP or Gmail API configured; skipping email")
            return False
        except Exception as e:
            logging.error(f"Failed to send ticket alert to {to_email}: {e}")
            return False
