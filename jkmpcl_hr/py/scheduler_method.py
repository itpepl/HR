import frappe
from frappe.utils import getdate, today,add_days,now_datetime,add_to_date, date_diff, get_last_day
from datetime import date,datetime
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
from frappe.utils import get_datetime
from datetime import datetime, time,timedelta
from frappe.utils import flt
import calendar

from jkmpcl_hr.py.utils import get_current_holiday_list


# from jkmpcl_hr.py.utils import send_notification_email
from jkmpcl_hr.py.utils import create_shift_assignment_rec, send_notification_email, get_emp_reporting_manager

@frappe.whitelist(allow_guest=True)
def create_shift_assignments():
    frappe.log_error("start_create_shift_assignments", "Scheduler Started")
    today_date = getdate(today())
    start_year = today_date.year if today_date.month >= 4 else today_date.year - 1
    
    emp_filters = {"status": "Active"}
    create_and_assign_shift_assignments_srinagar(today_date, start_year, emp_filters)
    create_and_assign_shift_assignments_jammu(today_date, start_year, emp_filters)
    frappe.log_error("end_create_shift_assignments", "Scheduler Ended")




def create_and_assign_shift_assignments_srinagar(today_date, start_year, emp_filters):
    frappe.log_error("start_create_and_assign_shift_assignments_srinagar", "Scheduler Started FOR Srinagar")
    
    apr_start_date = getdate(f"{start_year}-04-01")
    mar_end_date = getdate(f"{start_year+1}-03-31")
    # mar_end_date = date(start_year + 1, 3, 31)
    
    sep_end_sri  = getdate(f"{start_year}-09-30")
    oct_start_sri = getdate(f"{start_year}-10-01")
    
    # sep_end_sri  = date(start_year, 9, 30)
    # oct_start_sri = date(start_year, 10, 1)

    emp_filters["branch"] = "Jammu and Kashmir Milk Producers Co-operative Ltd Cheshmashahi Srinagar"
    emp_list = frappe.db.get_list("Employee", filters=emp_filters, fields=["name", "default_shift", "custom_attendance_source"])
        
    if not emp_list:
        return
        
    
    error_emp = []
    ds_not_set_emp = []
    
    for emp in emp_list:
        try:
            emp_id = emp.get("name")
            default_shift = emp.get("default_shift")
            
            eight_hours_sa_exists = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", apr_start_date], "end_date":[">=", sep_end_sri]}, limit=1)
            seven_hours_sa_exists = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", oct_start_sri], "end_date":[">=", mar_end_date]}, limit=1)
            
            emp_default_shift_details = frappe.db.get_values("Shift Type", default_shift, ["custom_shift_type", "custom_hours", "custom_branch"], as_dict=True)
            
            if not emp_default_shift_details:
                ds_not_set_emp.append(emp_id)
                continue
            
            if emp_default_shift_details[0].get("custom_hours") == "7hours":
                if emp.get("custom_attendance_source") == "Field" and emp_default_shift_details[0].get("custom_shift_type") == "General":
                    seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
                    
                    eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
                
                if emp.get("custom_attendance_source") == "Punch" and emp_default_shift_details[0].get("custom_shift_type") == "General":
                    seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Punch"}, "name")
                    
                    eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Punch"}, "name")
                else:
                    seven_hours_shift_id = default_shift
                    eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours",         "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
                            
            elif emp_default_shift_details[0].get("custom_hours") == "8hours":
                if emp.get("custom_attendance_source") == "Field" and emp_default_shift_details[0].get("custom_shift_type") == "General":
                    eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
                    seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
                    
                if emp.get("custom_attendance_source") == "Punch" and emp_default_shift_details[0].get("custom_shift_type") == "General":
                    eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Punch"}, "name")
                    seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Punch"}, "name")
                else:                                
                    eight_hours_shift_id = default_shift
                    seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
            
            if not eight_hours_sa_exists:
                create_shift_assignment_rec(emp_id, apr_start_date, sep_end_sri, eight_hours_shift_id)
            
            if not seven_hours_sa_exists:
                create_shift_assignment_rec(emp_id, oct_start_sri, mar_end_date, seven_hours_shift_id)
                
                        
            # return emp_default_shift_details
            # if not eight_hours_sa_exists:
                
            
        except Exception as e:
            error_emp.append({emp_id: str(e)})
            frappe.log_error(f"error_create_and_assign_shift_assignments_srinagar_{emp_id}", frappe.get_traceback())
            continue
    
    frappe.log_error("end_create_and_assign_shift_assignments_srinagar", f"Scheduler Ended FOR Srinagar\n ds_not_setupfor_this_emp: {ds_not_set_emp}")
    
    
    
def create_and_assign_shift_assignments_jammu(today_date, start_year, emp_filters):
    # apr_start_date = date(start_year, 4, 1)
    # mar_end_date = date(start_year + 1, 3, 31)
    frappe.log_error("start_create_and_assign_shift_assignments_jammu", "Scheduler Started FOR Jammu")
    
    apr_start_date = getdate(f"{start_year}-04-01")
    mar_end_date = getdate(f"{start_year+120137}-03-31")
    
    # nov_end_jammu = date(start_year, 11, 30)
    # dec_start_jammu = date(start_year, 12, 1)
    # jan_end_jammu = date(start_year + 1, 1, 31)
    
    nov_end_jammu = getdate(f"{start_year}-11-30")
    dec_start_jammu = getdate(f"{start_year}-12-01")
    jan_end_jammu = getdate(f"{start_year+1}-01-31")
    feb_start_jammu = getdate(f"{start_year+1}-02-01")
    
    emp_filters["branch"] = "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu"
    emp_list = frappe.db.get_list("Employee", filters=emp_filters, fields=["name", "default_shift", "gender", "custom_attendance_source"])
    
    if not emp_list:
        return
    
    error_emp = []
    ds_not_set_emp = []
    
    for emp in emp_list:
        try:
            emp_id = emp.get("name")
            default_shift = emp.get("default_shift")
            
            if not default_shift:
                    ds_not_set_emp.append(emp_id)
                    continue
            emp_default_shift_details = frappe.db.get_values("Shift Type", default_shift, ["custom_shift_type", "custom_hours", "custom_branch"], as_dict=True)
            
            if emp.get("gender") == "Female" and emp.get("custom_attendance_source") == "Field":
            
                eight_hours_sa_exists_first = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", apr_start_date], "end_date":[">=", nov_end_jammu]}, limit=1)
                seven_hours_sa_exists = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", dec_start_jammu], "end_date":[">=", jan_end_jammu]}, limit=1)
                eight_hours_sa_exists_second = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", feb_start_jammu], "end_date":[">=", mar_end_date]}, limit=1)
                
                
                if emp_default_shift_details[0].get("custom_hours") == "7hours":
                    
                    if emp_default_shift_details[0].get("custom_shift_type") == "General":
                        
                        seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
                        
                        eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
                    else:
                        seven_hours_shift_id = default_shift
                        eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
                                
                elif emp_default_shift_details[0].get("custom_hours") == "8hours":
                    if emp_default_shift_details[0].get("custom_shift_type") == "General":
                        eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
                        seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
                    else:
                    
                        eight_hours_shift_id = default_shift
                        seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
                
                if not eight_hours_sa_exists_first:
                    create_shift_assignment_rec(emp_id, apr_start_date, nov_end_jammu, eight_hours_shift_id)
                
                if not seven_hours_sa_exists:
                    create_shift_assignment_rec(emp_id, dec_start_jammu, jan_end_jammu, seven_hours_shift_id)
                    
                if not eight_hours_sa_exists_second:
                    create_shift_assignment_rec(emp_id, feb_start_jammu, mar_end_date, eight_hours_shift_id)

            
            else:
                sa_exists = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", apr_start_date], "end_date":[">=", mar_end_date]}, limit=1)
                    
                if emp_default_shift_details[0].get("custom_hours") == "7hours":
                    
                    if emp.get("custom_attendance_source") == "Field" and emp_default_shift_details[0].get("custom_shift_type") == "General":
                        eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
                    else:
                        eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
                                
                elif emp_default_shift_details[0].get("custom_hours") == "8hours":
                    if emp.get("custom_attendance_source") == "Field" and emp_default_shift_details[0].get("custom_shift_type") == "General":
                        eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
                    else:                    
                        eight_hours_shift_id = default_shift
                
                if not sa_exists:
                    create_shift_assignment_rec(emp_id, apr_start_date, mar_end_date, eight_hours_shift_id)
                
            # return emp_default_shift_details
            # if not eight_hours_sa_exists_first:
        
        except Exception as e:
            error_emp.append({emp_id: str(e)})
            frappe.log_error(f"error_create_and_assign_shift_assignments_jammu_{emp_id}", frappe.get_traceback())
            continue
    
    frappe.log_error("end_create_and_assign_shift_assignments_jammu", f"Scheduler Ended FOR Jammu \n ds_not_setupfor_this_emp: {ds_not_set_emp}")
    
    

def get_employee_leave_type(employee):
    policy = frappe.db.get_value(
        "Leave Policy Assignment",
        {
            "employee": employee,
            "docstatus": 1
        },
        "leave_policy"
    )

    if policy:
        leave_type = frappe.db.get_value(
            "Leave Policy Detail",
            {
                "parent": policy
            },
            "leave_type"
        )

        if leave_type:
            return leave_type

    # 🔥 Fallback to Leave Without Pay
    return "Leave Without Pay"


# =========================================================
# MAIN SCHEDULER METHOD
# =========================================================
@frappe.whitelist(allow_guest=True)
def run_attendance_from_to(from_date,to_date):
# def run_attendance_from_to():
    if not from_date or not to_date:
        frappe.throw("From Date and To Date are required")


    
    # from_date="2026-01-13"
    # to_date="2026-01-23"
    from_date = getdate(from_date)
    to_date = getdate(to_date)

    current_date = from_date

    while current_date <= to_date:
        run_daily_attendance(current_date, only_for_jammu=False)
        current_date = add_days(current_date, 1)

    return {
        "status": "success",
        "message": f"Attendance processed from {from_date} to {to_date}"
    }

def normalize_to_minute(dt):
    if not dt:
        return None
    return dt.replace(second=0, microsecond=0)

def get_employee_from_user():
    return frappe.db.get_value(
        "Employee",
        {"user_id": frappe.session.user, "status": "Active"},
        ["name", "branch"],
        as_dict=True,
    )


@frappe.whitelist()
def run_attendance_for_my_branch(att_date):

    if not att_date:
        frappe.throw("Attendance Date required")

    emp = get_employee_from_user()

    if not emp:
        frappe.throw("No Employee linked with this user")

    branch = emp.branch

    # employees = get_employees_by_branch(branch)

    # for e in employees:
    run_daily_attendance(getdate(att_date),branch)

    frappe.db.commit()

    return {
        "success": True,
        "message": f"Attendance processed for branch: {branch}"
    }

