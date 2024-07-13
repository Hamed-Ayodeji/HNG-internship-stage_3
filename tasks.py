import os
import smtplib
import logging
from celery import Celery
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

celery = Celery(
    'tasks',
    broker=os.getenv('CELERY_BROKER_URL'),
    backend=os.getenv('CELERY_RESULT_BACKEND')
)

EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT'))

logging.basicConfig(level=logging.INFO)

@celery.task
def send_email(email):
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = email
        msg['Subject'] = "Subject: Test"
        body = "This is a test email to know it works."
        msg.attach(MIMEText(body, 'plain'))

        server.sendmail(EMAIL, email, msg.as_string())
        server.quit()
        
        logging.info(f'Email sent to {email}')
        print("Email sent")
    except Exception as e:
        logging.error(f'Failed to send email to {email}: {e}')
        print("Email not sent")
