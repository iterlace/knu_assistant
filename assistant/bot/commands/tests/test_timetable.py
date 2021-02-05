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

        date = dt.date(year=2021, month=1, day=26)

        # Teachers
        koval = TeacherFactory()
        kondratyuk = TeacherFactory()

        # Lessons
        math = LessonFactory(name="M", lesson_format=0, students_group=group)
        # Programming practices are divided into 2 subgroups
        programming_1 = LessonFactory(teachers=[koval], subgroup="1",
                                      name="P", lesson_format=1, students_group=group)
        programming_2 = LessonFactory(teachers=[kondratyuk], subgroup="2",
                                      name="P", lesson_format=1, students_group=group)

        # User belongs to programming_1 subgroup
        user.subgroups.append(programming_1)

        # SingleLessons
        math_sl = SingleLessonFactory(
            lesson=math,
            date=date,
            starts_at=dt.time(8, 40),
            ends_at=dt.time(10, 15),
        )
        programming_1_sl = SingleLessonFactory(
            lesson=programming_1,
            date=date,
            starts_at=dt.time(10, 35),
            ends_at=dt.time(12, 10),
        )
        programming_2_sl = SingleLessonFactory(
            lesson=programming_2,
            date=date,
            starts_at=dt.time(10, 35),
            ends_at=dt.time(12, 10),
        )
        extra_sl = SingleLessonFactory(date=date)

        db_session.commit()

        result = build_timetable_day(db_session, user, date)
        assert result == f"""\
08:40 - 10:15
{e_books} <b>M</b> ({math.represent_lesson_format()})
{e_teacher} {math.teachers[0].short_name}

10:35 - 12:10
{e_books} <b>P</b> ({programming_1.represent_lesson_format()})
{e_teacher} {koval.short_name}\
"""

