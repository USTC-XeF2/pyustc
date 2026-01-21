from collections.abc import Iterable, Iterator
from typing import Any

from httpx import AsyncClient

from pyustc._singleton import singleton_by_field_meta


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
        result = f"{'success' if self.success else 'failed'}{(':' + self.error) if self.error else ''}"
        return f"<Response type={self.type} {result}>"


class CourseSelectionSystem:
    def __init__(
        self, turn_id: int, student_id: int, client_pool: Iterator[AsyncClient]
    ):
        self._turn_id = turn_id
        self._student_id = student_id
        self._client_pool = client_pool
        self._addable_lessons: list[Lesson] | None = None

    @property
    def turn_id(self):
        return self._turn_id

    @property
    def student_id(self):
        return self._student_id

    async def _get(self, url: str, data: dict[str, Any] | None = None):
        if not data:
            data = {"turnId": self.turn_id, "studentId": self.student_id}
        return (
            await next(self._client_pool).post(
                "/ws/for-std/course-select/" + url, data=data
            )
        ).json()

    async def get_addable_lessons(self):
        if self._addable_lessons is None:
            await self.refresh_addable_lessons()
        assert self._addable_lessons is not None
        return self._addable_lessons

    async def get_selected_lessons(self):
        data = await self._get("selected-lessons")
        return [Lesson(i) for i in data]

    async def refresh_addable_lessons(self):
        data = await self._get("addable-lessons")
        self._addable_lessons = [Lesson(i) for i in data]

    async def find_lessons(
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
            for lesson in await self.get_addable_lessons()
            if match(code, lesson.code)
            and match(name, lesson.course.name)
            and any(match(teacher, i) for i in lesson.teachers)
        ]

    async def get_lesson(self, code: str):
        for i in await self.get_addable_lessons():
            if i.code == code:
                return i
        return None

    async def _get_lesson_or_throw(self, code: str):
        lesson = await self.get_lesson(code)
        if lesson is None:
            raise ValueError(f"Lesson with code {code} not found")
        return lesson

    async def get_student_counts(self, lessons: Iterable[Lesson]):
        res: dict[str, int] = await self._get(
            "std-count", {"lessonIds[]": [lesson.id for lesson in lessons]}
        )
        return [(lesson, res.get(str(lesson.id))) for lesson in lessons]

    async def _add_drop_request(self, type: str, lesson: Lesson):
        data = {
            "courseSelectTurnAssoc": self.turn_id,
            "studentAssoc": self.student_id,
            "lessonAssoc": lesson.id,
        }
        request_id = (
            await next(self._client_pool).post(
                f"/ws/for-std/course-select/{type}-request", data=data
            )
        ).text
        res = None
        while not res:
            res = await self._get(
                "add-drop-response",
                {"studentId": self.student_id, "requestId": request_id},
            )
        return AddDropResponse(type, res)

    async def add(self, lesson: Lesson | str):
        if isinstance(lesson, str):
            lesson = await self._get_lesson_or_throw(lesson)
        return await self._add_drop_request("add", lesson)

    async def drop(self, lesson: Lesson | str):
        if isinstance(lesson, str):
            lesson = await self._get_lesson_or_throw(lesson)
        return await self._add_drop_request("drop", lesson)
