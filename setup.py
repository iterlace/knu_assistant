from setuptools import setup
from setuptools import find_packages
import pkg_resources
from assistant import __version__

setup(
    name="KNU Assistant",
    version=__version__,
    packages=find_packages(exclude=["*tests*"]),
    package_data={"migrations": ["alembic.ini"]},
    url="",
    license="Apache License",
    author="iterlace",
    author_email="iterlace@gmail.com",
    description="",
    python_requires="~=3.8",
    install_requires=[
        "python-telegram-bot==13.0",
        "SQLAlchemy==1.3.20",
        "alembic==1.4.3",
        "environs==9.2.0",
        "urllib3==1.26.2",
        "requests==2.25.0",
        "aiohttp==3.7.3",
        "urllib3==1.26.2",
        "psycopg2==2.8.6"
    ],
    setup_requires=[
        "pytest-runner",
        "flake8",
    ],
    tests_require=[
        "pytest",
        "mock==4.0.3",
        "pytest-asyncio==0.14.0",
        "telethon==1.17.5",
        "factory_boy==3.2.0",
        "pytest-mock==3.5.1",
    ],
    entry_points={
        "console_scripts": [
            "knu_assistant_run_bot=assistant.bot.worker:run",
            "knu_assistant_apply_migrations=migrations.apply:run",
        ]
    }
)
