from pyustc import CASClient, EAMSClient


async def example(client: EAMSClient):
    # Get current teaching week
    week = await client.get_current_teach_week()

    # Get the course table
    table = await client.get_course_table(week=week, semester=None)
    print(
        table.std_name,
        table.std_id,
        table.grade,
        table.major,
        table.admin_class,
        table.credits,
        table.week,
    )

    # Get all courses
    courses = table.courses
    table.get_courses(weekday=1, unit=3, place="5201")

    # Print course information
    course = courses[0]
    print(
        course.code,
        course.name,
        course.place,  # Place object, use `include` method to check if it contains a string
        course.weekday,
        course.teachers,  # List of Teacher objects
        course.student_count,
        course.start_time,
        course.end_time,
        course.unit,
    )
    print(
        course.time(format=True),
    )  # a string if `format` is True, otherwise a tuple of time objects


async def main():
    async with CASClient.login_by_pwd() as cas_client:
        eams_client = await EAMSClient.create(cas_client)

    async with eams_client as client:
        await example(client)
