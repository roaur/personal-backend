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
