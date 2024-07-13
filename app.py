import os
import logging
from flask import Flask, request, jsonify
from datetime import datetime
from dotenv import load_dotenv
from celery import Celery
from tasks import send_email
from celery.result import AsyncResult

# Load environment variables from .env file
load_dotenv()

# Ensure the logs directory exists; create it if it does not
if not os.path.exists('./logs'):
    os.makedirs('./logs')

# Initialize Flask app
app = Flask(__name__)

# Configure Celery with the broker and backend URLs from environment variables
celery = Celery(
    __name__,
    broker=os.getenv('CELERY_BROKER_URL'),
    backend=os.getenv('CELERY_RESULT_BACKEND')
)

# Set up logging configuration
log_path = './logs/messaging_system.log'
print(f"Log file path: {log_path}")

logging.basicConfig(
    filename=log_path,
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO  # Capture all log levels for detailed logging
)

# Configure console logging for real-time log output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Capture all log levels for detailed logging
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

print("Logging is configured")

@app.route('/')
def index():
    """
    Main route that handles requests to send emails.
    Requires 'sendmail' and 'talktome' parameters in the query string.
    Queues an email sending task if parameters are provided.
    """
    logging.info('Accessed index route.')
    print('Accessed index route.')
    sendmail = request.args.get('sendmail')
    talktome = request.args.get('talktome')

    if sendmail and talktome:
        # Queue the email sending task using Celery
        task = send_email.delay(sendmail)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f'Email task queued with task id: {task.id}')
        print(f'Email task queued with task id: {task.id}')
        return jsonify({
            'message': 'Email task has been queued.',
            'task_id': task.id
        }), 200

    # Log and return an error if required parameters are missing
    logging.warning('Both sendmail and talktome parameters are required.')
    print('Both sendmail and talktome parameters are required.')
    return 'Both sendmail and talktome parameters are required.', 400

@app.route('/task_status/<task_id>')
def get_task_status(task_id):
    """
    Route to check the status of an email sending task.
    Requires the task ID as a URL parameter.
    Returns the status and result of the task.
    """
    result = AsyncResult(task_id, app=celery)
    logging.info(f'Checking status for task id: {task_id}')
    print(f'Checking status for task id: {task_id}')
    status = result.state
    logging.info(f'Task status for {task_id}: {status}')
    print(f'Task status for {task_id}: {status}')

    if status == 'SUCCESS':
        # Task completed successfully
        result_data = result.result
        logging.info(f'Email sent successfully to {result_data["email"]}')
        print(f'Email sent successfully to {result_data["email"]}')
        return jsonify({
            'status': 'SUCCESS',
            'message': f'Email sent successfully to {result_data["email"]}'
        }), 200
    elif status == 'FAILURE':
        # Task failed to complete
        result_data = result.result
        logging.error(f'Failed to send email: {result_data["error"]}')
        print(f'Failed to send email: {result_data["error"]}')
        return jsonify({
            'status': 'FAILURE',
            'message': f'Failed to send email: {result_data["error"]}'
        }), 400
    elif status in ['PENDING', 'RECEIVED', 'STARTED']:
        # Task is still in progress
        logging.info('Email sending in progress')
        print('Email sending in progress')
        return jsonify({
            'status': 'PENDING',
            'message': 'Email sending in progress'
        }), 202
    else:
        # Task status is unknown or not handled
        logging.warning('Task status unknown')
        print('Task status unknown')
        return jsonify({
            'status': 'UNKNOWN',
            'message': 'Task status unknown'
        }), 500

if __name__ == '__main__':
    # Run the Flask app on all available IP addresses (0.0.0.0) at port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
