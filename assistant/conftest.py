import os
import sys
import threading
import pytest
from pytest import mark
from functools import wraps
import mock
import importlib
import logging
from typing import List, Tuple, Optional, Any

from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session as SqaSession
from alembic.command import upgrade as alembic_upgrade
from alembic.config import Config as AlembicConfig
from telethon import TelegramClient
from telethon.sessions import StringSession

from assistant import config

logger = logging.getLogger(__name__)

# Your API ID, hash and session string here
API_ID = int(os.environ["TELEGRAM_APP_ID"])
API_HASH = os.environ["TELEGRAM_APP_HASH"]
TG_SESSION = os.environ["TELETHON_SESSION"]


def pytest_configure(config):
    sys._called_from_test = True


def pytest_unconfigure(config):
    del sys._called_from_test


def reload_db_session_decorator():
    import assistant
    importlib.reload(assistant.bot.commands.basic)
    importlib.reload(assistant.bot.commands.timetable)
    importlib.reload(assistant.bot.commands.user)
    importlib.reload(assistant.bot.commands)


@pytest.fixture(scope="function")
def use_bot(db_session):
    """ Runs a telegram bot, which uses db session from the fixture """

    # Mock assistant.bot.decorators.db_session to be able to rollback the session after test completed
    def mock_db_session(func):
        """ Pushes session, controlled by the fixture """
        @wraps(func)
        def inner(*args, **kwargs):
            kwargs["session"] = db_session
            return func(*args, **kwargs)
        return inner

    db_session_mock = mock.patch("assistant.bot.decorators.db_session", mock_db_session)
    db_session_mock.start()
    reload_db_session_decorator()

    # Start the bot in a separate thread
    from assistant.bot.worker import run
    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()

    yield

    db_session_mock.stop()
    importlib.invalidate_caches()
    reload_db_session_decorator()


@pytest.fixture()
@mark.asyncio
async def client() -> TelegramClient:
    client = TelegramClient(
        StringSession(TG_SESSION), API_ID, API_HASH,
        sequential_updates=True,
    )

    # Connect to the server
    await client.connect()
    # Issue a high level command to start receiving message
    await client.get_me()
    # Fill the entity cache
    await client.get_dialogs()

    yield client

    await client.disconnect()
    await client.disconnected


@pytest.fixture(scope="session")
def db():
    engine = create_engine(config.DB_STRING, echo=True)
    session_factory = sessionmaker(bind=engine)

    _db = {
        "engine": engine,
        "session_factory": session_factory,
    }
    alembic_config = AlembicConfig("migrations/alembic.ini")
    # Run alembic migrations
    alembic_upgrade(alembic_config, "head")

    yield _db
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db) -> SqaSession:
    session = db["session_factory"]()
    session.begin_nested()  # Savepoint

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        """ Each time that SAVEPOINT ends, reopen it """
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()

    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def fill_teachers(db_session):
    from assistant.database import Teacher

    peterson = Teacher(first_name="Bob", middle_name="Fitzgerald", last_name="Peterson")
    smith = Teacher(first_name="Mary", middle_name="Elizabeth", last_name="Smith")

    db_session.add(peterson)
    db_session.add(smith)
    db_session.commit()

    yield [peterson, smith]


@pytest.fixture(scope="function")
def fill_faculties(db_session):
    from assistant.database import Faculty

    csc = Faculty(name="Computer Science and Cybernetics", shortcut="CSC")

    db_session.add(csc)
    db_session.commit()

    yield [csc]


@pytest.fixture(scope="function")
def fill_groups(db_session, fill_faculties):
    from assistant.database import StudentsGroup

    K11 = StudentsGroup(name="K-11", course=1, faculty=fill_faculties[0])
    K12 = StudentsGroup(name="K-12", course=1, faculty=fill_faculties[0])

    db_session.add(K11)
    db_session.add(K12)
    db_session.commit()

    yield [K11, K12]


@pytest.fixture(scope="function")
def fill_users(db_session, fill_groups):
    from assistant.database import User

    mike = User(tg_id=800000000, tg_username="mike", students_group=fill_groups[0])
    george = User(tg_id=800000001, tg_username="george", students_group=fill_groups[0])
    jane = User(tg_id=800000002, tg_username="jane", students_group=fill_groups[1])

    db_session.add(mike)
    db_session.add(george)
    db_session.add(jane)
    db_session.commit()

    yield [mike, george, jane]


@pytest.fixture(scope="function")
def fill_lessons(db_session, fill_teachers, fill_groups):
    from assistant.database import Lesson, Teacher

    algebra_lecture = Lesson(
        name="Algebra",
        students_group=fill_groups[0],
        subgroup=None,
        lesson_format=0,
        teachers=[fill_teachers[0]],
    )
    algebra_practice_1 = Lesson(
        name="Algebra",
        students_group=fill_groups[0],
        subgroup="1",
        lesson_format=2,
        teachers=[fill_teachers[0]],
    )
    algebra_practice_2 = Lesson(
        name="Algebra",
        students_group=fill_groups[0],
        subgroup="2",
        lesson_format=2,
        teachers=[fill_teachers[1]],
    )

    db_session.add(algebra_lecture)
    db_session.add(algebra_practice_1)
    db_session.add(algebra_practice_2)
    db_session.commit()

    yield [algebra_lecture, algebra_practice_1, algebra_practice_2]


# @pytest.fixture(scope="function")
# def fill_single_lessons(db_session, fill_lessons):
#     from assistant.database import SingleLesson, Lesson
#     # TODO