def run_daily_attendance(att_date=None, only_for_jammu=False, branch=None):

    frappe.log_error("start_run_daily_attendance", f"Scheduler Started FOR Date: {att_date}")

    if not att_date:
        att_date = add_days(getdate(), -1)
    else:
        att_date = getdate(att_date)
    if only_for_jammu:
        employees = frappe.get_all(
            "Employee",
            filters={
                "status": "Active",
                "branch": "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu",
            },
            pluck="name",
        )
    else:
        filters = {"status": "Active"}

        if branch:
            filters["branch"] = branch

        employees = frappe.get_all("Employee", filters=filters, pluck="name")

    for emp in employees:
        try:

            if has_approved_leave(emp, att_date):
                continue

            shift_type = get_employee_shift(emp, att_date)

            if not shift_type:
                log_attendance_error(emp, att_date, "Shift not assigned")
                continue

            shift_custom_type = frappe.db.get_value(
                "Shift Type", shift_type, "custom_shift_type"
            )

            is_holiday = is_holiday_or_weekoff(emp, att_date)
            off_day_approved = has_approved_off_day_work(emp, att_date)

            is_holiday_work = False

            if shift_custom_type == "24 hours":

                first_in, last_out, first_checkin_id, last_checkin_id, working_hours, log_count = (
                    get_24_hour_working_hours(emp, att_date, shift_type)
                )

                if log_count == 0:
                    if is_holiday:
                        continue

                    create_or_update_attendance(
                        emp,
                        att_date,
                        None,
                        None,
                        0,
                        None,
                        None,
                        skip_shift_time_rules=True,
                        is_holiday_work=False,
                    )
                    continue

                if is_holiday:
                    is_holiday_work = True

                if log_count == 1:
                    create_or_update_attendance(
                        emp,
                        att_date,
                        None,
                        None,
                        0,
                        first_checkin_id,
                        last_checkin_id,
                        skip_shift_time_rules=True,
                        is_holiday_work=is_holiday_work,
                    )
                    continue

                create_or_update_attendance(
                    emp,
                    att_date,
                    first_in,
                    last_out,
                    working_hours,
                    first_checkin_id,
                    last_checkin_id,
                    skip_shift_time_rules=True,
                    is_holiday_work=is_holiday_work,
                )
                continue

            if shift_custom_type == "Night":

                in_time, out_time, first_id, last_id, working_hours, log_count = (
                    get_night_shift_logs(emp, att_date)
                )

                if log_count == 0:
                    if is_holiday:
                        continue

                    create_or_update_attendance(
                        emp,
                        att_date,
                        None,
                        None,
                        0,
                        None,
                        None,
                        skip_shift_time_rules=True,
                        is_holiday_work=False,
                    )
                    continue

                if is_holiday:
                    is_holiday_work = True

                if log_count == 1:
                    create_or_update_attendance(
                        emp,
                        att_date,
                        None,
                        None,
                        0,
                        first_id,
                        last_id,
                        skip_shift_time_rules=True,
                        is_holiday_work=is_holiday_work,
                    )
                    continue

                create_or_update_attendance(
                    emp,
                    att_date,
                    in_time,
                    out_time,
                    working_hours,
                    first_id,
                    last_id,
                    skip_shift_time_rules=True,
                    is_holiday_work=is_holiday_work,
                )
                continue

            logs = frappe.db.sql(
                """
                SELECT name, time
                FROM `tabEmployee Checkin`
                WHERE employee=%s
                AND DATE(time)=%s
                ORDER BY time ASC
            """,
                (emp, att_date),
                as_dict=True,
            )

            logs = filter_close_checkins(logs, threshold_minutes=2)

            if not logs:
                if is_holiday:
                    continue

                create_or_update_attendance(
                    emp,
                    att_date,
                    None,
                    None,
                    0,
                    None,
                    None,
                    skip_shift_time_rules=False,
                    is_holiday_work=False,
                )
                continue

            if is_holiday:
                is_holiday_work = True

            if len(logs) < 2:
                create_or_update_attendance(
                    emp,
                    att_date,
                    None,
                    None,
                    0,
                    logs[0]["name"],
                    logs[-1]["name"],
                    skip_shift_time_rules=False,
                    is_holiday_work=is_holiday_work,
                )
                continue

            in_time = normalize_to_minute(logs[0]["time"])
            out_time = normalize_to_minute(logs[-1]["time"])

            if in_time and out_time and out_time > in_time:
                working_seconds = (out_time - in_time).total_seconds()
                working_hours = working_seconds / 3600
            else:
                working_hours = 0

            if working_hours <= 0:
                create_or_update_attendance(
                    emp,
                    att_date,
                    None,
                    None,
                    0,
                    logs[0]["name"],
                    logs[-1]["name"],
                    skip_shift_time_rules=False,
                    is_holiday_work=is_holiday_work,
                )
                continue

            create_or_update_attendance(
                emp,
                att_date,
                in_time,
                out_time,
                working_hours,
                logs[0]["name"],
                logs[-1]["name"],
                skip_shift_time_rules=False,
                is_holiday_work=is_holiday_work,
            )

        except Exception as e:
            log_attendance_error(emp, att_date, "Main Scheduler Failed", e)

    frappe.db.commit()

# def run_daily_attendance(att_date=None,only_for_jammu=False,branch=None):
    
#     frappe.log_error("start_run_daily_attendance", f"Scheduler Started FOR Date: {att_date}")    
#     if not att_date:
#         att_date = add_days(getdate(), -1)
#     else:
#         att_date = getdate(att_date)

#     if only_for_jammu:
#             employees = frappe.get_all(
#                 "Employee",
#                 filters={"status": "Active", "branch": "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu" },
#                 pluck="name"
#             )
#     else:
#         filters = {"status": "Active"}

#         if branch:
#             filters["branch"] = branch

#         employees = frappe.get_all(
#             "Employee",
#             filters=filters,
#             pluck="name"
#         )
    

#     for emp in employees:
#         try:
#             if has_approved_leave(emp, att_date):
#                 continue

#             shift_type = get_employee_shift(emp, att_date)
            
#             if not shift_type:
#                 log_attendance_error(emp, att_date, "Shift not assigned")
#                 continue

#             shift_custom_type = frappe.db.get_value(
#                 "Shift Type", shift_type, "custom_shift_type"
#             )
#             is_holiday = is_holiday_or_weekoff(emp, att_date)
#             off_day_approved = has_approved_off_day_work(emp, att_date)
#             is_holiday_work = is_holiday and off_day_approved
#             if shift_custom_type == "24 hours":
                
#                 first_in, last_out,first_checkin_id, last_checkin_id, working_hours, log_count = (
#                     get_24_hour_working_hours(emp, att_date,shift_type)
#                 )
#                 if log_count == 0:
#                     if log_count == 0 and is_holiday:
#                         continue
#                     create_or_update_attendance(
#                         emp,
#                         att_date,
#                         None,
#                         None,
#                         0,
#                         None,
#                         skip_shift_time_rules=True,
#                         is_holiday_work=is_holiday_work
#                     )
#                     continue

#                 if log_count == 1:
#                     if is_holiday and not off_day_approved:
#                         continue   
#                     create_or_update_attendance(
#                         emp,
#                         att_date,
#                         None,
#                         None,
#                         0,
#                         first_checkin_id,
#                         last_checkin_id,
#                         skip_shift_time_rules=True,
#                         is_holiday_work=is_holiday_work
#                     )
#                     continue

#                 create_or_update_attendance(
#                     emp,
#                     att_date,
#                     first_in,
#                     last_out,
#                     working_hours,
#                    first_checkin_id,
#                     last_checkin_id,
#                     skip_shift_time_rules=True,
#                     is_holiday_work=is_holiday_work
#                 )
#                 continue
                
            
#             if shift_custom_type == "Night":
        
#                 in_time, out_time, first_id, last_id, working_hours, log_count = \
#                     get_night_shift_logs(emp, att_date)

        
#                 if log_count == 0:
#                     if log_count == 0 and is_holiday:
#                         continue
#                     create_or_update_attendance(
#                         emp,
#                         att_date,
#                         None,
#                         None,
#                         0,
#                         None,
#                         None,
#                         skip_shift_time_rules=True,
#                         is_holiday_work=is_holiday_work
#                     )
#                     continue
#                 if log_count == 1:
#                     if is_holiday and not off_day_approved:
#                         continue  
#                     create_or_update_attendance(
#                         emp,
#                         att_date,
#                         None,
#                         None,
#                         0,
#                         first_id,
#                         last_id,
#                         skip_shift_time_rules=True,
#                         is_holiday_work=is_holiday_work
#                     )
#                     continue
#                 create_or_update_attendance(
#                     emp,
#                     att_date,
#                     in_time,
#                     out_time,
#                     working_hours,
#                     first_id,
#                     last_id,
#                     skip_shift_time_rules=True,
#                     is_holiday_work=is_holiday_work
#                 )
#                 continue
#             if is_holiday and not off_day_approved:
#                 continue
#             logs = frappe.db.sql("""
#                 SELECT
#                     name,
#                     time
#                 FROM `tabEmployee Checkin`
#                 WHERE employee=%s
#                 AND DATE(time)=%s
#                 ORDER BY time ASC
#             """, (emp, att_date), as_dict=True)
#             logs = filter_close_checkins(logs, threshold_minutes=2)
#             if not logs:
#                 if log_count == 0 and is_holiday:
#                         continue
#                 create_or_update_attendance(
#                     emp, att_date, None, None, 0, None,None,skip_shift_time_rules=False,is_holiday_work=is_holiday_work
#                 ),
#                 continue

#             if len(logs) < 2:
#                 if is_holiday and not off_day_approved:
#                         continue
#                 create_or_update_attendance(
#                     emp, att_date, None, None, 0, logs[0]["name"],logs[-1]["name"],skip_shift_time_rules=False,is_holiday_work=is_holiday_work
#                 )
#                 continue
            
#             in_time = logs[0]["time"]
#             out_time = logs[-1]["time"]
#             in_time = normalize_to_minute(in_time)
#             out_time = normalize_to_minute(out_time)

#             if in_time and out_time and out_time > in_time:
#                 working_seconds = (out_time - in_time).total_seconds()
#                 working_hours = working_seconds / 3600
#             else:
#                 working_hours = 0

#             if working_hours <= 0:
#                 create_or_update_attendance(
#                     emp, att_date, None, None, 0,logs[0]["name"], logs[-1]["name"],skip_shift_time_rules=False,is_holiday_work=is_holiday_work
#                 )
#                 continue

#             create_or_update_attendance(
#                 emp,
#                 att_date,
#                 in_time,
#                 out_time,
#                 working_hours,
#                 logs[0]["name"],
#                 logs[-1]["name"] ,skip_shift_time_rules=False,  # ✅ MAX CHECKIN ID,
#                 is_holiday_work=is_holiday_work
#             )

#         except Exception as e:
#             log_attendance_error(
#                 emp, att_date, "Main Scheduler Failed", e
#             )

#     frappe.db.commit()
def has_approved_off_day_work(employee, date):

    return frappe.db.exists(
        "Off-Day Work Request",
        {
            "employee": employee,
            "date": date,
            "workflow_state": "Approved"
        }
    )

# def get_24_hour_working_hours(employee, date):
#     logs = frappe.db.sql("""
#         SELECT name, time
#         FROM `tabEmployee Checkin`
#         WHERE employee=%s
#           AND DATE(time)=%s
#         ORDER BY time ASC
#     """, (employee, date), as_dict=True)

#     if not logs or len(logs) < 2:
#         return None, None, None, 0  

#     first_in = logs[0]["time"]     
#     last_out = logs[-1]["time"]    
#     last_checkin_id = logs[-1]["name"]

#     working_seconds = (last_out - first_in).total_seconds()
#     working_hours = working_seconds / 3600 

#     return first_in, last_out, last_checkin_id, working_hours
# def get_24_hour_working_hours(employee, date):
#     logs = frappe.db.sql("""
#         SELECT name, time
#         FROM `tabEmployee Checkin`
#         WHERE employee=%s
#           AND DATE(time)=%s
#         ORDER BY time ASC
#     """, (employee, date), as_dict=True)

