from pyustc import CASClient, EAMSClient


async def main():
    async with CASClient.login_by_pwd() as cas_client:
        client = await EAMSClient.create(cas_client)

    # Get open turns
    open_turns = await client.get_open_turns()
    print(open_turns)

    # Get the course selection system
    cs = await client.get_course_selection_system(open_turns.popitem()[0])

    lesson = await cs.get_lesson("MATH1007.01")
    if lesson:
        print(
            lesson.course,
            lesson.code,
            lesson.limit,
            lesson.unit,
            lesson.week,
            lesson.weekday,
            lesson.pinned,  # whether the lesson is set up
            lesson.teachers,
        )

    # Use keywords to find lessons
    lessons = await cs.find_lessons(name="数学分析")

    # Get current student counts for the lessons
    # This will only return the current student counts, not the limit
    await cs.get_student_counts(lessons)

    # Refresh the addable lessons to get the latest lesson list
    await cs.refresh_addable_lessons()

    if lesson:
        # Add the lesson
        print(await cs.add(lesson))

        # Drop the lesson
        print(await cs.drop(lesson))
