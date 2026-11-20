from pyustc import CASClient, EAMSClient


async def example(client: EAMSClient):
    # Get the exam arrangements of the current semester
    exams = await client.get_exams()

    for exam in exams:
        print(
            exam.class_id,
            exam.exam_type,
            exam.course_name,
            exam.time_text,  # raw text, e.g. "2026-11-07 14:30~16:30"
            exam.start,  # datetime | None
            exam.end,  # datetime | None
            exam.campus,
            exam.building,
            exam.room,
            exam.note,
        )


async def main():
    async with CASClient.login_by_pwd() as cas_client:
        eams_client = await EAMSClient.create(cas_client)

    async with eams_client as client:
        await example(client)
