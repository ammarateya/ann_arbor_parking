import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
import os
from datetime import datetime


class EmailNotifier:
    def __init__(self):
        self.smtp_host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('EMAIL_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.notification_email = os.getenv('NOTIFICATION_EMAIL', 'ammarat@umich.edu')
        
    def send_notification(self, successful_citations: List[Dict], total_processed: int, errors: List[str] = None, images_uploaded: int = 0):
        """Send email notification about scraper run results"""
        if not self.email_user or not self.email_password:
            logging.warning("Email credentials not configured, skipping notification")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = self.notification_email
            msg['Subject'] = f"Parking Citation Scraper Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
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
        html = f"""
        <html>
        <body>
            <h2>Parking Citation Scraper Report</h2>
            <p><strong>Run Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
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

    def send_ticket_alert(self, to_email: str, citation: Dict) -> bool:
        """Send a single ticket alert to a subscriber."""
        if not self.email_user or not self.email_password:
            logging.warning("Email credentials not configured, skipping subscriber email")
            return False
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = to_email
            subject_citation = citation.get('citation_number', 'New Citation')
            msg['Subject'] = f"Parking Ticket Alert: Citation {subject_citation}"

            details_url = citation.get('more_info_url', '#')
            amount_due = citation.get('amount_due')
            amount_str = f"${amount_due}" if amount_due is not None else "Unknown"
            plate = f"{citation.get('plate_state','')} {citation.get('plate_number','')}".strip()
            issue_date = citation.get('issue_date', 'Unknown')
            location = citation.get('location', 'Unknown')

            body = f"""
            <html>
            <body>
                <h2>Your vehicle may have received a parking ticket</h2>
                <ul>
                    <li><strong>Plate</strong>: {plate}</li>
                    <li><strong>Citation</strong>: {subject_citation}</li>
                    <li><strong>Issued</strong>: {issue_date}</li>
                    <li><strong>Amount Due</strong>: {amount_str}</li>
                    <li><strong>Location</strong>: {location}</li>
                </ul>
                <p><a href="{details_url}">View details</a></p>
                <p style="color:#666">You received this because you subscribed on the ticket map.</p>
            </body>
            </html>
            """
            msg.attach(MIMEText(body, 'html'))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            logging.info(f"Sent ticket alert to {to_email}")
            return True
        except Exception as e:
            logging.error(f"Failed to send ticket alert to {to_email}: {e}")
            return False
