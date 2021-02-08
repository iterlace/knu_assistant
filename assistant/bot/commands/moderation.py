import logging

from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
)
from telegram.ext import (
    CallbackContext,
)
import sqlalchemy as sqa
from sqlalchemy import func
from sqlalchemy.orm import Session

from assistant.config import bot
from assistant.database import User, StudentsGroup, Faculty, Lesson, LessonTeacher, LessonSubgroupMember
from assistant.bot.decorators import acquire_user, db_session, moderators_only
from assistant.bot.dictionaries import states
from assistant.bot.dictionaries.phrases import *
from assistant.bot.keyboards import build_keyboard_menu
from assistant.bot.commands.utils import end

from assistant.database import (
    Request,
    User,
    Lesson,
    Teacher,
    LessonTeacher,
    LessonSubgroupMember,
    SingleLesson,
)

logger = logging.getLogger(__name__)


def send_request(request: Request, session: Session, accept_callback: states.State, reject_callback: states.State):
    """
    Completes the given Request object and sends messages to moderator and initiator

    :param request: Request object with all fields set up,
        except moderator/moderator_id, accept_callbacks and reject_callback.
        The object would be completed and committed.
    :param session: DB Session
    :param accept_callback: State object for a "Accept" button callback
    :param reject_callback: State object for a "Reject" button callback
    :return: None
    """
    moderator = (
        session
        .query(User)
        .filter(
            (User.students_group_id == request.students_group.id) &
            (User.is_group_moderator == True)
        )
        .first()
    )
    request.moderator = moderator
    request.moderator_id = moderator.tg_id

    if not request.id:
        request.accept_callback = ""
        request.reject_callback = ""
        session.add(request)
        session.commit()
        request.accept_callback = accept_callback.build(request.id)
        request.reject_callback = reject_callback.build(request.id)
        session.commit()

    kb_buttons = [
        InlineKeyboardButton(
            text=f"{e_accept} Підтвердити",
            callback_data=request.accept_callback,
        ),
        InlineKeyboardButton(
            text=f"{e_cancel} Відхилити",
            callback_data=request.reject_callback,
        ),
    ]
    keyboard = build_keyboard_menu(kb_buttons, 3)

    bot.send_message(
        moderator.tg_id,
        text=request.message,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    bot.send_message(
        request.initiator_id,
        text=f"Запит #{request.id} надіслано до модератора групи!",
        parse_mode=ParseMode.HTML,
    )


@db_session
@acquire_user
@moderators_only
def accept_link_request(update: Update, ctx: CallbackContext, session: Session, user: User):
    request_id = ctx.match.group(1)
    request: Request = session.query(Request).get(request_id)
    if request is None or request.is_resolved \
            or request.meta.get("lesson_id", None) is None \
            or request.meta.get("link", None) is None:
        update.callback_query.answer()
        bot.delete_message(update.effective_user.id, update.message.message_id)
        return
    lesson = session.query(Lesson).get(request.meta.get("lesson_id", None))
    if lesson is None:
        request.is_resolved = True
        session.commit()
        update.callback_query.answer()
        bot.delete_message(update.effective_user.id, update.message.message_id)

    lesson.link = request.meta["link"]
    request.is_resolved = True
    session.commit()
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text=f"{e_accept} {request.message}",
        reply_markup=None,
        parse_mode=ParseMode.HTML,
    )
    bot.send_message(
        request.initiator.tg_id,
        text=f"{e_accept} Ваш запит #{request.id} було підтверджено!",
        parse_mode=ParseMode.HTML,
    )


@db_session
@acquire_user
@moderators_only
def reject_link_request(update: Update, ctx: CallbackContext, session: Session, user: User):
    request_id = ctx.match.group(1)
    request: Request = session.query(Request).get(request_id)
    if request is None or request.is_resolved:
        update.callback_query.answer()
        bot.delete_message(update.effective_user.id, update.message.message_id)
        return

    request.is_resolved = True
    session.commit()

    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text=f"{e_cancel} {request.message}",
        reply_markup=None,
        parse_mode=ParseMode.HTML,
    )
    bot.send_message(
        request.initiator.tg_id,
        text=f"{e_cancel} Ваш запит #{request.id} було відхилено!",
        parse_mode=ParseMode.HTML,
    )
