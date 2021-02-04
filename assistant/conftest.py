import os
import sys
import threading
import pytest
from pytest import mark
from functools import wraps
import mock
import importlib
import logging
from time import sleep
import datetime as dt
from typing import List, Tuple, Optional, Any

from sqlalchemy import orm
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session as SqaSession
from alembic.command import upgrade as alembic_upgrade
from alembic.config import Config as AlembicConfig
from telethon import TelegramClient
from telethon.sessions import StringSession

from assistant import config
from assistant.database import Session

logger = logging.getLogger(__name__)

# Your API ID, hash and session string here
API_ID = int(os.environ["TELEGRAM_APP_ID"])
API_HASH = os.environ["TELEGRAM_APP_HASH"]
TG_SESSION = os.environ["TELETHON_SESSION"]

session = Session()


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

    stop_event = threading.Event()

    def bot_thread():
        from assistant.bot.worker import run
        updater = run()
        # stop the bot on signal
        stop_event.wait()

        # A trick to speed up updater.stop (9s vs 1ms)
        # Job queue and httpd, which can break further tests, are stopped in blocking mode,
        # but other parts would be terminated in a separate daemon.
        updater.job_queue.stop()
        updater._stop_httpd()
        stop_thread = threading.Thread(target=updater.stop, daemon=True)
        stop_thread.start()

    thread = threading.Thread(target=bot_thread)
    thread.start()

    yield

    stop_event.set()
    db_session_mock.stop()
    importlib.invalidate_caches()
    reload_db_session_decorator()

    while thread.is_alive():
        sleep(0.01)


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
    alembic_config = AlembicConfig("migrations/alembic.ini")
    # Run alembic migrations
    alembic_upgrade(alembic_config, "head")

    yield


@pytest.fixture(scope="function", autouse=True)
def db_session(db) -> SqaSession:
    session.begin_nested()  # Savepoint

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        """ Each time that SAVEPOINT ends, reopen it """
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()

    yield session
    
    session.rollback()
    session.close()
    event.remove(session, "after_transaction_end", restart_savepoint)
