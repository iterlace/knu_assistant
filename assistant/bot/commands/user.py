import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CallbackContext,
)
from sqlalchemy.orm import Session

from assistant.config import bot
from assistant.database import User, StudentsGroup
from assistant.bot.decorators import acquire_user, db_session
from assistant.bot.dictionaries import states
from assistant.bot.keyboards import build_keyboard_menu

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