#     if not logs:
#         return None, None, None, None, 0, 0  # ✅ 6


#     if len(logs) < 2:
#         return None, None,logs[0]["name"], logs[-1]["name"], 0, len(logs)

#     first_in = logs[0]["time"]
#     last_out = logs[-1]["time"]
#     first_checkin_id=logs[0]["name"],
#     last_checkin_id = logs[-1]["name"]

#     working_hours = (last_out - first_in).total_seconds() / 3600

#     return first_in, last_out,first_checkin_id, last_checkin_id, working_hours, len(logs)
# def get_24_hour_working_hours(employee, date, shift_type):
#     shift = frappe.db.get_value(
#         "Shift Type",
#         shift_type,
#         ["start_time", "end_time", "custom_shift_type"],
#         as_dict=True
#     )

#     if not shift:
#         return None, None, None, None, 0, 0

        
#     is_24_hour = shift.custom_shift_type == "24 hours"
#     shift_start, shift_end = get_24_hour_shift_window(
#         date,
#         shift.start_time,
#         shift.end_time,
#         force_next_day=is_24_hour  # 🔥 THIS IS THE FIX
#     )

#     logs = frappe.db.sql("""
#         SELECT name, time
#         FROM `tabEmployee Checkin`
#         WHERE employee = %s
#           AND time >= %s
#           AND time < %s
#         ORDER BY time ASC
#     """, (employee, shift_start, shift_end), as_dict=True)

#     if not logs:
#         return None, None, None, None, 0, 0 

#     if len(logs) < 2:
#         return None, None, logs[0]["name"], logs[-1]["name"], 0, len(logs)
#     first_in = logs[0]["time"]
#     last_out = logs[-1]["time"]

#     working_hours = (last_out - first_in).total_seconds() / 3600
#     return (
#         first_in,
#         last_out,
#         logs[0]["name"],
#         logs[-1]["name"],
#         working_hours,
#         len(logs),
#     )
def get_24_hour_working_hours(employee, date, shift_type):
    shift = frappe.db.get_value(
        "Shift Type",
        shift_type,
        ["start_time", "end_time", "custom_shift_type"],
        as_dict=True
    )
    if not shift:
        return None, None, None, None, 0, 0

    is_24_hour = shift.custom_shift_type == "24 hours"

    shift_start, shift_end = get_24_hour_shift_window(
        date,
        shift.start_time,
        shift.end_time,
        force_next_day=is_24_hour
    )
    
    logs = frappe.db.sql("""
        SELECT name, time
        FROM `tabEmployee Checkin`
        WHERE employee = %s
          AND time >= %s
          AND time < %s
        ORDER BY time ASC
    """, (employee, shift_start, shift_end), as_dict=True)
    if employee =="20015": 
        print("ooooooooooo",logs,shift_start, shift_end)
    if not logs:
        return None, None, None, None, 0, 0
    logs = filter_close_checkins(logs, threshold_minutes=2)
    if not logs:
        return None, None, None, None, 0, 0
    if len(logs) < 2:
        return None, None, logs[0]["name"], logs[-1]["name"], 0, len(logs)
    first_in = logs[0]["time"]
    last_out = logs[-1]["time"]
    working_hours = (last_out - first_in).total_seconds() / 3600

    return (
        first_in,
        last_out,
        logs[0]["name"],
        logs[-1]["name"],
        working_hours,
        len(logs),
    )

def filter_close_checkins(logs, threshold_minutes=2):
    """
    Remove logs that occur within threshold_minutes of previous one.
    logs = list of dicts having key 'time'
    """
    if not logs:
        return []

    filtered = [logs[0]]
    threshold = timedelta(minutes=threshold_minutes)

    for log in logs[1:]:
        last_time = filtered[-1]["time"]
        current_time = log["time"]

        if current_time - last_time >= threshold:
            filtered.append(log)

    return filtered
from frappe.utils import get_datetime, add_days

def get_24_hour_shift_window(date, start_time, end_time, force_next_day=False):
    shift_start = get_datetime(f"{date} {start_time}")
    shift_end = get_datetime(f"{date} {end_time}")

    # 🔥 FORCE next day for 24-hour shifts
    if force_next_day:
        shift_end = add_days(shift_end, 1)

    # Normal cross-day logic (for night shifts)
    elif end_time <= start_time:
        shift_end = add_days(shift_end, 1)

    return shift_start, shift_end

def get_night_shift_logs(employee, att_date):
    """
    Night shift logic:
    IN  -> first log after 9 pM of attendance date
    OUT -> last log before 9 PM of next date
    """

    start_dt = get_datetime(att_date).replace(hour=9, minute=0)
    end_dt = get_datetime(add_days(att_date, 1)).replace(hour=8, minute=59, second=0)

    logs = frappe.get_all(
        "Employee Checkin",
        filters=[
            ["employee", "=", employee],
            ["time", ">=", start_dt],
            ["time", "<", end_dt]
        ],
        fields=["name", "time"],
        order_by="time asc"
    )

    if not logs:
        return None, None, None, None, 0, 0

    first_log = logs[0]
    last_log = logs[-1]

    in_time = normalize_to_minute(first_log["time"])
    out_time = normalize_to_minute(last_log["time"])

    if out_time > in_time:
        working_hours = (out_time - in_time).total_seconds() / 3600
    else:
        working_hours = 0

    return (
        in_time,
        out_time,
        first_log["name"],
        last_log["name"],
        working_hours,
        len(logs)
    )

# =========================================================
# LEAVE CHECK
# =========================================================

def has_approved_leave(employee, date):
    return frappe.db.exists(
        "Leave Application",
        {
            "employee": employee,
            "status": "Approved",
            "docstatus": 1,
            "from_date": ("<=", date),
            "to_date": (">=", date),
            "half_day": 0
        }
    )

# def has_approved_leave(employee, date):
#     return frappe.db.exists(
#         "Leave Application",
#         {
#             "employee": employee,
#             "status": "Approved",
#             "from_date": ("<=", date),
#             "to_date": (">=", date)
#         }
#     )
    


def is_holiday_or_weekoff(employee, date):
    holiday_list = frappe.db.get_value(
        "Employee", employee, "holiday_list"
    )

    # *For Safety
    correct_holiday_list = None
    
    
    assign_holiday_list = get_current_holiday_list(employee, date)
    
    if assign_holiday_list:
        # if not holiday_list:
        #     correct_holiday_list = assign_holiday_list
        # elif holiday_list != assign_holiday_list:
        #     correct_holiday_list = assign_holiday_list
        correct_holiday_list =  assign_holiday_list
    else:
        correct_holiday_list = holiday_list if holiday_list else None
    
    
    if not correct_holiday_list:
        log_attendance_error(
            employee, date, "Holiday list not set"
        )
        return False

    return frappe.db.exists(
        "Holiday",
        {
            "parent": correct_holiday_list,
            "holiday_date": date
        }
    )


# =========================================================
# MISSING CHECKOUT HANDLER
# =========================================================

def handle_missing_checkout(employee, date, in_time, shift_type):
    try:
        out_time = get_shift_end_datetime(shift_type, date)
        if not out_time:
            create_or_update_attendance(
                employee, date, in_time, None, 0,skip_shift_time_rules=False 
            )
            return

        working_hours = (out_time - in_time).total_seconds() / 3600

        create_or_update_attendance(
            employee, date, in_time, out_time, working_hours,skip_shift_time_rules=False 
        )

    except Exception as e:
        log_attendance_error(
            employee, date, "Missing Checkout Failed", e
        )

def create_or_update_attendance(
        employee,
        date,
        in_time,
        out_time,
        working_hours,
        first_checkin_id=None,
        last_checkin_id=None,
        skip_shift_time_rules=True,
        is_holiday_work=False
):
    try:
        no_checkin_found = not first_checkin_id and not last_checkin_id
 
        shift_type = get_employee_shift(employee, date)
        if not shift_type:
            return
        
        shift = frappe.db.get_value(
            "Shift Type",
            shift_type,
            [
                "start_time",
                "end_time",
                "late_entry_grace_period",
                "allow_check_out_after_shift_end_time",
                "working_hours_threshold_for_half_day",
                "working_hours_threshold_for_absent"
            ],
            as_dict=True
        )
        
        leave = frappe.db.get_value(
            "Leave Application",
            {
                "employee": employee,
                "status": "Approved",
                "from_date": ("<=", date),
                "to_date": (">=", date),
                "docstatus": 1
            },
            ["name", "half_day", "half_day_date"],
            as_dict=True
        )
 
        is_half_day_leave = bool(
            leave and leave.half_day and leave.half_day_date == date
        )
 
        late_entry = 0
        single_checkin = False
        if first_checkin_id and last_checkin_id:
            if first_checkin_id == last_checkin_id:
                single_checkin = True
                single_time = frappe.db.get_value(
                    "Employee Checkin",
                    first_checkin_id,
                    "time"
                )
                in_time = in_time or single_time
                out_time = None
            else:
                if in_time is None:
                    in_time = frappe.db.get_value(
                        "Employee Checkin",
                        first_checkin_id,
                        "time"
                    )
                if out_time is None:
                    out_time = frappe.db.get_value(
                        "Employee Checkin",
                        last_checkin_id,
                        "time"
                    )
 
        half_day_hours = float(
            shift.working_hours_threshold_for_half_day or 8
        )
        absent_hours = float(
            shift.working_hours_threshold_for_absent or 3
        )
 
        # 🔥 If holiday/weekoff work → only hours matter
        if is_holiday_work:
 
            if working_hours <= 0:
                status = "Absent"
            elif working_hours < half_day_hours:
                status = "Half Day"
            else:
                status = "Present"
 
        else:
            if working_hours <= absent_hours:
                status = "Absent"
            elif working_hours < half_day_hours:
                status = "Half Day"
            else:
                status = "Present"
 
 
 
        if is_half_day_leave:
            status = "Half Day"
        if single_checkin:
            status = "Partially"
        if status != "Absent":
            if in_time and out_time and not skip_shift_time_rules and not is_holiday_work:
 
                shift_start = combine_datetime(date, shift.start_time)
 
                allowed_late_minutes = shift.late_entry_grace_period
 
                if allowed_late_minutes and int(allowed_late_minutes) > 0:
 
                    latest_allowed_in = add_to_date(
                        shift_start,
                        minutes=int(allowed_late_minutes)
                    )
 
                    if in_time > latest_allowed_in:
                        late_entry = 1
                        status = "Half Day"
 
   
        attendance_name = frappe.db.exists(
            "Attendance",
            {
                "employee": employee,
                "attendance_date": date,
                "docstatus": ["!=", 2]
            }
        )
        old_status = None
        if attendance_name:
            old_status = frappe.db.get_value("Attendance", attendance_name, "status")
        employee_details = frappe.db.get_value(
            "Employee",
            employee,
            ["employee_name", "department", "company", "branch"],
            as_dict=True
        )
 
        if attendance_name:
 
            att_name = attendance_name
 
            frappe.db.set_value(
            "Attendance",
            att_name,
            {
                "in_time": in_time,
                "out_time": out_time,
                "working_hours": working_hours,
                "status": status,
                "late_entry": late_entry,
                "employee_name": employee_details.employee_name,
                "department": employee_details.department,
                "company": employee_details.company,
                "custom_branch": employee_details.branch,
            },
            update_modified=False
        )
        
        else:
 
            att_name = frappe.generate_hash(length=12)
 
            frappe.db.sql("""
                INSERT INTO `tabAttendance`
                (name, employee, employee_name, department, company,
                attendance_date, shift, in_time, out_time,
                working_hours, status, late_entry, custom_branch,
                docstatus, creation, modified, owner, modified_by)
 
                VALUES (%s,%s,%s,%s,%s,
                        %s,%s,%s,%s,
                        %s,%s,%s,%s,
                        1, NOW(), NOW(), %s, %s)
            """, (
                att_name,
                employee,
                employee_details.employee_name,
                employee_details.department,
                employee_details.company,
                date,
                shift_type,
                in_time,
                out_time,
                working_hours,
                status,
                late_entry,
                employee_details.branch,
                frappe.session.user,
                frappe.session.user,
            ))
 
            frappe.db.commit()
        if first_checkin_id:
            frappe.db.set_value(
                "Employee Checkin",
                first_checkin_id,
                "attendance",
                att_name,
                update_modified=False
            )
 
        if last_checkin_id:
            frappe.db.set_value(
                "Employee Checkin",
                last_checkin_id,
                "attendance",
                att_name,
                update_modified=False
            )
 
        if is_half_day_leave:
 
            absent_threshold = float(
                shift.working_hours_threshold_for_absent or 0
            )
            if working_hours <= absent_threshold:
                half_day_status = "Absent"
            else:
                half_day_status = "Present"
 
            frappe.db.set_value(
                "Attendance",
                att_name,
                "half_day_status",
                half_day_status,
                update_modified=False
            )
 
 
        # Clear old penalty first if status changed
        if old_status and old_status != status:
            revert_penalty_leave(att_name)
        if is_holiday_work:
            revert_penalty_leave(att_name)
        # Apply penalty only if checkin exists
        if not is_holiday_work:

            if status in ["Absent", "Half Day", "Partially"]:

                if not is_half_day_leave and not no_checkin_found:
                    deduct_leave_by_priority(
                        employee,
                        date,
                        status,
                        att_name
                    )
        
 
 
        
        # if old_status in ("Absent", "Half Day","Partially") and status == "Present":
        #     revert_penalty_leave(att_name)
        return att_name
        
    except Exception as e:
        log_attendance_error(
            employee,
            date,
            "Attendance Save Failed",
            e
        )

