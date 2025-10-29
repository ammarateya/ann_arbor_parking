#!/usr/bin/env python3
"""
Naive script to send a test email via SMTP
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def send_test_email():
    """Send a simple test email"""
    # Get SMTP configuration from environment
    smtp_host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('EMAIL_PORT', '587'))
    email_user = os.getenv('EMAIL_USER')
    email_password = os.getenv('EMAIL_PASSWORD')
    recipient = 'ammarat@umich.edu'
    
    # Check if credentials are available
    if not email_user or not email_password:
        print("❌ Error: EMAIL_USER or EMAIL_PASSWORD not found in environment")
        print(f"EMAIL_USER: {'SET' if email_user else 'NOT SET'}")
        print(f"EMAIL_PASSWORD: {'SET' if email_password else 'NOT SET'}")
        return False
    
    print(f"📧 Sending test email from {email_user} to {recipient}...")
    print(f"   SMTP Server: {smtp_host}:{smtp_port}")
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = recipient
        msg['Subject'] = 'Test Email from Parking Citation API'
        
        # Email body
        body = """
        <html>
        <body>
            <h2>Test Email</h2>
            <p>This is a test email sent from the parking citation API system.</p>
            <p>If you received this, the email functionality is working correctly! ✅</p>
            <hr>
            <p><em>Sent via SMTP at {smtp_host}</em></p>
        </body>
        </html>
        """.format(smtp_host=smtp_host)
        
        msg.attach(MIMEText(body, 'html'))
        
        # Connect to SMTP server and send
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)
        
        print("✅ Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

if __name__ == '__main__':
    send_test_email()

