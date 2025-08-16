from collections.abc import Callable, Iterable
from typing import Any, Literal, overload

import requests

from ..singleton import singleton_by_field_meta


class Course(metaclass=singleton_by_field_meta("id")):
    def __init__(self, data: dict[str, Any]):
        self.id: int = data["id"]
        self.name: str = data["nameZh"]
        self.code: str = data["code"]

    def __repr__(self):
        return f"<Course {self.code} {self.name}>"


class Lesson(metaclass=singleton_by_field_meta("id")):
    def __init__(self, data: dict[str, Any]):
        self.course = Course(data["course"])
        self.id: int = data["id"]
        self.code: str = data["code"]
        self.limit: int = data["limitCount"]
        self.unit: str = data["unitText"]["text"]
        self.week: str = data["weekText"]["text"]
        self.weekday: str = data["weekDayPlaceText"]["text"]
        self.pinned: bool = data.get("pinned", False)
        self.teachers: list[str] = [i["nameZh"] for i in data["teachers"]]

    def __repr__(self):
        return f"<Lesson {self.course.name}-{self.code}{(' Pinned' if self.pinned else '')}>"


class AddDropResponse:
    type: str
    success: bool
    error: str | None

    def __init__(self, type: str, data: dict[str, Any]):
        self.type = type
        self.success = data["success"]
        try:
            self.error = data["errorMessage"]["text"]
        except KeyError:
            self.error = None

    def __repr__(self):
        return f"<Response {self.type} {self.success}{(' ' + self.error) if self.error else ''}>"


class CourseSelectionSystem:
    def __init__(
        self,
        turn_id: int,
        student_id: int,
        request_func: Callable[..., requests.Response],
    ):
        self._turn_id = turn_id
        self._student_id = student_id
        self._request_func = request_func
        self._addable_lessons: list[Lesson] | None = None

    @property
    def turn_id(self):
        return self._turn_id

    @property
    def student_id(self):
        return self._student_id

    def _get(self, url: str, data: dict[str, Any] | None = None):
        if not data:
            data = {"turnId": self.turn_id, "studentId": self.student_id}
        return self._request_func(
            "ws/for-std/course-select/" + url, method="post", data=data
        )

    @property
    def addable_lessons(self):
        if self._addable_lessons is None:
            self.refresh_addable_lessons()
        assert self._addable_lessons is not None
        return self._addable_lessons

    @property
    def selected_lessons(self):
        data = self._get("selected-lessons").json()
        return [Lesson(i) for i in data]

    def refresh_addable_lessons(self):
        data = self._get("addable-lessons").json()
        self._addable_lessons = [Lesson(i) for i in data]

    def find_lessons(
        self,
        code: str | None = None,
        name: str | None = None,
        teacher: str | None = None,
        fuzzy: bool = True,
    ):
        def match(value: str | None, target: str):
            return value is None or (value in target if fuzzy else value == target)

        return [
            lesson
            for lesson in self.addable_lessons
            if match(code, lesson.code)
            and match(name, lesson.course.name)
            and any(match(teacher, i) for i in lesson.teachers)
        ]

    @overload
    def get_lesson(self, code: str, throw: Literal[True]) -> Lesson: ...
    @overload
    def get_lesson(self, code: str, throw: Literal[False] = False) -> Lesson | None: ...
    def get_lesson(self, code: str, throw: bool = False):
        for i in self.addable_lessons:
            if i.code == code:
                return i
        if throw:
            raise ValueError(f"Lesson with code {code} not found")
        return None

    def get_student_counts(self, lessons: Iterable[Lesson]):
        res: dict[str, int] = self._get(
            "std-count", {"lessonIds[]": [lesson.id for lesson in lessons]}
        ).json()
        return [(lesson, res.get(str(lesson.id))) for lesson in lessons]

    def _add_drop_request(self, type: str, lesson: Lesson):
        data = {
            "courseSelectTurnAssoc": self.turn_id,
            "studentAssoc": self.student_id,
            "lessonAssoc": lesson.id,
        }
        request_id = self._get(f"{type}-request", data).text
        res = None
        while not res:
            res = self._get(
                "add-drop-response",
                {"studentId": self.student_id, "requestId": request_id},
            ).json()
        return AddDropResponse(type, res)

    def add(self, lesson: Lesson | str):
        if isinstance(lesson, str):
            lesson = self.get_lesson(lesson, True)
        return self._add_drop_request("add", lesson)

    def drop(self, lesson: Lesson | str):
        if isinstance(lesson, str):
            lesson = self.get_lesson(lesson, True)
        return self._add_drop_request("drop", lesson)
