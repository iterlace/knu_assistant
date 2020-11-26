
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
                callback_data=states.UserSelectStudentsGroupStep.build_pattern.format(group.id),
            ))

        bot.sendMessage(update.effective_user.id, "З якої групи ти завітав?",
                        reply_markup=InlineKeyboardMarkup(build_keyboard_menu(kb_buttons, 4)))


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


def build_timetable_lesson(lesson: TimetableLesson):
    result_str = ""
    if lesson.starts_at and lesson.ends_at:
        result_str += "{} - {}\n".format(
            lesson.starts_at.strftime("%H:%M"),
            lesson.ends_at.strftime("%H:%M"),
        )
    if lesson.lesson or lesson.teacher:
        if lesson.lesson:
            result_str += "{}".format(lesson.lesson.name)
        if lesson.teacher:
            result_str += " ({})".format(lesson.teacher.full_name())
        result_str += "\n"
    return result_str


def build_timetable_day(group: StudentsGroup, session: Session, day: int):
    lessons = (
        session
        .query(TimetableLesson)
        .filter(
            (TimetableLesson.students_group_id == group.id) &
            (TimetableLesson.day_of_week == day)
        )
        .order_by("starts_at", "teacher_id")
        .all()
    )
    result_str = ""
    for lesson in lessons:
        result_str += "{}\n".format(build_timetable_lesson(lesson))
    return result_str


def build_timetable_week(group: StudentsGroup, session: Session):
    lessons_str = ""
    for day in days_of_week.DAYS_OF_WEEK:
        lessons_str += "**{}**\n{}\n".format(day.name, build_timetable_day(group, session, day))
    return lessons_str


@db_session
@acquire_user
def show_timetable(update: Update, ctx: CallbackContext, session: Session, user: User):
    if not update.callback_query:
        bot.sendMessage(update.effective_user.id,
                        text=build_timetable_week(user.students_group, session),
                        parse_mode="markdown")


@db_session
@acquire_user
def edit_timetable(update: Update, ctx: CallbackContext, session: Session, user: User):
    if not update.callback_query:
        kb_buttons = []
        for day in days_of_week.DAYS_OF_WEEK:
            kb_buttons.append(InlineKeyboardButton(
                # todo: pencil emoji
                text="Ред. {}".format(day.name.lower()),
                callback_data=states.EditTimetableDay.build_pattern.format(day),
            ))
        bot.sendMessage(update.effective_user.id,
                        text=build_timetable_week(user.students_group, session),
                        reply_markup=InlineKeyboardMarkup(build_keyboard_menu(kb_buttons, 2)),
                        parse_mode="markdown")


@db_session
@acquire_user
def edit_timetable_callback(update: Update, ctx: CallbackContext, session: Session, user: User):
    kb_buttons = []
    for day in days_of_week.DAYS_OF_WEEK:
        kb_buttons.append(InlineKeyboardButton(
            # todo: pencil emoji
            text="Ред. {}".format(day.name.lower()),
            callback_data=states.EditTimetableDay.build_pattern.format(day),
        ))
    bot.editMessageText(
        chat_id=update.effective_user.id,
        message_id=update.callback_query.message.message_id,
        text=build_timetable_week(user.students_group, session),
        reply_markup=InlineKeyboardMarkup(build_keyboard_menu(kb_buttons, 2)),
        parse_mode="markdown",
    )


@db_session
@acquire_user
def edit_timetable_day_callback(update: Update, ctx: CallbackContext, session: Session, user: User):
    match = states.EditTimetableDay.parse_pattern.match(update.callback_query.data)
    day = match.group(1)
    kb_buttons = []
    keyboard = InlineKeyboardMarkup(build_keyboard_menu(
        kb_buttons,
        footer_buttons=[
            InlineKeyboardButton(text="Додати",
                                 callback_data=states.AddLessonToTimetable.build_pattern.format(day)),
            InlineKeyboardButton(text="<<", callback_data=states.EditTimetable.build_pattern),
        ],
        n_cols=2,
    ))
    # TODO: iterate over existing lessons
    bot.editMessageText(
        chat_id=update.effective_user.id,
        message_id=update.callback_query.message.message_id,
        text=build_timetable_week(user.students_group, session),
        reply_markup=keyboard,
        parse_mode="markdown",
    )


