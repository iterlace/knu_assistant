import celery
import datetime as dt

from telegram import ParseMode
import telegram.error

from assistant.bot.commands.timetable import build_timetable_day, build_timetable_week
from assistant.bot.dictionaries.days_of_week import *
from assistant import config
from assistant.config import bot
from assistant.database import (
    Session,
    User,
    StudentsGroup,
    Lesson,
    SingleLesson,
    Teacher,
    LessonSubgroupMember,
    Request,
)
from assistant.tasks import celery as tasks_config
from assistant.tasks.celery import app


@app.task
def tomorrow_timetable():
    session = Session()
    users = session.query(User).all()
    tomorrow = dt.datetime.today().date() + dt.timedelta(days=1)
    for user in users:
        timetable = build_timetable_day(session, user, tomorrow)
        if not timetable:
            continue
        message = "Твій розклад на завтра ({day}):\n\n{timetable}\n\n".format(
            day=DAYS_OF_WEEK[tomorrow.weekday()].name,
            timetable=timetable,
        )
        try:
            bot.send_message(
                chat_id=user.tg_id,
                text=message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except telegram.error.TelegramError as e:
            continue
