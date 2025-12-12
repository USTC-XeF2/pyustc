from pyustc import CASClient, EAMSClient

client = EAMSClient(
    CASClient()
)  # See examples/cas_client.py for how to create a logged in CASClient instance

# Get open turns
open_turns = client.get_open_turns()
print(open_turns)

# Get the course selection system
cs = client.get_course_selection_system(open_turns.popitem()[0])

lesson = cs.get_lesson("MATH1007.01")
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
lessons = cs.find_lessons(name="数学分析")

# Get current student counts for the lessons
# This will only return the current student counts, not the limit
cs.get_student_counts(lessons)

# Refresh the addable lessons to get the latest lesson list
cs.refresh_addable_lessons()

if lesson:
    # Add the lesson
    print(cs.add(lesson))

    # Drop the lesson
    print(cs.drop(lesson))
