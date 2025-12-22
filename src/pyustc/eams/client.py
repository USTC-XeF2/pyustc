import re
from enum import StrEnum
from typing import NamedTuple

from fake_useragent import UserAgent
from httpx import AsyncClient

from .._url import generate_url, root_url
from ..cas import CASClient
from ._course import CourseTable
from ._grade import GradeManager
from .adjust import CourseAdjustmentSystem
from .select import CourseSelectionSystem

_ua = UserAgent(platforms="desktop")


class Season(StrEnum):
    SPRING = "春"
    SUMMER = "夏"
    AUTUMN = "秋"

    @classmethod
    def from_text(cls, text: str):
        for member in cls:
            if text.startswith(member.value):
                return member
        return None


class Semester(NamedTuple):
    year: int
    season: Season


class Turn(NamedTuple):
    id: int
    name: str


class EAMSClient:
    def __init__(self, client: AsyncClient):
        self._client = client
        self._student_id: int = 0
        self._semesters: dict[Semester, int] = {}
        self._current_semester: int = 0

    @classmethod
    async def create(cls, cas_client: CASClient, user_agent: str | None = None):
        client = AsyncClient(
            base_url=root_url["eams"],
            follow_redirects=True,
            headers={"User-Agent": user_agent or _ua.random},
        )

        ticket = await cas_client.get_ticket(generate_url("eams", "/ucas-sso/login"))
        res = await client.get("/ucas-sso/login", params={"ticket": ticket})
        if not res.url.path.endswith("home"):
            raise RuntimeError("Failed to login")

        return cls(client)

    async def __aenter__(self):
        res = await self._client.get("/for-std/course-table")
        student_id = res.url.path.split("/")[-1]
        if not student_id.isdigit():
            raise RuntimeError("Failed to get student id")
        self._student_id = int(student_id)

        matches = re.finditer(
            r'<option([^>]*)value="(\d+)"[^>]*>(\d+)年(.*?)学期', res.text
        )
        for match in matches:
            full_attr = match.group(1)
            value = int(match.group(2))
            year = int(match.group(3))
            season = Season.from_text(match.group(4))
            if not season:
                continue
            self._semesters[Semester(year, season)] = value
            if "selected" in full_attr:
                self._current_semester = value

        return self

    async def __aexit__(self, *_):
        await self._client.aclose()

    def _get_student_id_and_semesters(self):
        if not (self._student_id and self._semesters):
            raise RuntimeError(
                "EAMSClient is not initialized. Use `async with` to initialize it."
            )

        return self._student_id, self._semesters

    async def get_current_teach_week(self) -> int:
        """
        Get the current teaching week.
        """
        res = await self._client.get("/home/get-current-teach-week")
        return res.json()["weekIndex"]

    async def get_course_table(
        self, week: int | None = None, semester: Semester | None = None
    ):
        """
        Get the course table for the specified week and semester.
        """
        student_id, semesters = self._get_student_id_and_semesters()
        semester_id = semesters[semester] if semester else self._current_semester
        url = f"/for-std/course-table/semester/{semester_id}/print-data/{student_id}"
        params = {"weekIndex": week or ""}
        res = await self._client.get(url, params=params)
        return CourseTable(res.json()["studentTableVm"], week)

    def get_grade_manager(self):
        return GradeManager(self._client)

    async def get_open_turns(self):
        """
        Get the open turns for course selection.
        """
        student_id, _ = self._get_student_id_and_semesters()
        res = await self._client.post(
            "/ws/for-std/course-select/open-turns",
            data={"bizTypeId": 2, "studentId": student_id},
        )
        return [Turn(i["id"], i["name"]) for i in res.json()]

    def get_course_selection_system(self, turn: Turn):
        student_id, _ = self._get_student_id_and_semesters()
        return CourseSelectionSystem(turn.id, student_id, self._client)

    def get_course_adjustment_system(
        self, turn: Turn, semester: Semester | None = None
    ):
        student_id, semesters = self._get_student_id_and_semesters()
        semester_id = semesters[semester] if semester else self._current_semester
        return CourseAdjustmentSystem(turn.id, semester_id, student_id, self._client)