# def create_or_update_attendance(
#         employee,
#         date,
#         in_time,
#         out_time,
#         working_hours,
#         first_checkin_id=None,
#         last_checkin_id=None,
#         skip_shift_time_rules=True,
#         is_holiday_work=False
# ):
#     try:
#         no_checkin_found = not first_checkin_id and not last_checkin_id
 
#         shift_type = get_employee_shift(employee, date)
#         if not shift_type:
#             return
        
#         shift = frappe.db.get_value(
#             "Shift Type",
#             shift_type,
#             [
#                 "start_time",
#                 "end_time",
#                 "late_entry_grace_period",
#                 "allow_check_out_after_shift_end_time",
#                 "working_hours_threshold_for_half_day",
#                 "working_hours_threshold_for_absent"
#             ],
#             as_dict=True
#         )
        
#         leave = frappe.db.get_value(
#             "Leave Application",
#             {
#                 "employee": employee,
#                 "status": "Approved",
#                 "from_date": ("<=", date),
#                 "to_date": (">=", date),
#                 "docstatus": 1
#             },
#             ["name", "half_day", "half_day_date"],
#             as_dict=True
#         )
 
#         is_half_day_leave = bool(
#             leave and leave.half_day and leave.half_day_date == date
#         )
 
#         late_entry = 0
#         single_checkin = False
#         if first_checkin_id and last_checkin_id:
#             if first_checkin_id == last_checkin_id:
#                 single_checkin = True
#                 single_time = frappe.db.get_value(
#                     "Employee Checkin",
#                     first_checkin_id,
#                     "time"
#                 )
#                 in_time = in_time or single_time
#                 out_time = None
#             else:
#                 if in_time is None:
#                     in_time = frappe.db.get_value(
#                         "Employee Checkin",
#                         first_checkin_id,
#                         "time"
#                     )
#                 if out_time is None:
#                     out_time = frappe.db.get_value(
#                         "Employee Checkin",
#                         last_checkin_id,
#                         "time"
#                     )
 
#         half_day_hours = float(
#             shift.working_hours_threshold_for_half_day or 8
#         )
#         absent_hours = float(
#             shift.working_hours_threshold_for_absent or 3
#         )
 
#         # 🔥 If holiday/weekoff work → only hours matter
#         if is_holiday_work:
 
#             if working_hours <= 0:
#                 status = "Absent"
#             elif working_hours < half_day_hours:
#                 status = "Half Day"
#             else:
#                 status = "Present"
 
#         else:
#             if working_hours <= absent_hours:
#                 status = "Absent"
#             elif working_hours < half_day_hours:
#                 status = "Half Day"
#             else:
#                 status = "Present"
 
 
 
#         if is_half_day_leave:
#             status = "Half Day"
#         if single_checkin:
#             status = "Partially"
#         if status != "Absent":
#             if in_time and out_time and not skip_shift_time_rules and not is_holiday_work:
 
#                 shift_start = combine_datetime(date, shift.start_time)
 
#                 allowed_late_minutes = shift.late_entry_grace_period
 
#                 if allowed_late_minutes and int(allowed_late_minutes) > 0:
 
#                     latest_allowed_in = add_to_date(
#                         shift_start,
#                         minutes=int(allowed_late_minutes)
#                     )
 
#                     if in_time > latest_allowed_in:
#                         late_entry = 1
#                         status = "Half Day"
 
   
#         attendance_name = frappe.db.exists(
#             "Attendance",
#             {
#                 "employee": employee,
#                 "attendance_date": date,
#                 "docstatus": ["!=", 2]
#             }
#         )
#         old_status = None
#         if attendance_name:
#             old_status = frappe.db.get_value("Attendance", attendance_name, "status")
#         employee_details = frappe.db.get_value(
#             "Employee",
#             employee,
#             ["employee_name", "department", "company", "branch"],
#             as_dict=True
#         )
 
#         if attendance_name:
 
#             att_name = attendance_name
 
#             frappe.db.set_value(
#             "Attendance",
#             att_name,
#             {
#                 "in_time": in_time,
#                 "out_time": out_time,
#                 "working_hours": working_hours,
#                 "status": status,
#                 "late_entry": late_entry,
#                 "employee_name": employee_details.employee_name,
#                 "department": employee_details.department,
#                 "company": employee_details.company,
#                 "custom_branch": employee_details.branch,
#             },
#             update_modified=False
#         )
        
#         else:
 
#             att_name = frappe.generate_hash(length=12)
 
#             frappe.db.sql("""
#                 INSERT INTO `tabAttendance`
#                 (name, employee, employee_name, department, company,
#                 attendance_date, shift, in_time, out_time,
#                 working_hours, status, late_entry, custom_branch,
#                 docstatus, creation, modified, owner, modified_by)
 
#                 VALUES (%s,%s,%s,%s,%s,
#                         %s,%s,%s,%s,
#                         %s,%s,%s,%s,
#                         1, NOW(), NOW(), %s, %s)
#             """, (
#                 att_name,
#                 employee,
#                 employee_details.employee_name,
#                 employee_details.department,
#                 employee_details.company,
#                 date,
#                 shift_type,
#                 in_time,
#                 out_time,
#                 working_hours,
#                 status,
#                 late_entry,
#                 employee_details.branch,
#                 frappe.session.user,
#                 frappe.session.user,
#             ))
 
#             frappe.db.commit()
#         if first_checkin_id:
#             frappe.db.set_value(
#                 "Employee Checkin",
#                 first_checkin_id,
#                 "attendance",
#                 att_name,
#                 update_modified=False
#             )
 
#         if last_checkin_id:
#             frappe.db.set_value(
#                 "Employee Checkin",
#                 last_checkin_id,
#                 "attendance",
#                 att_name,
#                 update_modified=False
#             )
 
#         if is_half_day_leave:
 
#             absent_threshold = float(
#                 shift.working_hours_threshold_for_absent or 0
#             )
#             if working_hours <= absent_threshold:
#                 half_day_status = "Absent"
#             else:
#                 half_day_status = "Present"
 
#             frappe.db.set_value(
#                 "Attendance",
#                 att_name,
#                 "half_day_status",
#                 half_day_status,
#                 update_modified=False
#             )
 
 
#         # Clear old penalty first if status changed
#         if old_status and old_status != status:
#             revert_penalty_leave(att_name)
 
#         # Apply penalty only if checkin exists
#         if status in ["Absent", "Half Day", "Partially"]:
 
#             if not is_half_day_leave and not no_checkin_found:
#                 deduct_leave_by_priority(
#                     employee,
#                     date,
#                     status,
#                     att_name
#                 )
 
 
 
        
#         # if old_status in ("Absent", "Half Day","Partially") and status == "Present":
#         #     revert_penalty_leave(att_name)
#         return att_name
        
#     except Exception as e:
#         log_attendance_error(
#             employee,
#             date,
#             "Attendance Save Failed",
#             e
#         )


# def create_or_update_attendance(
#         employee,
#         date,
#         in_time,
#         out_time,
#         working_hours,
#         first_checkin_id=None,
#         last_checkin_id=None,
#         skip_shift_time_rules=True,
#         is_holiday_work=False
# ):
#     try:
#         shift_type = get_employee_shift(employee, date)
#         if not shift_type:
#             return
        
#         shift = frappe.db.get_value(
#             "Shift Type",
#             shift_type,
#             [
#                 "start_time",
#                 "end_time",
#                 "late_entry_grace_period",
#                 "allow_check_out_after_shift_end_time",
#                 "working_hours_threshold_for_half_day",
#                 "working_hours_threshold_for_absent"
#             ],
#             as_dict=True
#         )
        
#         leave = frappe.db.get_value(
#             "Leave Application",
#             {
#                 "employee": employee,
#                 "status": "Approved",
#                 "from_date": ("<=", date),
#                 "to_date": (">=", date),
#                 "docstatus": 1
#             },
#             ["name", "half_day", "half_day_date"],
#             as_dict=True
#         )

#         is_half_day_leave = bool(
#             leave and leave.half_day and leave.half_day_date == date
#         )

#         late_entry = 0
#         single_checkin = False
#         if first_checkin_id and last_checkin_id:
#             if first_checkin_id == last_checkin_id:
#                 single_checkin = True
#                 single_time = frappe.db.get_value(
#                     "Employee Checkin",
#                     first_checkin_id,
#                     "time"
#                 )
#                 in_time = in_time or single_time
#                 out_time = None
#             else:
#                 if in_time is None:
#                     in_time = frappe.db.get_value(
#                         "Employee Checkin",
#                         first_checkin_id,
#                         "time"
#                     )
#                 if out_time is None:
#                     out_time = frappe.db.get_value(
#                         "Employee Checkin",
#                         last_checkin_id,
#                         "time"
#                     )

#         half_day_hours = float(
#             shift.working_hours_threshold_for_half_day or 8
#         )
#         absent_hours = float(
#             shift.working_hours_threshold_for_absent or 3
#         )

#         # 🔥 If holiday/weekoff work → only hours matter
#         if is_holiday_work:

#             if working_hours <= 0:
#                 status = "Absent"
#             elif working_hours < half_day_hours:
#                 status = "Half Day"
#             else:
#                 status = "Present"

