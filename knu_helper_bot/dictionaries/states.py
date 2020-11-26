import re


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


EmptyStep = State('')

# User selects his own group
# 1 argument: group id
UserSelectStudentsGroupStep = State("user_select_students_group",
                                    "user_select_students_group_{}",
                                    re.compile(r"^user_select_students_group_(.*)$"))

# Administrator edits a whole timetable
EditTimetable = State("edit_timetable",
                      "edit_timetable",
                      re.compile(r"^edit_timetable$"))
# Administrator edits a day in a timetable
# 1 argument: day idx
EditTimetableDay = State("edit_timetable_day",
                         "edit_timetable_day_{}",
                         re.compile(r"^edit_timetable_day_(\d)$"))
# Administrator edits a day in a timetable
# 1 argument: day idx
AddLessonToTimetable = State("edit_timetable_day_add_lesson",
                             "edit_timetable_day_{}_add_lesson",
                             re.compile(r"^edit_timetable_day_(\d)_add_lesson$"))
