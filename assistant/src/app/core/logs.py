import logging  # noqa
import logging.config  # noqa

from app.core.config import settings

__all__ = []


logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": True,
        "loggers": {
            "app": {
                "handlers": ["console"],
                "level": "INFO",
            },
            "__main__": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "": {
                "handlers": ["console"],
                "level": "INFO",
            },
        },
        "handlers": {
            "console": {
                "formatter": "std_out",
                "class": "logging.StreamHandler",
                "level": "DEBUG",
            }
        },
        "formatters": {
            "std_out": {
                "format": "%(asctime)s : %(levelname)s "
                "[%(name)s.%(funcName)s:%(lineno)s]: %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            }
        },
    }
)


if settings.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.pure_eval import PureEvalIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    sentry_sdk.init(
        settings.SENTRY_DSN,
        integrations=[
            RedisIntegration(),
            SqlalchemyIntegration(),
            CeleryIntegration(),
            PureEvalIntegration(),
        ],
    )
