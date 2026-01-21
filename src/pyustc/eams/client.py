import asyncio
import re
from enum import StrEnum
from itertools import cycle
from typing import NamedTuple

from fake_useragent import UserAgent
from httpx import AsyncClient

from pyustc._url import generate_url, root_url
from pyustc.cas import CASClient

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

    @classmethod
    def from_text(cls, text: str):
        match = re.match(r"(\d{4})年(.)季学期", text)
        if match:
            year = int(match.group(1))
            season = Season.from_text(match.group(2))
            if season:
                return cls(year, season)
        raise ValueError(f"Invalid semester text: {text}")


class Turn(NamedTuple):
    id: int
    name: str
    semester: Semester


class EAMSClient:
    """The Educational Administration Management System (EAMS) client for USTC."""

    def __init__(self, clients: list[AsyncClient]):
        if len(clients) == 0:
            raise ValueError("At least one client is required")

        self._clients = clients
        self._client_pool = cycle(clients)
        self._student_id: int = 0
        self._semesters: dict[Semester, int] = {}
        self._current_semester: int = 0

    @classmethod
    async def create(
        cls, cas_client: CASClient, client_count: int = 1, user_agent: str | None = None
    ):
        """Create an EAMSClient instance by logging in through the provided CASClient.

        :param cas_client: The CASClient instance to use for authentication.
        :type cas_client: CASClient
        :param client_count: Number of client instances to create in the pool.
        :type client_count: int
        :param user_agent: User-Agent string to use for the clients. If None, a random one will be used.
        :type user_agent: str | None
        """
        clients = [
            AsyncClient(
                base_url=root_url["eams"],
                follow_redirects=True,
                headers={"User-Agent": user_agent or _ua.random},
            )
            for _ in range(client_count)
        ]

        async def login_client(c: AsyncClient):
            ticket = await cas_client.get_ticket(
                generate_url("eams", "/ucas-sso/login")
            )
            res = await c.get("/ucas-sso/login", params={"ticket": ticket})
            if not res.url.path.endswith("home"):
                raise RuntimeError("Failed to login")

        await asyncio.gather(*(login_client(client) for client in clients))

        return cls(clients)

    @property
    def _client(self):
        return next(self._client_pool)

    async def __aenter__(self):
        res = await self._client.get("/for-std/course-table")
        student_id = res.url.path.split("/")[-1]
        if not student_id.isdigit():
            raise RuntimeError("Failed to get student id")
        self._student_id = int(student_id)

        matches = re.finditer(
            r'<option([^>]*)value="(\d+)"[^>]*>(.+?)</option>', res.text
        )
        for match in matches:
            full_attr = match.group(1)
            value = int(match.group(2))
            semester = Semester.from_text(match.group(3))
            self._semesters[semester] = value
            if "selected" in full_attr:
                self._current_semester = value

        return self

    async def __aexit__(self, *_):
        await asyncio.gather(*(c.aclose() for c in self._clients))

    def _get_student_id_and_semesters(self):
        if not (self._student_id and self._semesters):
            raise RuntimeError(
                "EAMSClient is not initialized. Use `async with` to initialize it."
            )

        return self._student_id, self._semesters

    async def get_current_teach_week(self) -> int:
        """Get the current teaching week."""
        res = await self._client.get("/home/get-current-teach-week")
        return res.json()["weekIndex"]

    async def get_course_table(
        self, week: int | None = None, semester: Semester | None = None
    ):
        """Get the course table for the specified week and semester."""
        student_id, semesters = self._get_student_id_and_semesters()
        semester_id = semesters[semester] if semester else self._current_semester
        url = f"/for-std/course-table/semester/{semester_id}/print-data/{student_id}"
        params = {"weekIndex": week or ""}
        res = await self._client.get(url, params=params)
        return CourseTable(res.json()["studentTableVm"], week)

    def get_grade_manager(self):
        """Get the grade manager."""
        return GradeManager(self._client_pool)

    async def get_open_turns(self):
        """Get the list of open course selection turns."""
        student_id, _ = self._get_student_id_and_semesters()
        res = await self._client.post(
            "/ws/for-std/course-select/open-turns",
            data={"bizTypeId": 2, "studentId": student_id},
        )
        return [
            Turn(i["id"], i["name"], Semester.from_text(i["semesterName"]))
            for i in res.json()
        ]

    def get_course_selection_system(self, turn: Turn):
        """Get the course selection system for the specified turn.

        :param turn: Course selection turn.
        :type turn: Turn
        """
        student_id, _ = self._get_student_id_and_semesters()
        return CourseSelectionSystem(turn.id, student_id, self._client_pool)

    def get_course_adjustment_system(self, turn: Turn):
        """Get the course adjustment system for the specified turn.

        :param turn: Course selection turn.
        :type turn: Turn
        """
        student_id, semesters = self._get_student_id_and_semesters()
        semester_id = semesters[turn.semester]
        return CourseAdjustmentSystem(
            turn.id, semester_id, student_id, self._client_pool
        )
