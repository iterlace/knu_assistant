from logging.config import dictConfig

import sentry_sdk
from telegram import Bot
from environs import Env


env = Env()
# Read .env into os.environ
env.read_env(".env")

DEBUG = env.bool("DEBUG")
BOT_TOKEN = env.str("BOT_TOKEN")
BOT_NAME = env.str("BOT_NAME")
BOT_WORKERS = env.int("BOT_WORKERS")

DB_HOST = env.str("DB_HOST")
DB_PORT = env.int("DB_PORT")
DB_NAME = env.str("DB_NAME")
DB_USERNAME = env.str("DB_USERNAME")
DB_PASSWORD = env.str("DB_PASSWORD")
DB_STRING = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}".format(
    user=DB_USERNAME,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    name=DB_NAME,
)

bot = Bot(token=BOT_TOKEN)

dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - [%(levelname)s] %(name)s [%(module)s.%(funcName)s:%(lineno)d]: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "default": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": "DEBUG",
            "propagate": False,
        },
        "assistant": {
            "handlers": ["default"],
            "level": "DEBUG",
            "propagate": False,
        },
        "__main__": {  # if __name__ == "__main__"
            "handlers": ["default"],
            "level": "DEBUG",
            "propagate": False,
        },
        # "telegram": {
        #     "handler": ["default"],
        #     "level": "ERROR",
        #     "propagate": False,
        # },
    },
    "root": {
        "level": "WARNING",
        "handlers": ["default"],
    },
})

try:
    SENTRY_DSN = env.str("SENTRY_DSN")
except Exception as e:
    # TODO
    pass
else:
    sentry_sdk.init(
        SENTRY_DSN,
        traces_sample_rate=1.0
    )