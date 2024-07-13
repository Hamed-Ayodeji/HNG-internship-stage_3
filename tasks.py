import os
import smtplib
import logging
from celery import Celery
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Celery with broker and backend from environment variables
celery = Celery(
    'tasks',
    broker=os.getenv('CELERY_BROKER_URL'),
    backend=os.getenv('CELERY_RESULT_BACKEND')
)

# Retrieve email configuration from environment variables
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT'))

# Configure basic logging
logging.basicConfig(level=logging.INFO)

@celery.task
def send_email(email):
    try:
        # Set up SMTP server connection
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Upgrade connection to secure
        server.login(EMAIL, PASSWORD)  # Log in to the SMTP server
        
        # Create email message with MIME multipart format
        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = email
        msg['Subject'] = "Subject: Test"
        body = "This is a test email to know it works."
        msg.attach(MIMEText(body, 'plain'))  # Attach email body

        # Send email and close server connection
        server.sendmail(EMAIL, email, msg.as_string())
        server.quit()
        
        # Log success
        logging.info(f'Email sent to {email}')
        print("Email sent")
    except Exception as e:
        # Log any exceptions during email send process
        logging.error(f'Failed to send email to {email}: {e}')
        print("Email not sent")
