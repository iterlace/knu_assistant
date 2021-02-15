from celery import Celery
from celery.schedules import crontab

from assistant import config

app = Celery("knu_assistant", broker="sqla+{}".format(config.DB_STRING))
app.conf.beat_schedule = {
    "tomorrow-timetable": {
        "task": "assistant.tasks.scheduled.tomorrow_timetable",
        "schedule": crontab(hour=23, minute=0),
        "args": [],
    }
}
