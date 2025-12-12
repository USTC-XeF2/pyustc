import time

from pyustc import CASClient, EAMSClient
from pyustc.eams.select import CourseSelectionSystem, Lesson


def select_courses(
    cs: CourseSelectionSystem,
    lesson_pairs: dict[str, list[str]],
    count_refresh_interval: float = 0.3,
    lesson_refresh_frequency: int = 5,
):
    """
    Automatically select courses based on the lesson code.

    Arguments:
        cs: `CourseSelectionSystem` - Course selection system instance
        lesson_pairs: `dict[str, list[str]]` - Dictionary of lesson codes

            *Key*: Target new lesson code

            *Value*: List of currently selected conflicting lesson codes that will be dropped
        count_refresh_interval: `float` - Interval to refresh the student counts
        lesson_refresh_frequency: `int` - Frequency to refresh the addable lessons based on the number of iterations
    Yields:
        The lesson codes of successfully selected courses.
    """
    selected_lessons = cs.selected_lessons
    lessons: dict[Lesson, list[Lesson]] = {}
    for k, v in lesson_pairs.items():
        new_lesson = cs.get_lesson(k)
        if not new_lesson:
            continue
        if new_lesson in selected_lessons:
            yield new_lesson.code
        else:
            lessons[new_lesson] = [l for i in v if (l := cs.get_lesson(i))]

    last_refresh = 0
    while lessons:
        if not last_refresh:
            cs.refresh_addable_lessons()
            last_refresh = lesson_refresh_frequency
        last_refresh -= 1
        for new_lesson, count in cs.get_student_counts(lessons.keys()):
            if count is None or count >= new_lesson.limit:
                continue
            dropped_old_lessons: list[Lesson] = []
            drop_success = True
            for old_lesson in lessons[new_lesson]:
                print(f"Drop lesson {old_lesson} for {new_lesson}")
                dropped_old_lessons.append(old_lesson)
                if not cs.drop(old_lesson).success:
                    print("Drop lesson failed")
                    drop_success = False
                    break
            if drop_success:
                print(f"Add lesson {new_lesson}")
                if cs.add(new_lesson).success:
                    print("Add lesson success")
                    lessons.pop(new_lesson)
                    yield new_lesson.code
                    continue
                print("Add lesson failed")
            for old_lesson in dropped_old_lessons:
                print(f"Re-adding lesson {old_lesson}")
                if not cs.add(old_lesson).success:
                    print("Re-adding lesson failed")
        time.sleep(count_refresh_interval)


def main():
    cas_client = CASClient()
    cas_client.login_by_pwd()
    eams_client = EAMSClient(cas_client)

    turn = eams_client.get_open_turns().popitem()
    print(f"Begin course selection for turn {turn[1]}")
    cs = eams_client.get_course_selection_system(turn[0])

    lesson_pairs: dict[str, list[str]] = {}
    for code in select_courses(cs, lesson_pairs):
        print(code)
    print("Course selection completed")


if __name__ == "__main__":
    main()
