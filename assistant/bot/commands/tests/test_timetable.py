import datetime as dt

from pytest import mark
from telethon import TelegramClient
from telethon.tl.custom.message import Message

from assistant import config
from assistant.bot.dictionaries.phrases import *
from assistant.database import User
from assistant.bot.commands.tests.utils import flatten_keyboard
from assistant.database import StudentsGroup, Faculty, SingleLesson

from assistant.bot.commands.timetable import build_timetable_lesson, build_timetable_day

from assistant.database import Session
from assistant.tests.factories import (
    FacultyFactory,
    LessonFactory,
    TeacherFactory,
    SingleLessonFactory,
    UserFactory,
    StudentsGroupFactory,
)


class TestTimetable:

    def test_build_timetable_lesson(self, db_session):

        # TODO: use a SingleLesson from a fixture
        single_lesson = SingleLessonFactory(
            starts_at=dt.time(hour=10, minute=0, second=0),
            ends_at=dt.time(hour=11, minute=30, second=0),
        )
        user = UserFactory(students_group=single_lesson.lesson.students_group)

        result = build_timetable_lesson(db_session, user, single_lesson)

        assert result == f"10:00 - 11:30\n" \
                         f"{e_books} <b>{single_lesson.lesson.name}</b> " \
                         f"({single_lesson.lesson.represent_lesson_format()})\n" \
                         f"{e_teacher} {single_lesson.lesson.teachers[0].short_name}"

    def test_build_timetable_day(self, db_session):
        group = StudentsGroupFactory()
        user = UserFactory(students_group=group)
        math = LessonFactory(students_group=group)

        date = dt.date(year=2021, month=1, day=26)
        math_1 = SingleLessonFactory(
            lesson=math,
            date=date,
            starts_at=dt.time(hour=10, minute=0, second=0),
            ends_at=dt.time(hour=11, minute=30, second=0),
        )
        math_2 = SingleLessonFactory(
            lesson=math,
            date=date,
            starts_at=dt.time(hour=12, minute=0, second=0),
            ends_at=dt.time(hour=13, minute=30, second=0),
        )
        extra_lesson = SingleLessonFactory(date=date)

        db_session.commit()

        result = build_timetable_day(db_session, user, date)

        assert result == f"""\
10:00 - 11:30
{e_books} <b>{math.name}</b> ({math.represent_lesson_format()})
{e_teacher} {math.teachers[0].short_name}

12:00 - 13:30
{e_books} <b>{math.name}</b> ({math.represent_lesson_format()})
{e_teacher} {math.teachers[0].short_name}\
"""

