import re

from app.bot.dictionaries import states
from app.bot.dictionaries.phrases import *
from app.bot.api import bot
from app.tests.factories import RequestFactory, StudentsGroupFactory, UserFactory

AcceptState = states.State("accept", "accept_{}", re.compile(r"^accept_(\d+)$"))
RejectState = states.State("reject", "reject_{}", re.compile(r"^reject_(\d+)$"))


class TestSendRequest:

    def test_send_request(self, db_session, mocker):
        from app.bot.commands.moderation import send_request
        group = StudentsGroupFactory()
        initiator = UserFactory(students_group=group)
        moderator = UserFactory(
            students_group=group,
            is_group_moderator=True,
        )
        db_session.commit()

        request = RequestFactory(initiator=initiator)

        send_message = mocker.patch.object(bot, "send_message")
        send_request(request, db_session, AcceptState, RejectState)

        # the first one is for moderator, the second is for initiator
        assert send_message.call_count == 2

        moderator_message = send_message.call_args_list[0]
        keyboard = moderator_message.kwargs["reply_markup"].inline_keyboard[0]
        assert moderator_message.args[0] == moderator.tg_id
        assert moderator_message.kwargs["text"] == request.message
        assert keyboard[0].text == f"{E_ACCEPT} Підтвердити"
        assert keyboard[0].callback_data == AcceptState.build(request.id)
        assert keyboard[1].text == f"{E_CANCEL} Відхилити"
        assert keyboard[1].callback_data == RejectState.build(request.id)

        initiator_message = send_message.call_args_list[1]
        assert initiator_message.args[0] == initiator.tg_id
        assert initiator_message.kwargs["text"] == \
               f"Запит #{request.id} надіслано до модератора групи!"

# TODO
# class TestLessonLinkRequest:
#
#     def test_accept(self, db_session):
#         from app.bot.commands.moderation import accept_link_request
