import logging

import sqlalchemy as sqa
from sqlalchemy import func
from sqlalchemy.orm import Session
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import CallbackContext

from app.bot.commands.utils import end
from app.bot.decorators import acquire_user, db_session
from app.bot.dictionaries import states
from app.bot.dictionaries.phrases import *
from app.bot.keyboards import build_keyboard_menu
from app.bot.api import bot
from app.database import Faculty, Lesson, StudentsGroup, User

logger = logging.getLogger(__name__)


@db_session
@acquire_user
def change_group(update: Update, ctx: CallbackContext, session: Session, user: User):
    # Ask for a course

    if user.is_group_moderator:
        bot.send_message(
            update.effective_user.id,
            "<b>Увага!</b>\nПереходячи до іншої групи, ви назавжди втратите роль модератора в "
            "даній!",
            parse_mode=ParseMode.HTML,
        )

    kb_buttons = []
    for course in session.query(StudentsGroup.course).distinct(StudentsGroup.course).order_by(
            StudentsGroup.course):
        kb_buttons.append(InlineKeyboardButton(
            text=course[0],
            callback_data=course[0],
        ))

    kb_footer = None
    if user.students_group_id is not None:
        kb_footer = [InlineKeyboardButton(text=P_CANCEL, callback_data=states.END)]

    keyboard = build_keyboard_menu(kb_buttons, 4, footer_buttons=kb_footer)
    bot.send_message(update.effective_user.id, "На якому курсі ти навчаєшся?",
                     reply_markup=InlineKeyboardMarkup(keyboard))
    return states.UserSelectCourse


@db_session
@acquire_user
def select_course(update: Update, ctx: CallbackContext, session: Session, user: User):
    is_valid = session.query(
        sqa.exists().where(StudentsGroup.course == update.callback_query.data)).scalar()
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
        kb_footer = [InlineKeyboardButton(text=P_CANCEL, callback_data=states.END)]

    keyboard = build_keyboard_menu(kb_buttons, 4, footer_buttons=kb_footer)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        "На якому факультеті?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
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
        kb_footer = [InlineKeyboardButton(text=P_CANCEL, callback_data=states.END)]

    update.callback_query.answer()
    keyboard = build_keyboard_menu(kb_buttons, 4, footer_buttons=kb_footer)
    update.callback_query.edit_message_text(
        "Обери свою групу",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return states.UserSelectGroup


@db_session
@acquire_user
def select_group(update: Update, ctx: CallbackContext, session: Session, user: User):
    is_valid = session.query(
        sqa.exists().where(StudentsGroup.id == update.callback_query.data)).scalar()
    if not is_valid:
        return None  # TODO: handle error
    ctx.user_data["group_id"] = update.callback_query.data

    update.callback_query.answer()
    update.callback_query.edit_message_text("Групу встановлено!", reply_markup=None)
    update.callback_query = None
    return select_subgroups(update=update, ctx=ctx, session=session, user=user)


@db_session
@acquire_user
def select_subgroups(update: Update, ctx: CallbackContext, session: Session, user: User):
    # list of already chosen subgroups (Lesson) to exclude them in further steps
    ctx.user_data.setdefault("subgroups", list())
    # lesson that is being selected by the user (tuple of (name, lesson_format))
    ctx.user_data.setdefault("current_subgroup_lesson", None)

    # if "select_subgroups" called from "select_group"
    if update.callback_query is None:
        ctx.user_data["current_subgroup_lesson"] = None
    else:
        lesson_name, lesson_format = ctx.user_data["current_subgroup_lesson"]
        subgroup = update.callback_query.data
        lesson = session.query(Lesson).filter(
            Lesson.students_group_id == ctx.user_data["group_id"],
            Lesson.subgroup == subgroup,
            Lesson.name == lesson_name,
            Lesson.lesson_format == lesson_format,
        ).first()
        if not lesson:
            return None  # TODO: handle error
        ctx.user_data["subgroups"].append(lesson)
        update.callback_query.answer()

    # filters to exclude already selected groups from the InputKeyboard
    filters = []
    for lesson in ctx.user_data["subgroups"]:
        filters.append(~(
                (Lesson.name == lesson.name) &
                (Lesson.lesson_format == lesson.lesson_format)
        ))
    # remaining lessons
    lessons = (
        session.query(Lesson.name, Lesson.lesson_format)
        .filter(
            Lesson.students_group_id == ctx.user_data["group_id"],
            *filters,
        )
        .order_by(Lesson.name)
        .group_by(Lesson.name, Lesson.students_group_id, Lesson.lesson_format)
        .having(func.count(1) > 1)
        .all()
    )

    if lessons:
        lesson_name, lesson_format = lessons[0]
        ctx.user_data["current_subgroup_lesson"] = (lesson_name, lesson_format)

        # Ask for a group
        kb_buttons = []
        for subgroup in session.query(Lesson) \
                .filter_by(students_group_id=ctx.user_data["group_id"],
                           name=lesson_name, lesson_format=lesson_format) \
                .order_by(Lesson.subgroup):
            teachers = []
            for teacher in subgroup.teachers:
                teachers.append(teacher.short_name)

            kb_buttons.append(InlineKeyboardButton(
                text="[#{subgroup}] {teachers}".format(
                    subgroup=subgroup.subgroup,
                    teachers=", ".join(teachers),
                ),
                callback_data=subgroup.subgroup,
            ))
        kb_footer = None
        if user.students_group_id is not None:
            kb_footer = [InlineKeyboardButton(text=P_CANCEL, callback_data=states.END)]
        keyboard = build_keyboard_menu(kb_buttons, n_cols=2, footer_buttons=kb_footer)

        if update.callback_query is not None:
            update.callback_query.edit_message_text(
                # TODO: lesson_format representation
                text="Обери свою підгрупу з {} ({})".format(lesson_name, lesson_format),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            bot.send_message(
                update.effective_user.id,
                text="Обери свою підгрупу з {} ({})".format(lesson_name, lesson_format),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        return states.UserSelectSubgroups

    # if all subgroups were selected - push all changes to the database

    # attach the group to the user
    group = session.query(StudentsGroup).get(ctx.user_data["group_id"])
    user.students_group = group

    user.is_group_moderator = False

    user.subgroups.clear()
    for lesson in ctx.user_data["subgroups"]:
        lesson = session.merge(lesson)
        user.subgroups.append(lesson)
    session.commit()
    if update.callback_query is not None and len(user.subgroups) > 0:
        update.callback_query.edit_message_text(
            text="Підгрупи визначено!",
            reply_markup=None
        )
    return end(update=update, ctx=ctx)
