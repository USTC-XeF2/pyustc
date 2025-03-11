import requests

class Course:
    _course_list = {}
    def __new__(cls, data: dict[str]):
        course_id = data["id"]
        if course_id in cls._course_list:
            return cls._course_list[course_id]
        obj = super().__new__(cls)
        cls._course_list[course_id] = obj
        return obj

    def __init__(self, data: dict[str]):
        if hasattr(self, "id"):
            return
        self.id: int = data["id"]
        self.name: str = data["nameZh"]
        self.code: str = data["code"]

    def __repr__(self):
        return f"<Course {self.name}>"

class Lesson:
    _lesson_list = {}
    def __new__(cls, data: dict[str]):
        lesson_id = data["id"]
        if lesson_id in cls._lesson_list:
            return cls._lesson_list[lesson_id]
        obj = super().__new__(cls)
        cls._lesson_list[lesson_id] = obj
        return obj

    def __init__(self, data: dict[str]):
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
    def __init__(self, type: str, data: dict[str]):
        self.type = type
        self.success: bool = data["success"]
        try:
            self.error: str = data["errorMessage"]["text"]
        except:
            self.error = None

    def __repr__(self):
        return f"<Response {self.type} {self.success}{(' ' + self.error) if self.error else ''}>"

class CourseSelectionSystem:
    def __init__(self, turn_id: int, student_id: int, request_func):
        self._data = {
            "turn_id": turn_id,
            "student_id": student_id
        }
        self._request_func = request_func
        self._addable_lessons = None

    @property
    def turn_id(self):
        return self._data["turn_id"]

    @property
    def student_id(self):
        return self._data["student_id"]

    def _get(self, url: str, data: dict[str] = None) -> requests.Response:
        if not data:
            data = {
                "turnId": self.turn_id,
                "studentId": self.student_id
            }
        return self._request_func("ws/for-std/course-select/" + url, method="post", data=data)

    @property
    def addable_lessons(self) -> list[Lesson]:
        if self._addable_lessons == None:
            self.refresh_addable_lessons()
        return self._addable_lessons

    @property
    def selected_lessons(self) -> list[Lesson]:
        data = self._get("selected-lessons").json()
        return [Lesson(i) for i in data]

    def refresh_addable_lessons(self, data: dict[str] = None):
        if not data:
            data = self._get("addable-lessons").json()
        self._addable_lessons = [Lesson(i) for i in data]
        self._data["addable_lessons"] = data

    def find_lessons(
            self,
            code: str = None,
            name: str = None,
            teacher: str = None,
            fuzzy: bool = True
        ) -> list[Lesson]:
        results = []
        for lesson in self.addable_lessons:
            if code:
                if fuzzy:
                    if code not in lesson.code: continue
                else:
                    if code != lesson.code: continue
            if name:
                if fuzzy:
                    if name not in lesson.course.name: continue
                else:
                    if name != lesson.course.name: continue
            if teacher:
                if fuzzy:
                    if not any(teacher in i for i in lesson.teachers): continue
                else:
                    if teacher not in lesson.teachers: continue
            results.append(lesson)   
        return results

    def get_lesson(self, code: str) -> Lesson | None:
        for i in self.addable_lessons:
            if i.code == code:
                return i

    def get_student_counts(self, lessons: list[Lesson]) -> list[tuple[Lesson, int]]:
        res: dict[str, int] = self._get("std-count", {
            "lessonIds[]": [lesson.id for lesson in lessons]
        }).json()
        return [(lesson, res.get(str(lesson.id))) for lesson in lessons]

    def _add_drop_request(self, type: str, lesson: Lesson):
        data = {
            "courseSelectTurnAssoc": self.turn_id,
            "studentAssoc": self.student_id,
            "lessonAssoc": lesson.id
        }
        return AddDropResponse(type, self._get("add-drop-response", {
            "studentId": self.student_id,
            "requestId": self._get(f"{type}-request", data).text
        }).json())

    def add(self, lesson: Lesson | str):
        if isinstance(lesson, str):
            lesson = self.get_lesson(lesson)
        return self._add_drop_request("add", lesson)

    def drop(self, lesson: Lesson | str):
        if isinstance(lesson, str):
            lesson = self.get_lesson(lesson)
        return self._add_drop_request("drop", lesson)
