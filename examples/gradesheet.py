from pyustc import CASClient, EAMSClient


async def main():
    async with CASClient.login_by_pwd() as cas_client:
        client = await EAMSClient.create(cas_client)

    # Get the grade manager
    gm = client.get_grade_manager()
    print(await gm.get_train_types(), await gm.get_semesters())

    # Get the grade sheet
    sheet = await gm.get_grade_sheet()
    print(sheet.total_courses, sheet.total_credits, sheet.gpa)
    print(sheet.arithmetic_score, sheet.weighted_score)
    for course in sheet.courses:
        print(
            course.id,
            course.name,
            course.code,
            course.train_type,
            course.semester,
            course.hour,
            course.credits,
            course.score,
            course.gpa,  # None if the course is not graded
            course.passed,
            course.abandoned,  # True if the course is abandoned (not counted in GPA and credits)
        )
