import logging

from sqlalchemy.orm import Session
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import CallbackContext

from app.bot.decorators import acquire_user, db_session, moderators_only
from app.bot.dictionaries import states
from app.bot.dictionaries.phrases import *
from app.bot.keyboards import build_keyboard_menu
from app.bot.api import bot
from app.database import Lesson, Request, User

logger = logging.getLogger(__name__)


def send_request(request: Request, session: Session,
                 accept_callback: states.State, reject_callback: states.State) -> bool:
    """
    Completes the given Request object and sends messages to moderator and initiator

    :param request: Request object with all fields set up,
        except moderator/moderator_id, accept_callbacks and reject_callback.
        The object would be completed and committed.
    :param session: DB Session
    :param accept_callback: State object for a "Accept" button callback
    :param reject_callback: State object for a "Reject" button callback
    :return: is messages sent successfully
    """
    moderator = (
        session.query(User)
        .filter(
            (User.students_group_id == request.students_group.id) &
            (User.is_group_moderator == True)
        )
        .first()
    )
    request.moderator = moderator
    if moderator is None:
        return False

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
            text=f"{E_ACCEPT} Підтвердити",
            callback_data=request.accept_callback,
        ),
        InlineKeyboardButton(
            text=f"{E_CANCEL} Відхилити",
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
    return True


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
        text=f"{E_ACCEPT} {request.message}",
        reply_markup=None,
        parse_mode=ParseMode.HTML,
    )
    bot.send_message(
        request.initiator.tg_id,
        text=f"{E_ACCEPT} Ваш запит #{request.id} було підтверджено!",
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
        text=f"{E_CANCEL} {request.message}",
        reply_markup=None,
        parse_mode=ParseMode.HTML,
    )
    bot.send_message(
        request.initiator.tg_id,
        text=f"{E_CANCEL} Ваш запит #{request.id} було відхилено!",
        parse_mode=ParseMode.HTML,
    )
