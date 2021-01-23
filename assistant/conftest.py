import os
import threading
import pytest
from pytest import mark
from functools import wraps
import mock
import importlib
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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
            # print("mock_db_session called for {}".format(func))
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
def db_session(db):
    session = db["session_factory"]()
    session.begin_nested()  # Savepoint
    yield session
    session.rollback()
    session.close()

