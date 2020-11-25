
import logging

import telegram as tg
from telegram import (
    Bot,
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
from knu_helper_bot.database import User, StudentsGroup
from knu_helper_bot.decorators import acquire_user, db_session
from knu_helper_bot import states
from knu_helper_bot.keyboards import build_keyboard_menu

logger = logging.getLogger(__name__)


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
                callback_data=user.current_state.build_pattern.format(group.id),
            ))

        bot.sendMessage(update.effective_user.id, "З якої групи ти завітав?",
                        reply_markup=InlineKeyboardMarkup(build_keyboard_menu(kb_buttons, 4)))


@db_session
@acquire_user
def select_students_group(update: Update, ctx: CallbackContext, session: Session, user: User):
    if not update.callback_query:
        user.current_state = states.UserSelectStudentsGroupStep
        kb_buttons = []
        for group in session.query(StudentsGroup).order_by("name"):
            kb_buttons.append(InlineKeyboardButton(
                text=group.name,
                callback_data="{}_{}".format(user.current_state, group.id),
            ))
        bot.sendMessage(update.effective_user.id, "Обери свою групу",
                        reply_markup=InlineKeyboardMarkup(build_keyboard_menu(kb_buttons, 4)))
    else:
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


def help(update: Update, ctx: CallbackContext):
    update.message.reply_text("Со всеми вопросами пока обращаться к @the_Yttra или @iterlace")

