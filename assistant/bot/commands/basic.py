
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

from assistant.config import bot
from assistant.database import User, StudentsGroup
from assistant.bot.decorators import acquire_user, db_session
from assistant.bot.dictionaries import states
from assistant.bot.keyboards import build_keyboard_menu

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
    logger.debug("start ends its work")


def help(update: Update, ctx: CallbackContext):
    update.message.reply_text("Со всеми вопросами пока обращаться к @iterlace")
