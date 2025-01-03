import json

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
        self.weekday: int = data["weekDayPlaceText"]["text"]
        self.pinned: bool = data.get("pinned", False)
        self.teachers: list[str] = [i["nameZh"] for i in data["teachers"]]

    def __repr__(self):
        return f"<Lesson {self.course.name}-{self.code}{(' Pinned' if self.pinned else '')}>"

class Response:
    def __init__(self, data: dict[str]):
        self.success: bool = data["success"]
        self.error: str = data["errorMessage"]
        if self.error: self.error = self.error["text"]

    def __repr__(self):
        return f"<Response {self.success}{(' ' + self.error) if self.error else ''}>"

class CourseSelectionSystem:
    def __init__(self, turn: int, student_id: int, request_func):
        self._data = {
            "turn": turn,
            "student_id": student_id
        }
        self._request_func = request_func
        self._addable_lessons = None

    @property
    def turn(self):
        return self._data["turn"]

    @property
    def student_id(self):
        return self._data["student_id"]

    def _get(self, url: str, data: dict[str] = None) -> dict[str]:
        if not data:
            data = {
                "turnId": self.turn,
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
        "ws/for-std/course-select/add-request"

    def find_lesson(self, code: str) -> Lesson:
        for i in self.addable_lessons:
            if i.code == code:
                return i
        raise ValueError("Lesson not found")

    def get_student_count(self, lesson: Lesson):
        return self._get("std-count", {
            "lessonIds[]": lesson.id
        }).json()[str(lesson.id)]

    def _add_drop_request(self, type: str, lesson: Lesson):
        data = {
            "courseSelectTurnAssoc": self.turn,
            "studentAssoc": self.student_id,
            "lessonAssoc": lesson.id
        }
        return Response(self._get("add-drop-response", {
            "studentId": self.student_id,
            "requestId": self._get(f"{type}-request", data).text
        }).json())

    def add(self, lesson: Lesson):
        return self._add_drop_request("add", lesson)

    def drop(self, lesson: Lesson):
        return self._add_drop_request("drop", lesson)

    def save(self, path: str):
        with open(path, "w") as f:
            json.dump(self._data, f)

    @classmethod
    def load(cls, path: str, es):
        with open(path) as f:
            data = json.load(f)
        obj = cls(data["turn"], data["student_id"], es._request)
        if "addable_lessons" in data:
            obj.refresh_addable_lessons(data["addable_lessons"])
        return obj

    def __repr__(self):
        return f"<CourseSelectionSystem lessons={len(self.lessons)}>"
