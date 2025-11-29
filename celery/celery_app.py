import os
import redis
from celery import Celery

# Configure Celery app
# Use Redis as the message broker
app = Celery('personal_backend', broker=os.getenv('CELERY_BROKER_URL'))
app.conf.task_compression = 'gzip' # Compress messages to save Redis memory

# Include task modules so Celery can find them
app.conf.imports = ['tasks.fetching', 'tasks.analysis']

# Initialize Redis client for distributed locking
# We reuse the broker URL for the Redis client connection
redis_client = redis.from_url(os.getenv('CELERY_BROKER_URL'))

# Define Beat Schedule
app.conf.beat_schedule = {
    'orchestrator-every-60-seconds': {
        'task': 'tasks.fetching.orchestrator',
        'schedule': 60.0,
    },
    'analysis-enqueuer-every-60-seconds': {
        'task': 'tasks.analysis.enqueue_analysis_tasks',
        'schedule': 60.0,
    },
}

# Optional: Trigger tasks immediately on startup
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # We can't easily import the tasks here without circular imports if they import app
    # So we use send_task by name
    try:
        sender.send_task('tasks.fetching.orchestrator')
        sender.send_task('tasks.analysis.enqueue_analysis_tasks')
    except Exception as e:
        print(f"Failed to trigger startup tasks: {e}")
