import re
import enum

from telegram.ext import ConversationHandler


class State(str):
    parse_pattern = None
    build_pattern = None

    def __new__(cls, name, build_pattern: str = None, parse_pattern: re.Pattern = None):
        """
        User's current state.
        Can be used to remember last step, build and parse callbacks.
        :param name: state title
        :param build_pattern: string, containing placeholders ("{}") to build callback value
        :param parse_pattern: compiled regular expression, designed to match & release callback data
        """
        obj = super().__new__(cls, name)

        if parse_pattern is not None:
            obj.parse_pattern = parse_pattern

        if build_pattern is not None:
            obj.build_pattern = build_pattern

        return obj

    def build(self, *args, **kwargs):
        return self.build_pattern.format(*args, **kwargs)


EmptyStep = State('')

# User selects their course
UserSelectCourse = State("select_student_course",
                         "{}",
                         re.compile(r"^(\d+)$"))

# User selects their faculty
UserSelectFaculty = State("select_student_faculty",
                          "{}",
                          re.compile(r"^(\d+)$"))

# User selects their group
UserSelectGroup = State("select_student_group",
                        "{}",
                        re.compile(r"^(\d+)$"))


# User selects their subgroups
UserSelectSubgroups = State("select_subgroups",
                            "{}",
                            re.compile(r"^(\w+)$"))


TimetableWeekSelection = State("timetable_week_selection",
                               "tt_week_selection_{}",
                               re.compile(r"^tt_week_selection_(\d{4}-\d{2}-\d{2})$"))


TimetableDaySelection = State("timetable_day_selection",
                              "tt_day_selection_{}",
                              re.compile(r"^tt_day_selection_(\d{4}-\d{2}-\d{2})$"))


# ========= Moderation Requests =========

# Change Lesson link
LinkWait = State("link_wait",
                 "{}",
                 re.compile(r"^.*$"))

ModeratorAcceptLink = State("moderator_accept_lesson_link",
                            "moderator_accept_lesson_link_{}",
                            re.compile(r"^moderator_accept_lesson_link_(\d+)$"))
ModeratorRejectLink = State("moderator_reject_lesson_link",
                            "moderator_reject_lesson_link_{}",
                            re.compile(r"^moderator_reject_lesson_link_(\d+)$"))

END = ConversationHandler.END

