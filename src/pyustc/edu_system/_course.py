import datetime

class Place:
    def __init__(self, data: dict[str]):
        self.name: str = data["room"] or data["customPlace"]
        self.building: str = data["building"]
        self.campus: str = data["campus"]

    def include(self, place: str):
        return place in self.name or place in self.building or place in self.campus

    def __repr__(self):
        return self.name

class Teacher:
    def __init__(self, data: dict[str]):
        self.id: int = data["id"]
        self.name: str = data["person"]["nameZh"]
        self.degree: (str | None) = data["teacherDegree"] and data["teacherDegree"]["nameZh"]
        self.type: (str | None) = data["type"] and data["type"]["nameZh"]
        self.department: str = data["department"]["simpleNameZh"]

    def __repr__(self):
        return self.name

class Course:
    def __init__(self, data: dict[str]):
        self.code: str = data["lessonCode"]
        self.name: str = data["courseName"]
        self.place = Place(data)
        self.weekday: int = data["weekday"]
        self.teachers = [Teacher(i) for i in data["teacherDeepVms"]]
        self.student_count: int = data["stdCount"]
        get_time = lambda x: datetime.datetime.strptime(x, "%H:%M").time()
        self.start_time = get_time(data["startDate"])
        self.end_time = get_time(data["endDate"])
        self.unit: tuple[int, int] = (data["startUnit"], data["endUnit"])

    def time(self, format: bool = True):
        if format:
            return f"{self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"
        else:
            return self.start_time, self.end_time

    def __repr__(self):
        return f"<Course {repr(self.name)}>"

class CourseTable:
    def __init__(self, data: dict[str], week: int):
        self.std_name: str = data["name"]
        self.std_id: str = data["code"]
        self.grade: str = data["grade"]
        self.major: str = data["major"]
        self.admin_class: str = data["adminclass"]
        self.credits: float = data["credits"]
        self.courses = [Course(i) for i in data["activities"]]
        self.week = week

    def get_courses(self, weekday: int = None, unit: int = None, place: Place | str = None):
        """
        Get courses that meet the conditions.
        """
        courses = list[Course]()
        for i in self.courses:
            if weekday and i.weekday != weekday:
                continue
            if unit and not i.unit[0] <= unit <= i.unit[1]:
                continue
            if place:
                if isinstance(place, str):
                    if not i.place.include(place):
                        continue
                elif i.place != place:
                    continue
            courses.append(i)
        return courses

    def __repr__(self):
        return f"<CourseTable week={self.week or 'all'}>"