#         else:
#             if working_hours <= absent_hours:
#                 status = "Absent"
#             elif working_hours < half_day_hours:
#                 status = "Half Day"
#             else:
#                 status = "Present"



#         if is_half_day_leave:
#             status = "Half Day"
#         if single_checkin:
#             status = "Partially"
#         if status != "Absent":
#             if in_time and out_time and not skip_shift_time_rules and not is_holiday_work:

#                 shift_start = combine_datetime(date, shift.start_time)

#                 allowed_late_minutes = shift.late_entry_grace_period

#                 if allowed_late_minutes and int(allowed_late_minutes) > 0:

#                     latest_allowed_in = add_to_date(
#                         shift_start,
#                         minutes=int(allowed_late_minutes)
#                     )

#                     if in_time > latest_allowed_in:
#                         late_entry = 1
#                         status = "Half Day"

   
#         attendance_name = frappe.db.exists(
#             "Attendance",
#             {
#                 "employee": employee,
#                 "attendance_date": date,
#                 "docstatus": ["!=", 2]
#             }
#         )
#         old_status = None
#         if attendance_name:
#             old_status = frappe.db.get_value("Attendance", attendance_name, "status")
#         employee_details = frappe.db.get_value(
#             "Employee",
#             employee,
#             ["employee_name", "department", "company", "branch"],
#             as_dict=True
#         )

#         if attendance_name:

#             att_name = attendance_name

#             frappe.db.set_value(
#             "Attendance",
#             att_name,
#             {
#                 "in_time": in_time,
#                 "out_time": out_time,
#                 "working_hours": working_hours,
#                 "status": status,
#                 "late_entry": late_entry,
#                 "employee_name": employee_details.employee_name,
#                 "department": employee_details.department,
#                 "company": employee_details.company,
#                 "custom_branch": employee_details.branch,
#             },
#             update_modified=False
#         )
        
#         else:

#             att_name = frappe.generate_hash(length=12)

#             frappe.db.sql("""
#                 INSERT INTO `tabAttendance`
#                 (name, employee, employee_name, department, company,
#                 attendance_date, shift, in_time, out_time,
#                 working_hours, status, late_entry, custom_branch,
#                 docstatus, creation, modified, owner, modified_by)

#                 VALUES (%s,%s,%s,%s,%s,
#                         %s,%s,%s,%s,
#                         %s,%s,%s,%s,
#                         1, NOW(), NOW(), %s, %s)
#             """, (
#                 att_name,
#                 employee,
#                 employee_details.employee_name,
#                 employee_details.department,
#                 employee_details.company,
#                 date,
#                 shift_type,
#                 in_time,
#                 out_time,
#                 working_hours,
#                 status,
#                 late_entry,
#                 employee_details.branch,
#                 frappe.session.user,
#                 frappe.session.user,
#             ))

#             frappe.db.commit()
#         if first_checkin_id:
#             frappe.db.set_value(
#                 "Employee Checkin",
#                 first_checkin_id,
#                 "attendance",
#                 att_name,
#                 update_modified=False
#             )

#         if last_checkin_id:
#             frappe.db.set_value(
#                 "Employee Checkin",
#                 last_checkin_id,
#                 "attendance",
#                 att_name,
#                 update_modified=False
#             )

#         if is_half_day_leave:

#             absent_threshold = float(
#                 shift.working_hours_threshold_for_absent or 0
#             )
#             if working_hours <= absent_threshold:
#                 half_day_status = "Absent"
#             else:
#                 half_day_status = "Present"

#             frappe.db.set_value(
#                 "Attendance",
#                 att_name,
#                 "half_day_status",
#                 half_day_status,
#                 update_modified=False
#             )


#         # 🔥 Clear old penalty first if status changed
#         if old_status and old_status != status:
#             revert_penalty_leave(att_name)

#         if status in ["Absent", "Half Day", "Partially"]:
#             if not is_half_day_leave:
#                 deduct_leave_by_priority(
#                     employee,
#                     date,
#                     status,
#                     att_name
#                 )


        
#         # if old_status in ("Absent", "Half Day","Partially") and status == "Present":
#         #     revert_penalty_leave(att_name)
#         return att_name
        
#     except Exception as e:
#         log_attendance_error(
#             employee,
#             date,
#             "Attendance Save Failed",
#             e
#         )


def combine_datetime(date, shift_time):
    """
    Handles both time and timedelta from Shift Type
    """
    if isinstance(shift_time, timedelta):
        seconds = int(shift_time.total_seconds())
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return datetime.combine(date, time(hours, minutes))

    return datetime.combine(date, shift_time)


# def deduct_leave_by_priority(employee, date, status, attendance):
#     priority = [
#         "Casual Leave",
#         "Sick Leave",
#         "Privilege Leave",
#         "Leave Without Pay"
#     ]

#     leave_days = 0.5 if status == "Half Day" else 1
#     att = frappe.get_doc("Attendance", attendance)
#     for leave_type in priority:
#         leave_type_doc = frappe.get_cached_doc("Leave Type", leave_type)

#         if leave_type_doc.is_lwp:
#             continue

#         balance = get_leave_balance_on(employee, leave_type, date)

#         if balance < leave_days:
#             continue

#         att.db_set({
#             "custom_penalty_leave_type": leave_type,
#             "custom_penalty_leave_count": leave_days,
#             "custom_is_penalize": 1
#         })

#         create_leave_ledger(
#             employee, leave_type, date, status, attendance
#         )

#         return  


#     lwp_type = next(
#         (lt for lt in priority
#          if frappe.get_cached_doc("Leave Type", lt).is_lwp),
#         None
#     )

#     if lwp_type:
#         att.db_set({
#             "custom_penalty_leave_type": lwp_type,
#             "custom_penalty_leave_count": leave_days,
#             "custom_is_penalize": 1
#         })

def deduct_leave_by_priority(employee, date, status, attendance):
    priority = [
        "Casual Leave",
        "Sick Leave",
        "Privilege Leave",
        "Leave Without Pay"
    ]

    if status == "Half Day":
        total_penalty_days = 0.5
    else:
        total_penalty_days = 1.0   # Absent OR Partially

    remaining_days = total_penalty_days

    att = frappe.get_doc("Attendance", attendance)

    if att.custom_is_penalize:
        return

    for leave_type in priority:
        balance = flt(get_leave_balance_on(employee, leave_type, date), 2)

        if balance <= 0:
            continue

        if balance < remaining_days:
            continue

        att.db_set({
            "custom_penalty_leave_type": leave_type,
            "custom_penalty_leave_count": -total_penalty_days,
            "custom_is_penalize": 1
        })

        create_leave_ledger(
            employee=employee,
            leave_type=leave_type,
            date=date,
            status=status,
            attendance=attendance,
            leave_days=remaining_days
        )

        return 

    lwp_type = frappe.db.get_value(
        "Leave Type", {"is_lwp": 1}, "name"
    )

    if lwp_type:
        att.db_set({
            "custom_penalty_leave_type": lwp_type,
            "custom_penalty_leave_count": -remaining_days,
            "custom_is_penalize": 1
        })

        create_leave_ledger(
            employee=employee,
            leave_type=lwp_type,
            date=date,
            status=status,
            attendance=attendance,
            leave_days=remaining_days,
            is_lwp=1
        )


def get_leave_allocation(employee, leave_type, date):
    allocation = frappe.db.sql("""
        SELECT name
        FROM `tabLeave Allocation`
        WHERE employee = %s
          AND leave_type = %s
          AND docstatus = 1
          AND from_date <= %s
          AND to_date >= %s
        ORDER BY from_date DESC
        LIMIT 1
    """, (employee, leave_type, date, date), as_dict=True)

    return allocation[0].name if allocation else None


def get_leave_balance(employee, leave_type, date):
    try:
        return frappe.get_value(
            "Leave Ledger Entry",
            {"employee": employee, "leave_type": leave_type},
            "sum(leaves)"
        ) or 0
    except Exception:
        return 0

# def create_leave_ledger(employee, leave_type, date, status, attendance):
#     employee_doc = frappe.get_cached_doc("Employee", employee)
#     leave_type_doc = frappe.get_cached_doc("Leave Type", leave_type)

#     if leave_type_doc.is_lwp:
#         return

#     leave_days = 0.5 if status == "Half Day" else 1
#     allocation = get_leave_allocation(employee, leave_type, date)

#     if not allocation:
#         return

#     if frappe.db.exists(
#         "Leave Ledger Entry",
#         {
#             "employee": employee,
#             "from_date": date,
#             "transaction_type": "Leave Allocation",
#             "transaction_name": allocation,
#             "custom_attendance":attendance,
#             "custom_is_penalty": 1
#         }
#     ):
#         return

#     doc = frappe.get_doc({
#         "doctype": "Leave Ledger Entry",
#         "employee": employee,
#         "employee_name": employee_doc.employee_name,
#         "company": employee_doc.company,
#         "holiday_list": employee_doc.holiday_list,
#         "leave_type": leave_type,
#         "posting_date": date,
#         "from_date": date,
#         "to_date": date,
#         "leaves": -leave_days,
#         "is_lwp": 0,
#         "custom_is_penalty": 1,
#         "custom_attendance": attendance,
#         "transaction_type": "Leave Allocation",
#         "transaction_name": allocation
#     })

#     doc.insert(ignore_permissions=True)
#     doc.submit()
def create_leave_ledger(
    employee,
    leave_type,
    date,
    status,
    attendance,
    leave_days=None,
    is_lwp=0
):
    employee_doc = frappe.get_cached_doc("Employee", employee)
    leave_type_doc = frappe.get_cached_doc("Leave Type", leave_type)

    if leave_days is None:
        leave_days = 0.5 if status == "Half Day" else 1

    allocation = None
    if not leave_type_doc.is_lwp:
        allocation = get_leave_allocation(employee, leave_type, date)
        if not allocation:
            return

    t_date = getdate(date)
    if t_date.month >= 4:
        to_date = getdate(f"{t_date.year + 1}-03-31")
    else:
        to_date = getdate(f"{t_date.year}-03-31")
    
    doc = frappe.get_doc({
        "doctype": "Leave Ledger Entry",
        "employee": employee,
        "employee_name": employee_doc.employee_name,
        "company": employee_doc.company,
        "holiday_list": employee_doc.holiday_list,
        "leave_type": leave_type,
        "posting_date": date,
        "from_date": date,
        "to_date": to_date,
        "leaves": -leave_days,
        "is_lwp": 1 if leave_type_doc.is_lwp or is_lwp else 0,
        "custom_is_penalty": 1,
        "custom_attendance": attendance,
        "transaction_type": "Leave Allocation" if allocation else "Leave Application",
        "transaction_name": allocation
    })

    doc.insert(ignore_permissions=True)
    doc.submit()

JAMMU_BRANCH = "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu"
SRINAGAR_BRANCH = "Jammu and Kashmir Milk Producers Co-operative Ltd Srinagar"


# =========================================================
# SHIFT HELPERS
# =========================================================

# def get_required_hours_by_date(employee, date):
#     date = getdate(date)

#     emp = frappe.db.get_value(
#         "Employee",
#         employee,
#         ["branch", "gender", "custom_attendance_source"],
#         as_dict=True
#     )

#     if (
#         emp.branch == JAMMU_BRANCH
#         and emp.gender == "Female"
#         and emp.custom_attendance_source == "Field"
#         and date.month in (12, 1)
#     ):
#         return 7

#     if emp.branch == SRINAGAR_BRANCH:
#         if 4 <= date.month <= 9:
#             return 8
#         return 7

