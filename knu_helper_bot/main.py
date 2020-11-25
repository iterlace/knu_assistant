
import logging

from telegram.ext import (
    Updater,
    Filters,
    CommandHandler,
    CallbackQueryHandler,
)

from knu_helper_bot import config, commands, states

logger = logging.getLogger(__name__)


def main():
    updater = Updater(config.BOT_TOKEN, workers=config.BOT_WORKERS)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", commands.start))
    dp.add_handler(CommandHandler("help", commands.help))
    dp.add_handler(CommandHandler("change_group", commands.select_students_group))

    dp.add_handler(CallbackQueryHandler(
        commands.select_students_group,
        states.UserSelectStudentsGroupStep.parse_pattern,
    ))

    updater.start_polling()

    # Bot gracefully stops on SIGINT, SIGTERM or SIGABRT.
    updater.idle()


if __name__ == '__main__':
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.DEBUG if config.DEBUG else logging.INFO,
    )
    main()