@db_session
@acquire_user
def add_lesson_callback(update: Update, ctx: CallbackContext, session: Session, user: User):
    match = states.AddLessonToTimetable.parse_pattern.match(update.callback_query.data)
    ctx.user_data["day"] = match.group(1)
    kb_buttons = []
    for lesson in session.query(Lesson).order_by("name"):
        kb_buttons.append(InlineKeyboardButton(
            text=lesson.name,
            callback_data=lesson.id,
        ))
    keyboard = InlineKeyboardMarkup(build_keyboard_menu(
        kb_buttons,
        footer_buttons=[
            # TODO: cancel button
        ],
        n_cols=2,
    ))
    # TODO: iterate over existing lessons
    bot.editMessageText(
        chat_id=update.effective_user.id,
        message_id=update.callback_query.message.message_id,
        text="Який предмет додамо?",
        reply_markup=keyboard,
        parse_mode="markdown",
    )
    return "read_lesson"


@db_session
@acquire_user
def add_lesson_lesson_callback(update: Update, ctx: CallbackContext, session: Session, user: User):
    lesson_id = update.callback_query.data
    lesson = session.query(Lesson).get(lesson_id)
    if lesson is None:
        # TODO
        pass
    ctx.user_data["lesson_id"] = lesson_id
    kb_buttons = []
    for teacher in session.query(Teacher).order_by("last_name"):
        kb_buttons.append(InlineKeyboardButton(
            text=teacher.full_name(),
            callback_data=teacher.id,
        ))
    keyboard = InlineKeyboardMarkup(build_keyboard_menu(
        kb_buttons,
        footer_buttons=[
            # TODO: cancel button
        ],
        n_cols=2,
    ))

    bot.editMessageText(
        chat_id=update.effective_user.id,
        message_id=update.callback_query.message.message_id,
        text="Предмет - {}".format(lesson.name),
        reply_markup=None,
        parse_mode="markdown",
    )
    bot.sendMessage(
        chat_id=update.effective_user.id,
        text="Хто викладає?",
        reply_markup=keyboard,
        parse_mode="markdown",
    )
    return "read_teacher"


@db_session
@acquire_user
def add_lesson_teacher_callback(update: Update, ctx: CallbackContext, session: Session, user: User):
    teacher_id = update.callback_query.data
    teacher = session.query(Teacher).get(teacher_id)
    if teacher is None:
        # TODO
        pass
    ctx.user_data["teacher_id"] = teacher_id

    keyboard = InlineKeyboardMarkup(build_keyboard_menu(
        [],
        footer_buttons=[
            # TODO: cancel button
        ],
        n_cols=2,
    ))

    bot.editMessageText(
        chat_id=update.effective_user.id,
        message_id=update.callback_query.message.message_id,
        text="Викладач - {}".format(teacher.full_name()),
        reply_markup=None,
        parse_mode="markdown",
    )
    # TODO: iterate over existing lessons
    bot.sendMessage(
        chat_id=update.effective_user.id,
        text="О котрій проводиться пара?\nЗаписуйте розклад у вигляді \"8:40 - 10:15\".",
        reply_markup=keyboard,
        parse_mode="markdown",
    )
    return "read_time"


@db_session
@acquire_user
def add_lesson_time(update: Update, ctx: CallbackContext, session: Session, user: User):
    if (match := timetable.time_span_pattern.match(update.message.text)) is None:
        keyboard = InlineKeyboardMarkup(build_keyboard_menu(
            [],
            footer_buttons=[
                # TODO: cancel button
            ],
            n_cols=2,
        ))
        bot.sendMessage(
            chat_id=update.effective_user.id,
            text="Некоректний формат!\nЗаписуйте розклад у вигляді \"8:40 - 10:15\".",
            reply_markup=keyboard,
            parse_mode="markdown",
        )
        return "read_time"
    else:
        _, start_hour, start_minute, _, end_hour, end_minute = match.groups()
        # TODO: filter start_hour, start_minute, end_hour, end_minute
        # TODO: timezone
        ctx.user_data["starts_at"] = dt.time(hour=int(start_hour), minute=int(start_minute))
        ctx.user_data["ends_at"] = dt.time(hour=int(end_hour), minute=int(end_minute))

    keyboard = InlineKeyboardMarkup(build_keyboard_menu(
        [],
        footer_buttons=[
            # TODO: cancel button
        ],
        n_cols=2,
    ))

    created_lesson = TimetableLesson(
        students_group_id=user.students_group_id,
        lesson_id=ctx.user_data["lesson_id"],
        teacher_id=ctx.user_data["teacher_id"],
        day_of_week=ctx.user_data["day"],
        starts_at=ctx.user_data["starts_at"],
        ends_at=ctx.user_data["ends_at"],
    )

    session.add(created_lesson)
    session.commit()

    # TODO: iterate over existing lessons
    bot.sendMessage(
        chat_id=update.effective_user.id,
        text="Предмет додано:\n{}".format(build_timetable_lesson(created_lesson)),
        reply_markup=keyboard,
        parse_mode="markdown",
    )


def help(update: Update, ctx: CallbackContext):
    update.message.reply_text("Со всеми вопросами пока обращаться к @the_Yttra или @iterlace")