#     return 8
JAMMU_BRANCH = "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu"
SRINAGAR_BRANCH = "Jammu and Kashmir Milk Producers Co-operative Ltd Cheshmashahi Srinagar"
DEC_JAN = (12, 1)

def get_required_hours_by_date(employee, date):
    date = getdate(date)

    emp = frappe.db.get_value(
        "Employee",
        employee,
        ["branch", "gender", "custom_attendance_source"],
        as_dict=True
    )

    if (
        emp.branch == JAMMU_BRANCH
        and emp.gender == "Female"
        and emp.custom_attendance_source == "Field"
        and date.month in DEC_JAN
    ):
        return 7

    if emp.branch == JAMMU_BRANCH:
        return 8

    if emp.branch == SRINAGAR_BRANCH:
        if 4 <= date.month <= 9: 
            return 8
        return 7

    return 8



# def get_employee_shift(employee, date):
#     date = getdate(date)

#     assigned_shift = frappe.db.get_value(
#         "Shift Assignment",
#         {
#             "employee": employee,
#             "start_date": ("<=", date),
#             "end_date": (">=", date),
#             "status": "Active"
#         },
#         "shift_type"
#     )

#     if assigned_shift:
#         return assigned_shift

#     default_shift = frappe.db.get_value(
#         "Employee", employee, "default_shift"
#     )

#     if not default_shift:
#         return None

#     shift_type = frappe.db.get_value(
#         "Shift Type", default_shift, "custom_shift_type"
#     )
    

#     if not shift_type:
#         return default_shift

#     required_hours = get_required_hours_by_date(employee, date)

#     branch = frappe.db.get_value("Employee", employee, "branch")

#     shift = frappe.db.get_value(
#         "Shift Type",
#         {
#             "custom_branch": branch,
#             "custom_shift_type": shift_type,   # General / Morning / Day / Night / 24H
#             "custom_hours": f"{required_hours}hours"
#         },
#         "name"
#     )

#     if shift:
#         return shift

#     return default_shift

def get_employee_shift(employee, date):
    date = getdate(date)
    
    assigned_shift = frappe.db.get_value(
        "Shift Assignment",
        {
            "employee": employee,
            "start_date": ("<=", date),
            "end_date": (">=", date),
            "status": "Active"
        },
        "shift_type"
    )

    if assigned_shift:
        return assigned_shift

    emp = frappe.db.get_value(
        "Employee",
        employee,
        [
            "default_shift",
            "branch",
            "custom_attendance_source"
        ],
        as_dict=True
    )

    if not emp or not emp.default_shift:
        return None

    shift_type = frappe.db.get_value(
        "Shift Type",
        emp.default_shift,
        "custom_shift_type"
    )
    if not shift_type:
        return emp.default_shift

    required_hours = get_required_hours_by_date(employee, date)

    shift = frappe.db.get_value(
        "Shift Type",
        {
            "custom_branch": emp.branch,
            "custom_shift_type": shift_type,
            "custom_attendance_source": emp.custom_attendance_source, 
            "custom_hours": f"{required_hours}hours"                 
        },
        "name"
    )
    if employee=="20015":
        print("call",emp.default_shift)
    # 6️⃣ Return matched shift or fallback
    return shift or emp.default_shift
def get_shift_end_datetime(shift_type, date):
    end_time = frappe.db.get_value(
        "Shift Type", shift_type, "end_time"
    )
    if not end_time:
        return None

    return datetime.combine(date, end_time)



def log_attendance_error(employee, date, step, exc=None):
    message = f"""
Employee : {employee}
Date     : {date}
Step     : {step}
"""

    if exc:
        message += "\n\n" + frappe.get_traceback()

    frappe.log_error(
        title=f"Auto Attendance Error : {date}",
        message=message
    )





# =========================================================
# ENTRY POINT (Scheduler – Daily) for Auto Comp-Off Creation
# =========================================================

@frappe.whitelist()
def process_comp_off_scheduler(comp_off_date=None):
    """
    Runs daily.
    Checks only comp_off_date.
    """

    if not comp_off_date:
        comp_off_date = add_days(getdate(), -1)
    else:
        comp_off_date = getdate(comp_off_date)

    frappe.log_error("start_process_comp_off_scheduler", f"Scheduler Started FOR Date: {comp_off_date}")

    requests = frappe.get_all(
        "Off-Day Work Request",
        filters={
            "workflow_state": "Approved",
            "date": comp_off_date,
            "docstatus": 1,
            "comp_off_created": 0
        },
        fields=["name", "employee", "date"]
    )

    frappe.log_error("comp_off_request_list", f"{requests}")
    for req in requests:
        
        try:
            process_working_day(req)
        
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Comp-Off Scheduler Error - {req.name}"
            )
    frappe.db.commit()

# =========================================================
# PROCESS SINGLE REQUEST
# =========================================================


def process_working_day(req):
    """
    Main entry point per Off-Day Working Request
    """

    attendance = get_attendance(req["employee"], req["date"])
    if not attendance:
        frappe.log_error("start_process_comp_off_scheduler", f"Full day Attendance not found for employee: {req['date']} - {req['employee']}")
        return

    if(req["employee"] == "20082: Harshiya Gupta"):
        frappe.log_error("comp_off_day_Working", f"{attendance}")
    
    
    holiday = get_holiday_details(req["employee"], req["date"])
    if(req["employee"] == "20082: Harshiya Gupta"):
        frappe.log_error("compoff_holiday", f"{holiday}")
    
    if not holiday:
        frappe.log_error("start_process_comp_off_scheduler", f"Holiday details not found for employee: {req['date']} - {req['employee']}")
        return

    # WO OR Normal Holiday OR RH+WO
    if holiday["is_wo"] or not holiday["is_rh"]:
        if(req["employee"] == "20082: Harshiya Gupta"):
            frappe.log_error("comp_off", "is wo")
        allocation = create_comp_off(req["employee"], req["date"])

        # Update Request
        if(req["employee"] == "20082: Harshiya Gupta"):
            frappe.log_error("comp_off_allocation", f"{allocation}")
        frappe.db.set_value(
            "Off-Day Work Request",
            req["name"],
            {
                "attendance": attendance,
                "leave_allocation": allocation.name,
                "comp_off_created": 1
            }
        )
        try:
            handle_workflow_notification(req["name"])
        except Exception as e:
            frappe.log_error("handle notification errror", f"{frappe.get_traceback()}")    
        return

    # RH only
    handle_rh_only(req, attendance, holiday)


# =========================================================
# ATTENDANCE CHECK
# =========================================================


def get_attendance(employee, date):
    return frappe.db.get_value(
        "Attendance",
        {
            "employee": employee,
            "attendance_date": date,
            "status": "Present",
            "docstatus": 1
        },
        "name"
    )


# =========================================================
# DAY TYPE IDENTIFICATION
# =========================================================


def get_holiday_details(employee, date):
    holiday_list = frappe.db.get_value(
        "Employee",
        employee,
        "holiday_list"
    )
    if not holiday_list:
        return None

    holiday = frappe.db.get_value(
        "Holiday",
        {
            "parent": holiday_list,
            "holiday_date": date
        },
        [
            "weekly_off",
            "custom_is_restricted_holiday",
            "custom_restricted_holiday_date"
        ],
        as_dict=True
    )

    if not holiday:
        return None

    return {
        "is_wo": bool(holiday.weekly_off),
        "is_rh": bool(holiday.custom_is_restricted_holiday),
        "pair_date": holiday.custom_restricted_holiday_date
    }


# =========================================================
# RH ONLY HANDLER
# =========================================================


def handle_rh_only(req, attendance, holiday):

    pair_date = holiday.get("pair_date")
    if not pair_date:
        return

    pair_holiday = get_holiday_details(req["employee"], pair_date)

    # RH + WO (past or future) → immediate
    if pair_holiday and pair_holiday["is_wo"]:
        allocation = create_comp_off(req["employee"], req["date"])

        # Update Request
        frappe.db.set_value(
            "Off-Day Work Request",
            req["name"],
            {
                "attendance": attendance,
                "leave_allocation": allocation.name,
                "comp_off_created": 1
            }
        )
        handle_workflow_notification(req["name"])
        return

    # Pair is future RH-only → skip
    if pair_date > req["date"]:
        return

    # Pair is past RH-only → both must be present
    pair_attendance = get_attendance(req["employee"], pair_date)
    if pair_attendance:
        allocation = create_comp_off(req["employee"], req["date"])

        # Update Request
        frappe.db.set_value(
            "Off-Day Work Request",
            req["name"],
            {
                "attendance": attendance,
                "leave_allocation": allocation.name,
                "comp_off_created": 1
            }
        )
        handle_workflow_notification(req["name"])


# =========================================================
# Comp Off ALLOCATION CREATION
# =========================================================


def create_comp_off(employee, date):
    """
    Creates 1 Comp-Off Leave Allocation
    Validity: 45 days
    """

    date = getdate(date)

    if already_created(employee, date):
        if(employee == "20082: Harshiya Gupta"):
            frappe.log_error("compoff_already_created", "already created")
        return

    leave_type = frappe.db.get_value(
        "Leave Type",
        {
            "is_compensatory": 1
        },
        "custom_validity_days"
    )
    if(employee == "20082: Harshiya Gupta"):
        frappe.log_error("comp_off leave type", f"{leave_type}")
    
    validity_days = leave_type if leave_type else 45

    if(employee == "20082: Harshiya Gupta"):
        frappe.log_error("comp_off_validate_days", f"{validity_days}")
    try:
        allocation = frappe.get_doc({
            "doctype": "Leave Allocation",
            "employee": employee,
            "leave_type": "Compensatory Off",
            "from_date": date,
            "to_date": add_days(date, validity_days),
            "new_leaves_allocated": 1
        })

        allocation.insert(ignore_permissions=True)
        allocation.submit()
    except Exception as e:
        frappe.log_error("compff_error", f"{frappe.get_traceback()}")

    return allocation


# =========================================================
# DUPLICATE CHECK
# =========================================================


def already_created(employee, date):
    return frappe.db.exists(
        "Leave Allocation",
        {
            "employee": employee,
            "leave_type": "Compensatory Off",
            "from_date": date,
            "docstatus": 1
        }
    )


def handle_workflow_notification(req_name):
    try:
        req = frappe.get_doc("Off-Day Work Request", req_name)
        
        frappe.log_error("off_dar_rec", f"{req}")
        recipients = []
        user = frappe.db.get_value("Employee", req.employee, "user_id")
        recipients.append(user)

        notification_name = "Compensatory Off Created"

        notification_doc = frappe.get_doc("Notification", notification_name)
        if notification_doc:

            # Call your custom notification function
            send_notification_email(
                recipients=recipients,
                doctype=req.doctype,
                docname=req.name,
                notification_name=notification_name,
                send_link=False,
                fallback_subject=f"Off-Day Work Request for {req.date}",
                fallback_message=f"Off-Day Work Request for { req.date } is now in '{ req.workflow_state }' state.",
                enabled=notification_doc.enabled,
                send_system_notification=notification_doc.send_system_notification,
                channel=notification_doc.channel
            )
    except Exception as e:
        frappe.log_error("error_handle_workflow_notification", frappe.get_traceback())


