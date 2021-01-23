
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
from .dictionaries import states

logger = logging.getLogger(__name__)


def run():
    updater = Updater(config.BOT_TOKEN, workers=config.BOT_WORKERS)
    dp = updater.dispatcher

    dp.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("start", commands.start)],
            states={
                states.UserSelectStudentsGroupStep: [
                    CallbackQueryHandler(commands.select_students_group)
                ],
            },
            fallbacks=[CommandHandler("start", commands.start)]
        ),
    )
    dp.add_handler(CommandHandler("help", commands.help))

    # Managing user's group
    dp.add_handler(CommandHandler("change_group", commands.select_students_group))
    dp.add_handler(CallbackQueryHandler(
        commands.select_students_group,
        pattern=states.UserSelectStudentsGroupStep.parse_pattern,
    ))

    # Managing group's timetable
    dp.add_handler(CommandHandler("show_timetable", commands.show_timetable))
    dp.add_handler(CommandHandler("edit_timetable", commands.edit_timetable))
    dp.add_handler(CallbackQueryHandler(
        commands.edit_timetable_callback,
        pattern=states.EditTimetable.parse_pattern,
    ))
    dp.add_handler(CallbackQueryHandler(
        commands.edit_timetable_day_callback,
        pattern=states.EditTimetableDay.parse_pattern,
    ))
    # Edit a day of a timetable
    dp.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(
                commands.add_lesson_callback,
                pattern=states.AddLessonToTimetable.parse_pattern,
            )],
            states={
                "read_lesson": [
                    # cancel button
                    CallbackQueryHandler(
                        commands.cancel_add_lesson_callback,
                        pattern=states.CancelAddLessonToTimetable.parse_pattern,
                        pass_user_data=True,
                    ),
                    # response handler
                    CallbackQueryHandler(
                        commands.add_lesson_lesson_callback,
                        pass_user_data=True,
                    ),
                ],
                "read_lesson_type": [
                    # cancel button
                    CallbackQueryHandler(
                        commands.cancel_add_lesson_callback,
                        pattern=states.CancelAddLessonToTimetable.parse_pattern,
                        pass_user_data=True,
                    ),
                    # response handler
                    CallbackQueryHandler(
                        commands.add_lesson_lesson_type_callback,
                        pass_user_data=True,
                    ),
                ],
                "read_teacher": [
                    # cancel button
                    CallbackQueryHandler(
                        commands.cancel_add_lesson_callback,
                        pattern=states.CancelAddLessonToTimetable.parse_pattern,
                        pass_user_data=True,
                    ),
                    # response handler
                    CallbackQueryHandler(
                        commands.add_lesson_teacher_callback,
                        pass_user_data=True,
                    )
                ],
                "read_time": [
                    # cancel button
                    CallbackQueryHandler(
                        commands.cancel_add_lesson_callback,
                        pattern=states.CancelAddLessonToTimetable.parse_pattern,
                        pass_user_data=True,
                    ),
                    # response handler
                    MessageHandler(
                        Filters.text,
                        commands.add_lesson_time,
                        pass_user_data=True,
                    ),
                ],
            },
            fallbacks=[CallbackQueryHandler(
                commands.cancel_add_lesson_callback,
                pattern=states.CancelAddLessonToTimetable.parse_pattern,
                pass_user_data=True,
            )],
            allow_reentry=True,
        ),
    )

    updater.start_polling()

    try:
        # Bot gracefully stops on SIGINT, SIGTERM or SIGABRT.
        updater.idle()
    except ValueError as e:
        if "signal only works in main thread" in str(e):
            logger.warning(e)
        else:
            raise e
    return


if __name__ == '__main__':
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.DEBUG if config.DEBUG else logging.INFO,
    )
    run()
