import os
import logging
from flask import Flask, request, jsonify
from datetime import datetime
from dotenv import load_dotenv
from celery import Celery
from tasks import send_email
from celery.result import AsyncResult

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize Celery with broker and result backend from environment variables
celery = Celery(
    __name__,
    broker=os.getenv('CELERY_BROKER_URL'),
    backend=os.getenv('CELERY_RESULT_BACKEND')
)

# Configure logging
logging.basicConfig(
    filename='./logs/messaging_system.log',  # Log file path
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    level=logging.INFO  # Log level
)
# Add console handler to logger
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

@app.route('/')
def index():
    # Retrieve query parameters
    sendmail = request.args.get('sendmail')
    talktime = request.args.get('talktime')

    # Check if both parameters are provided
    if sendmail and talktime:
        # Queue email sending task
        task = send_email.delay(sendmail)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f'Email task queued with task id: {task.id}')
        return jsonify({
            'message': 'Email task has been queued.',
            'task_id': task.id
        }), 200
    # Log warning if parameters are missing
    logging.warning('Both sendmail and talktime parameters are required.')
    return 'Both sendmail and talktime parameters are required.', 400

@app.route('/task_status/<task_id>')
def get_task_status(task_id):
    # Retrieve task result
    result = AsyncResult(task_id, app=celery)
    # Respond based on task status
    if result.successful():
        return jsonify({
            'status': 'SUCCESS',
            'message': f'Email sent successfully to {result.result}'
        }), 200
    elif result.failed():
        return jsonify({
            'status': 'FAILURE',
            'message': 'Failed to send email'
        }), 400
    else:
        return jsonify({
            'status': 'PENDING',
            'message': 'Email sending in progress'
        }), 202

if __name__ == '__main__':
    app.run(debug=True)
