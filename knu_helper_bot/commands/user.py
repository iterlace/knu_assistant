
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


@db_session
@acquire_user
def select_students_group(update: Update, ctx: CallbackContext, session: Session, user: User):
    if not update.callback_query:
        # User wants to change their group
        kb_buttons = []
        for group in session.query(StudentsGroup).order_by("name"):
            kb_buttons.append(InlineKeyboardButton(
                text=group.name,
                callback_data=states.UserSelectStudentsGroupStep.build_pattern.format(group.id),
            ))
        bot.sendMessage(update.effective_user.id, "Обери свою групу",
                        reply_markup=InlineKeyboardMarkup(build_keyboard_menu(kb_buttons, 4)))
    else:
        # User selected his group
        group_id = states.UserSelectStudentsGroupStep.parse_pattern.match(update.callback_query.data)
        if group_id is None:
            logger.error("Received unexpected group_id: {}! Update: {}".format(update.callback_query.data, update))
            return
        group_id = group_id.group(1)
        group = session.query(StudentsGroup).get(group_id)
        if group is None:
            logger.error("Received non-existing group: {}! Update: {}".format(group_id, update))
            return
        user.students_group_id = group_id
        session.commit()
        bot.editMessageReplyMarkup(update.effective_user.id, update.callback_query.message.message_id, reply_markup=None)
        bot.sendMessage(update.effective_user.id, "Групу {} встановлено!".format(group.name))