# * METHOD TO ALLOCATE CASUAL LEAVE AND SICK LEAVE TO CONFIRMED EMPLOYEES
# * THIS METHOD WILL RUN EVERY FIRST DAY OF THE FINANCIAL YEAR, I.E., 1ST APRIL
@frappe.whitelist()
def allocate_leaves_to_confirmed_employee(dt=None):
    try:
        frappe.log_error("Leave Allocation Job Started", "Allocating Casual Leave And Sick Leave")
        if dt:
            today_date = getdate(dt)
        else:
            today_date = getdate()
        financial_year_start = getdate(f"{today_date.year}-04-01")
        financial_year_end = getdate(f"{today_date.year + 1}-03-31")
        
        if today_date == financial_year_start:
            
            is_casual_leave_type = True if frappe.db.get_value("Leave Type", "Casual Leave", ["custom_leave_type"]) == "Casual Leave" else False
            
            is_sick_leave_type = True if frappe.db.get_value("Leave Type", "Sick Leave", ["custom_leave_type"]) == "Sick Leave" else False
            
            confirmed_employees = frappe.get_all("Employee", {"employment_type": "Confirmed", "status": "Active"}, ["name"])
            
            if is_casual_leave_type or is_sick_leave_type:
            # if is_casual_leave_type:
                for emp in confirmed_employees:
                    
                    if is_casual_leave_type and not frappe.db.exists("Leave Allocation", {"employee": emp.name, "leave_type": "Casual Leave", "from_date":["<=", financial_year_start], "to_date": [">=", financial_year_end]}):
                    # if is_casual_leave_type:
                        try:                                                                                                                            
                            cl_leave_allocation = frappe.get_doc({
                                "doctype": "Leave Allocation",
                                "employee": emp.name,
                                "leave_type": "Casual Leave",
                                "from_date": financial_year_start,
                                "to_date": financial_year_end,
                                "new_leaves_allocated": 12,
                                "custom_last_allocation_date": today_date
                            })
                            cl_leave_allocation.insert(ignore_permissions=True)
                            cl_leave_allocation.submit()
                        except Exception as e:
                            frappe.log_error(f"error_allocate_casual_leaves_{emp.name}", frappe.get_traceback())
                            
                            
                    
                    if is_sick_leave_type and not frappe.db.exists("Leave Allocation", {"employee": emp.name, "leave_type": "Sick Leave", "from_date":["<=", financial_year_start], "to_date": [">=", financial_year_end]}):
                        try:
                            
                            last_year_leave_balance = get_leave_balance_on(emp.name, "Sick Leave", getdate(f"{financial_year_start.year}-03-31"))
                            
                            if last_year_leave_balance > flt(28, 2):
                                sl_opening_balance = flt(28,2)
                                extra_sl = flt(last_year_leave_balance - flt(28,2), 2)
                            else:
                                sl_opening_balance = last_year_leave_balance
                                extra_sl = 0                                         
                            sl_leave_allocation = frappe.get_doc({
                                "doctype": "Leave Allocation",
                                "employee": emp.name,
                                "leave_type": "Sick Leave",
                                "from_date": financial_year_start,
                                "to_date": financial_year_end,
                                "new_leaves_allocated": 7,
                                "custom_opening_balance": sl_opening_balance,
                                "custom_last_allocation_date": today_date,
                                "custom_extra_sl_carry_forwarded_to_pl": extra_sl
                            })
                            sl_leave_allocation.insert(ignore_permissions=True)
                            sl_leave_allocation.submit()
                            
                            if extra_sl > 0:
                                extra_sl_allocation = frappe.get_doc({
                                    "doctype": "Leave Allocation",
                                    "employee": emp.name,
                                    "leave_type": "Privilege Leave",
                                    "from_date": financial_year_start,
                                    "to_date": financial_year_end,
                                    "new_leaves_allocated": extra_sl,
                                    "carry_forward": 1,
                                    "custom_extra_sl_carry_forwarded_to_pl": extra_sl,
                                    "custom_last_allocation_date": today_date
                                })
                                extra_sl_allocation.insert(ignore_permissions=True)
                                extra_sl_allocation.submit()
                            
                            
                        except Exception as e:
                            frappe.log_error(f"error_allocate_sick_leaves_{emp.name}", frappe.get_traceback())
                            
                frappe.db.commit()                                
            frappe.log_error("Leave Allocation Job Completed", "Completed Allocating Casual Leave and Sick Leave")
    except Exception as e:
        frappe.log_error(f"error_allocate_leaves_main", frappe.get_traceback())

# * METHOD TO ALLOCATE CASUAL LEAVE TO PROBATION AND CONTRACTUAL EMPLOYEES
# * THIS METHOD WILL RUN EVERY FIRST DAY OF THE MONTH
@frappe.whitelist()
def allocate_cl_to_probation_and_contract_employees(dt=None):
    try:
        frappe.log_error("CL Allocation to Probation and Contractual Employees Job Started", "CL Allocation to Probation and Contractual Employees rty")
        if dt:
            today_date = getdate(dt)
        else:
            today_date = getdate()
            
        month_start_date = getdate(f"{today_date.year}-{today_date.month}-01")
        
        if today_date == month_start_date:
                
        
            fy_start_date = getdate(f"{today_date.year - 1}-04-01") if today_date.month < 4 else getdate(f"{today_date.year}-04-01")
            fy_end_date   = getdate(f"{today_date.year}-03-31") if today_date.month < 4 else getdate(f"{today_date.year + 1}-03-31")
            # return f_year_end_date
            
            cl_leave_type = "Casual Leave"
            
            is_casual_leave = True if frappe.db.get_value("Leave Type", cl_leave_type, "custom_leave_type") == "Casual Leave" else False
            
            if is_casual_leave:
            
                p_and_employees = frappe.db.get_all("Employee", {"employment_type": ["in", ["Probation", "Contractual"]], "status": "Active"},["name", "employment_type", "contract_end_date", "date_of_joining"])
                            
                for emp in p_and_employees:
                    try:                        
                        if emp.employment_type == "Contractual" and emp.contract_end_date and getdate(emp.contract_end_date) > month_start_date:
                            to_date = min(getdate(emp.contract_end_date), fy_end_date)
                        else:
                            to_date = fy_end_date

                        # from_date = max(fy_start_date, emp.date_of_joining)
                        allocation_det = frappe.db.get_all("Leave Allocation", {"employee": emp.name, "leave_type": cl_leave_type, "docstatus": 1, "from_date": ["<=", today_date], "to_date": [">=", today_date]}, "name", order_by="from_date desc", limit_page_length=1)
                        
                        allocation_name = allocation_det[0].name if allocation_det else None
                        
                        if allocation_name:
                            allocation = frappe.get_doc("Leave Allocation", allocation_name)
                            last_cl_allocation_date = getdate(allocation.custom_last_allocation_date)
                            if last_cl_allocation_date and (last_cl_allocation_date >= today_date or last_cl_allocation_date.month == today_date.month):
                                frappe.log_error(f"last_allocation_date: {last_cl_allocation_date}", f"Employee: {emp.name} {last_cl_allocation_date.month} {today_date.month} 123")
                                continue
                            
                            allocation.new_leaves_allocated += 1
                            allocation.custom_last_allocation_date = today_date
                            allocation.save(ignore_permissions=True)
                        
                        else:
                            allocation = frappe.get_doc({
                                "doctype": "Leave Allocation",
                                "employee": emp.name,
                                "leave_type": cl_leave_type,
                                "from_date": month_start_date,
                                "to_date": to_date,
                                "new_leaves_allocated": 1,
                                "custom_last_allocation_date": today_date
                            })
                            allocation.insert(ignore_permissions=True)
                            allocation.submit()
                    except Exception as e:
                        frappe.log_error(f"error_allocate_cl_to_probation_and_contract_employees_{emp.name}", f"{frappe.get_traceback()} \n \n {month_start_date} {to_date}")
                        continue
                frappe.db.commit()
            frappe.log_error("CL Allocation to Probation and Contractual Employees Job Completed", "CL Allocated to Probation and Contractual Employees")
        
    except Exception as e:
        frappe.log_error(f"error_main_allocate_cl_to_probation_and_contract_employees", frappe.get_traceback())

# * METHOD TO ALLOCATE SICK LEAVE TO PROBATION AND CONTRACTUAL EMPLOYEES
# * THIS METHOD WILL RUN EVERY DAY
@frappe.whitelist()
def allocate_sl_to_probation_and_contract_employees(dt=None):
    try:
        if dt:
            today_date = getdate(dt)
        else:
            today_date = getdate()
            
        # today_date = getdate()
        monthly_sl = flt(0.58)
        allocate_after_days = 52
        sl_leave_type = "Sick Leave"

        month_end_date = getdate(get_last_day(today_date))
        
        
        if today_date.month < 4:
            current_fy_start = getdate(f"{today_date.year - 1}-04-01")
            current_fy_end   = getdate(f"{today_date.year}-03-31")
            
        else:
            current_fy_start = getdate(f"{today_date.year}-04-01")
            current_fy_end   = getdate(f"{today_date.year + 1}-03-31")
            
        
        
        if today_date != month_end_date and today_date != current_fy_start:
            return
        new_financial_year = today_date == current_fy_start

        if frappe.db.get_value("Leave Type", sl_leave_type, "custom_leave_type") != "Sick Leave":
            return

        employees = frappe.db.get_all(
            "Employee",
            {
                "employment_type": ["in", ["Probation", "Contractual"]],
                "status": "Active",
            },
            ["name", "employment_type", "date_of_joining", "contract_end_date"],
        )

        for emp in employees:
            try:
                joining_date = getdate(emp.date_of_joining)

                is_new_emp = True if joining_date.month == month_end_date.month else False
                if emp.employment_type == "Contractual" and emp.contract_end_date:
                    if today_date > getdate(emp.contract_end_date):
                        continue

                effective_to_date = current_fy_end
                if emp.employment_type == "Contractual" and emp.contract_end_date:
                    effective_to_date = min(getdate(emp.contract_end_date), current_fy_end)

                current_alloc = frappe.db.get_all(
                    "Leave Allocation",
                    {
                        "employee": emp.name,
                        "leave_type": sl_leave_type,
                        "docstatus": 1,
                        "from_date": ["<=", today_date],
                        "to_date": [">=", today_date],
                    },
                    ["name", "custom_last_allocation_date"],
                    order_by="from_date desc",
                    limit_page_length=1,
                )

                last_alloc_date = None
                if current_alloc and current_alloc[0].custom_last_allocation_date:
                    last_alloc_date = getdate(current_alloc[0].custom_last_allocation_date)
                else:
                    last_alloc_date = joining_date

                
                already_allocated_this_month = True if last_alloc_date and last_alloc_date.year == today_date.year and last_alloc_date.month == today_date.month else False
            
                if not new_financial_year:
                    if current_alloc and not already_allocated_this_month:
                        
                        alloc_doc = frappe.get_doc("Leave Allocation", current_alloc[0].name)
                        alloc_doc.new_leaves_allocated = flt(alloc_doc.new_leaves_allocated) + monthly_sl
                        alloc_doc.custom_last_allocation_date = today_date
                        alloc_doc.save(ignore_permissions=True)
                    elif not current_alloc:
                        if is_new_emp:
                            total_days = month_end_date.day
                            remaining_days = total_days - joining_date.day + 1
                            
                            monthly_sl = flt((remaining_days / total_days) * monthly_sl, 2)
                            # monthly_sl = 
                        
                        
                        new_alloc = frappe.get_doc({
                            "doctype": "Leave Allocation",
                            "employee": emp.name,
                            "leave_type": sl_leave_type,
                            "from_date": today_date,
                            "to_date": effective_to_date,
                            "new_leaves_allocated": monthly_sl,
                            "custom_last_allocation_date": today_date,
                        })
                        new_alloc.insert(ignore_permissions=True)
                        new_alloc.submit()
                else:
                    prev_fy_end = getdate(f"{today_date.year}-03-31")
                    last_year_balance = get_leave_balance_on(
                        emp.name,
                        sl_leave_type,
                        prev_fy_end,
                    ) or 0
                    

                    prev_fy_alloc = frappe.db.get_all(
                        "Leave Allocation",
                        {
                            "employee": emp.name,
                            "leave_type": sl_leave_type,
                            "docstatus": 1,
                            "from_date": ["<=", prev_fy_end],
                            "to_date": [">=", prev_fy_end],
                        },
                        ["custom_last_allocation_date"],
                        order_by="from_date desc",
                        limit_page_length=1,
                    )

                    if prev_fy_alloc and prev_fy_alloc[0].custom_last_allocation_date:
                        last_alloc_date = getdate(prev_fy_alloc[0].custom_last_allocation_date)
                    else:
                        last_alloc_date = joining_date

                    if(emp.name == "00400"):
                        frappe.log_error(f"current_alloc: {last_alloc_date}", f"Employee: {emp.name} 123")
                    
                    
                    if date_diff(today_date, last_alloc_date) >= allocate_after_days:
                        new_leaves = 1
                    else:
                        new_leaves = 0

                    fy_alloc = frappe.get_doc({
                        "doctype": "Leave Allocation",
                        "employee": emp.name,
                        "leave_type": sl_leave_type,
                        "from_date": current_fy_start,
                        "to_date": effective_to_date,
                        "custom_opening_balance": last_year_balance,
                        "new_leaves_allocated": new_leaves,
                        "custom_last_allocation_date": today_date if new_leaves else last_alloc_date,
                    })
                    fy_alloc.insert(ignore_permissions=True)
                    fy_alloc.submit()

            except Exception:
                frappe.log_error(
                    f"error_allocate_sl_{emp.name}",
                    frappe.get_traceback(),
                )
                continue

        frappe.db.commit()
        frappe.log_error(
            "SL Allocation Job Completed",
            f"Scheduler run completed on {today_date}",
        )

    except Exception:
        frappe.log_error(
            "error_allocate_sl_main",
            frappe.get_traceback(),
        )

    



