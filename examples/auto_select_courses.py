import asyncio
import time

from pyustc import CASClient, EAMSClient
from pyustc.eams.select import CourseSelectionSystem, Lesson


async def try_select_lesson(
    cs: CourseSelectionSystem, new_lesson: Lesson, old_lessons: list[Lesson]
) -> bool:
    """
    Try to select a new lesson by dropping old conflicting lessons.

    Returns:
        True if the lesson was successfully selected, False otherwise.
    """
    dropped_old_lessons: list[Lesson] = []
    drop_success = True

    # Drop conflicting lessons
    for old_lesson in old_lessons:
        print(f"Drop lesson {old_lesson} for {new_lesson}")
        dropped_old_lessons.append(old_lesson)
        if not (await cs.drop(old_lesson)).success:
            print("Drop lesson failed")
            drop_success = False
            break

    if drop_success:
        print(f"Add lesson {new_lesson}")
        if (await cs.add(new_lesson)).success:
            print("Add lesson success")
            return True
        print("Add lesson failed")

    # Restore dropped lessons if selection failed
    for old_lesson in dropped_old_lessons:
        print(f"Re-adding lesson {old_lesson}")
        if not (await cs.add(old_lesson)).success:
            print("Re-adding lesson failed")

    return False


async def select_courses(
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
    selected_lessons = await cs.get_selected_lessons()
    lessons: dict[Lesson, list[Lesson]] = {}
    for k, v in lesson_pairs.items():
        new_lesson = await cs.get_lesson(k)
        if not new_lesson:
            continue
        if new_lesson in selected_lessons:
            yield new_lesson.code
        else:
            old_lessons = await asyncio.gather(*[cs.get_lesson(i) for i in v])
            lessons[new_lesson] = list(filter(None, old_lessons))

    last_refresh = 0
    while lessons:
        if not last_refresh:
            await cs.refresh_addable_lessons()
            last_refresh = lesson_refresh_frequency
        last_refresh -= 1

        # Get all lessons that can be selected
        student_counts = await cs.get_student_counts(lessons.keys())

        # Create tasks for all available lessons (concurrent execution)
        tasks: list[asyncio.Task[bool]] = []
        task_lessons: list[Lesson] = []
        for new_lesson, count in student_counts:
            if count is None or count >= new_lesson.limit:
                continue
            tasks.append(
                asyncio.create_task(
                    try_select_lesson(cs, new_lesson, lessons[new_lesson])
                )
            )
            task_lessons.append(new_lesson)

        # Execute all tasks concurrently
        if tasks:
            results = await asyncio.gather(*tasks)
            for new_lesson, success in zip(task_lessons, results):
                if success:
                    lessons.pop(new_lesson)
                    yield new_lesson.code

        time.sleep(count_refresh_interval)


async def main():
    async with CASClient.login_by_pwd() as cas_client:
        eams_client = await EAMSClient.create(cas_client)

    turn = (await eams_client.get_open_turns()).popitem()
    print(f"Begin course selection for turn {turn[1]}")
    cs = await eams_client.get_course_selection_system(turn[0])

    lesson_pairs: dict[str, list[str]] = {}
    async for code in select_courses(cs, lesson_pairs):
        print(code)
    print("Course selection completed")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
