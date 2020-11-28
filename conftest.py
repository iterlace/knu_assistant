import os

import pytest
from pytest import mark

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic.command import upgrade as alembic_upgrade
from alembic.config import Config as AlembicConfig
from telethon import TelegramClient
from telethon.sessions import StringSession, MemorySession

from knu_helper_bot import config

# Your API ID, hash and session string here
api_id = int(os.environ["TELEGRAM_APP_ID"])
api_hash = os.environ["TELEGRAM_APP_HASH"]
session = os.environ["TELETHON_SESSION"]
updater = None


def pytest_sessionstart(session):
    from knu_helper_bot.main import main
    global updater
    # FIXME
    updater = main(blocking=False)


def pytest_sessionfinish(session, exitstatus):
    updater.stop()


@pytest.fixture()
@mark.asyncio
async def client() -> TelegramClient:
    client = TelegramClient(
        StringSession(session), api_id, api_hash,
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
def db(request):
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
def db_session(request, db):
    session = db["session_factory"]()
    yield session
    session.rollback()
    session.close()

