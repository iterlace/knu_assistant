
import datetime as dt
import logging
import re

import telegram as tg
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
    CallbackContext,
)
from sqlalchemy.orm import Session

from knu_helper_bot.config import bot
from knu_helper_bot.database import User, StudentsGroup, Lesson, TimetableLesson, Teacher
from knu_helper_bot.decorators import acquire_user, db_session
from knu_helper_bot.dictionaries import states, days_of_week, timetable
from knu_helper_bot.keyboards import build_keyboard_menu
from knu_helper_bot.dictionaries.phrases import *

logger = logging.getLogger(__name__)
__all__ = ["start", "help"]


@db_session
@acquire_user
def start(update: Update, ctx: CallbackContext, session: Session, user: User):
    bot.sendMessage(update.effective_user.id, """
Привіт!
    """)
    if user.students_group_id is None:
        kb_buttons = []
        for group in session.query(StudentsGroup).order_by("name"):
            kb_buttons.append(InlineKeyboardButton(
                text=group.name,
                callback_data=states.UserSelectStudentsGroupStep.build_pattern.format(group.id),
            ))

        bot.sendMessage(update.effective_user.id, "З якої групи ти завітав?",
                        reply_markup=InlineKeyboardMarkup(build_keyboard_menu(kb_buttons, 4)))


def help(update: Update, ctx: CallbackContext):
    update.message.reply_text("Со всеми вопросами пока обращаться к @the_Yttra или @iterlace")
