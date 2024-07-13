import os
import smtplib
import logging
from celery import Celery
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Configure Celery with the broker and backend URLs from environment variables
celery = Celery(
    'tasks',
    broker=os.getenv('CELERY_BROKER_URL'),
    backend=os.getenv('CELERY_RESULT_BACKEND')
)

# Fetch email configurations from environment variables
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT'))

# Set the path for the log file
log_path = '/var/log/messaging_system.log'
print(f"Log file path: {log_path}")

# Configure logging to write to a file and include timestamps and log levels
logging.basicConfig(
    filename=log_path,
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO  # Set log level to INFO to capture all log levels for detailed logging
)

# Add a console handler to also output logs to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Set console log level to INFO
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

print("Logging is configured")

@celery.task(bind=True)
def send_email(self, email):
    """
    Celery task to send an email.
    
    Args:
        self (Task): The current task instance (automatically passed by Celery).
        email (str): The recipient's email address.
    
    Returns:
        dict: A dictionary containing the status of the task and the email or error message.
    """
    try:
        # Set up the SMTP server connection
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
        server.login(EMAIL, PASSWORD)  # Log in to the email server
        
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = email
        msg['Subject'] = "Subject: Test"
        body = "This is the stage 3 task given by HNG internship."
        msg.attach(MIMEText(body, 'plain'))

        # Send the email
        server.sendmail(EMAIL, email, msg.as_string())
        server.quit()  # Terminate the SMTP session
        
        # Log success and return a success status
        logging.info(f'Email sent to {email}')
        print(f"Email sent to {email}")
        return {'status': 'SUCCESS', 'email': email}
    except Exception as e:
        # Log the error and retry the task up to 3 times with a 60-second delay between retries
        logging.error(f'Failed to send email to {email}: {e}')
        print(f"Failed to send email to {email}: {e}")
        self.retry(exc=e, countdown=60, max_retries=3)
        return {'status': 'FAILURE', 'error': str(e)}
