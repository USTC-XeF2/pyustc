from pyustc import EduSystem

es = EduSystem(...) # See examples/edu_system.py for how to create a EduSystem instance

# Get the grade manager
gm = es.get_grade_manager()
print(gm.train_types, gm.semesters)

# Get the grade sheet
sheet = gm.get_grade_sheet()
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
        course.gpa, # None if the course is not graded 
        course.passed,
        course.abandoned # True if the course is abandoned (not counted in GPA and credits)
    )
