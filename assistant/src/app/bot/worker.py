import logging

from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    Updater,
)

from app.core.config import settings
from app.bot import commands
from app.bot.dictionaries import states

logger = logging.getLogger(__name__)


def run():
    updater = Updater(settings.TELEGRAM_BOT_TOKEN, workers=settings.TELEGRAM_BOT_WORKERS)
    dispatcher = updater.dispatcher

    # /change_group
    select_group_handler = ConversationHandler(
        entry_points=[CommandHandler("change_group", commands.change_group)],
        states={
            states.UserSelectCourse: [
                CallbackQueryHandler(commands.select_course,
                                     pattern=states.UserSelectCourse.parse_pattern)],
            states.UserSelectFaculty: [
                CallbackQueryHandler(commands.select_faculty,
                                     pattern=states.UserSelectFaculty.parse_pattern)],
            states.UserSelectGroup: [
                CallbackQueryHandler(commands.select_group,
                                     pattern=states.UserSelectGroup.parse_pattern)],
            states.UserSelectSubgroups: [
                CallbackQueryHandler(commands.select_subgroups,
                                     pattern=states.UserSelectSubgroups.parse_pattern)]
        },
        fallbacks=[
            CallbackQueryHandler(commands.end_callback, pattern=r"^{}$".format(states.END)),
        ],
    )
    dispatcher.add_handler(select_group_handler)

    # /start
    start_handler = ConversationHandler(
        entry_points=[CommandHandler("start", commands.start)],
        states=select_group_handler.states,
        fallbacks=[],
    )
    dispatcher.add_handler(start_handler)

    # /help
    dispatcher.add_handler(CommandHandler("help", commands.help))

    # /day
    dispatcher.add_handler(ConversationHandler(
        entry_points=[CommandHandler("day", commands.show_day_timetable)],
        states={
            states.TimetableDaySelection: [
                CallbackQueryHandler(commands.show_day_timetable,
                                     pattern=states.TimetableDaySelection.parse_pattern)],
        },
        fallbacks=[],
        allow_reentry=True,
    ))

    # /week
    dispatcher.add_handler(ConversationHandler(
        entry_points=[CommandHandler("week", commands.show_week_timetable)],
        states={
            states.TimetableWeekSelection: [
                CallbackQueryHandler(commands.show_week_timetable,
                                     pattern=states.TimetableWeekSelection.parse_pattern)],
        },
        fallbacks=[],
        allow_reentry=True,
    ))

    # /link@lesson_id
    dispatcher.add_handler(ConversationHandler(
        entry_points=[MessageHandler(Filters.text & Filters.regex(r"/link@(\d+)"), commands.link)],
        states={
            states.LinkWait: [MessageHandler(Filters.text, commands.set_lesson_link)],
        },
        fallbacks=[
            CallbackQueryHandler(commands.end_callback, pattern=r"^{}$".format(states.END)),
        ],
    ))

    # ======== Moderation ========
    # Lesson link change
    dispatcher.add_handler(CallbackQueryHandler(commands.accept_link_request,
                                                pattern=states.ModeratorAcceptLink.parse_pattern))
    dispatcher.add_handler(CallbackQueryHandler(commands.reject_link_request,
                                                pattern=states.ModeratorRejectLink.parse_pattern))

    updater.start_polling()

    try:
        # Bot gracefully stops on SIGINT, SIGTERM or SIGABRT.
        updater.idle()
    except ValueError as e:
        if "signal only works in main thread" in str(e):
            print(e)
        else:
            raise e
    return updater


if __name__ == '__main__':
    run()
