
import logging

from telegram.ext import (
    Updater,
    CommandHandler,
)

import config
import commands

logger = logging.getLogger(__name__)


def main():
    updater = Updater(config.BOT_TOKEN, workers=config.BOT_WORKERS)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", commands.start))
    dp.add_handler(CommandHandler("help", commands.help))

    updater.start_polling()

    # Bot gracefully stops on SIGINT, SIGTERM or SIGABRT.
    updater.idle()


if __name__ == '__main__':
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.DEBUG if config.DEBUG else logging.INFO,
    )
    main()
