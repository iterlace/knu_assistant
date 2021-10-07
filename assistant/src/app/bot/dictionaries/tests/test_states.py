import re

from app.bot.dictionaries import states


class TestState:

    def test_new(self):
        name = "test"
        build_pattern = "test_{}"
        parse_pattern = re.compile(r"^test_(\d)$")

        state = states.State(name, build_pattern, parse_pattern)
        assert state == name
        assert state.parse_pattern == parse_pattern
        assert state.build_pattern == build_pattern
        assert isinstance(state, str)
