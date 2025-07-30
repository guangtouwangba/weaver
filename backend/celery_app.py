"""
Celery application configuration for Research Agent RAG System
"""
import os
from celery import Celery
from dotenv import load_dotenv
from config import Config

# Load environment variables
load_dotenv()

# Create Celery app with configuration from Config class
celery_app = Celery(
    'research_agent_rag',
    broker=Config.get_celery_broker_url(),
    backend=Config.get_celery_result_backend(),
    include=['tasks.research_tasks']  # Import task modules
)

# Celery configuration using Config class
celery_app.conf.update(
    # Task serialization
    task_serializer=Config.CELERY_TASK_SERIALIZER,
    accept_content=[Config.CELERY_ACCEPT_CONTENT],
    result_serializer=Config.CELERY_RESULT_SERIALIZER,
    
    # Timezone
    timezone=Config.CELERY_TIMEZONE,
    enable_utc=Config.CELERY_ENABLE_UTC,
    
    # Task routing
    task_routes={
        'tasks.research_tasks.execute_research_job': {'queue': 'research'},
        'tasks.research_tasks.process_papers': {'queue': 'processing'},
    },
    
    # Worker settings
    worker_prefetch_multiplier=Config.CELERY_WORKER_PREFETCH_MULTIPLIER,
    task_acks_late=Config.CELERY_TASK_ACKS_LATE,
    
    # Task execution settings
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
    
    # Result backend settings
    result_expires=Config.CELERY_RESULT_EXPIRES,
    
    # Retry settings
    task_default_retry_delay=Config.CELERY_TASK_DEFAULT_RETRY_DELAY,
    task_max_retries=Config.CELERY_TASK_MAX_RETRIES,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Security
    worker_hijack_root_logger=False,
)

# Define queues
celery_app.conf.task_routes = {
    'tasks.research_tasks.*': {'queue': 'research'},
}

if __name__ == '__main__':
    celery_app.start()