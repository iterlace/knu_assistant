import mock
from assistant.bot.dictionaries import states


class TestEnd:

    def test_end(self):
        from assistant.bot.commands.utils import end
        update = mock.MagicMock()
        ctx = mock.MagicMock()
        result = end(update=update, ctx=ctx)
        assert ctx.user_data.clear.call_count == 1
        assert result == states.END
