import logging

from telegram.ext import (
    Updater,
    Filters,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
)

from assistant import config
from assistant.bot import commands
from assistant.bot.dictionaries import states

logger = logging.getLogger(__name__)


def run():
    updater = Updater(config.BOT_TOKEN, workers=config.BOT_WORKERS)
    dp = updater.dispatcher

    # /change_group
    select_group_handler = ConversationHandler(
        entry_points=[CommandHandler("change_group", commands.change_group)],
        states={
            states.UserSelectCourse: [CallbackQueryHandler(commands.select_course,
                                                           pattern=states.UserSelectCourse.parse_pattern)],
            states.UserSelectFaculty: [CallbackQueryHandler(commands.select_faculty,
                                                            pattern=states.UserSelectFaculty.parse_pattern)],
            states.UserSelectGroup: [CallbackQueryHandler(commands.select_group,
                                                          pattern=states.UserSelectGroup.parse_pattern)],
            states.UserSelectSubgroups: [CallbackQueryHandler(commands.select_subgroups,
                                                              pattern=states.UserSelectSubgroups.parse_pattern)]
        },
        fallbacks=[
            CallbackQueryHandler(commands.home, pattern=r"^{}$".format(states.END))
        ]
    )
    dp.add_handler(select_group_handler)

    # /start
    start_handler = ConversationHandler(
        entry_points=[CommandHandler("start", commands.start)],
        states=select_group_handler.states,
        fallbacks=[],
    )
    dp.add_handler(start_handler)

    # /help
    dp.add_handler(CommandHandler("help", commands.help))

    # /week
    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler("week", commands.show_week_timetable)],
        states={
            states.TimetableWeekSelection: [CallbackQueryHandler(commands.show_week_timetable,
                                                                 pattern=states.TimetableWeekSelection.parse_pattern)],
        },
        fallbacks=[]
    ))

    updater.start_polling()

    try:
        # Bot gracefully stops on SIGINT, SIGTERM or SIGABRT.
        updater.idle()
    except ValueError as e:
        if "signal only works in main thread" in str(e):
            print(e)
        else:
            raise e
    return


if __name__ == '__main__':
    # logging.basicConfig(
    #     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    #     level=logging.DEBUG if config.DEBUG else logging.INFO,
    # )
    run()
