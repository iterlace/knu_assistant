""" Crontab tasks """

import datetime as dt

import telegram.error
from telegram import ParseMode

from app.bot.commands.timetable import build_timetable_day
from app.bot.api import bot
from app.bot.dictionaries import week
from app.core.config import settings
from app.database import Session, User
from app.core.celery import app


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
