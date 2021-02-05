import datetime as dt
import mock
from pytest import mark

from telethon import TelegramClient
from telethon.tl.custom.message import Message
from sqlalchemy.orm import sessionmaker

from assistant import config
from assistant.database import User
from assistant.database import Session

from assistant.tests.factories import (
    FacultyFactory,
    LessonFactory,
    TeacherFactory,
    SingleLessonFactory,
    UserFactory,
    StudentsGroupFactory,
)


class TestDbSession:

    def test_db_session(self):
        from assistant.bot.decorators import db_session

        @db_session
        def func(session):
            assert session is not None

        with mock.patch.object(sessionmaker, "__call__") as session_mock:
            func()
            assert session_mock.call_count == 1

    def test_already_passed_session(self):
        from assistant.bot.decorators import db_session

        @db_session
        def func(session):
            assert session is not None

        s = Session()

        with mock.patch.object(sessionmaker, "__call__") as session_mock:
            func(session=s)
            assert session_mock.call_count == 0


class TestAcquireUser:

    def test_non_existent_user(self, db_session):
        from assistant.bot.decorators import acquire_user

        @acquire_user
        def handler(update, session, user):
            assert user.tg_id == 10000000
            assert user.tg_username == "john"

        update = mock.Mock()
        update.effective_user = mock.Mock()
        update.effective_user.id = 10000000
        update.effective_user.username = "john"

        with mock.patch.object(db_session, "add") as session_add_mock:
            handler(update=update, session=db_session)
            assert session_add_mock.call_count == 1

    def test_already_passed_user(self, db_session):
        """ Test if user argument is already passed to the function """
        from assistant.bot.decorators import acquire_user

        update = mock.Mock()
        user_ = UserFactory()

        @acquire_user
        def handler(update, session, user):
            assert user == user_

        handler(update=update, session=db_session, user=user_)

    def test_updated_username(self, db_session):
        """ Test if actual username and database username differs, acquire_user updates it """
        from assistant.bot.decorators import acquire_user

        update = mock.Mock()
        update.effective_user = mock.Mock()
        update.effective_user.id = 10000000
        update.effective_user.username = "john"
        user_ = UserFactory(
            tg_id=update.effective_user.id,
            tg_username="michael",
        )

        @acquire_user
        def handler(update, session, user):
            assert user.tg_username == "john"

        with mock.patch.object(db_session, "add") as session_add_mock:
            handler(update=update, session=db_session)
            assert session_add_mock.call_count == 0


class TestModeratorsOnly:

    def test_moderator(self):
        from assistant.bot.decorators import moderators_only

        user_ = UserFactory(is_group_moderator=True)

        @moderators_only
        def handler(user):
            return 1

        assert handler(user=user_) == 1

    def test_not_moderator(self):
        from assistant.bot.decorators import moderators_only

        user_ = UserFactory(is_group_moderator=False)

        @moderators_only
        def handler(user):
            return 1

        assert handler(user=user_) is None


class TestAdminsOnly:

    def test_admin(self):
        from assistant.bot.decorators import admins_only

        user_ = UserFactory(is_admin=True)

        @admins_only
        def handler(user):
            return 1

        assert handler(user=user_) == 1

    def test_not_admin(self):
        from assistant.bot.decorators import admins_only

        user_ = UserFactory(is_admin=False)

        @admins_only
        def handler(user):
            return 1

        assert handler(user=user_) is None