# * SCHEDULER METHOD TO SET CURRENT REPORTING MANAGER AND HOLIDAY LIST IN THE EMPLOYEE
#* THIS WILL RUN EVERY DAY
@frappe.whitelist()
def set_approvers_in_employee(dt=None):
    try:
        if dt:
            from_date = getdate(dt)
        else:
            from_date = getdate()
        
        frappe.log_error("Set Approvers in Employee Job Started", "Set Approvers in Employee Job Started")
        employees = frappe.db.get_all("Employee", {"status": "Active"}, ["name", "holiday_list"])
        if employees:
            for emp in employees:
                try:
                    current_emp_shift_approver = frappe.db.get_value("Employee", emp.name, "shift_request_approver") or None
                    current_emp_leave_approver = frappe.db.get_value("Employee", emp.name, "leave_approver") or None
                    current_emp_reports_to = frappe.db.get_value("Employee", emp.name, "reports_to") or None
                    
                    
                    current_holiday_list = get_current_holiday_list(emp.name, from_date)
                    frappe.log_error("Holiday List", f"{current_holiday_list} {emp.holiday_list}")
                    if current_holiday_list:
                        if not emp.holiday_list:
                            frappe.db.set_value("Employee", emp.name, "holiday_list", current_holiday_list)
                        
                        elif emp.holiday_list != current_holiday_list:
                            frappe.db.set_value("Employee", emp.name, "holiday_list", current_holiday_list)
                            

                    
                    
                    emp_rm = get_emp_reporting_manager(emp.name)
                    emp_rm_emp = frappe.db.get_value("Employee", {"user_id": emp_rm}, "name") if emp_rm else None
                    if not emp_rm_emp:
                        frappe.log_error(f"Reporting Manager Employee Not Found for User ID: {emp_rm}", f"Employee: {emp.name}")
                    
                    if emp_rm:
                        if current_emp_shift_approver != emp_rm:
                            frappe.db.set_value("Employee", emp.name, "shift_request_approver", emp_rm)
                        if current_emp_leave_approver != emp_rm:
                            frappe.db.set_value("Employee", emp.name, "leave_approver", emp_rm)                        
                        if current_emp_reports_to != emp_rm_emp:
                            frappe.db.set_value("Employee", emp.name, "reports_to", emp_rm_emp)
                                                                                
                except Exception as e:
                    frappe.log_error(f"error_set_approvers_in_employee_{emp.name}", frappe.get_traceback())
                    continue
            
            frappe.db.commit()
        frappe.log_error("Set Approvers in Employee Job Completed", "Set Approvers in Employee Job Completed")
        
        
    except Exception as e:        frappe.log_error(
            f"error_set_approvers_in_employee",
            frappe.get_traceback(),
        )




def get_employees_by_branch(branch):
    return frappe.get_all(
        "Employee",
        filters={
            "status": "Active",
            "branch": branch,
        },
        pluck="name",
    )

def process_employee_attendance(employee, att_date):
    try:
        shift_type = get_employee_shift(employee, att_date)

        if not shift_type:
            log_attendance_error(employee, att_date, "Shift not assigned")
            return

        shift = frappe.db.get_value(
            "Shift Type",
            shift_type,
            [
                "start_time",
                "end_time",
                "late_entry_grace_period",
                "working_hours_threshold_for_half_day",
                "working_hours_threshold_for_absent",
            ],
            as_dict=True,
        )

        is_holiday = is_holiday_or_weekoff(employee, att_date)

        logs = frappe.db.sql(
            """
            SELECT name, time
            FROM `tabEmployee Checkin`
            WHERE employee=%s
            AND DATE(time)=%s
            ORDER BY time ASC
            """,
            (employee, att_date),
            as_dict=True,
        )

        if not logs:
            if is_holiday:
                return

            save_attendance_record(
                employee,
                att_date,
                shift_type,
                None,
                None,
                0,
                {"status": "Absent", "late_entry": 0},
            )
            return

        if len(logs) == 1:
            if is_holiday:
                return

            save_attendance_record(
                employee,
                att_date,
                shift_type,
                logs[0]["time"],
                None,
                0,
                {"status": "Partially", "late_entry": 0},
                logs[0]["name"],
                logs[0]["name"],
            )
            return

        in_time = normalize_to_minute(logs[0]["time"])
        out_time = normalize_to_minute(logs[-1]["time"])

        if in_time and out_time and out_time > in_time:
            working_seconds = (out_time - in_time).total_seconds()
            working_hours = working_seconds / 3600
        else:
            working_hours = 0

        result = calculate_attendance_result(
            employee,
            att_date,
            shift,
            in_time,
            out_time,
            working_hours,
            logs[0]["name"],
            logs[-1]["name"],
            skip_shift_time_rules=False,
        )

        save_attendance_record(
            employee,
            att_date,
            shift_type,
            in_time,
            out_time,
            working_hours,
            result,
            logs[0]["name"],
            logs[-1]["name"],
        )

    except Exception as e:
        log_attendance_error(employee, att_date, "Process Attendance Failed", e)

def revert_penalty_leave(attendance_name):
    att = frappe.get_doc("Attendance", attendance_name)

    if not att.custom_is_penalize:
        return

    leave_type = att.custom_penalty_leave_type
    leave_count = att.custom_penalty_leave_count
    attendance_date = att.attendance_date

    frappe.db.delete(
        "Leave Ledger Entry",
        {
            "employee": att.employee,
            "leave_type": leave_type,
            "from_date": attendance_date,
            "custom_is_penalty": 1,              # ✅ recommended if you have this field
            "custom_attendance":att.name,
        }
    )

    att.db_set({
        "custom_penalty_leave_type": None,
        "custom_penalty_leave_count": 0,
        "custom_is_penalize": 0
    })

    frappe.db.commit()

def save_attendance_record(
    employee,
    date,
    shift_type,
    in_time,
    out_time,
    working_hours,
    result,
    first_checkin_id=None,
    last_checkin_id=None,
):
    employee_details = frappe.db.get_value(
        "Employee",
        employee,
        ["employee_name", "department", "company", "branch"],
        as_dict=True,
    )

    attendance_name = frappe.db.exists(
        "Attendance",
        {
            "employee": employee,
            "attendance_date": date,
            "docstatus": ["!=", 2],
        },
    )

    old_status = None
    if attendance_name:
        old_status = frappe.db.get_value("Attendance", attendance_name, "status")

    values = {
        "in_time": in_time,
        "out_time": out_time,
        "working_hours": working_hours,
        "status": result["status"],
        "late_entry": result["late_entry"],
        "employee_name": employee_details.employee_name,
        "department": employee_details.department,
        "company": employee_details.company,
        "custom_branch": employee_details.branch,
        "shift": shift_type,
    }


    if attendance_name:
        frappe.db.set_value(
            "Attendance",
            attendance_name,
            values,
            update_modified=False,
        )

        att_name = attendance_name


    else:
        att_name = frappe.generate_hash(length=12)

        frappe.db.sql(
            """
            INSERT INTO `tabAttendance`
            (name, employee, employee_name, department, company,
             attendance_date, shift, in_time, out_time,
             working_hours, status, late_entry, custom_branch,
             docstatus, creation, modified, owner, modified_by)

            VALUES (%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,
                    %s,%s,%s,%s,
                    1, NOW(), NOW(), %s, %s)
            """,
            (
                att_name,
                employee,
                employee_details.employee_name,
                employee_details.department,
                employee_details.company,
                date,
                shift_type,
                in_time,
                out_time,
                working_hours,
                result["status"],
                result["late_entry"],
                employee_details.branch,
                frappe.session.user,
                frappe.session.user,
            ),
        )


    if first_checkin_id:
        frappe.db.set_value(
            "Employee Checkin",
            first_checkin_id,
            "attendance",
            att_name,
            update_modified=False,
        )

    if last_checkin_id and last_checkin_id != first_checkin_id:
        frappe.db.set_value(
            "Employee Checkin",
            last_checkin_id,
            "attendance",
            att_name,
            update_modified=False,
        )


    if old_status in ("Absent", "Half Day") and result["status"] == "Present":
        revert_penalty_leave(att_name)

    return att_name



def calculate_attendance_result(
    employee,
    date,
    shift,
    in_time,
    out_time,
    working_hours,
    first_checkin_id=None,
    last_checkin_id=None,
    skip_shift_time_rules=False,
):

    result = {
        "status": "Absent",
        "late_entry": 0,
    }


    if not out_time:
        result["status"] = "Partially"
        return result

    half_day_hours = float(shift.working_hours_threshold_for_half_day or 8)
    absent_hours = float(shift.working_hours_threshold_for_absent or 3)

    if working_hours <= absent_hours:
        result["status"] = "Absent"
    elif working_hours < half_day_hours:
        result["status"] = "Half Day"
    else:
        result["status"] = "Present"

    if (
        result["status"] != "Absent"
        and not skip_shift_time_rules
        and in_time
        and shift.late_entry_grace_period
    ):
        shift_start = combine_datetime(date, shift.start_time)

        latest_allowed = add_to_date(
            shift_start,
            minutes=int(shift.late_entry_grace_period),
        )

        if in_time > latest_allowed:
            result["late_entry"] = 0.5
            result["status"] = "Half Day"

    return result
