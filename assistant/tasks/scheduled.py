""" Crontab tasks """

import datetime as dt

import telegram.error
from telegram import ParseMode

from assistant.bot.commands.timetable import build_timetable_day
from assistant.bot.dictionaries import week
from assistant.config import bot
from assistant.database import (
    Session,
    User,
)
from assistant.tasks.config import app


@app.task
def tomorrow_timetable():
    """ Sends each user their timetable for the next day, if present """
    session = Session()
    users = session.query(User).all()
    tomorrow = dt.datetime.today().date() + dt.timedelta(days=1)
    for user in users:
        timetable = build_timetable_day(session, user, tomorrow)
        if not timetable:
            continue
        message = "Твій розклад на завтра ({day}):\n\n{timetable}\n\n".format(
            day=week.LIST[tomorrow.weekday()].name,
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
