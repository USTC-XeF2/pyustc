import requests

class Course:
    def __init__(self, data: dict[str]):
        self.id: int = data["id"]
        self.name: str = data["courseNameCh"]
        self.code: int = data["courseAssoc"]
        self.train_type: int = data["trainTypeAssoc"]
        self.semester: int = data["semesterAssoc"]
        self.hour: int = int(data["total"])
        self.credits: float = data["credits"]
        self.score: str = data["scoreCh"]
        self.gpa: float | None = data["gp"]
        self.passed: bool = data["passed"]
        self.abandoned: bool = not data["transcript"]

grade_score_map = {
    "A+": 98,
    "A": 93,
    "A-": 88,
    "B+": 84,
    "B": 80,
    "B-": 77,
    "C+": 74,
    "C": 70,
    "C-": 67,
    "D+": 65,
    "D": 63,
    "D-": 61,
    "F": 0
}

class GradeSheet:
    def __init__(self, data: list[dict[str]]):
        self.courses = [Course(j) for i in data for j in i["scores"]]

    @property
    def total_courses(self):
        return len(self.courses)

    @property
    def total_credits(self) -> float:
        return sum(i.credits for i in self.courses)

    @property
    def gpa(self):
        total_gpa = 0.0
        total_credits = 0.0
        for course in self.courses:
            if course.gpa is not None and not course.abandoned:
                total_gpa += course.gpa * course.credits
                total_credits += course.credits
        return total_gpa / total_credits if total_credits else float("nan")

    def _calculate_score(self, weighted: bool = False):
        total_score = 0.0
        total_weight = 0.0
        for course in self.courses:
            if course.abandoned:
                continue
            weight = course.credits if weighted else 1.0
            if course.score.replace(".", "").isdigit():
                total_score += float(course.score) * weight
                total_weight += weight
            elif course.score in grade_score_map:
                total_score += grade_score_map[course.score] * weight
                total_weight += weight
        return total_score / total_weight if total_weight else float("nan")

    @property
    def arithmetic_score(self):
        return self._calculate_score(weighted=False)

    @property
    def weighted_score(self):
        return self._calculate_score(weighted=True)

class GradeManager:
    def __init__(self, request_func):
        self._request_func = request_func

        self.train_types: dict[int, str] = {i["id"]: i["name"]
                                            for i in self._get("getGradeSheetTypes").json()}
        self.semesters: dict[int, tuple[str, str]] = {i["id"]: (i["nameZh"], i["schoolYear"])
                                                      for i in self._get("getSemesters").json()}

    def _get(self, url: str, params: dict[str] = None) -> requests.Response:
        return self._request_func("for-std/grade/sheet/" + url, params=params)

    def get_grade_sheet(self, train_type: int = None, semesters: int | list[int] = None):
        res = self._get("getGradeList", params={
            "trainTypeId": train_type,
            "semesterIds": semesters or ""
        })
        return GradeSheet(res.json()["semesters"])
