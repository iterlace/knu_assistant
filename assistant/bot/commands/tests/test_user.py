from datetime import datetime
import asyncio

from pytest import mark
from telethon import TelegramClient
from telethon.tl.custom.message import Message

from assistant import config
from assistant.database import User
from assistant.bot.commands.tests.utils import flatten_keyboard
from assistant.database import StudentsGroup, Faculty, LessonSubgroupMember

from assistant.tests.factories import (
    FacultyFactory,
    LessonFactory,
    TeacherFactory,
    SingleLessonFactory,
    UserFactory,
    StudentsGroupFactory,
)


class TestChangeGroup:

    @mark.asyncio
    async def test_full_conversation(self, client: TelegramClient, db_session, use_bot):

        # faculty that would be selected
        csc = FacultyFactory(name="CSC", shortcut="CSC")
        extra_faculty = FacultyFactory()

        # group that would be selected
        group = StudentsGroupFactory(course=1, faculty=csc)
        # group from another faculty
        extra_group_1 = StudentsGroupFactory(course=1, faculty=extra_faculty)
        # group from this faculty but the 2nd course
        extra_group_2 = StudentsGroupFactory(course=2, faculty=csc)

        # Math lesson, divided into 2 subgroups
        molodcov = TeacherFactory()
        denisov = TeacherFactory()
        math_1 = LessonFactory(teachers=[molodcov], subgroup="1",
                               name="M", lesson_format=1, students_group=group)
        math_2 = LessonFactory(teachers=[denisov], subgroup="2",
                               name="M", lesson_format=1, students_group=group)

        # Programming lesson, divided into 2 subgroups
        koval = TeacherFactory()
        kondratyuk = TeacherFactory()
        programming_1 = LessonFactory(teachers=[koval], subgroup="1",
                                      name="P", lesson_format=1, students_group=group)
        programming_2 = LessonFactory(teachers=[kondratyuk], subgroup="2",
                                      name="P", lesson_format=1, students_group=group)

        # Current user
        user = UserFactory(tg_id=(await client.get_me()).id, students_group=group)

        async with client.conversation("@{}".format(config.BOT_NAME), timeout=5) as conv:
            await conv.send_message("/change_group")

            # course choice
            r = await conv.get_response()
            kb = flatten_keyboard(r.buttons)
            assert "курс" in r.raw_text.lower()
            assert len(kb) == 2+1  # 1st and 2nd courses + END button
            await r.click(data=b"1")

            # faculty choice
            r = await conv.get_edit()
            kb = flatten_keyboard(r.buttons)
            assert "факультет" in r.raw_text.lower()
            assert len(kb) == 2+1  # csc and extra_faculty + END button
            # select "CSC"
            await r.click(data=str(csc.id).encode("utf-8"))

            # group choice
            r = await conv.get_edit()
            kb = flatten_keyboard(r.buttons)
            assert "груп" in r.raw_text.lower()
            assert len(kb) == 1+1  # ensure extra_groups are excluded from this list + END button
            # select group
            await r.click(data=str(group.id).encode("utf-8"))

            r = await conv.get_edit()
            assert r.text == "Групу встановлено!"

            # math subgroup choice
            r = await conv.get_response()
            kb = flatten_keyboard(r.buttons)
            assert "підгрупу з {name} ({format})".format(name=math_1.name, format=math_1.lesson_format) \
                   in r.raw_text
            assert kb[0].text == "[1] {teacher}".format(teacher=molodcov.short_name)
            assert kb[1].text == "[2] {teacher}".format(teacher=denisov.short_name)
            assert kb[2].data == b"-1"
            await kb[0].click()  # Select math_1

            # programming subgroup choice
            r = await conv.get_edit()
            kb = flatten_keyboard(r.buttons)
            assert "підгрупу з {name} ({format})".format(name=programming_1.name, format=programming_1.lesson_format) \
                   in r.raw_text
            assert kb[0].text == "[1] {teacher}".format(teacher=koval.short_name)
            assert kb[1].text == "[2] {teacher}".format(teacher=kondratyuk.short_name)
            assert kb[2].data == b"-1"
            await kb[0].click()  # Select programming_1

            r = await conv.get_edit()
            assert r.text == "Підгрупи визначено!"

            db_session.refresh(user)

            assert user.students_group == group

            subgroups = (
                db_session
                .query(LessonSubgroupMember.c.lesson_id, LessonSubgroupMember.c.user_id)
                .order_by(LessonSubgroupMember.c.lesson_id)
                .all()
            )
            assert len(subgroups) == 2  # math_1 and programming_1
            assert subgroups[0] == (math_1.id, user.tg_id)
            assert subgroups[1] == (programming_1.id, user.tg_id)

    @mark.asyncio
    async def test_end_button(self, client: TelegramClient, db_session, use_bot):
        """ Test END callback button works properly """
        group = StudentsGroupFactory(course=1)
        user = UserFactory(tg_id=(await client.get_me()).id, students_group=group)

        async with client.conversation("@{}".format(config.BOT_NAME), timeout=5) as conv:
            await conv.send_message("/change_group")
            r = await conv.get_response()
            kb = flatten_keyboard(r.buttons)
            await kb[-1].click()

            # Ensure user left the conversation and is able to send /change_group command once again
            await conv.send_message("/change_group")
            await conv.get_response()