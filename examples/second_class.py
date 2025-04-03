from pyustc import CASClient, YouthService
from pyustc.young import SecondClass, SCFilter, Module, Department

client = CASClient()
client.login_by_pwd()

with YouthService(client):
    # Get the list of second classes by name
    sc = next(SecondClass.find("xxx"))

    # Or get the list of second classes by filter
    root_dept = Department.get_root_dept()
    filter = SCFilter(
        name="xxx",
        module=Module.get_available_tags(text="体")[0],
        department=root_dept.find_one("跑步")
    )
    SecondClass.find(
        filter=filter,
        apply_ended=False,
        expand_series=True # Expand series to get all second classes in the series
    )

    # Get the list of second classes you have participated in
    SecondClass.get_participated()

    print(
        sc.id,
        sc.name,
        sc.status,
        sc.create_time,
        sc.apply_time,
        sc.hold_time,
        sc.tel,
        sc.valid_hour,
        sc.apply_num,
        sc.apply_limit,
        sc.applied,
        sc.applyable,
        sc.need_sign_info,
        sc.module,
        sc.department,
        sc.labels,
        sc.conceive,
        sc.labels
    )
    if sc.is_series:
        print(sc.children)

    sc.update() # Get the latest information of the second class
    sc.get_applicants() # Get the list of applicants
    sc.apply(
        force=True, # Force apply even if the second class is not applyable
        auto_cancel=True, # Auto cancel the application with time conflict
    )
    sc.cancel_apply()
