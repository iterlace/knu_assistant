import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

import pytest

from app.database import Faculty, Lesson, SingleLesson, StudentsGroup, Teacher
from app.timetable_scrapper.worker import TimetableScrapper


@dataclass
class FakeResponse:
    """ Pseudo requests.Response class """
    status_code: int
    body: Optional[Union[Dict, List]] = None
    body_str: Optional[str] = None

    def json(self):
        if self.body is not None:
            return self.body
        elif self.body_str is not None:
            return json.loads(self.body_str)
        else:
            raise ValueError("neither body nor body_str is set!")

    @property
    def content(self):
        if self.body is not None:
            return json.dumps(self.body)
        elif self.body_str is not None:
            return self.body_str
        else:
            raise ValueError("neither body nor body_str is set!")


URL = str
ResponsesMapping = List[Tuple[URL, FakeResponse]]


@pytest.fixture(scope="function")
def scrapper(db_session):
    return TimetableScrapper(db_session=db_session)


class TestTimetableScrapper:

    def get(self, mapping: ResponsesMapping):
        mapping = dict(mapping)

        def _get(url):
            return mapping[url]

        return _get

    @pytest.mark.parametrize(
        "mapping,result",
        [
            # Simple single-page case
            (
                [("0", FakeResponse(status_code=200, body={"next": None, "results": []}))],
                {"next": None, "results": []}
            ),
            # Multi-page different keys merge
            (
                [
                    ("0", FakeResponse(status_code=200, body={"next": "1", "results": []})),
                    ("1", FakeResponse(status_code=200, body={"next": None, "answers": [1, 2]})),
                ],
                {"next": "1", "results": [], "answers": [1, 2]}
            ),
            # Multi-page lists join
            (
                [
                    ("0", FakeResponse(status_code=200,
                                       body={"next": "1", "results": [{"id": 1}]})),
                    ("1", FakeResponse(status_code=200,
                                       body={"next": None, "results": [{"id": 2}]})),
                ],
                {"next": "1", "results": [{"id": 1}, {"id": 2}]}
            ),
            # Multi-page equivalent lists join
            (
                [
                    ("0", FakeResponse(status_code=200,
                                       body={"next": "1", "enum": [{"monday": 1}]})),
                    ("1", FakeResponse(status_code=200,
                                       body={"next": None, "enum": [{"monday": 1}]})),
                ],
                {"next": "1", "enum": [{"monday": 1}]}
            ),
            # Multi-page dicts join
            (
                [
                    ("0", FakeResponse(status_code=200, body={"next": "1", "keywords": {"o": 1}})),
                    ("1", FakeResponse(status_code=200, body={"next": None, "keywords": {"t": 2}})),
                ],
                {"next": "1", "keywords": {"o": 1, "t": 2}}
            ),
            # Multi-page equivalent dicts join
            (
                [
                    ("0", FakeResponse(status_code=200,
                                       body={"next": "1", "enum": {"monday": 1}})),
                    ("1", FakeResponse(status_code=200,
                                       body={"next": None, "enum": {"monday": 1}})),
                ],
                {"next": "1", "enum": {"monday": 1}}
            ),
        ]
    )
    def test_get_join(self, mapping: ResponsesMapping, result: Union[Dict, List], db_session,
                      scrapper, mocker):
        mocker.patch.object(scrapper.session, "get", self.get(mapping))
        got = scrapper.get(mapping[0][0])
        assert got == result

    def test_get_http_error(self, db_session, scrapper, mocker):
        mocker.patch.object(scrapper.session, "get",
                            lambda _: FakeResponse(status_code=400, body={"error": "test"}))
        got = scrapper.get("0")
        assert got is None

    def test_get_json_error(self, db_session, scrapper, mocker):
        mocker.patch.object(scrapper.session, "get",
                            lambda _: FakeResponse(status_code=400, body_str="(invalid json)"))
        got = scrapper.get("0")
        assert got is None

    def test_run(self, scrapper, db_session, mocker):
        routing = [
            ("https://api.mytimetable.live/rest/groups/?univ=1",
             FakeResponse(status_code=200, body={
                 "next": None,
                 "results": [
                     {
                         "name": "К-14",
                         "short_name": "К-14",
                         "slug": "K-14",
                         "course_name": "1",
                         "course_degree": "0",
                     },
                 ]
             })),
            ("https://api.mytimetable.live/rest/timetable/?group=K-14",
             FakeResponse(status_code=200, body={
                 "show_numbers": True,
                 "lessons": [
                     {
                         "name_full": "Програмування",
                         "name_short": "Прог",
                         "housing": None,
                         "room": None,
                         "conduct_type": "online",
                         "link": "",
                         "lesson_time": 1,
                         "format": 3,
                         "subgroup": "1",
                         "teachers": [
                             {
                                 "full_name": "Коваль Юрій Віталійович",
                                 "short_name": "Коваль Ю.В.",
                                 "degree": 2,
                                 "slug": "Koval-UV"
                             }
                         ],
                         "dates": [
                             "2021-01-29",
                             "2021-02-05",
                         ],
                         "faculty": {
                             "name": "Комп'ютерних наук та кібернетики",
                             "short_name": "КНК",
                             "slug": "CSC"
                         }
                     },
                     {
                         "name_full": "Програмування",
                         "name_short": "Прог",
                         "housing": None,
                         "room": None,
                         "conduct_type": "online",
                         "link": "",
                         "lesson_time": 3,
                         "format": 0,
                         "subgroup": "",
                         "teachers": [
                             {
                                 "full_name": "Ставровський Андрій Борисович",
                                 "short_name": "Ставровський А.Б.",
                                 "degree": 2,
                                 "slug": "Stavrovskii-AB"
                             }
                         ],
                         "dates": [
                             "2021-01-26",
                             "2021-02-02",
                         ],
                         "faculty": {
                             "name": "Комп'ютерних наук та кібернетики",
                             "short_name": "КНК",
                             "slug": "CSC"
                         }
                     },
                 ],
                 "lesson_time": [
                     {"id": 1, "start": "08:40", "end": "10:15"},
                     {"id": 2, "start": "10:35", "end": "12:10"},
                     {"id": 3, "start": "12:20", "end": "13:55"},
                     {"id": 4, "start": "14:05", "end": "15:40"},
                 ],
                 "periods": [
                     {"id": 104, "start": "2021-01-25", "end": "2021-06-06", "kind": 0},
                     {"id": 105, "start": "2021-06-07", "end": "2021-06-30", "kind": 3},
                 ],
             })),
        ]
        mocker.patch.object(scrapper.session, "get", self.get(routing))
        scrapper.run()

        assert db_session.query(Faculty).count() == 1
        assert db_session.query(StudentsGroup).count() == 1
        assert db_session.query(Teacher).count() == 2
        assert db_session.query(Lesson).count() == 2
        assert db_session.query(SingleLesson).count() == 4  # each lesson contains 2 entries

        lesson: Lesson = db_session.query(Lesson).first()
        assert lesson.name == "Програмування"
        assert lesson.lesson_format == 3
        assert lesson.subgroup == "1"

        group = lesson.students_group
        assert group.name == "К-14"
        assert group.course == 1

        teacher = lesson.teachers[0]
        assert teacher.first_name == "Юрій"
        assert teacher.last_name == "Коваль"
        assert teacher.middle_name == "Віталійович"

        # TODO: test dates and lesson start/end time
