import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CallbackContext,
)
import sqlalchemy as sqa
from sqlalchemy.orm import Session

from assistant.config import bot
from assistant.database import User, StudentsGroup, Faculty
from assistant.bot.decorators import acquire_user, db_session
from assistant.bot.dictionaries import states
from assistant.bot.dictionaries.phrases import *
from assistant.bot.keyboards import build_keyboard_menu

logger = logging.getLogger(__name__)


@db_session
@acquire_user
def change_group(update: Update, ctx: CallbackContext, session: Session, user: User):
    # Ask for a course
    kb_buttons = []
    for course in session.query(StudentsGroup.course).distinct(StudentsGroup.course).order_by(StudentsGroup.course):
        kb_buttons.append(InlineKeyboardButton(
            text=course[0],
            callback_data=course[0],
        ))

    kb_footer = None
    if user.students_group_id is not None:
        kb_footer = [InlineKeyboardButton(text=p_cancel, callback_data=states.END)]

    keyboard = build_keyboard_menu(kb_buttons, 4, footer_buttons=kb_footer)
    bot.send_message(update.effective_user.id, "На якому курсі ти навчаєшся?",
                     reply_markup=InlineKeyboardMarkup(keyboard))
    return states.UserSelectCourse


@db_session
@acquire_user
def select_course(update: Update, ctx: CallbackContext, session: Session, user: User):
    is_valid = session.query(sqa.exists().where(StudentsGroup.course == update.callback_query.data)).scalar()
    if not is_valid:
        return  # TODO: handle error
    ctx.user_data["course"] = update.callback_query.data

    # Ask for a faculty
    kb_buttons = []
    for faculty in session.query(Faculty).order_by(Faculty.id):
        kb_buttons.append(InlineKeyboardButton(
            text=faculty.name,
            callback_data=faculty.id,
        ))

    kb_footer = None
    if user.students_group_id is not None:
        kb_footer = [InlineKeyboardButton(text=p_cancel, callback_data=states.END)]

    update.callback_query.answer()
    keyboard = build_keyboard_menu(kb_buttons, 4, footer_buttons=kb_footer)
    bot.edit_message_reply_markup(update.effective_user.id, update.callback_query.message.message_id, reply_markup=None)
    bot.send_message(update.effective_user.id, "На якому факультеті?",
                     reply_markup=InlineKeyboardMarkup(keyboard))
    return states.UserSelectFaculty


@db_session
@acquire_user
def select_faculty(update: Update, ctx: CallbackContext, session: Session, user: User):
    is_valid = session.query(sqa.exists().where(Faculty.id == update.callback_query.data)).scalar()
    if not is_valid:
        return  # TODO: handle error
    ctx.user_data["faculty_id"] = update.callback_query.data

    # Ask for a group
    kb_buttons = []
    for group in session.query(StudentsGroup) \
            .filter_by(faculty_id=ctx.user_data["faculty_id"], course=ctx.user_data["course"]) \
            .order_by(StudentsGroup.name):
        kb_buttons.append(InlineKeyboardButton(
            text=group.name,
            callback_data=group.id,
        ))

    kb_footer = None
    if user.students_group_id is not None:
        kb_footer = [InlineKeyboardButton(text=p_cancel, callback_data=states.END)]

    update.callback_query.answer()
    keyboard = build_keyboard_menu(kb_buttons, 4, footer_buttons=kb_footer)
    bot.edit_message_reply_markup(update.effective_user.id, update.callback_query.message.message_id, reply_markup=None)
    bot.send_message(update.effective_user.id, "Обери свою групу",
                     reply_markup=InlineKeyboardMarkup(keyboard))
    return states.UserSelectGroup


@db_session
@acquire_user
def select_group(update: Update, ctx: CallbackContext, session: Session, user: User):
    is_valid = session.query(sqa.exists().where(StudentsGroup.id == update.callback_query.data)).scalar()
    if not is_valid:
        return  # TODO: handle error
    ctx.user_data["group_id"] = update.callback_query.data

    # Attach the group to the user
    group = session.query(StudentsGroup).get(ctx.user_data["group_id"])
    user.students_group = group
    session.commit()
    update.callback_query.answer()
    bot.edit_message_reply_markup(update.effective_user.id, update.callback_query.message.message_id, reply_markup=None)
    bot.send_message(update.effective_user.id, "Групу {} встановлено!".format(group.name))
    return states.END
