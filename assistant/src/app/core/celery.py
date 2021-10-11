from urllib.parse import urlparse

from celery import Celery
from kombu import Queue
from celery.schedules import crontab

from app.core.config import settings


class CeleryConfig:
    broker_transport_options = {"visibility_timeout": 24 * 3600}  # 31 * 24 * 3600

    broker_url = settings.CELERY_BROKER_URL
    task_default_queue = "default"
    task_queues = (Queue("default"),)
    worker_prefetch_multiplier = 1
    beat_scheduler = "celery.beat:PersistentScheduler"

    timezone = "Europe/Kiev"
    enable_utc = True

    beat_schedule = {
        "tomorrow-timetable": {
            "task": "app.tasks.timetable.tomorrow_timetable",
            "schedule": crontab(hour=21, minute=00),
            "args": [],
        }
    }

    def __init__(self):
        parsed_broker_url = urlparse(self.broker_url)
        self.backend = parsed_broker_url.scheme
        self.task_always_eager = getattr(settings, "CELERY_TASKS_ALWAYS_EAGER", False)
        setattr(self, f"{self.backend}_host", parsed_broker_url.hostname)
        setattr(self, f"{self.backend}_port", parsed_broker_url.port)


appConfig = CeleryConfig()
app = Celery(
    "app",
    backend=appConfig.backend,
    broker=settings.CELERY_BROKER_URL,
)
app.config_from_object(appConfig)

app.log.setup()
app.autodiscover_tasks(
    [
        "app",
    ]
)
