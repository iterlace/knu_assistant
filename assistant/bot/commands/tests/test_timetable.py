import datetime as dt

import mock
from pytest import mark
from telethon import TelegramClient
from telethon.tl.custom.message import Message

from assistant import config
from assistant.bot.dictionaries.phrases import *
from assistant.database import User
from assistant.bot.commands.tests.utils import flatten_keyboard
from assistant.database import StudentsGroup, Faculty, SingleLesson

from assistant.bot.commands.timetable import (
    build_timetable_lesson,
    build_timetable_day,
    build_timetable_week,
)

from assistant.database import Session
from assistant.tests.factories import (
    FacultyFactory,
    LessonFactory,
    TeacherFactory,
    SingleLessonFactory,
    UserFactory,
    StudentsGroupFactory,
)


class TestTimetableBuilders:

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

    def test_build_timetable_week(self, db_session):
        group = StudentsGroupFactory()
        user = UserFactory(students_group=group)

        monday = dt.date(year=2021, month=2, day=1)

        # Lessons
        math = LessonFactory(name="M", lesson_format=0, students_group=group)
        # SingleLessons
        math_sl = SingleLessonFactory(
            lesson=math,
            date=monday,
            starts_at=dt.time(8, 40),
            ends_at=dt.time(10, 15),
        )
        db_session.commit()

        with mock.patch("assistant.bot.commands.timetable.build_timetable_day",
                        side_effect=build_timetable_day) as build_day_mock:
            # from assistant.bot.commands.timetable import build_timetable_week, build_timetable_day
            result = build_timetable_week(db_session, user, monday)
            assert build_day_mock.call_count == 7
        assert result == f"""\
[ <b>Понеділок</b> ]
08:40 - 10:15
{e_books} <b>M</b> ({math.represent_lesson_format()})
{e_teacher} {math.teachers[0].short_name}

[ <b>Вівторок</b> ]


[ <b>Середа</b> ]


[ <b>Четвер</b> ]


[ <b>П'ятниця</b> ]


[ <b>Субота</b> ]


[ <b>Неділя</b> ]
"""


class TestTimetableCommands:

    @mark.asyncio
    async def test_day(self, db_session, client: TelegramClient, use_bot):
        group = StudentsGroupFactory()
        user = UserFactory(tg_id=(await client.get_me()).id, students_group=group)

        today = dt.date(2021, 2, 1)
        yesterday = today - dt.timedelta(days=1)
        tomorrow = today + dt.timedelta(days=1)

        with mock.patch("assistant.bot.commands.timetable.dt") as dt_mock:
            dt_mock.date.today = mock.Mock(return_value=today)
            dt_mock.datetime = dt.datetime
            dt_mock.timedelta = dt.timedelta

            # Lessons
            math = LessonFactory(name="M", lesson_format=0, students_group=group)
            # SingleLessons
            math_today_sl = SingleLessonFactory(
                lesson=math,
                date=today,
                starts_at=dt.time(8, 40),
                ends_at=dt.time(10, 15),
            )
            math_yesterday_sl = SingleLessonFactory(
                lesson=math,
                date=yesterday,
                starts_at=dt.time(8, 40),
                ends_at=dt.time(10, 15),
            )
            db_session.commit()

            async with client.conversation("@{}".format(config.BOT_NAME), timeout=5) as conv:
                await conv.send_message("/day")
                r: Message

                r = await conv.get_response()
                kb = flatten_keyboard(r.buttons)
                expected_timetable = build_timetable_day(db_session, user, today)
                assert r.text == "<b>Понеділок</b> (01.02)\n\n{}".format(expected_timetable)
                assert kb[0].text == "< {}".format(yesterday.strftime("%d.%m.%Y"))
                assert kb[1].text == "Сьогодні".format(today.strftime("%d.%m.%Y"))
                assert kb[2].text == "{} >".format(tomorrow.strftime("%d.%m.%Y"))

                # Select previous day
                await kb[0].click()

                r = await conv.get_edit()
                kb = flatten_keyboard(r.buttons)
                expected_timetable = build_timetable_day(db_session, user, yesterday)
                assert r.text == "<b>Неділя</b> (31.01)\n\n{}".format(expected_timetable)

                # Select today
                await kb[1].click()

                r = await conv.get_edit()
                kb = flatten_keyboard(r.buttons)
                expected_timetable = build_timetable_day(db_session, user, yesterday)
                assert r.text == "<b>Понеділок</b> (01.02)\n\n{}".format(expected_timetable)


