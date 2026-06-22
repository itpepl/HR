# import frappe
# from frappe.utils import getdate, today,add_days,now_datetime,add_to_date, date_diff, get_last_day, get_first_day

# from datetime import date,datetime
# from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

# from frappe.utils import get_datetime
# from datetime import datetime, time,timedelta
# from frappe.utils import flt
# import calendar




# from jkmpcl_hr.py.utils import get_current_holiday_list, custom_create_additional_leave_ledger_entry, get_ceo_employees


# # from jkmpcl_hr.py.utils import send_notification_email
# from jkmpcl_hr.py.utils import create_shift_assignment_rec, send_notification_email, get_emp_reporting_manager

# @frappe.whitelist(allow_guest=True)
# def create_shift_assignments():
#     frappe.log_error("start_create_shift_assignments", "Scheduler Started")
#     today_date = getdate(today())
#     start_year = today_date.year if today_date.month >= 4 else today_date.year - 1
    
#     emp_filters = {"status": "Active"}
#     create_and_assign_shift_assignments_srinagar(today_date, start_year, emp_filters)
#     create_and_assign_shift_assignments_jammu(today_date, start_year, emp_filters)
#     frappe.log_error("end_create_shift_assignments", "Scheduler Ended")




# def create_and_assign_shift_assignments_srinagar(today_date, start_year, emp_filters):
#     frappe.log_error("start_create_and_assign_shift_assignments_srinagar", "Scheduler Started FOR Srinagar")
    
#     apr_start_date = getdate(f"{start_year}-04-01")
#     mar_end_date = getdate(f"{start_year+1}-03-31")
#     # mar_end_date = date(start_year + 1, 3, 31)
    
#     sep_end_sri  = getdate(f"{start_year}-09-30")
#     oct_start_sri = getdate(f"{start_year}-10-01")
    
#     # sep_end_sri  = date(start_year, 9, 30)
#     # oct_start_sri = date(start_year, 10, 1)

#     emp_filters["branch"] = "Jammu and Kashmir Milk Producers Co-operative Ltd Cheshmashahi Srinagar"
#     emp_list = frappe.db.get_list("Employee", filters=emp_filters, fields=["name", "default_shift", "custom_attendance_source"])
        
#     if not emp_list:
#         return
        
    
#     error_emp = []
#     ds_not_set_emp = []
    
#     for emp in emp_list:
#         try:
#             emp_id = emp.get("name")
#             default_shift = emp.get("default_shift")
            
#             eight_hours_sa_exists = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", apr_start_date], "end_date":[">=", sep_end_sri]}, limit=1)
#             seven_hours_sa_exists = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", oct_start_sri], "end_date":[">=", mar_end_date]}, limit=1)
            
#             emp_default_shift_details = frappe.db.get_values("Shift Type", default_shift, ["custom_shift_type", "custom_hours", "custom_branch"], as_dict=True)
            
#             if not emp_default_shift_details:
#                 ds_not_set_emp.append(emp_id)
#                 continue
            
#             if emp_default_shift_details[0].get("custom_hours") == "7hours":
#                 if emp.get("custom_attendance_source") == "Field" and emp_default_shift_details[0].get("custom_shift_type") == "General":
#                     seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
                    
#                     eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
                
#                 if emp.get("custom_attendance_source") == "Punch" and emp_default_shift_details[0].get("custom_shift_type") == "General":
#                     seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Punch"}, "name")
                    
#                     eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Punch"}, "name")
#                 else:
#                     seven_hours_shift_id = default_shift
#                     eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours",         "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
                            
#             elif emp_default_shift_details[0].get("custom_hours") == "8hours":
#                 if emp.get("custom_attendance_source") == "Field" and emp_default_shift_details[0].get("custom_shift_type") == "General":
#                     eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
#                     seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
                    
#                 if emp.get("custom_attendance_source") == "Punch" and emp_default_shift_details[0].get("custom_shift_type") == "General":
#                     eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Punch"}, "name")
#                     seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Punch"}, "name")
#                 else:                                
#                     eight_hours_shift_id = default_shift
#                     seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
            
#             if not eight_hours_sa_exists:
#                 create_shift_assignment_rec(emp_id, apr_start_date, sep_end_sri, eight_hours_shift_id)
            
#             if not seven_hours_sa_exists:
#                 create_shift_assignment_rec(emp_id, oct_start_sri, mar_end_date, seven_hours_shift_id)
                
                        
#             # return emp_default_shift_details
#             # if not eight_hours_sa_exists:
                
            
#         except Exception as e:
#             error_emp.append({emp_id: str(e)})
#             frappe.log_error(f"error_create_and_assign_shift_assignments_srinagar_{emp_id}", frappe.get_traceback())
#             continue
    
#     frappe.log_error("end_create_and_assign_shift_assignments_srinagar", f"Scheduler Ended FOR Srinagar\n ds_not_setupfor_this_emp: {ds_not_set_emp}")
    
    
    
# def create_and_assign_shift_assignments_jammu(today_date, start_year, emp_filters):
#     # apr_start_date = date(start_year, 4, 1)
#     # mar_end_date = date(start_year + 1, 3, 31)
#     frappe.log_error("start_create_and_assign_shift_assignments_jammu", "Scheduler Started FOR Jammu")
    
#     apr_start_date = getdate(f"{start_year}-04-01")
#     mar_end_date = getdate(f"{start_year+120137}-03-31")
    
#     # nov_end_jammu = date(start_year, 11, 30)
#     # dec_start_jammu = date(start_year, 12, 1)
#     # jan_end_jammu = date(start_year + 1, 1, 31)
    
#     nov_end_jammu = getdate(f"{start_year}-11-30")
#     dec_start_jammu = getdate(f"{start_year}-12-01")
#     jan_end_jammu = getdate(f"{start_year+1}-01-31")
#     feb_start_jammu = getdate(f"{start_year+1}-02-01")
    
#     emp_filters["branch"] = "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu"
#     emp_list = frappe.db.get_list("Employee", filters=emp_filters, fields=["name", "default_shift", "gender", "custom_attendance_source"])
    
#     if not emp_list:
#         return
    
#     error_emp = []
#     ds_not_set_emp = []
    
#     for emp in emp_list:
#         try:
#             emp_id = emp.get("name")
#             default_shift = emp.get("default_shift")
            
#             if not default_shift:
#                     ds_not_set_emp.append(emp_id)
#                     continue
#             emp_default_shift_details = frappe.db.get_values("Shift Type", default_shift, ["custom_shift_type", "custom_hours", "custom_branch"], as_dict=True)
            
#             if emp.get("gender") == "Female" and emp.get("custom_attendance_source") == "Field":
            
#                 eight_hours_sa_exists_first = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", apr_start_date], "end_date":[">=", nov_end_jammu]}, limit=1)
#                 seven_hours_sa_exists = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", dec_start_jammu], "end_date":[">=", jan_end_jammu]}, limit=1)
#                 eight_hours_sa_exists_second = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", feb_start_jammu], "end_date":[">=", mar_end_date]}, limit=1)
                
                
#                 if emp_default_shift_details[0].get("custom_hours") == "7hours":
                    
#                     if emp_default_shift_details[0].get("custom_shift_type") == "General":
                        
#                         seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
                        
#                         eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
#                     else:
#                         seven_hours_shift_id = default_shift
#                         eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
                                
#                 elif emp_default_shift_details[0].get("custom_hours") == "8hours":
#                     if emp_default_shift_details[0].get("custom_shift_type") == "General":
#                         eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
#                         seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
#                     else:
                    
#                         eight_hours_shift_id = default_shift
#                         seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
                
#                 if not eight_hours_sa_exists_first:
#                     create_shift_assignment_rec(emp_id, apr_start_date, nov_end_jammu, eight_hours_shift_id)
                
#                 if not seven_hours_sa_exists:
#                     create_shift_assignment_rec(emp_id, dec_start_jammu, jan_end_jammu, seven_hours_shift_id)
                    
#                 if not eight_hours_sa_exists_second:
#                     create_shift_assignment_rec(emp_id, feb_start_jammu, mar_end_date, eight_hours_shift_id)

            
#             else:
#                 sa_exists = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", apr_start_date], "end_date":[">=", mar_end_date]}, limit=1)
                    
#                 if emp_default_shift_details[0].get("custom_hours") == "7hours":
                    
#                     if emp.get("custom_attendance_source") == "Field" and emp_default_shift_details[0].get("custom_shift_type") == "General":
#                         eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
#                     else:
#                         eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
                                
#                 elif emp_default_shift_details[0].get("custom_hours") == "8hours":
#                     if emp.get("custom_attendance_source") == "Field" and emp_default_shift_details[0].get("custom_shift_type") == "General":
#                         eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
#                     else:                    
#                         eight_hours_shift_id = default_shift
                
#                 if not sa_exists:
#                     create_shift_assignment_rec(emp_id, apr_start_date, mar_end_date, eight_hours_shift_id)
                
#             # return emp_default_shift_details
#             # if not eight_hours_sa_exists_first:
        
#         except Exception as e:
#             error_emp.append({emp_id: str(e)})
#             frappe.log_error(f"error_create_and_assign_shift_assignments_jammu_{emp_id}", frappe.get_traceback())
#             continue
    
#     frappe.log_error("end_create_and_assign_shift_assignments_jammu", f"Scheduler Ended FOR Jammu \n ds_not_setupfor_this_emp: {ds_not_set_emp}")
    
    

# def get_employee_leave_type(employee):
#     policy = frappe.db.get_value(
#         "Leave Policy Assignment",
#         {
#             "employee": employee,
#             "docstatus": 1
#         },
#         "leave_policy"
#     )

#     if policy:
#         leave_type = frappe.db.get_value(
#             "Leave Policy Detail",
#             {
#                 "parent": policy
#             },
#             "leave_type"
#         )

#         if leave_type:
#             return leave_type

#     # 🔥 Fallback to Leave Without Pay
#     return "Leave Without Pay"


# # =========================================================
# # MAIN SCHEDULER METHOD
# # =========================================================
# @frappe.whitelist(allow_guest=True)
# def run_attendance_from_to(from_date,to_date):
# # def run_attendance_from_to():
#     if not from_date or not to_date:
#         frappe.throw("From Date and To Date are required")


    
#     # from_date="2026-01-13"
#     # to_date="2026-01-23"
#     from_date = getdate(from_date)
#     to_date = getdate(to_date)

#     current_date = from_date

#     while current_date <= to_date:
#         run_daily_attendance(current_date, only_for_jammu=False)
#         current_date = add_days(current_date, 1)

#     return {
#         "status": "success",
#         "message": f"Attendance processed from {from_date} to {to_date}"
#     }

# def normalize_to_minute(dt):
#     if not dt:
#         return None
#     return dt.replace(second=0, microsecond=0)

# def get_employee_from_user():
#     return frappe.db.get_value(
#         "Employee",
#         {"user_id": frappe.session.user, "status": "Active"},
#         ["name", "branch"],
#         as_dict=True,
#     )


# @frappe.whitelist()
# def run_attendance_for_my_branch(att_date):

#     if not att_date:
#         frappe.throw("Attendance Date required")

#     emp = get_employee_from_user()

#     if not emp:
#         frappe.throw("No Employee linked with this user")

#     branch = emp.branch

#     # employees = get_employees_by_branch(branch)

#     # for e in employees:
#     frappe.log_error("run_attendance_for_my_branch", f"Running attendance for branch: {branch} and date:{att_date}")
#     run_daily_attendance(getdate(att_date), branch=branch)

#     frappe.db.commit()

#     return {
#         "success": True,
#         "message": f"Attendance processed for branch: {branch}"
#     }

# # def run_daily_attendance(att_date=None, only_for_jammu=False, branch=None):

# #     frappe.log_error("start_run_daily_attendance", f"Scheduler Started FOR Date: {att_date}")

# #     if not att_date:
# #         att_date = add_days(getdate(), -1)
# #     else:
# #         att_date = getdate(att_date)
# #     if only_for_jammu:
# #         frappe.log_error("run_daily_attendance_only_for_jammu", f"Running attendance only for Jammu branch for date: {att_date}")
# #         employees = frappe.get_all(
# #             "Employee",
# #             filters={
# #                 "status": "Active",
# #                 "branch": "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu",
# #             },
# #             pluck="name",
# #         )
# #     else:
# #         filters = {"status": "Active"}

# #         if branch:
# #             filters["branch"] = branch
# #         frappe.log_error("run_daily_attendance_filters", f"Filters applied: {filters}")
# #         employees = frappe.get_all("Employee", filters=filters, pluck="name")
# #         frappe.log_error("run_daily_attendance_emplist", f"Employees fetched: {len(employees)}")

# #     for emp in employees:
# #         try:

# #             if has_approved_leave(emp, att_date):
# #                 continue

# #             shift_type = get_employee_shift(emp, att_date)

# #             if not shift_type:
# #                 log_attendance_error(emp, att_date, "Shift not assigned")
# #                 continue

# #             shift_custom_type = frappe.db.get_value(
# #                 "Shift Type", shift_type, "custom_shift_type"
# #             )

# #             # shift_start_time =  frappe.db.get_value(
# #             #     "Shift Type", shift_type, "start_time"
# #             # )
            
# #             # shift_end_time =  frappe.db.get_value(
# #             #     "Shift Type", shift_type, "end_time"
# #             # )
            
# #             # begin_checkin_in_minutes = frappe.db.get_value(
# #             #     "Shift Type", shift_type, "begin_check_in_before_shift_start_time"
# #             # )
            
# #             # allow_checkout_in_minutes = frappe.db.get_value(
# #             #     "Shift Type", shift_type, "allow_check_out_after_shift_end_time"
# #             # )
            
            
# #             # new_shift_start_time = add_to_date(get_datetime(f"{att_date} {shift_start_time}"), minutes=-begin_checkin_in_minutes)
# #             # new_shift_end_time = add_to_date(get_datetime(f"{att_date} {shift_end_time}"), minutes=allow_checkout_in_minutes)
            
# #             # frappe.log_error(f"shift_value_type{emp}", f" shift start time {shift_start_time} shift end time {shift_end_time}  new_start {new_shift_start_time} new_end {new_shift_end_time}")
            
            
# #             is_holiday = is_holiday_or_weekoff(emp, att_date)
# #             off_day_approved = has_approved_off_day_work(emp, att_date)

# #             is_holiday_work = False

# #             if shift_custom_type == "24 hours":

# #                 first_in, last_out, first_checkin_id, last_checkin_id, working_hours, log_count = (
# #                     get_24_hour_working_hours(emp, att_date, shift_type)
# #                 )

# #                 if log_count == 0:
# #                     if is_holiday:
# #                         continue

# #                     create_or_update_attendance(
# #                         emp,
# #                         att_date,
# #                         None,
# #                         None,
# #                         0,
# #                         None,
# #                         None,
# #                         skip_shift_time_rules=True,
# #                         is_holiday_work=False,
# #                     )
# #                     continue

# #                 if is_holiday:
# #                     is_holiday_work = True

# #                 if log_count == 1:
# #                     create_or_update_attendance(
# #                         emp,
# #                         att_date,
# #                         None,
# #                         None,
# #                         0,
# #                         first_checkin_id,
# #                         last_checkin_id,
# #                         skip_shift_time_rules=True,
# #                         is_holiday_work=is_holiday_work,
# #                     )
# #                     continue

# #                 create_or_update_attendance(
# #                     emp,
# #                     att_date,
# #                     first_in,
# #                     last_out,
# #                     working_hours,
# #                     first_checkin_id,
# #                     last_checkin_id,
# #                     skip_shift_time_rules=True,
# #                     is_holiday_work=is_holiday_work,
# #                 )
# #                 continue

# #             if shift_custom_type == "Night":
# #                 # new_shift_end_time = add_to_date(get_datetime(f"{att_date} {shift_end_time}"), days=1, minutes=allow_checkout_in_minutes)
                
# #                 in_time, out_time, first_id, last_id, working_hours, log_count = (
# #                     get_night_shift_logs(emp, att_date)
# #                 )

# #                 if log_count == 0:
# #                     if is_holiday:
# #                         continue

# #                     create_or_update_attendance(
# #                         emp,
# #                         att_date,
# #                         None,
# #                         None,
# #                         0,
# #                         None,
# #                         None,
# #                         skip_shift_time_rules=True,
# #                         is_holiday_work=False,
# #                     )
# #                     continue

# #                 if is_holiday:
# #                     is_holiday_work = True

# #                 if log_count == 1:
# #                     create_or_update_attendance(
# #                         emp,
# #                         att_date,
# #                         None,
# #                         None,
# #                         0,
# #                         first_id,
# #                         last_id,
# #                         skip_shift_time_rules=True,
# #                         is_holiday_work=is_holiday_work,
# #                     )
# #                     continue

# #                 create_or_update_attendance(
# #                     emp,
# #                     att_date,
# #                     in_time,
# #                     out_time,
# #                     working_hours,
# #                     first_id,
# #                     last_id,
# #                     skip_shift_time_rules=True,
# #                     is_holiday_work=is_holiday_work,
# #                 )
# #                 continue

            
# #             previous_date = add_days(att_date, -1)
# #             prev_shift = get_employee_shift(emp, previous_date)
            
            
            
# #             logs = frappe.db.sql(
# #                 """
# #                 SELECT name, time
# #                 FROM `tabEmployee Checkin`
# #                 WHERE employee=%s
# #                 AND DATE(time)=%s
# #                 ORDER BY time ASC
# #             """,
# #                 (emp, att_date),
# #                 as_dict=True,
# #             )
# #             # logs = frappe.db.sql(
# #             #     """
# #             #     SELECT name, time
# #             #     FROM `tabEmployee Checkin`
# #             #     WHERE employee = %s
# #             #     AND time >= %s
# #             #     AND time <= %s
# #             #     ORDER BY time ASC
# #             #     """,
# #             #     (emp, new_shift_start_time, new_shift_end_time),
# #             #     as_dict=True,
# #             # )

# #             logs = filter_close_checkins(logs, threshold_minutes=2)

# #             if not logs:
# #                 if is_holiday:
# #                     continue

# #                 create_or_update_attendance(
# #                     emp,
# #                     att_date,
# #                     None,
# #                     None,
# #                     0,
# #                     None,
# #                     None,
# #                     skip_shift_time_rules=False,
# #                     is_holiday_work=False,
# #                 )
# #                 continue

# #             if is_holiday:
# #                 is_holiday_work = True

# #             if len(logs) < 2:
# #                 create_or_update_attendance(
# #                     emp,
# #                     att_date,
# #                     None,
# #                     None,
# #                     0,
# #                     logs[0]["name"],
# #                     logs[-1]["name"],
# #                     skip_shift_time_rules=False,
# #                     is_holiday_work=is_holiday_work,
# #                 )
# #                 continue

# #             in_time = normalize_to_minute(logs[0]["time"])
# #             out_time = normalize_to_minute(logs[-1]["time"])

# #             if in_time and out_time and out_time > in_time:
# #                 working_seconds = (out_time - in_time).total_seconds()
# #                 working_hours = working_seconds / 3600
# #             else:
# #                 working_hours = 0

# #             if working_hours <= 0:
# #                 create_or_update_attendance(
# #                     emp,
# #                     att_date,
# #                     None,
# #                     None,
# #                     0,
# #                     logs[0]["name"],
# #                     logs[-1]["name"],
# #                     skip_shift_time_rules=False,
# #                     is_holiday_work=is_holiday_work,
# #                 )
# #                 continue

# #             create_or_update_attendance(
# #                 emp,
# #                 att_date,
# #                 in_time,
# #                 out_time,
# #                 working_hours,
# #                 logs[0]["name"],
# #                 logs[-1]["name"],
# #                 skip_shift_time_rules=False,
# #                 is_holiday_work=is_holiday_work,
# #             )

# #         except Exception as e:
# #             log_attendance_error(emp, att_date, "Main Scheduler Failed", e)

# #     frappe.db.commit()

# def run_daily_attendance(att_date=None, only_for_jammu=False, branch=None):

#     frappe.log_error("start_run_daily_attendance", f"Scheduler Started FOR Date: {att_date}")


#     ceo_employees = get_ceo_employees()
    
#     if not att_date:
#         att_date = add_days(getdate(), -1)
#     else:
#         att_date = getdate(att_date)


#     # if not regularize_attendance:
#     # ==============================
#     # Fetch Employees
#     # ==============================
    
    
    
#     if only_for_jammu:
#         if ceo_employees:
            
#             employees = frappe.get_all(
#                 "Employee",
#                 filters={
#                     "status": "Active",
#                     "branch": "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu",
#                     "name": ["not in", ceo_employees]
#                 },
#                 pluck="name",
#             )
#         else:
#             employees = frappe.get_all(
#                 "Employee",
#                 filters={
#                     "status": "Active",
#                     "branch": "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu",            
#                 },
#                 pluck="name",
#             )
#     else:
#         filters = {"status": "Active"}
        
#         if branch:
#             filters["branch"] = branch

#         if ceo_employees:
#             filters["name"]=["not in", ceo_employees]

#         employees = frappe.get_all("Employee", filters=filters, pluck="name")

#     # ==============================
#     # Process Each Employee
#     # ==============================
#     for emp in employees:
#         try:
#             mark_attendance(emp, att_date)
#             # if has_approved_leave(emp, att_date):
#             #     continue

#             # shift_type = get_employee_shift(emp, att_date)

#             # if not shift_type:
#             #     log_attendance_error(emp, att_date, "Shift not assigned")
#             #     continue

#             # shift_custom_type = frappe.db.get_value(
#             #     "Shift Type", shift_type, "custom_shift_type"
#             # )

#             # is_holiday = is_holiday_or_weekoff(emp, att_date)
#             # off_day_approved = has_approved_off_day_work(emp, att_date)
#             # is_holiday_work = False

#             # # ==========================================================
#             # # 24 HOURS SHIFT
#             # # ==========================================================
#             # if shift_custom_type == "24 hours":

#             #     first_in, last_out, first_checkin_id, last_checkin_id, working_hours, log_count = (
#             #         get_24_hour_working_hours(emp, att_date, shift_type)
#             #     )

#             #     if log_count == 0:
#             #         if is_holiday:
#             #             continue

#             #         create_or_update_attendance(
#             #             emp, att_date, None, None, 0,
#             #             None, None,
#             #             skip_shift_time_rules=True,
#             #             is_holiday_work=False,
#             #         )
#             #         continue

#             #     if is_holiday:
#             #         is_holiday_work = True

#             #     if log_count == 1:
#             #         create_or_update_attendance(
#             #             emp, att_date, None, None, 0,
#             #             first_checkin_id, last_checkin_id,
#             #             skip_shift_time_rules=True,
#             #             is_holiday_work=is_holiday_work,
#             #         )
#             #         continue

#             #     create_or_update_attendance(
#             #         emp, att_date,
#             #         first_in, last_out, working_hours,
#             #         first_checkin_id, last_checkin_id,
#             #         skip_shift_time_rules=True,
#             #         is_holiday_work=is_holiday_work,
#             #     )
#             #     continue

#             # # ==========================================================
#             # # NIGHT SHIFT
#             # # ==========================================================
#             # if shift_custom_type == "Night":

#             #     in_time, out_time, first_id, last_id, working_hours, log_count = (
#             #         get_night_shift_logs(emp, att_date)
#             #     )

#             #     if log_count == 0:
#             #         if is_holiday:
#             #             continue

#             #         create_or_update_attendance(
#             #             emp, att_date, None, None, 0,
#             #             None, None,
#             #             skip_shift_time_rules=True,
#             #             is_holiday_work=False,
#             #         )
#             #         continue

#             #     if is_holiday:
#             #         is_holiday_work = True

#             #     if log_count == 1:
#             #         create_or_update_attendance(
#             #             emp, att_date, None, None, 0,
#             #             first_id, last_id,
#             #             skip_shift_time_rules=True,
#             #             is_holiday_work=is_holiday_work,
#             #         )
#             #         continue

#             #     create_or_update_attendance(
#             #         emp, att_date,
#             #         in_time, out_time, working_hours,
#             #         first_id, last_id,
#             #         skip_shift_time_rules=True,
#             #         is_holiday_work=is_holiday_work,
#             #     )
#             #     continue

#             # # ==========================================================
#             # # NORMAL SHIFT LOGIC
#             # # ==========================================================

#             # logs = frappe.db.sql(
#             #     """
#             #     SELECT name, time
#             #     FROM `tabEmployee Checkin`
#             #     WHERE employee=%s
#             #     AND DATE(time)=%s
#             #     ORDER BY time ASC
#             #     """,
#             #     (emp, att_date),
#             #     as_dict=True,
#             # )

#             # # ----------------------------------------------------------
#             # # NEW LOGIC:
#             # # If previous day was Night shift,
#             # # ignore logs before previous OUT time
#             # # ----------------------------------------------------------
#             # previous_date = add_days(att_date, -1)
#             # prev_shift = get_employee_shift(emp, previous_date)

#             # if prev_shift:
#             #     prev_shift_type = frappe.db.get_value(
#             #         "Shift Type", prev_shift, "custom_shift_type"
#             #     )

#             #     if prev_shift_type == "Night":
#             #         frappe.log_error("Night Shift Previous Day", f"Employee: {emp}, Previous Date: {previous_date}, Previous Shift: {prev_shift}")
#             #         prev_att = frappe.db.get_value(
#             #             "Attendance",
#             #             {
#             #                 "employee": emp,
#             #                 "attendance_date": previous_date,
#             #                 "docstatus": 1
#             #             },
#             #             ["out_time"],
#             #             as_dict=True
#             #         )
#             #         frappe.log_error("Previous Day Attendance", f"Employee: {emp}, Previous Date: {previous_date}, Previous Attendance: {prev_att} logs {logs}")
#             #         if prev_att and prev_att.out_time:
#             #             logs = [
#             #                 log for log in logs
#             #                 if normalize_to_minute(log["time"]) > normalize_to_minute(prev_att.out_time) and normalize_to_minute(log["time"]) != normalize_to_minute(prev_att.out_time)
#             #             ]
#             #         frappe.log_error("Filtered Logs After Night Shift Check", f"Employee: {emp}, Previous Date: {previous_date}, Logs: {logs}")
#             # # ----------------------------------------------------------

#             # logs = filter_close_checkins(logs, threshold_minutes=2)

#             # if not logs:
#             #     if is_holiday:
#             #         continue

#             #     create_or_update_attendance(
#             #         emp, att_date,
#             #         None, None, 0,
#             #         None, None,
#             #         skip_shift_time_rules=False,
#             #         is_holiday_work=False,
#             #     )
#             #     continue

#             # if is_holiday:
#             #     is_holiday_work = True

#             # if len(logs) < 2:
#             #     create_or_update_attendance(
#             #         emp, att_date,
#             #         None, None, 0,
#             #         logs[0]["name"], logs[-1]["name"],
#             #         skip_shift_time_rules=False,
#             #         is_holiday_work=is_holiday_work,
#             #     )
#             #     continue

#             # in_time = normalize_to_minute(logs[0]["time"])
#             # out_time = normalize_to_minute(logs[-1]["time"])

#             # if in_time and out_time and out_time > in_time:
#             #     working_seconds = (out_time - in_time).total_seconds()
#             #     working_hours = working_seconds / 3600
#             # else:
#             #     working_hours = 0

#             # if working_hours <= 0:
#             #     create_or_update_attendance(
#             #         emp, att_date,
#             #         None, None, 0,
#             #         logs[0]["name"], logs[-1]["name"],
#             #         skip_shift_time_rules=False,
#             #         is_holiday_work=is_holiday_work,
#             #     )
#             #     continue

#             # create_or_update_attendance(
#             #     emp, att_date,
#             #     in_time, out_time, working_hours,
#             #     logs[0]["name"], logs[-1]["name"],
#             #     skip_shift_time_rules=False,
#             #     is_holiday_work=is_holiday_work,
#             # )

#         except Exception as e:
#             log_attendance_error(emp, att_date, "Main Scheduler Failed", e)
#     # else:
        
#     #     if not employee_id:
#     #         frappe.throw("Please Provide Employee ID")
#     #         frappe.log_error("run_daily_attendance", "No employee id found while regularizing attendance")
        
#     #     att_id = mark_attendance(employee_id, att_date)
#     #     return att_id
        
#     frappe.db.commit()







# def mark_attendance(emp, att_date):
    
#     if has_approved_leave(emp, att_date):
#                 return

#     shift_type = get_employee_shift(emp, att_date)

#     if not shift_type:
#         log_attendance_error(emp, att_date, "Shift not assigned")
#         return

#     shift_custom_type = frappe.db.get_value(
#         "Shift Type", shift_type, "custom_shift_type"
#     )

#     # is_holiday = is_holiday_or_weekoff(emp, att_date)
#     # off_day_approved = has_approved_off_day_work(emp, att_date)
#     # is_holiday_work = False
    
#     # ==========================================================
#     # ✅ HOLIDAY + OFF DAY LOGIC (FIXED)
#     # ==========================================================
#     holiday_type = get_holiday_type(emp, att_date)

#     off_day_approved = has_approved_off_day_work(emp, att_date)

#     frappe.log_error(
#         "DEBUG OFF DAY",
#         f"Emp: {emp}, Date: {att_date}, Holiday: {holiday_type}, OffDayApproved: {off_day_approved}"
#     )

#     if holiday_type:
#         if off_day_approved:
#             is_holiday_work = True
#         else:
#             is_holiday_work = False
#     else:
#         is_holiday_work = False

#     # ==========================================================
#     # 24 HOURS SHIFT
#     # ==========================================================
#     # if shift_custom_type == "24 hours":

#     #     first_in, last_out, first_checkin_id, last_checkin_id, working_hours, log_count = (
#     #         get_24_hour_working_hours(emp, att_date, shift_type)
#     #     )

#     #     if log_count == 0:
#     #         if is_holiday:
#     #             return

#     #         create_or_update_attendance(
#     #             emp, att_date, None, None, 0,
#     #             None, None,
#     #             skip_shift_time_rules=True,
#     #             is_holiday_work=False,
#     #         )
#     #         return

#     #     if is_holiday:
#     #         is_holiday_work = True

#     #     if log_count == 1:
#     #         create_or_update_attendance(
#     #             emp, att_date, None, None, 0,
#     #             first_checkin_id, last_checkin_id,
#     #             skip_shift_time_rules=True,
#     #             is_holiday_work=is_holiday_work,
#     #         )
#     #         return

#     #     create_or_update_attendance(
#     #         emp, att_date,
#     #         first_in, last_out, working_hours,
#     #         first_checkin_id, last_checkin_id,
#     #         skip_shift_time_rules=True,
#     #         is_holiday_work=is_holiday_work,
#     #     )
#     #     return
#     if shift_custom_type == "24 hours":

#         first_in, last_out, first_checkin_id, last_checkin_id, working_hours, log_count = (
#             get_24_hour_working_hours(emp, att_date, shift_type)
#         )

#         if log_count == 0:
#             if holiday_type:
#                 create_or_update_attendance(
#                     emp, att_date, None, None, 0,
#                     None, None,
#                     skip_shift_time_rules=True,
#                     is_holiday_work=False,
#                     off_day_approved=off_day_approved,
#                     holiday_type=holiday_type
#                 )
#                 frappe.db.set_value(
#                     "Attendance",
#                     {"employee": emp, "attendance_date": att_date},
#                     "status",
#                     holiday_type
#                 )
#                 return

#             create_or_update_attendance(
#                 emp, att_date, None, None, 0,
#                 None, None,
#                 skip_shift_time_rules=True,
#                 is_holiday_work=False,
#                 off_day_approved=off_day_approved,
#                 holiday_type=holiday_type
#             )
#             return

#         if log_count == 1:
#             create_or_update_attendance(
#                 emp, att_date, None, None, 0,
#                 first_checkin_id, last_checkin_id,
#                 skip_shift_time_rules=True,
#                 is_holiday_work=is_holiday_work,
#                 off_day_approved=off_day_approved,
#                 holiday_type=holiday_type
#             )
#             return

#         create_or_update_attendance(
#             emp, att_date,
#             first_in, last_out, working_hours,
#             first_checkin_id, last_checkin_id,
#             skip_shift_time_rules=True,
#             is_holiday_work=is_holiday_work,
#             off_day_approved=off_day_approved,
#             holiday_type=holiday_type
#         )
#         return
#     # ==========================================================
#     # NIGHT SHIFT
#     # ==========================================================
#     # if shift_custom_type == "Night":

#     #     in_time, out_time, first_id, last_id, working_hours, log_count = (
#     #         get_night_shift_logs(emp, att_date)
#     #     )

#     #     if log_count == 0:
#     #         if is_holiday:
#     #             return

#     #         create_or_update_attendance(
#     #             emp, att_date, None, None, 0,
#     #             None, None,
#     #             skip_shift_time_rules=True,
#     #             is_holiday_work=False,
#     #         )
#     #         return

#     #     if is_holiday:
#     #         is_holiday_work = True

#     #     if log_count == 1:
#     #         create_or_update_attendance(
#     #             emp, att_date, None, None, 0,
#     #             first_id, last_id,
#     #             skip_shift_time_rules=True,
#     #             is_holiday_work=is_holiday_work,
#     #         )
#     #         return

#     #     create_or_update_attendance(
#     #         emp, att_date,
#     #         in_time, out_time, working_hours,
#     #         first_id, last_id,
#     #         skip_shift_time_rules=True,
#     #         is_holiday_work=is_holiday_work,
#     #     )
#     #     return
    
#     if shift_custom_type == "Night":

#         in_time, out_time, first_id, last_id, working_hours, log_count = (
#             get_night_shift_logs(emp, att_date)
#         )

#         if log_count == 0:
#             if holiday_type:
#                 create_or_update_attendance(
#                     emp, att_date, None, None, 0,
#                     None, None,
#                     skip_shift_time_rules=True,
#                     is_holiday_work=False,
#                     off_day_approved=off_day_approved,
#                     holiday_type=holiday_type
#                 )
#                 frappe.db.set_value(
#                     "Attendance",
#                     {"employee": emp, "attendance_date": att_date},
#                     "status",
#                     holiday_type
#                 )
#                 return

#             create_or_update_attendance(
#                 emp, att_date, None, None, 0,
#                 None, None,
#                 skip_shift_time_rules=True,
#                 is_holiday_work=False,
#                 off_day_approved=off_day_approved,
#                 holiday_type=holiday_type
#             )
#             return

#         if log_count == 1:
#             create_or_update_attendance(
#                 emp, att_date, None, None, 0,
#                 first_id, last_id,
#                 skip_shift_time_rules=True,
#                 is_holiday_work=is_holiday_work,
#                 off_day_approved=off_day_approved,
#                 holiday_type=holiday_type
#             )
#             return

#         create_or_update_attendance(
#             emp, att_date,
#             in_time, out_time, working_hours,
#             first_id, last_id,
#             skip_shift_time_rules=True,
#             is_holiday_work=is_holiday_work,
#             off_day_approved=off_day_approved,
#             holiday_type=holiday_type
#         )
#         return

#     # ==========================================================
#     # NORMAL SHIFT LOGIC
#     # ==========================================================

#     # logs = frappe.db.sql(
#     #     """
#     #     SELECT name, time
#     #     FROM `tabEmployee Checkin`
#     #     WHERE employee=%s
#     #     AND DATE(time)=%s
#     #     ORDER BY time ASC
#     #     """,
#     #     (emp, att_date),
#     #     as_dict=True,
#     # )

#     # # ----------------------------------------------------------
#     # # NEW LOGIC:
#     # # If previous day was Night shift,
#     # # ignore logs before previous OUT time
#     # # ----------------------------------------------------------
#     # previous_date = add_days(att_date, -1)
#     # prev_shift = get_employee_shift(emp, previous_date)

#     # if prev_shift:
#     #     prev_shift_type = frappe.db.get_value(
#     #         "Shift Type", prev_shift, "custom_shift_type"
#     #     )

#     #     if prev_shift_type == "Night":
            
#     #         prev_att = frappe.db.get_value(
#     #             "Attendance",
#     #             {
#     #                 "employee": emp,
#     #                 "attendance_date": previous_date,
#     #                 "docstatus": 1
#     #             },
#     #             ["out_time"],
#     #             as_dict=True
#     #         )

#     #         # if prev_att and prev_att.out_time:
#     #         #     logs = [
#     #         #         log for log in logs
#     #         #         if normalize_to_minute(log["time"]) > normalize_to_minute(prev_att.out_time) and normalize_to_minute(log["time"]) != normalize_to_minute(prev_att.out_time)
#     #         #     ]
            
            
#     logs = frappe.db.sql(
#         """
#         SELECT name, time
#         FROM `tabEmployee Checkin`
#         WHERE employee=%s
#         AND DATE(time)=%s
#         ORDER BY time ASC
#         """,
#         (emp, att_date),
#         as_dict=True,
#     )

#     # Night shift spillover fix
#     previous_date = add_days(att_date, -1)
#     prev_shift = get_employee_shift(emp, previous_date)

#     if prev_shift:
#         prev_shift_type = frappe.db.get_value(
#             "Shift Type", prev_shift, "custom_shift_type"
#         )

#         if prev_shift_type == "Night":
#             prev_att = frappe.db.get_value(
#                 "Attendance",
#                 {
#                     "employee": emp,
#                     "attendance_date": previous_date,
#                     "docstatus": 1
#                 },
#                 ["out_time"],
#                 as_dict=True
#             )

#             if prev_att and prev_att.out_time:
#                 logs = [
#                     log for log in logs
#                     if normalize_to_minute(log["time"]) > normalize_to_minute(prev_att.out_time)
#                 ]

#     logs = filter_close_checkins(logs, threshold_minutes=2)
#     # # ----------------------------------------------------------

#     # logs = filter_close_checkins(logs, threshold_minutes=2)

#     # ==========================================================
#     # NO LOGS CASE
#     # ==========================================================
#     if not logs:

#         if holiday_type and not off_day_approved:
#             att_id = create_or_update_attendance(
#                 emp,
#                 att_date,
#                 None,
#                 None,
#                 0,
#                 None,
#                 None,
#                 skip_shift_time_rules=True,
#                 is_holiday_work=False,
#                 off_day_approved=off_day_approved,
#                 holiday_type=holiday_type
#             )

#             frappe.db.set_value(
#                 "Attendance",
#                 att_id,
#                 "status",
#                 holiday_type
#             )
#             return

#         create_or_update_attendance(
#             emp, att_date,
#             None, None, 0,
#             None, None,
#             skip_shift_time_rules=False,
#             is_holiday_work=False,
#         )
#         return

#     # holiday_type = get_holiday_type(emp, att_date)
#     # if holiday_type:
#     #     off_day_approved = has_approved_off_day_work(emp, att_date)

#     #     if off_day_approved:
#     #         is_holiday_work = True
#     #     else:
#     #         is_holiday_work = False

#     if len(logs) < 2:
#         create_or_update_attendance(
#             emp, att_date,
#             None, None, 0,
#             logs[0]["name"], logs[-1]["name"],
#             skip_shift_time_rules=False,
#             is_holiday_work=is_holiday_work,
#         )
#         return

#     in_time = normalize_to_minute(logs[0]["time"])
#     out_time = normalize_to_minute(logs[-1]["time"])

#     if in_time and out_time and out_time > in_time:
#         working_seconds = (out_time - in_time).total_seconds()
#         working_hours = working_seconds / 3600
#     else:
#         working_hours = 0

#     if working_hours <= 0:
#         att_id = create_or_update_attendance(
#             emp, att_date,
#             None, None, 0,
#             logs[0]["name"], logs[-1]["name"],
#             skip_shift_time_rules=False,
#             is_holiday_work=is_holiday_work,
#         )
#         return att_id

#     att_id = create_or_update_attendance(
#         emp, att_date,
#         in_time, out_time, working_hours,
#         logs[0]["name"], logs[-1]["name"],
#         skip_shift_time_rules=False,
#         is_holiday_work=is_holiday_work,
#         off_day_approved=off_day_approved,
#         holiday_type=holiday_type
#     )
#     return att_id




# # def mark_attendance(emp, att_date):
    
# #     frappe.log_error("Mark Attendance Called", f"employee {emp}, att_date {att_date}")
# #     if has_approved_leave(emp, att_date):
# #                 return

# #     shift_type = get_employee_shift(emp, att_date)

# #     if not shift_type:
# #         log_attendance_error(emp, att_date, "Shift not assigned")
# #         return

# #     shift_custom_type = frappe.db.get_value(
# #         "Shift Type", shift_type, "custom_shift_type"
# #     )

# #     is_holiday = is_holiday_or_weekoff(emp, att_date)
# #     off_day_approved = has_approved_off_day_work(emp, att_date)
# #     is_holiday_work = False

# #     # ==========================================================
# #     # 24 HOURS SHIFT
# #     # ==========================================================
# #     if shift_custom_type == "24 hours":

# #         first_in, last_out, first_checkin_id, last_checkin_id, working_hours, log_count = (
# #             get_24_hour_working_hours(emp, att_date, shift_type)
# #         )

# #         if log_count == 0:
# #             if is_holiday:
# #                 return

# #             create_or_update_attendance(
# #                 emp, att_date, None, None, 0,
# #                 None, None,
# #                 skip_shift_time_rules=True,
# #                 is_holiday_work=False,
# #             )
# #             return

# #         if is_holiday:
# #             is_holiday_work = True

# #         if log_count == 1:
# #             create_or_update_attendance(
# #                 emp, att_date, None, None, 0,
# #                 first_checkin_id, last_checkin_id,
# #                 skip_shift_time_rules=True,
# #                 is_holiday_work=is_holiday_work,
# #             )
# #             return

# #         create_or_update_attendance(
# #             emp, att_date,
# #             first_in, last_out, working_hours,
# #             first_checkin_id, last_checkin_id,
# #             skip_shift_time_rules=True,
# #             is_holiday_work=is_holiday_work,
# #         )
# #         return

# #     # ==========================================================
# #     # NIGHT SHIFT
# #     # ==========================================================
# #     if shift_custom_type == "Night":

# #         in_time, out_time, first_id, last_id, working_hours, log_count = (
# #             get_night_shift_logs(emp, att_date)
# #         )

# #         if log_count == 0:
# #             if is_holiday:
# #                 return

# #             create_or_update_attendance(
# #                 emp, att_date, None, None, 0,
# #                 None, None,
# #                 skip_shift_time_rules=True,
# #                 is_holiday_work=False,
# #             )
# #             return

# #         if is_holiday:
# #             is_holiday_work = True

# #         if log_count == 1:
# #             create_or_update_attendance(
# #                 emp, att_date, None, None, 0,
# #                 first_id, last_id,
# #                 skip_shift_time_rules=True,
# #                 is_holiday_work=is_holiday_work,
# #             )
# #             return

# #         create_or_update_attendance(
# #             emp, att_date,
# #             in_time, out_time, working_hours,
# #             first_id, last_id,
# #             skip_shift_time_rules=True,
# #             is_holiday_work=is_holiday_work,
# #         )
# #         return

# #     # ==========================================================
# #     # NORMAL SHIFT LOGIC
# #     # ==========================================================

# #     logs = frappe.db.sql(
# #         """
# #         SELECT name, time
# #         FROM `tabEmployee Checkin`
# #         WHERE employee=%s
# #         AND DATE(time)=%s
# #         ORDER BY time ASC
# #         """,
# #         (emp, att_date),
# #         as_dict=True,
# #     )

# #     # ----------------------------------------------------------
# #     # NEW LOGIC:
# #     # If previous day was Night shift,
# #     # ignore logs before previous OUT time
# #     # ----------------------------------------------------------
# #     previous_date = add_days(att_date, -1)
# #     prev_shift = get_employee_shift(emp, previous_date)

# #     if prev_shift:
# #         prev_shift_type = frappe.db.get_value(
# #             "Shift Type", prev_shift, "custom_shift_type"
# #         )

# #         if prev_shift_type == "Night":
# #             frappe.log_error("Night Shift Previous Day", f"Employee: {emp}, Previous Date: {previous_date}, Previous Shift: {prev_shift}")
# #             prev_att = frappe.db.get_value(
# #                 "Attendance",
# #                 {
# #                     "employee": emp,
# #                     "attendance_date": previous_date,
# #                     "docstatus": 1
# #                 },
# #                 ["out_time"],
# #                 as_dict=True
# #             )
# #             frappe.log_error("Previous Day Attendance", f"Employee: {emp}, Previous Date: {previous_date}, Previous Attendance: {prev_att} logs {logs}")
# #             if prev_att and prev_att.out_time:
# #                 logs = [
# #                     log for log in logs
# #                     if normalize_to_minute(log["time"]) > normalize_to_minute(prev_att.out_time) and normalize_to_minute(log["time"]) != normalize_to_minute(prev_att.out_time)
# #                 ]
# #             frappe.log_error("Filtered Logs After Night Shift Check", f"Employee: {emp}, Previous Date: {previous_date}, Logs: {logs}")
# #     # ----------------------------------------------------------

# #     logs = filter_close_checkins(logs, threshold_minutes=2)

# #     if not logs:
# #         if is_holiday:
# #             return

# #         create_or_update_attendance(
# #             emp, att_date,
# #             None, None, 0,
# #             None, None,
# #             skip_shift_time_rules=False,
# #             is_holiday_work=False,
# #         )
# #         return

# #     if is_holiday:
# #         is_holiday_work = True

# #     if len(logs) < 2:
# #         create_or_update_attendance(
# #             emp, att_date,
# #             None, None, 0,
# #             logs[0]["name"], logs[-1]["name"],
# #             skip_shift_time_rules=False,
# #             is_holiday_work=is_holiday_work,
# #         )
# #         return

# #     in_time = normalize_to_minute(logs[0]["time"])
# #     out_time = normalize_to_minute(logs[-1]["time"])

# #     if in_time and out_time and out_time > in_time:
# #         working_seconds = (out_time - in_time).total_seconds()
# #         working_hours = working_seconds / 3600
# #     else:
# #         working_hours = 0

# #     if working_hours <= 0:
# #         att_id = create_or_update_attendance(
# #             emp, att_date,
# #             None, None, 0,
# #             logs[0]["name"], logs[-1]["name"],
# #             skip_shift_time_rules=False,
# #             is_holiday_work=is_holiday_work,
# #         )
# #         return att_id

# #     att_id = create_or_update_attendance(
# #         emp, att_date,
# #         in_time, out_time, working_hours,
# #         logs[0]["name"], logs[-1]["name"],
# #         skip_shift_time_rules=False,
# #         is_holiday_work=is_holiday_work,
# #     )
# #     return att_id


# # def run_daily_attendance(att_date=None,only_for_jammu=False,branch=None):
    
# #     frappe.log_error("start_run_daily_attendance", f"Scheduler Started FOR Date: {att_date}")    
# #     if not att_date:
# #         att_date = add_days(getdate(), -1)
# #     else:
# #         att_date = getdate(att_date)

# #     if only_for_jammu:
# #             employees = frappe.get_all(
# #                 "Employee",
# #                 filters={"status": "Active", "branch": "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu" },
# #                 pluck="name"
# #             )
# #     else:
# #         filters = {"status": "Active"}

# #         if branch:
# #             filters["branch"] = branch

# #         employees = frappe.get_all(
# #             "Employee",
# #             filters=filters,
# #             pluck="name"
# #         )
    

# #     for emp in employees:
# #         try:
# #             if has_approved_leave(emp, att_date):
# #                 continue

# #             shift_type = get_employee_shift(emp, att_date)
            
# #             if not shift_type:
# #                 log_attendance_error(emp, att_date, "Shift not assigned")
# #                 continue

# #             shift_custom_type = frappe.db.get_value(
# #                 "Shift Type", shift_type, "custom_shift_type"
# #             )
# #             is_holiday = is_holiday_or_weekoff(emp, att_date)
# #             off_day_approved = has_approved_off_day_work(emp, att_date)
# #             is_holiday_work = is_holiday and off_day_approved
# #             if shift_custom_type == "24 hours":
                
# #                 first_in, last_out,first_checkin_id, last_checkin_id, working_hours, log_count = (
# #                     get_24_hour_working_hours(emp, att_date,shift_type)
# #                 )
# #                 if log_count == 0:
# #                     if log_count == 0 and is_holiday:
# #                         continue
# #                     create_or_update_attendance(
# #                         emp,
# #                         att_date,
# #                         None,
# #                         None,
# #                         0,
# #                         None,
# #                         skip_shift_time_rules=True,
# #                         is_holiday_work=is_holiday_work
# #                     )
# #                     continue

# #                 if log_count == 1:
# #                     if is_holiday and not off_day_approved:
# #                         continue   
# #                     create_or_update_attendance(
# #                         emp,
# #                         att_date,
# #                         None,
# #                         None,
# #                         0,
# #                         first_checkin_id,
# #                         last_checkin_id,
# #                         skip_shift_time_rules=True,
# #                         is_holiday_work=is_holiday_work
# #                     )
# #                     continue

# #                 create_or_update_attendance(
# #                     emp,
# #                     att_date,
# #                     first_in,
# #                     last_out,
# #                     working_hours,
# #                    first_checkin_id,
# #                     last_checkin_id,
# #                     skip_shift_time_rules=True,
# #                     is_holiday_work=is_holiday_work
# #                 )
# #                 continue
                
            
# #             if shift_custom_type == "Night":
        
# #                 in_time, out_time, first_id, last_id, working_hours, log_count = \
# #                     get_night_shift_logs(emp, att_date)

        
# #                 if log_count == 0:
# #                     if log_count == 0 and is_holiday:
# #                         continue
# #                     create_or_update_attendance(
# #                         emp,
# #                         att_date,
# #                         None,
# #                         None,
# #                         0,
# #                         None,
# #                         None,
# #                         skip_shift_time_rules=True,
# #                         is_holiday_work=is_holiday_work
# #                     )
# #                     continue
# #                 if log_count == 1:
# #                     if is_holiday and not off_day_approved:
# #                         continue  
# #                     create_or_update_attendance(
# #                         emp,
# #                         att_date,
# #                         None,
# #                         None,
# #                         0,
# #                         first_id,
# #                         last_id,
# #                         skip_shift_time_rules=True,
# #                         is_holiday_work=is_holiday_work
# #                     )
# #                     continue
# #                 create_or_update_attendance(
# #                     emp,
# #                     att_date,
# #                     in_time,
# #                     out_time,
# #                     working_hours,
# #                     first_id,
# #                     last_id,
# #                     skip_shift_time_rules=True,
# #                     is_holiday_work=is_holiday_work
# #                 )
# #                 continue
# #             if is_holiday and not off_day_approved:
# #                 continue
# #             logs = frappe.db.sql("""
# #                 SELECT
# #                     name,
# #                     time
# #                 FROM `tabEmployee Checkin`
# #                 WHERE employee=%s
# #                 AND DATE(time)=%s
# #                 ORDER BY time ASC
# #             """, (emp, att_date), as_dict=True)
# #             logs = filter_close_checkins(logs, threshold_minutes=2)
# #             if not logs:
# #                 if log_count == 0 and is_holiday:
# #                         continue
# #                 create_or_update_attendance(
# #                     emp, att_date, None, None, 0, None,None,skip_shift_time_rules=False,is_holiday_work=is_holiday_work
# #                 ),
# #                 continue

# #             if len(logs) < 2:
# #                 if is_holiday and not off_day_approved:
# #                         continue
# #                 create_or_update_attendance(
# #                     emp, att_date, None, None, 0, logs[0]["name"],logs[-1]["name"],skip_shift_time_rules=False,is_holiday_work=is_holiday_work
# #                 )
# #                 continue
            
# #             in_time = logs[0]["time"]
# #             out_time = logs[-1]["time"]
# #             in_time = normalize_to_minute(in_time)
# #             out_time = normalize_to_minute(out_time)

# #             if in_time and out_time and out_time > in_time:
# #                 working_seconds = (out_time - in_time).total_seconds()
# #                 working_hours = working_seconds / 3600
# #             else:
# #                 working_hours = 0

# #             if working_hours <= 0:
# #                 create_or_update_attendance(
# #                     emp, att_date, None, None, 0,logs[0]["name"], logs[-1]["name"],skip_shift_time_rules=False,is_holiday_work=is_holiday_work
# #                 )
# #                 continue

# #             create_or_update_attendance(
# #                 emp,
# #                 att_date,
# #                 in_time,
# #                 out_time,
# #                 working_hours,
# #                 logs[0]["name"],
# #                 logs[-1]["name"] ,skip_shift_time_rules=False,  # ✅ MAX CHECKIN ID,
# #                 is_holiday_work=is_holiday_work
# #             )

# #         except Exception as e:
# #             log_attendance_error(
# #                 emp, att_date, "Main Scheduler Failed", e
# #             )

# #     frappe.db.commit()
# def has_approved_off_day_work(employee, date):

#     return frappe.db.exists(
#         "Off-Day Work Request",
#         {
#             "employee": employee,
#             "date": date,
#             "workflow_state": "Approved"
#         }
#     )

# # def get_24_hour_working_hours(employee, date):
# #     logs = frappe.db.sql("""
# #         SELECT name, time
# #         FROM `tabEmployee Checkin`
# #         WHERE employee=%s
# #           AND DATE(time)=%s
# #         ORDER BY time ASC
# #     """, (employee, date), as_dict=True)

# #     if not logs or len(logs) < 2:
# #         return None, None, None, 0  

# #     first_in = logs[0]["time"]     
# #     last_out = logs[-1]["time"]    
# #     last_checkin_id = logs[-1]["name"]

# #     working_seconds = (last_out - first_in).total_seconds()
# #     working_hours = working_seconds / 3600 

# #     return first_in, last_out, last_checkin_id, working_hours
# # def get_24_hour_working_hours(employee, date):
# #     logs = frappe.db.sql("""
# #         SELECT name, time
# #         FROM `tabEmployee Checkin`
# #         WHERE employee=%s
# #           AND DATE(time)=%s
# #         ORDER BY time ASC
# #     """, (employee, date), as_dict=True)

# #     if not logs:
# #         return None, None, None, None, 0, 0  # ✅ 6


# #     if len(logs) < 2:
# #         return None, None,logs[0]["name"], logs[-1]["name"], 0, len(logs)

# #     first_in = logs[0]["time"]
# #     last_out = logs[-1]["time"]
# #     first_checkin_id=logs[0]["name"],
# #     last_checkin_id = logs[-1]["name"]

# #     working_hours = (last_out - first_in).total_seconds() / 3600

# #     return first_in, last_out,first_checkin_id, last_checkin_id, working_hours, len(logs)
# # def get_24_hour_working_hours(employee, date, shift_type):
# #     shift = frappe.db.get_value(
# #         "Shift Type",
# #         shift_type,
# #         ["start_time", "end_time", "custom_shift_type"],
# #         as_dict=True
# #     )

# #     if not shift:
# #         return None, None, None, None, 0, 0

        
# #     is_24_hour = shift.custom_shift_type == "24 hours"
# #     shift_start, shift_end = get_24_hour_shift_window(
# #         date,
# #         shift.start_time,
# #         shift.end_time,
# #         force_next_day=is_24_hour  # 🔥 THIS IS THE FIX
# #     )

# #     logs = frappe.db.sql("""
# #         SELECT name, time
# #         FROM `tabEmployee Checkin`
# #         WHERE employee = %s
# #           AND time >= %s
# #           AND time < %s
# #         ORDER BY time ASC
# #     """, (employee, shift_start, shift_end), as_dict=True)

# #     if not logs:
# #         return None, None, None, None, 0, 0 

# #     if len(logs) < 2:
# #         return None, None, logs[0]["name"], logs[-1]["name"], 0, len(logs)
# #     first_in = logs[0]["time"]
# #     last_out = logs[-1]["time"]

# #     working_hours = (last_out - first_in).total_seconds() / 3600
# #     return (
# #         first_in,
# #         last_out,
# #         logs[0]["name"],
# #         logs[-1]["name"],
# #         working_hours,
# #         len(logs),
# #     )
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
#         force_next_day=is_24_hour
#     )
    
#     logs = frappe.db.sql("""
#         SELECT name, time
#         FROM `tabEmployee Checkin`
#         WHERE employee = %s
#           AND time >= %s
#           AND time < %s
#         ORDER BY time ASC
#     """, (employee, shift_start, shift_end), as_dict=True)
#     if employee =="20015": 
#         print("ooooooooooo",logs,shift_start, shift_end)
#     if not logs:
#         return None, None, None, None, 0, 0
#     logs = filter_close_checkins(logs, threshold_minutes=2)
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

# def filter_close_checkins(logs, threshold_minutes=2):
#     """
#     Remove logs that occur within threshold_minutes of previous one.
#     logs = list of dicts having key 'time'
#     """
#     if not logs:
#         return []

#     filtered = [logs[0]]
#     threshold = timedelta(minutes=threshold_minutes)

#     for log in logs[1:]:
#         last_time = filtered[-1]["time"]
#         current_time = log["time"]

#         if current_time - last_time >= threshold:
#             filtered.append(log)

#     return filtered


# def get_24_hour_shift_window(date, start_time, end_time, force_next_day=False):
#     shift_start = get_datetime(f"{date} {start_time}")
#     shift_end = get_datetime(f"{date} {end_time}")

#     # 🔥 FORCE next day for 24-hour shifts
#     if force_next_day:
#         shift_end = add_days(shift_end, 1)

#     # Normal cross-day logic (for night shifts)
#     elif end_time <= start_time:
#         shift_end = add_days(shift_end, 1)

#     return shift_start, shift_end

# def get_night_shift_logs(employee, att_date):
#     """
#     Night shift logic:
#     IN  -> first log after 9 pM of attendance date
#     OUT -> last log before 9 PM of next date
#     """

#     start_dt = get_datetime(att_date).replace(hour=9, minute=0)
#     end_dt = get_datetime(add_days(att_date, 1)).replace(hour=8, minute=59, second=0)

#     logs = frappe.get_all(
#         "Employee Checkin",
#         filters=[
#             ["employee", "=", employee],
#             ["time", ">=", start_dt],
#             ["time", "<", end_dt]
#         ],
#         fields=["name", "time"],
#         order_by="time asc"
#     )

#     if not logs:
#         return None, None, None, None, 0, 0

#     first_log = logs[0]
#     last_log = logs[-1]

#     in_time = normalize_to_minute(first_log["time"])
#     out_time = normalize_to_minute(last_log["time"])

#     if out_time > in_time:
#         working_hours = (out_time - in_time).total_seconds() / 3600
#     else:
#         working_hours = 0

#     return (
#         in_time,
#         out_time,
#         first_log["name"],
#         last_log["name"],
#         working_hours,
#         len(logs)
#     )

# # =========================================================
# # LEAVE CHECK
# # =========================================================

# def has_approved_leave(employee, date):
#     return frappe.db.exists(
#         "Leave Application",
#         {
#             "employee": employee,
#             "status": "Approved",
#             "docstatus": 1,
#             "from_date": ("<=", date),
#             "to_date": (">=", date),
#             "half_day": 0
#         }
#     )

# # def has_approved_leave(employee, date):
# #     return frappe.db.exists(
# #         "Leave Application",
# #         {
# #             "employee": employee,
# #             "status": "Approved",
# #             "from_date": ("<=", date),
# #             "to_date": (">=", date)
# #         }
# #     )
    


# def is_holiday_or_weekoff(employee, date):
#     holiday_list = frappe.db.get_value(
#         "Employee", employee, "holiday_list"
#     )

#     # *For Safety
#     correct_holiday_list = None
    
    
#     assign_holiday_list = get_current_holiday_list(employee, date)
    
#     if assign_holiday_list:
#         # if not holiday_list:
#         #     correct_holiday_list = assign_holiday_list
#         # elif holiday_list != assign_holiday_list:
#         #     correct_holiday_list = assign_holiday_list
#         correct_holiday_list =  assign_holiday_list
#     else:
#         correct_holiday_list = holiday_list if holiday_list else None
    
    
#     if not correct_holiday_list:
#         log_attendance_error(
#             employee, date, "Holiday list not set"
#         )
#         return False

#     return frappe.db.exists(
#         "Holiday",
#         {
#             "parent": correct_holiday_list,
#             "holiday_date": date
#         }
#     )


# # =========================================================
# # MISSING CHECKOUT HANDLER
# # =========================================================

# def handle_missing_checkout(employee, date, in_time, shift_type):
#     try:
#         out_time = get_shift_end_datetime(shift_type, date)
#         if not out_time:
#             create_or_update_attendance(
#                 employee, date, in_time, None, 0,skip_shift_time_rules=False 
#             )
#             return

#         working_hours = (out_time - in_time).total_seconds() / 3600

#         create_or_update_attendance(
#             employee, date, in_time, out_time, working_hours,skip_shift_time_rules=False 
#         )

#     except Exception as e:
#         log_attendance_error(
#             employee, date, "Missing Checkout Failed", e
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
#         is_holiday_work=False,
#         off_day_approved=False,
#         holiday_type=None
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
#                 "early_exit_grace_period",
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
#         early_exit = 0
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
        
#         holiday_type = get_holiday_type(employee, date)
 
#         # 🔥 If holiday/weekoff work → only hours matter
#         if holiday_type:

#             # ❌ No approval → ALWAYS holiday
#             if not off_day_approved:
#                 status = holiday_type

#             # ✅ Approved → check hours
#             else:
#                 if working_hours >= half_day_hours:
#                     status = "Present"
#                 else:
#                     status = holiday_type
 
#         else:
#             if working_hours <= absent_hours:
#                 status = "Absent"
#             elif working_hours < half_day_hours:
#                 status = "Half Day"
#             else:
#                 status = "Present"
 
 
 
#         if is_half_day_leave:
#             status = "Half Day"
#         if single_checkin and not is_half_day_leave:
#             status = "Partially"
            
#         if status != "Absent":
#             if in_time and out_time and not skip_shift_time_rules and not is_holiday_work:
 
#                 shift_start = combine_datetime(date, shift.start_time)
#                 shift_end = combine_datetime(date, shift.end_time)
                
#                 allowed_late_minutes = shift.late_entry_grace_period
#                 allowed_early_exit_minutes = shift.early_exit_grace_period
                    
#                 if allowed_late_minutes and int(allowed_late_minutes) > 0:
 
#                     latest_allowed_in = add_to_date(
#                         shift_start,
#                         minutes=int(allowed_late_minutes)
#                     )
 
#                     if in_time > latest_allowed_in and not is_half_day_leave:
#                         late_entry = 1
#                         status = "Half Day"
                
                
#                 if not late_entry and allowed_early_exit_minutes and int(allowed_early_exit_minutes) > 0:
                    
#                     latest_allowed_out = add_to_date(
#                         shift_end,
#                         minutes=-int(allowed_early_exit_minutes)
#                     )
                        
#                     if out_time < latest_allowed_out and not is_half_day_leave:
#                         early_exit = 1
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
#                 "shift": shift_type,
#                 "in_time": in_time,
#                 "out_time": out_time,
#                 "working_hours": working_hours,
#                 "status": status,
#                 "late_entry": late_entry,
#                 "early_exit": early_exit,
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
#                 working_hours, status, late_entry, early_exit, custom_branch,
#                 docstatus, creation, modified, owner, modified_by)
 
#                 VALUES (%s,%s,%s,%s,%s,
#                         %s,%s,%s,%s, %s,
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
#                 early_exit,
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
                
#                 if no_checkin_found or single_checkin:
#                     revert_penalty_leave(att_name)
#                     deduct_leave_by_priority(employee, date, status, att_name, force_lwp=True)
#                 else:
#                     revert_penalty_leave(att_name)
#                     deduct_leave_by_priority(employee, date, status, att_name, force_lwp=False)
#                 # elif single_checkin:
#                 #     revert_penalty_leave(att_name)
#                 #     deduct_leave_by_priority(employee, date, status, att_name, force_lwp=True)
#                 # else:
#                 #     revert_penalty_leave(att_name)
                
#             else:
#                 half_day_status = "Present"
#                 revert_penalty_leave(att_name)
 
#             frappe.db.set_value(
#                 "Attendance",
#                 att_name,
#                 "half_day_status",
#                 half_day_status,
#                 update_modified=False
#             )

#         # Clear old penalty first if status changed
#         # if old_status and old_status != "Present" and status =="Present":
#             # revert_penalty_leave(att_name)
#         if is_holiday_work:
#             revert_penalty_leave(att_name)
#         # Apply penalty only if checkin exists
                
#         if not is_holiday_work and not holiday_type:
        
#             if not is_half_day_leave:
#                 if status == "Partially":
#                     revert_penalty_leave(att_name)
#                     deduct_leave_by_priority(employee, date, status, att_name, force_lwp=True)
#                 elif status == "Absent" and no_checkin_found:
#                     revert_penalty_leave(att_name)                    
#                     deduct_leave_by_priority(employee, date, status, att_name, force_lwp=True)
#                 elif status in ["Absent", "Half Day"]:
#                     revert_penalty_leave(att_name)
                    
#                     deduct_leave_by_priority(
#                         employee,
#                         date,
#                         status,
#                         att_name
#                     )
#                 else:
#                     revert_penalty_leave(att_name)
            
                
#         #     if status in ["Absent", "Half Day", "Partially"]:
    
#         #         if not is_half_day_leave and not no_checkin_found:
    
#         #             deduct_leave_by_priority(
#         #                 employee,
#         #                 date,
#         #                 status,
#         #                 att_name
#         #             )
        

#         if holiday_type and not is_holiday_work and status != "Present":
#             frappe.db.set_value(
#             "Attendance",
#             att_name,
#             "status",
#             holiday_type,
#             update_modified=False
#         )
        
        
#         # if old_status in ("Absent", "Half Day","Partially") and status == "Present":
#         #     revert_penalty_leave(att_name)
#         return att_name
        
#     except Exception as e:
#         frappe.log_error("create_or_update attendance", frappe.get_traceback())
#         log_attendance_error(
#             employee,
#             date,
#             "Attendance Save Failed",
#             e
#         )


# # * ------------------------------------------------------------------was using---------------------------------------------------------------------------------------
# # def create_or_update_attendance(
# #         employee,
# #         date,
# #         in_time,
# #         out_time,
# #         working_hours,
# #         first_checkin_id=None,
# #         last_checkin_id=None,
# #         skip_shift_time_rules=True,
# #         is_holiday_work=False
# # ):
# #     try:
# #         if employee == "001100: CL Test Eleven":
# #                 frappe.log_error(f"mark attendance for {employee}", f"{date}  in time {in_time}  out time{out_time}")
# #         no_checkin_found = not first_checkin_id and not last_checkin_id
# #         frappe.log_error("Checkin Found or not", f"no checkin found {no_checkin_found}, first in {first_checkin_id}, last_check {last_checkin_id}")
# #         shift_type = get_employee_shift(employee, date)
# #         if not shift_type:
# #             return
        
# #         shift = frappe.db.get_value(
# #             "Shift Type",
# #             shift_type,
# #             [
# #                 "start_time",
# #                 "end_time",
# #                 "late_entry_grace_period",
# #                 "early_exit_grace_period",
# #                 "allow_check_out_after_shift_end_time",
# #                 "working_hours_threshold_for_half_day",
# #                 "working_hours_threshold_for_absent"
# #             ],
# #             as_dict=True
# #         )
        
# #         leave = frappe.db.get_value(
# #             "Leave Application",
# #             {
# #                 "employee": employee,
# #                 "status": "Approved",
# #                 "from_date": ("<=", date),
# #                 "to_date": (">=", date),
# #                 "docstatus": 1
# #             },
# #             ["name", "half_day", "half_day_date"],
# #             as_dict=True
# #         )
 
# #         is_half_day_leave = bool(
# #             leave and leave.half_day and leave.half_day_date == date
# #         )
 
# #         late_entry = 0
# #         early_exit = 0
# #         single_checkin = False
# #         if first_checkin_id and last_checkin_id:
# #             if first_checkin_id == last_checkin_id:
# #                 single_checkin = True
# #                 single_time = frappe.db.get_value(
# #                     "Employee Checkin",
# #                     first_checkin_id,
# #                     "time"
# #                 )
# #                 in_time = in_time or single_time
# #                 out_time = None
# #             else:
# #                 if in_time is None:
# #                     in_time = frappe.db.get_value(
# #                         "Employee Checkin",
# #                         first_checkin_id,
# #                         "time"
# #                     )
# #                 if out_time is None:
# #                     out_time = frappe.db.get_value(
# #                         "Employee Checkin",
# #                         last_checkin_id,
# #                         "time"
# #                     )
 
# #         half_day_hours = float(
# #             shift.working_hours_threshold_for_half_day or 8
# #         )
# #         absent_hours = float(
# #             shift.working_hours_threshold_for_absent or 3
# #         )
 
# #         # 🔥 If holiday/weekoff work → only hours matter
# #         if is_holiday_work:
 
# #             if working_hours <= 0:
# #                 status = "Absent"
# #             elif working_hours < half_day_hours:
# #                 status = "Half Day"
# #             else:
# #                 status = "Present"
 
# #         else:
# #             if working_hours <= absent_hours:
# #                 status = "Absent"
# #             elif working_hours < half_day_hours:
# #                 status = "Half Day"
# #             else:
# #                 status = "Present"
 
 
 
# #         if is_half_day_leave:
# #             status = "Half Day"
# #         if single_checkin:
# #             status = "Partially"
# #         if status != "Absent":
# #             if in_time and out_time and not skip_shift_time_rules and not is_holiday_work:
 
# #                 shift_start = combine_datetime(date, shift.start_time)
# #                 shift_end = combine_datetime(date, shift.end_time)
                
# #                 allowed_late_minutes = shift.late_entry_grace_period
# #                 allowed_early_exit_minutes = shift.early_exit_grace_period
                
# #                 if employee == "001100: CL Test Eleven":
# #                     frappe.log_error(f"mark_attednance{employee}", f" allowed exit {allowed_early_exit_minutes}  allowed late minutes{allowed_late_minutes}")
                    
# #                 if allowed_late_minutes and int(allowed_late_minutes) > 0:
 
# #                     latest_allowed_in = add_to_date(
# #                         shift_start,
# #                         minutes=int(allowed_late_minutes)
# #                     )
 
# #                     if in_time > latest_allowed_in:
# #                         late_entry = 1
# #                         status = "Half Day"
                
                
# #                 if not late_entry and allowed_early_exit_minutes and int(allowed_early_exit_minutes) > 0:
                    
# #                     latest_allowed_out = add_to_date(
# #                         shift_end,
# #                         minutes=-int(allowed_early_exit_minutes)
# #                     )
# #                     if employee == "001100: CL Test Eleven":
# #                         frappe.log_error(f"Early Exit {employee}", f" allowed exit{allowed_early_exit_minutes} allowed time {latest_allowed_out}  out time {out_time}  end time {shift_end}")
                        
# #                     if out_time < latest_allowed_out:
# #                         early_exit = 1
# #                         status = "Half Day"
                        
                
# #         attendance_name = frappe.db.exists(
# #             "Attendance",
# #             {
# #                 "employee": employee,
# #                 "attendance_date": date,
# #                 "docstatus": ["!=", 2]
# #             }
# #         )
# #         old_status = None
# #         if attendance_name:
# #             old_status = frappe.db.get_value("Attendance", attendance_name, "status")
# #         employee_details = frappe.db.get_value(
# #             "Employee",
# #             employee,
# #             ["employee_name", "department", "company", "branch"],
# #             as_dict=True
# #         )
 
# #         if attendance_name:
 
# #             att_name = attendance_name
# #             if employee == "001100: CL Test Eleven":
# #                 frappe.log_error(f"Marking Attendance {employee}", f" early exit{early_exit}")
# #             frappe.db.set_value(
# #             "Attendance",
# #             att_name,
# #             {
# #                 "shift": shift_type,
# #                 "in_time": in_time,
# #                 "out_time": out_time,
# #                 "working_hours": working_hours,
# #                 "status": status,
# #                 "late_entry": late_entry,
# #                 "early_exit": early_exit,
# #                 "employee_name": employee_details.employee_name,
# #                 "department": employee_details.department,
# #                 "company": employee_details.company,
# #                 "custom_branch": employee_details.branch,
# #             },
# #             update_modified=False
# #         )
        
# #         else:
# #             frappe.log_error("Attendance not created", "assa")
# #             att_name = frappe.generate_hash(length=12)
 
# #             frappe.db.sql("""
# #                 INSERT INTO `tabAttendance`
# #                 (name, employee, employee_name, department, company,
# #                 attendance_date, shift, in_time, out_time,
# #                 working_hours, status, late_entry, early_exit, custom_branch,
# #                 docstatus, creation, modified, owner, modified_by)
 
# #                 VALUES (%s,%s,%s,%s,%s,
# #                         %s,%s,%s,%s, %s,
# #                         %s,%s,%s,%s,
# #                         1, NOW(), NOW(), %s, %s)
# #             """, (
# #                 att_name,
# #                 employee,
# #                 employee_details.employee_name,
# #                 employee_details.department,
# #                 employee_details.company,
# #                 date,
# #                 shift_type,
# #                 in_time,
# #                 out_time,
# #                 working_hours,
# #                 status,
# #                 late_entry,
# #                 early_exit,
# #                 employee_details.branch,
# #                 frappe.session.user,
# #                 frappe.session.user,
# #             ))
 
# #             frappe.db.commit()
# #         if first_checkin_id:
# #             frappe.db.set_value(
# #                 "Employee Checkin",
# #                 first_checkin_id,
# #                 "attendance",
# #                 att_name,
# #                 update_modified=False
# #             )
 
# #         if last_checkin_id:
# #             frappe.db.set_value(
# #                 "Employee Checkin",
# #                 last_checkin_id,
# #                 "attendance",
# #                 att_name,
# #                 update_modified=False
# #             )
 
# #         if is_half_day_leave:
 
# #             absent_threshold = float(
# #                 shift.working_hours_threshold_for_absent or 0
# #             )
# #             if working_hours <= absent_threshold:
# #                 half_day_status = "Absent"
# #             else:
# #                 half_day_status = "Present"
 
# #             frappe.db.set_value(
# #                 "Attendance",
# #                 att_name,
# #                 "half_day_status",
# #                 half_day_status,
# #                 update_modified=False
# #             )
 
 
# #         # Clear old penalty first if status changed
# #         if old_status and old_status != status:
# #             revert_penalty_leave(att_name)
# #         if is_holiday_work:
# #             revert_penalty_leave(att_name)
# #         # Apply penalty only if checkin exists
        
# #         frappe.log_error("is holiday work",f"\n\n is holiday work {is_holiday_work} status {status}\n\n")
# #         if not is_holiday_work:
# #             if employee == "001100: CL Test Eleven":
# #                 frappe.log_error("not holiday work", f"\n\n is not holiday work  {is_holiday_work}\n\n")
# #             if status in ["Absent", "Half Day", "Partially"]:
# #                 frappe.log_error("Status", f"\n\n  status {status}is in {['Absent', 'Half Day', 'Partially']}\n\n")
# #                 frappe.log_error("checkin found", f"checkin found or not {no_checkin_found}")
# #                 if not is_half_day_leave and not no_checkin_found:
# #                     frappe.log_error("deducting Leave",f"\n\n deducting LEAVE by prio rity\n\n")
# #                     deduct_leave_by_priority(
# #                         employee,
# #                         date,
# #                         status,
# #                         att_name
# #                     )
        
 
 
        
# #         # if old_status in ("Absent", "Half Day","Partially") and status == "Present":
# #         #     revert_penalty_leave(att_name)
# #         return att_name
        
# #     except Exception as e:
# #         frappe.log_error("create_or_update attendance", frappe.get_traceback())
# #         log_attendance_error(
# #             employee,
# #             date,
# #             "Attendance Save Failed",
# #             e
# #         )

# # * ------------------------------------------------------------------was using---------------------------------------------------------------------------------------
# # def create_or_update_attendance(
# #         employee,
# #         date,
# #         in_time,
# #         out_time,
# #         working_hours,
# #         first_checkin_id=None,
# #         last_checkin_id=None,
# #         skip_shift_time_rules=True,
# #         is_holiday_work=False
# # ):
# #     try:
# #         no_checkin_found = not first_checkin_id and not last_checkin_id
 
# #         shift_type = get_employee_shift(employee, date)
# #         if not shift_type:
# #             return
        
# #         shift = frappe.db.get_value(
# #             "Shift Type",
# #             shift_type,
# #             [
# #                 "start_time",
# #                 "end_time",
# #                 "late_entry_grace_period",
# #                 "allow_check_out_after_shift_end_time",
# #                 "working_hours_threshold_for_half_day",
# #                 "working_hours_threshold_for_absent"
# #             ],
# #             as_dict=True
# #         )
        
# #         leave = frappe.db.get_value(
# #             "Leave Application",
# #             {
# #                 "employee": employee,
# #                 "status": "Approved",
# #                 "from_date": ("<=", date),
# #                 "to_date": (">=", date),
# #                 "docstatus": 1
# #             },
# #             ["name", "half_day", "half_day_date"],
# #             as_dict=True
# #         )
 
# #         is_half_day_leave = bool(
# #             leave and leave.half_day and leave.half_day_date == date
# #         )
 
# #         late_entry = 0
# #         single_checkin = False
# #         if first_checkin_id and last_checkin_id:
# #             if first_checkin_id == last_checkin_id:
# #                 single_checkin = True
# #                 single_time = frappe.db.get_value(
# #                     "Employee Checkin",
# #                     first_checkin_id,
# #                     "time"
# #                 )
# #                 in_time = in_time or single_time
# #                 out_time = None
# #             else:
# #                 if in_time is None:
# #                     in_time = frappe.db.get_value(
# #                         "Employee Checkin",
# #                         first_checkin_id,
# #                         "time"
# #                     )
# #                 if out_time is None:
# #                     out_time = frappe.db.get_value(
# #                         "Employee Checkin",
# #                         last_checkin_id,
# #                         "time"
# #                     )
 
# #         half_day_hours = float(
# #             shift.working_hours_threshold_for_half_day or 8
# #         )
# #         absent_hours = float(
# #             shift.working_hours_threshold_for_absent or 3
# #         )
 
# #         # 🔥 If holiday/weekoff work → only hours matter
# #         if is_holiday_work:
 
# #             if working_hours <= 0:
# #                 status = "Absent"
# #             elif working_hours < half_day_hours:
# #                 status = "Half Day"
# #             else:
# #                 status = "Present"
 
# #         else:
# #             if working_hours <= absent_hours:
# #                 status = "Absent"
# #             elif working_hours < half_day_hours:
# #                 status = "Half Day"
# #             else:
# #                 status = "Present"
 
 
 
# #         if is_half_day_leave:
# #             status = "Half Day"
# #         if single_checkin:
# #             status = "Partially"
# #         if status != "Absent":
# #             if in_time and out_time and not skip_shift_time_rules and not is_holiday_work:
 
# #                 shift_start = combine_datetime(date, shift.start_time)
 
# #                 allowed_late_minutes = shift.late_entry_grace_period
 
# #                 if allowed_late_minutes and int(allowed_late_minutes) > 0:
 
# #                     latest_allowed_in = add_to_date(
# #                         shift_start,
# #                         minutes=int(allowed_late_minutes)
# #                     )
 
# #                     if in_time > latest_allowed_in:
# #                         late_entry = 1
# #                         status = "Half Day"
 
   
# #         attendance_name = frappe.db.exists(
# #             "Attendance",
# #             {
# #                 "employee": employee,
# #                 "attendance_date": date,
# #                 "docstatus": ["!=", 2]
# #             }
# #         )
# #         old_status = None
# #         if attendance_name:
# #             old_status = frappe.db.get_value("Attendance", attendance_name, "status")
# #         employee_details = frappe.db.get_value(
# #             "Employee",
# #             employee,
# #             ["employee_name", "department", "company", "branch"],
# #             as_dict=True
# #         )
 
# #         if attendance_name:
 
# #             att_name = attendance_name
 
# #             frappe.db.set_value(
# #             "Attendance",
# #             att_name,
# #             {
# #                 "in_time": in_time,
# #                 "out_time": out_time,
# #                 "working_hours": working_hours,
# #                 "status": status,
# #                 "late_entry": late_entry,
# #                 "employee_name": employee_details.employee_name,
# #                 "department": employee_details.department,
# #                 "company": employee_details.company,
# #                 "custom_branch": employee_details.branch,
# #             },
# #             update_modified=False
# #         )
        
# #         else:
 
# #             att_name = frappe.generate_hash(length=12)
 
# #             frappe.db.sql("""
# #                 INSERT INTO `tabAttendance`
# #                 (name, employee, employee_name, department, company,
# #                 attendance_date, shift, in_time, out_time,
# #                 working_hours, status, late_entry, custom_branch,
# #                 docstatus, creation, modified, owner, modified_by)
 
# #                 VALUES (%s,%s,%s,%s,%s,
# #                         %s,%s,%s,%s,
# #                         %s,%s,%s,%s,
# #                         1, NOW(), NOW(), %s, %s)
# #             """, (
# #                 att_name,
# #                 employee,
# #                 employee_details.employee_name,
# #                 employee_details.department,
# #                 employee_details.company,
# #                 date,
# #                 shift_type,
# #                 in_time,
# #                 out_time,
# #                 working_hours,
# #                 status,
# #                 late_entry,
# #                 employee_details.branch,
# #                 frappe.session.user,
# #                 frappe.session.user,
# #             ))
 
# #             frappe.db.commit()
# #         if first_checkin_id:
# #             frappe.db.set_value(
# #                 "Employee Checkin",
# #                 first_checkin_id,
# #                 "attendance",
# #                 att_name,
# #                 update_modified=False
# #             )
 
# #         if last_checkin_id:
# #             frappe.db.set_value(
# #                 "Employee Checkin",
# #                 last_checkin_id,
# #                 "attendance",
# #                 att_name,
# #                 update_modified=False
# #             )
 
# #         if is_half_day_leave:
 
# #             absent_threshold = float(
# #                 shift.working_hours_threshold_for_absent or 0
# #             )
# #             if working_hours <= absent_threshold:
# #                 half_day_status = "Absent"
# #             else:
# #                 half_day_status = "Present"
 
# #             frappe.db.set_value(
# #                 "Attendance",
# #                 att_name,
# #                 "half_day_status",
# #                 half_day_status,
# #                 update_modified=False
# #             )
 
 
# #         # Clear old penalty first if status changed
# #         if old_status and old_status != status:
# #             revert_penalty_leave(att_name)
 
# #         # Apply penalty only if checkin exists
# #         if status in ["Absent", "Half Day", "Partially"]:
 
# #             if not is_half_day_leave and not no_checkin_found:
# #                 deduct_leave_by_priority(
# #                     employee,
# #                     date,
# #                     status,
# #                     att_name
# #                 )
 
 
 
        
# #         # if old_status in ("Absent", "Half Day","Partially") and status == "Present":
# #         #     revert_penalty_leave(att_name)
# #         return att_name
        
# #     except Exception as e:
# #         log_attendance_error(
# #             employee,
# #             date,
# #             "Attendance Save Failed",
# #             e
# #         )


# # def create_or_update_attendance(
# #         employee,
# #         date,
# #         in_time,
# #         out_time,
# #         working_hours,
# #         first_checkin_id=None,
# #         last_checkin_id=None,
# #         skip_shift_time_rules=True,
# #         is_holiday_work=False
# # ):
# #     try:
# #         shift_type = get_employee_shift(employee, date)
# #         if not shift_type:
# #             return
        
# #         shift = frappe.db.get_value(
# #             "Shift Type",
# #             shift_type,
# #             [
# #                 "start_time",
# #                 "end_time",
# #                 "late_entry_grace_period",
# #                 "allow_check_out_after_shift_end_time",
# #                 "working_hours_threshold_for_half_day",
# #                 "working_hours_threshold_for_absent"
# #             ],
# #             as_dict=True
# #         )
        
# #         leave = frappe.db.get_value(
# #             "Leave Application",
# #             {
# #                 "employee": employee,
# #                 "status": "Approved",
# #                 "from_date": ("<=", date),
# #                 "to_date": (">=", date),
# #                 "docstatus": 1
# #             },
# #             ["name", "half_day", "half_day_date"],
# #             as_dict=True
# #         )

# #         is_half_day_leave = bool(
# #             leave and leave.half_day and leave.half_day_date == date
# #         )

# #         late_entry = 0
# #         single_checkin = False
# #         if first_checkin_id and last_checkin_id:
# #             if first_checkin_id == last_checkin_id:
# #                 single_checkin = True
# #                 single_time = frappe.db.get_value(
# #                     "Employee Checkin",
# #                     first_checkin_id,
# #                     "time"
# #                 )
# #                 in_time = in_time or single_time
# #                 out_time = None
# #             else:
# #                 if in_time is None:
# #                     in_time = frappe.db.get_value(
# #                         "Employee Checkin",
# #                         first_checkin_id,
# #                         "time"
# #                     )
# #                 if out_time is None:
# #                     out_time = frappe.db.get_value(
# #                         "Employee Checkin",
# #                         last_checkin_id,
# #                         "time"
# #                     )

# #         half_day_hours = float(
# #             shift.working_hours_threshold_for_half_day or 8
# #         )
# #         absent_hours = float(
# #             shift.working_hours_threshold_for_absent or 3
# #         )

# #         # 🔥 If holiday/weekoff work → only hours matter
# #         if is_holiday_work:

# #             if working_hours <= 0:
# #                 status = "Absent"
# #             elif working_hours < half_day_hours:
# #                 status = "Half Day"
# #             else:
# #                 status = "Present"

# #         else:
# #             if working_hours <= absent_hours:
# #                 status = "Absent"
# #             elif working_hours < half_day_hours:
# #                 status = "Half Day"
# #             else:
# #                 status = "Present"



# #         if is_half_day_leave:
# #             status = "Half Day"
# #         if single_checkin:
# #             status = "Partially"
# #         if status != "Absent":
# #             if in_time and out_time and not skip_shift_time_rules and not is_holiday_work:

# #                 shift_start = combine_datetime(date, shift.start_time)

# #                 allowed_late_minutes = shift.late_entry_grace_period

# #                 if allowed_late_minutes and int(allowed_late_minutes) > 0:

# #                     latest_allowed_in = add_to_date(
# #                         shift_start,
# #                         minutes=int(allowed_late_minutes)
# #                     )

# #                     if in_time > latest_allowed_in:
# #                         late_entry = 1
# #                         status = "Half Day"

   
# #         attendance_name = frappe.db.exists(
# #             "Attendance",
# #             {
# #                 "employee": employee,
# #                 "attendance_date": date,
# #                 "docstatus": ["!=", 2]
# #             }
# #         )
# #         old_status = None
# #         if attendance_name:
# #             old_status = frappe.db.get_value("Attendance", attendance_name, "status")
# #         employee_details = frappe.db.get_value(
# #             "Employee",
# #             employee,
# #             ["employee_name", "department", "company", "branch"],
# #             as_dict=True
# #         )

# #         if attendance_name:

# #             att_name = attendance_name

# #             frappe.db.set_value(
# #             "Attendance",
# #             att_name,
# #             {
# #                 "in_time": in_time,
# #                 "out_time": out_time,
# #                 "working_hours": working_hours,
# #                 "status": status,
# #                 "late_entry": late_entry,
# #                 "employee_name": employee_details.employee_name,
# #                 "department": employee_details.department,
# #                 "company": employee_details.company,
# #                 "custom_branch": employee_details.branch,
# #             },
# #             update_modified=False
# #         )
        
# #         else:

# #             att_name = frappe.generate_hash(length=12)

# #             frappe.db.sql("""
# #                 INSERT INTO `tabAttendance`
# #                 (name, employee, employee_name, department, company,
# #                 attendance_date, shift, in_time, out_time,
# #                 working_hours, status, late_entry, custom_branch,
# #                 docstatus, creation, modified, owner, modified_by)

# #                 VALUES (%s,%s,%s,%s,%s,
# #                         %s,%s,%s,%s,
# #                         %s,%s,%s,%s,
# #                         1, NOW(), NOW(), %s, %s)
# #             """, (
# #                 att_name,
# #                 employee,
# #                 employee_details.employee_name,
# #                 employee_details.department,
# #                 employee_details.company,
# #                 date,
# #                 shift_type,
# #                 in_time,
# #                 out_time,
# #                 working_hours,
# #                 status,
# #                 late_entry,
# #                 employee_details.branch,
# #                 frappe.session.user,
# #                 frappe.session.user,
# #             ))

# #             frappe.db.commit()
# #         if first_checkin_id:
# #             frappe.db.set_value(
# #                 "Employee Checkin",
# #                 first_checkin_id,
# #                 "attendance",
# #                 att_name,
# #                 update_modified=False
# #             )

# #         if last_checkin_id:
# #             frappe.db.set_value(
# #                 "Employee Checkin",
# #                 last_checkin_id,
# #                 "attendance",
# #                 att_name,
# #                 update_modified=False
# #             )

# #         if is_half_day_leave:

# #             absent_threshold = float(
# #                 shift.working_hours_threshold_for_absent or 0
# #             )
# #             if working_hours <= absent_threshold:
# #                 half_day_status = "Absent"
# #             else:
# #                 half_day_status = "Present"

# #             frappe.db.set_value(
# #                 "Attendance",
# #                 att_name,
# #                 "half_day_status",
# #                 half_day_status,
# #                 update_modified=False
# #             )


# #         # 🔥 Clear old penalty first if status changed
# #         if old_status and old_status != status:
# #             revert_penalty_leave(att_name)

# #         if status in ["Absent", "Half Day", "Partially"]:
# #             if not is_half_day_leave:
# #                 deduct_leave_by_priority(
# #                     employee,
# #                     date,
# #                     status,
# #                     att_name
# #                 )


        
# #         # if old_status in ("Absent", "Half Day","Partially") and status == "Present":
# #         #     revert_penalty_leave(att_name)
# #         return att_name
        
# #     except Exception as e:
# #         log_attendance_error(
# #             employee,
# #             date,
# #             "Attendance Save Failed",
# #             e
# #         )


# def combine_datetime(date, shift_time):
#     """
#     Handles both time and timedelta from Shift Type
#     """
#     if isinstance(shift_time, timedelta):
#         seconds = int(shift_time.total_seconds())
#         hours = seconds // 3600
#         minutes = (seconds % 3600) // 60
#         return datetime.combine(date, time(hours, minutes))

#     return datetime.combine(date, shift_time)


# # def deduct_leave_by_priority(employee, date, status, attendance):
# #     priority = [
# #         "Casual Leave",
# #         "Sick Leave",
# #         "Privilege Leave",
# #         "Leave Without Pay"
# #     ]

# #     leave_days = 0.5 if status == "Half Day" else 1
# #     att = frappe.get_doc("Attendance", attendance)
# #     for leave_type in priority:
# #         leave_type_doc = frappe.get_cached_doc("Leave Type", leave_type)

# #         if leave_type_doc.is_lwp:
# #             continue

# #         balance = get_leave_balance_on(employee, leave_type, date)

# #         if balance < leave_days:
# #             continue

# #         att.db_set({
# #             "custom_penalty_leave_type": leave_type,
# #             "custom_penalty_leave_count": leave_days,
# #             "custom_is_penalize": 1
# #         })

# #         create_leave_ledger(
# #             employee, leave_type, date, status, attendance
# #         )

# #         return  


# #     lwp_type = next(
# #         (lt for lt in priority
# #          if frappe.get_cached_doc("Leave Type", lt).is_lwp),
# #         None
# #     )

# #     if lwp_type:
# #         att.db_set({
# #             "custom_penalty_leave_type": lwp_type,
# #             "custom_penalty_leave_count": leave_days,
# #             "custom_is_penalize": 1
# #         })

# def deduct_leave_by_priority(employee, date, status, attendance, force_lwp = False):
    
#     priority = [
#         "Casual Leave",
#         "Sick Leave",
#         "Privilege Leave",
#         # "Leave Without Pay"
#     ]

#     if employee == "001100: CL Test Eleven":
#             frappe.log_error(f"penalty already applied{employee}", f"is forced lwp {force_lwp}")
            
#     if status == "Half Day":    
#         total_penalty_days = 0.5
#     else:
#         total_penalty_days = 1.0   # Absent OR Partially

#     remaining_days = total_penalty_days

#     att = frappe.get_doc("Attendance", attendance)

#     if att.custom_is_penalize:
        
#         return

#     if not force_lwp:
#         for leave_type in priority:
#             balance = flt(get_leave_balance_on(employee, leave_type, date), 2)

#             if employee == "001100: CL Test Eleven":
#                 frappe.log_error(f"Leave Balance{employee}", f"{balance}")
#             if balance <= 0:
#                 continue

#             if balance < remaining_days:
#                 continue

#             att.db_set({
#                 "custom_penalty_leave_type": leave_type,
#                 "custom_penalty_leave_count": -total_penalty_days,
#                 "custom_is_penalize": 1
#             })

#             create_leave_ledger(
#                 employee=employee,
#                 leave_type=leave_type,
#                 date=date,
#                 status=status,
#                 attendance=attendance,
#                 leave_days=remaining_days
#             )

#             return 

#     lwp_type = frappe.db.get_value(
#         "Leave Type", {"is_lwp": 1}, "name"
#     )

#     if lwp_type:
#         att.db_set({
#             "custom_penalty_leave_type": lwp_type,
#             "custom_penalty_leave_count": -remaining_days,
#             "custom_is_penalize": 1
#         })

#         create_leave_ledger(
#             employee=employee,
#             leave_type=lwp_type,
#             date=date,
#             status=status,
#             attendance=attendance,
#             leave_days=remaining_days,
#             is_lwp=1
#         )
#     else:
#         frappe.log_error("error_deduct_leave_by_priority", f"NO lWP LEAVE TYPE FOUND")
#     return

# def get_leave_allocation(employee, leave_type, date):
#     allocation = frappe.db.sql("""
#         SELECT name
#         FROM `tabLeave Allocation`
#         WHERE employee = %s
#           AND leave_type = %s
#           AND docstatus = 1
#           AND from_date <= %s
#           AND to_date >= %s
#         ORDER BY from_date DESC
#         LIMIT 1
#     """, (employee, leave_type, date, date), as_dict=True)

#     return allocation[0].name if allocation else None


# def get_leave_balance(employee, leave_type, date):
#     try:
#         return frappe.get_value(
#             "Leave Ledger Entry",
#             {"employee": employee, "leave_type": leave_type},
#             "sum(leaves)"
#         ) or 0
#     except Exception:
#         return 0

# # def create_leave_ledger(employee, leave_type, date, status, attendance):
# #     employee_doc = frappe.get_cached_doc("Employee", employee)
# #     leave_type_doc = frappe.get_cached_doc("Leave Type", leave_type)

# #     if leave_type_doc.is_lwp:
# #         return

# #     leave_days = 0.5 if status == "Half Day" else 1
# #     allocation = get_leave_allocation(employee, leave_type, date)

# #     if not allocation:
# #         return

# #     if frappe.db.exists(
# #         "Leave Ledger Entry",
# #         {
# #             "employee": employee,
# #             "from_date": date,
# #             "transaction_type": "Leave Allocation",
# #             "transaction_name": allocation,
# #             "custom_attendance":attendance,
# #             "custom_is_penalty": 1
# #         }
# #     ):
# #         return

# #     doc = frappe.get_doc({
# #         "doctype": "Leave Ledger Entry",
# #         "employee": employee,
# #         "employee_name": employee_doc.employee_name,
# #         "company": employee_doc.company,
# #         "holiday_list": employee_doc.holiday_list,
# #         "leave_type": leave_type,
# #         "posting_date": date,
# #         "from_date": date,
# #         "to_date": date,
# #         "leaves": -leave_days,
# #         "is_lwp": 0,
# #         "custom_is_penalty": 1,
# #         "custom_attendance": attendance,
# #         "transaction_type": "Leave Allocation",
# #         "transaction_name": allocation
# #     })

# #     doc.insert(ignore_permissions=True)
# #     doc.submit()
# def create_leave_ledger(
#     employee,
#     leave_type,
#     date,
#     status,
#     attendance,
#     leave_days=None,
#     is_lwp=0
# ):
#     employee_doc = frappe.get_cached_doc("Employee", employee)
#     leave_type_doc = frappe.get_cached_doc("Leave Type", leave_type)

#     if leave_days is None:
#         leave_days = 0.5 if status == "Half Day" else 1

#     allocation = None
#     if not leave_type_doc.is_lwp:
#         allocation = get_leave_allocation(employee, leave_type, date)
#         if not allocation:
#             return

#     t_date = getdate(date)
#     if t_date.month >= 4:
#         to_date = getdate(f"{t_date.year + 1}-03-31")
#     else:
#         to_date = getdate(f"{t_date.year}-03-31")
    
    
#     correct_holiday_list = get_current_holiday_list(employee, date) or None
    
#     doc = frappe.get_doc({
#         "doctype": "Leave Ledger Entry",
#         "employee": employee,
#         "employee_name": employee_doc.employee_name,
#         "company": employee_doc.company,
#         "holiday_list": correct_holiday_list if correct_holiday_list else employee_doc.holiday_list,
#         "leave_type": leave_type,
#         "posting_date": date,
#         "from_date": date,
#         "to_date": to_date,
#         "leaves": -leave_days,
#         "is_lwp": 1 if leave_type_doc.is_lwp or is_lwp else 0,
#         "custom_is_penalty": 1,
#         "custom_attendance": attendance,
#         "transaction_type": "Leave Allocation" if allocation else "Leave Application",
#         "transaction_name": allocation
#     })

#     doc.insert(ignore_permissions=True)
#     doc.submit()

# JAMMU_BRANCH = "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu"
# SRINAGAR_BRANCH = "Jammu and Kashmir Milk Producers Co-operative Ltd Srinagar"


# # =========================================================
# # SHIFT HELPERS
# # =========================================================

# # def get_required_hours_by_date(employee, date):
# #     date = getdate(date)

# #     emp = frappe.db.get_value(
# #         "Employee",
# #         employee,
# #         ["branch", "gender", "custom_attendance_source"],
# #         as_dict=True
# #     )

# #     if (
# #         emp.branch == JAMMU_BRANCH
# #         and emp.gender == "Female"
# #         and emp.custom_attendance_source == "Field"
# #         and date.month in (12, 1)
# #     ):
# #         return 7

# #     if emp.branch == SRINAGAR_BRANCH:
# #         if 4 <= date.month <= 9:
# #             return 8
# #         return 7

# #     return 8
# JAMMU_BRANCH = "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu"
# SRINAGAR_BRANCH = "Jammu and Kashmir Milk Producers Co-operative Ltd Cheshmashahi Srinagar"
# DEC_JAN = (12, 1)

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
#         and date.month in DEC_JAN
#     ):
#         return 7

#     if emp.branch == JAMMU_BRANCH:
#         return 8

#     if emp.branch == SRINAGAR_BRANCH:
#         if 4 <= date.month <= 9: 
#             return 8
#         return 7

#     return 8



# # def get_employee_shift(employee, date):
# #     date = getdate(date)

# #     assigned_shift = frappe.db.get_value(
# #         "Shift Assignment",
# #         {
# #             "employee": employee,
# #             "start_date": ("<=", date),
# #             "end_date": (">=", date),
# #             "status": "Active"
# #         },
# #         "shift_type"
# #     )

# #     if assigned_shift:
# #         return assigned_shift

# #     default_shift = frappe.db.get_value(
# #         "Employee", employee, "default_shift"
# #     )

# #     if not default_shift:
# #         return None

# #     shift_type = frappe.db.get_value(
# #         "Shift Type", default_shift, "custom_shift_type"
# #     )
    

# #     if not shift_type:
# #         return default_shift

# #     required_hours = get_required_hours_by_date(employee, date)

# #     branch = frappe.db.get_value("Employee", employee, "branch")

# #     shift = frappe.db.get_value(
# #         "Shift Type",
# #         {
# #             "custom_branch": branch,
# #             "custom_shift_type": shift_type,   # General / Morning / Day / Night / 24H
# #             "custom_hours": f"{required_hours}hours"
# #         },
# #         "name"
# #     )

# #     if shift:
# #         return shift

# #     return default_shift

# def get_employee_shift(employee, date):
#     date = getdate(date)
    
#     # assigned_shift = frappe.db.get_value(
#     #     "Shift Assignment",
#     #     {
#     #         "employee": employee,
#     #         "start_date": ("<=", date),
#     #         "end_date": (">=", date),
#     #         "status": "Active"
#     #     },
#     #     "shift_type"
#     # )

#     shift_assignment = frappe.db.get_list(
#         "Shift Assignment",
#         filters={
#             "employee": employee,
#             "start_date": ["<=", date],
#             "status": "Active"
#         },
#         or_filters=[
#             {"end_date": [">=", date]},
#             {"end_date": ["is", "not set"]}
#         ],
#         fields=["shift_type"],
#         # order_by="start_date desc",
#         limit=1
#     )

#     assigned_shift = shift_assignment[0].shift_type if shift_assignment else None

#     if assigned_shift:
#         return assigned_shift

#     emp = frappe.db.get_value(
#         "Employee",
#         employee,
#         [
#             "default_shift",
#             "branch",
#             "custom_attendance_source"
#         ],
#         as_dict=True
#     )

#     if not emp or not emp.default_shift:
#         return None

#     # shift_type = frappe.db.get_value(
#     #     "Shift Type",
#     #     emp.default_shift,
#     #     "custom_shift_type"
#     # )
#     # if not shift_type:
#     #     return emp.default_shift
    
#     # shift = frappe.db.get_value(
#     #     "Shift Type",
#     #     {
#     #         "custom_branch": emp.branch,
#     #         "custom_shift_type": shift_type,
#     #         "custom_attendance_source": emp.custom_attendance_source, 
#     #         "custom_hours": f"{required_hours}hours"                 
#     #     },
#     #     "name"
#     # )
    
#     # 6️⃣ Return matched shift or fallback
#     # return shift or emp.default_shift
#     return emp.default_shift
# def get_shift_end_datetime(shift_type, date):
#     end_time = frappe.db.get_value(
#         "Shift Type", shift_type, "end_time"
#     )
#     if not end_time:
#         return None

#     return datetime.combine(date, end_time)



# def log_attendance_error(employee, date, step, exc=None):
#     message = f"""
# Employee : {employee}
# Date     : {date}
# Step     : {step}
# """

#     if exc:
#         message += "\n\n" + frappe.get_traceback()

#     frappe.log_error(
#         title=f"Auto Attendance Error : {date}",
#         message=message
#     )





# # =========================================================
# # ENTRY POINT (Scheduler – Daily) for Auto Comp-Off Creation
# # =========================================================

# def process_comp_off_by_branch(comp_off_date):
#     if not comp_off_date:
#         frappe.throw("Attendance Date required")
    
#     emp = get_employee_from_user()
#     if not emp:
#         frappe.throw("No Employee linked with this user")
#     branch = emp.branch
    
#     process_comp_off_scheduler(comp_off_date=comp_off_date, branch=branch)    
    
#     return {
#         "success": True,
#         "message": f"CompOff Generated processed for branch: {branch}"
#     }

# @frappe.whitelist()
# def process_comp_off_scheduler(comp_off_date=None, branch=None):
#     """
#     Runs daily.
#     Checks only comp_off_date.
#     """

#     if not comp_off_date:
#         comp_off_date = add_days(getdate(), -1)
#     else:
#         comp_off_date = getdate(comp_off_date)

#     frappe.log_error("start_process_comp_off_scheduler", f"Scheduler Started FOR Date: {comp_off_date}")
#     if branch:
#         requests = frappe.get_all(
#             "Off-Day Work Request",
#             filters={
#                 "workflow_state": "Approved",
#                 "date": comp_off_date,
#                 "docstatus": 1,
#                 "branch":branch,
#                 "comp_off_created": 0
#             },
#             fields=["name", "employee", "date"]
#         )
#     else:
#         requests = frappe.get_all(
#             "Off-Day Work Request",
#             filters={
#                 "workflow_state": "Approved",
#                 "date": comp_off_date,
#                 "docstatus": 1,
#                 "comp_off_created": 0
#             },
#             fields=["name", "employee", "date"]
#         )

#     frappe.log_error("comp_off_request_list", f"{requests}")
#     for req in requests:
        
#         try:
#             process_working_day(req)
        
#         except Exception:
#             frappe.log_error(
#                 frappe.get_traceback(),
#                 f"Comp-Off Scheduler Error - {req.name}"
#             )
#             # continue
#     frappe.db.commit()

# # =========================================================
# # PROCESS SINGLE REQUEST
# # =========================================================


# def process_working_day(req):
#     """
#     Main entry point per Off-Day Working Request
#     """

#     attendance = get_attendance(req["employee"], req["date"])
#     if not attendance:
#         frappe.log_error("start_process_comp_off_scheduler", f"Full day Attendance not found for employee: {req['date']} - {req['employee']}")
#         return
    
#     holiday = get_holiday_details(req["employee"], req["date"])
#     if(req["employee"] == "20082: Harshiya Gupta"):
#         frappe.log_error("compoff_holiday", f"{holiday}")
    
#     if not holiday:
#         frappe.log_error("start_process_comp_off_scheduler", f"Holiday details not found for employee: {req['date']} - {req['employee']}")
#         return

#     # WO OR Normal Holiday OR RH+WO
#     if holiday["is_wo"] or not holiday["is_rh"]:
#         if(req["employee"] == "20082: Harshiya Gupta"):
#             frappe.log_error("comp_off", "is wo")
#         allocation = create_comp_off(req["employee"], req["date"])

#         frappe.db.set_value(
#             "Off-Day Work Request",
#             req["name"],
#             {
#                 "attendance": attendance,
#                 "leave_allocation": allocation.get("name"),
#                 "comp_off_created": 1
#             }
#         )
#         try:
#             handle_workflow_notification(req["name"])
#         except Exception as e:
#             frappe.log_error("handle notification error", f"{frappe.get_traceback()}")    
#         return

#     # RH only
#     handle_rh_only(req, attendance, holiday)


# # =========================================================
# # ATTENDANCE CHECK
# # =========================================================


# def get_attendance(employee, date):
#     return frappe.db.get_value(
#         "Attendance",
#         {
#             "employee": employee,
#             "attendance_date": date,
#             "status": "Present",
#             "docstatus": 1
#         },
#         "name"
#     )


# # =========================================================
# # DAY TYPE IDENTIFICATION
# # =========================================================


# def get_holiday_details(employee, date):
#     holiday_list = frappe.db.get_value(
#         "Employee",
#         employee,
#         "holiday_list"
#     )
    
#     #* FOR SAFETY
#     correct_holiday_list = None
    
#     current_holiday_list = get_current_holiday_list(employee, date)
    
#     if current_holiday_list:
#         correct_holiday_list = current_holiday_list
#     else:
#         correct_holiday_list = holiday_list
    
#     if not correct_holiday_list:
#         return None

#     holiday = frappe.db.get_value(
#         "Holiday",
#         {
#             "parent": correct_holiday_list,
#             "holiday_date": date
#         },
#         [
#             "weekly_off",
#             "custom_is_restricted_holiday",
#             "custom_restricted_holiday_date"
#         ],
#         as_dict=True
#     )

#     if not holiday:
#         return None

#     return {
#         "is_wo": bool(holiday.weekly_off),
#         "is_rh": bool(holiday.custom_is_restricted_holiday),
#         "pair_date": holiday.custom_restricted_holiday_date
#     }


# # =========================================================
# # RH ONLY HANDLER
# # =========================================================


# def handle_rh_only(req, attendance, holiday):

#     pair_date = holiday.get("pair_date")
#     if not pair_date:
#         return

#     pair_holiday = get_holiday_details(req["employee"], pair_date)

#     # RH + WO (past or future) → immediate
#     if pair_holiday and pair_holiday["is_wo"]:
#         allocation = create_comp_off(req["employee"], req["date"])

#         # Update Request
#         frappe.db.set_value(
#             "Off-Day Work Request",
#             req["name"],
#             {
#                 "attendance": attendance,
#                 "leave_allocation": allocation.get("name"),
#                 "comp_off_created": 1
#             }
#         )
#         handle_workflow_notification(req["name"])
#         return

#     # Pair is future RH-only → skip
#     if pair_date > req["date"]:
#         return

#     # Pair is past RH-only → both must be present
#     pair_attendance = get_attendance(req["employee"], pair_date)
#     if pair_attendance:
#         allocation = create_comp_off(req["employee"], req["date"])

#         # Update Request
#         frappe.db.set_value(
#             "Off-Day Work Request",
#             req["name"],
#             {
#                 "attendance": attendance,
#                 "leave_allocation": allocation.get("name"),
#                 "comp_off_created": 1
#             }
#         )
#         handle_workflow_notification(req["name"])


# # =========================================================
# # Comp Off ALLOCATION CREATION
# # =========================================================


# def create_comp_off(employee, date):
#     """
#     Creates 1 Comp-Off Leave Allocation
#     Validity: 45 days
#     """

#     date = getdate(date)
#     frappe.log_error("create_comp_off", f"Creating Comp-Off for employee: {employee} on date: {date}")
    
#     al_created = already_created(employee, date)
    
#     if al_created:        
#         frappe.log_error("compoff_already_created", "already created")
#         return {"name":al_created}

#     leave_type = frappe.db.get_value(
#         "Leave Type",
#         {
#             "is_compensatory": 1
#         },
#         "custom_validity_days"
#     )
#     if(employee == "20082: Harshiya Gupta"):
#         frappe.log_error("comp_off leave type", f"{leave_type}")
    
#     validity_days = leave_type if leave_type else 45

#     if(employee == "20082: Harshiya Gupta"):
#         frappe.log_error("comp_off_validate_days", f"{validity_days}")
#     try:
#         allocation = frappe.get_doc({
#             "doctype": "Leave Allocation",
#             "employee": employee,
#             "leave_type": "Compensatory Off",
#             "from_date": date,
#             "to_date": add_days(date, validity_days),
#             "new_leaves_allocated": 1
#         })

#         allocation.insert(ignore_permissions=True)
#         allocation.submit()
#     except Exception as e:
#         frappe.log_error("compff_error", f"{frappe.get_traceback()}")

#     return allocation


# # =========================================================
# # DUPLICATE CHECK
# # =========================================================


# def already_created(employee, date):
#     return frappe.db.exists(
#         "Leave Allocation",
#         {
#             "employee": employee,
#             "leave_type": "Compensatory Off",
#             "from_date": date,
#             "docstatus": 1
#         },
#         "name",        
#     )


# def handle_workflow_notification(req_name):
#     try:
#         req = frappe.get_doc("Off-Day Work Request", req_name)
        
#         frappe.log_error("off_dar_rec", f"{req}")
#         recipients = []
#         user = frappe.db.get_value("Employee", req.employee, "user_id")
#         recipients.append(user)

#         notification_name = "Compensatory Off Created"

#         notification_doc = frappe.get_doc("Notification", notification_name)
#         if notification_doc:

#             # Call your custom notification function
#             send_notification_email(
#                 recipients=recipients,
#                 doctype=req.doctype,
#                 docname=req.name,
#                 notification_name=notification_name,
#                 send_link=False,
#                 fallback_subject=f"Off-Day Work Request for {req.date}",
#                 fallback_message=f"Off-Day Work Request for { req.date } is now in '{ req.workflow_state }' state.",
#                 enabled=notification_doc.enabled,
#                 send_system_notification=notification_doc.send_system_notification,
#                 channel=notification_doc.channel
#             )
#     except Exception as e:
#         frappe.log_error("error_handle_workflow_notification", frappe.get_traceback())


# # * METHOD TO ALLOCATE CASUAL LEAVE AND SICK LEAVE TO CONFIRMED EMPLOYEES
# # * THIS METHOD WILL RUN EVERY FIRST DAY OF THE FINANCIAL YEAR, I.E., 1ST APRIL
# @frappe.whitelist()
# def allocate_leaves_to_confirmed_employee(dt=None):
#     try:
#         frappe.log_error("Leave Allocation Job Started", "Allocating Casual Leave And Sick Leave")
#         if dt:
#             today_date = getdate(dt)
#         else:
#             today_date = getdate()
#         financial_year_start = getdate(f"{today_date.year}-04-01")
#         financial_year_end = getdate(f"{today_date.year + 1}-03-31")
        
#         if today_date == financial_year_start:
            
#             is_casual_leave_type = True if frappe.db.get_value("Leave Type", "Casual Leave", ["custom_leave_type"]) == "Casual Leave" else False
            
#             is_sick_leave_type = True if frappe.db.get_value("Leave Type", "Sick Leave", ["custom_leave_type"]) == "Sick Leave" else False
            
#             confirmed_employees = frappe.get_all("Employee", {"employment_type": "Confirmed", "status": "Active"}, ["name"])
            
#             if is_casual_leave_type or is_sick_leave_type:
#             # if is_casual_leave_type:
#                 for emp in confirmed_employees:
                    
#                     if is_casual_leave_type and not frappe.db.exists("Leave Allocation", {"employee": emp.name, "leave_type": "Casual Leave", "from_date":["<=", financial_year_start], "to_date": [">=", financial_year_end]}):
#                     # if is_casual_leave_type:
#                         try:                                                                                                                            
#                             cl_leave_allocation = frappe.get_doc({
#                                 "doctype": "Leave Allocation",
#                                 "employee": emp.name,
#                                 "leave_type": "Casual Leave",
#                                 "from_date": financial_year_start,
#                                 "to_date": financial_year_end,
#                                 "new_leaves_allocated": 12,
#                                 "custom_last_allocation_date": today_date
#                             })
#                             cl_leave_allocation.insert(ignore_permissions=True)
#                             cl_leave_allocation.submit()
#                         except Exception as e:
#                             frappe.log_error(f"error_allocate_casual_leaves_{emp.name}", frappe.get_traceback())
                            
                            
                    
#                     if is_sick_leave_type and not frappe.db.exists("Leave Allocation", {"employee": emp.name, "leave_type": "Sick Leave", "from_date":["<=", financial_year_start], "to_date": [">=", financial_year_end]}):
#                         try:
                            
#                             last_year_leave_balance = get_leave_balance_on(emp.name, "Sick Leave", getdate(f"{financial_year_start.year}-03-31"))
                            
#                             if last_year_leave_balance > flt(28, 2):
#                                 sl_opening_balance = flt(28,2)
#                                 extra_sl = flt(last_year_leave_balance - flt(28,2), 2)
#                             else:
#                                 sl_opening_balance = last_year_leave_balance
#                                 extra_sl = 0                                         
#                             sl_leave_allocation = frappe.get_doc({
#                                 "doctype": "Leave Allocation",
#                                 "employee": emp.name,
#                                 "leave_type": "Sick Leave",
#                                 "from_date": financial_year_start,
#                                 "to_date": financial_year_end,
#                                 "new_leaves_allocated": 7,
#                                 "custom_opening_balance": sl_opening_balance,
#                                 "custom_last_allocation_date": today_date,
#                                 "custom_extra_sl_carry_forwarded_to_pl": extra_sl
#                             })
#                             sl_leave_allocation.insert(ignore_permissions=True)
#                             sl_leave_allocation.submit()
                            
#                             if extra_sl > 0:
#                                 extra_sl_allocation = frappe.get_doc({
#                                     "doctype": "Leave Allocation",
#                                     "employee": emp.name,
#                                     "leave_type": "Privilege Leave",
#                                     "from_date": financial_year_start,
#                                     "to_date": financial_year_end,
#                                     "new_leaves_allocated": extra_sl,
#                                     "carry_forward": 1,
#                                     "custom_extra_sl_carry_forwarded_to_pl": extra_sl,
#                                     "custom_last_allocation_date": today_date
#                                 })
#                                 extra_sl_allocation.insert(ignore_permissions=True)
#                                 extra_sl_allocation.submit()
                            
                            
#                         except Exception as e:
#                             frappe.log_error(f"error_allocate_sick_leaves_{emp.name}", frappe.get_traceback())
                            
#                 frappe.db.commit()                                
#             frappe.log_error("Leave Allocation Job Completed", "Completed Allocating Casual Leave and Sick Leave")
#     except Exception as e:
#         frappe.log_error(f"error_allocate_leaves_main", frappe.get_traceback())

# # * METHOD TO ALLOCATE CASUAL LEAVE TO PROBATION AND CONTRACTUAL EMPLOYEES
# # * THIS METHOD WILL RUN EVERY FIRST DAY OF THE MONTH
# @frappe.whitelist()
# def allocate_cl_to_probation_and_contract_employees(dt=None):
#     try:
#         frappe.log_error("CL Allocation to Probation and Contractual Employees Job Started", "CL Allocation to Probation and Contractual Employees rty")
#         if dt:
#             today_date = getdate(dt)
#         else:
#             today_date = getdate()
            
#         month_start_date = getdate(f"{today_date.year}-{today_date.month}-01")
        
#         if today_date == month_start_date:
                
        
#             fy_start_date = getdate(f"{today_date.year - 1}-04-01") if today_date.month < 4 else getdate(f"{today_date.year}-04-01")
#             fy_end_date   = getdate(f"{today_date.year}-03-31") if today_date.month < 4 else getdate(f"{today_date.year + 1}-03-31")
#             # return f_year_end_date
            
#             cl_leave_type = "Casual Leave"
            
#             is_casual_leave = True if frappe.db.get_value("Leave Type", cl_leave_type, "custom_leave_type") == "Casual Leave" else False
            
#             if is_casual_leave:
            
#                 p_and_employees = frappe.db.get_all("Employee", {"employment_type": ["in", ["Probation", "Contractual"]], "status": "Active"},["name", "employment_type", "contract_end_date", "date_of_joining"])
                            
#                 for emp in p_and_employees:
#                     try:                        
#                         if emp.employment_type == "Contractual" and emp.contract_end_date and getdate(emp.contract_end_date) > month_start_date:
#                             to_date = min(getdate(emp.contract_end_date), fy_end_date)
#                         else:
#                             to_date = fy_end_date

#                         # from_date = max(fy_start_date, emp.date_of_joining)
#                         allocation_det = frappe.db.get_all("Leave Allocation", {"employee": emp.name, "leave_type": cl_leave_type, "docstatus": 1, "from_date": ["<=", today_date], "to_date": [">=", today_date]}, "name", order_by="from_date desc", limit_page_length=1)
                        
#                         allocation_name = allocation_det[0].name if allocation_det else None
                        
#                         if allocation_name:
#                             allocation = frappe.get_doc("Leave Allocation", allocation_name)
                        
                            
#                             last_cl_allocation_date = getdate(allocation.custom_last_allocation_date)
#                             if last_cl_allocation_date and (last_cl_allocation_date >= today_date or last_cl_allocation_date.month == today_date.month):
#                                 frappe.log_error(f"last_allocation_date: {last_cl_allocation_date}", f"Employee: {emp.name} {last_cl_allocation_date.month} {today_date.month} 123")
#                                 continue
                            
#                             new_allocation = flt(allocation.total_leaves_allocated) + flt(1)
                            
#                             if new_allocation != allocation.total_leaves_allocated:
#                                 allocation.db_set("total_leaves_allocated", new_allocation, update_modified=False)

#                                 date = today_date or frappe.flags.current_date or getdate()
#                                 custom_create_additional_leave_ledger_entry(allocation, 1, date, is_accrual=1)
                            
#                                 frappe.get_doc({
#                                     "doctype": "Leave Accrual",
#                                     "parent": allocation.name,
#                                     "parenttype": "Leave Allocation",
#                                     "parentfield": "custom_leave_accrual",
#                                     "from_date": month_start_date,
#                                     "to_date": to_date,
#                                     "leave_allocated": 1,
#                                 }).insert(ignore_permissions=True)

                                
#                                 allocation.db_set(
#                                     "custom_last_allocation_date",
#                                     today_date,
#                                     update_modified=False
#                                 )
#                             # allocation.new_leaves_allocated += 1
#                             # allocation.custom_last_allocation_date = today_date
#                             # allocation.save(ignore_permissions=True)
                        
#                         else:
#                             allocation = frappe.get_doc({
#                                 "doctype": "Leave Allocation",
#                                 "employee": emp.name,
#                                 "leave_type": cl_leave_type,
#                                 "from_date": month_start_date,
#                                 "to_date": to_date,
#                                 "new_leaves_allocated": 1,
#                                 "custom_last_allocation_date": today_date
#                             })
#                             allocation.insert(ignore_permissions=True)
#                             allocation.submit()
#                             frappe.get_doc({
#                                     "doctype": "Leave Accrual",
#                                     "parent": allocation.name,
#                                     "parenttype": "Leave Allocation",
#                                     "parentfield": "custom_leave_accrual",
#                                     "from_date": month_start_date,
#                                     "to_date": to_date,
#                                     "leave_allocated": 1,
#                             }).insert(ignore_permissions=True)
                            
#                     except Exception as e:
#                         frappe.log_error(f"error_allocate_cl_to_probation_and_contract_employees_{emp.name}", f"{frappe.get_traceback()} \n \n {month_start_date} {to_date}")
#                         continue
#                 frappe.db.commit()
#             frappe.log_error("CL Allocation to Probation and Contractual Employees Job Completed", "CL Allocated to Probation and Contractual Employees")
        
#     except Exception as e:
#         frappe.log_error(f"error_main_allocate_cl_to_probation_and_contract_employees", frappe.get_traceback())

# # * METHOD TO ALLOCATE SICK LEAVE TO PROBATION AND CONTRACTUAL EMPLOYEES
# # * THIS METHOD WILL RUN EVERY DAY
# @frappe.whitelist()
# def allocate_sl_to_probation_and_contract_employees(dt=None):
#     try:
#         if dt:
#             today_date = getdate(dt)
#         else:
#             today_date = getdate()
            
#         # today_date = getdate()
#         monthly_sl = flt(0.58)
#         frappe.log_error(f"monthly {monthly_sl}", f"{monthly_sl}")
        
#         sl_leave_type = "Sick Leave"

#         month_end_date = getdate(get_last_day(today_date))
#         month_start_date = getdate(get_first_day(today_date))
        
#         if today_date.month < 4:
#             current_fy_start = getdate(f"{today_date.year - 1}-04-01")
#             current_fy_end   = getdate(f"{today_date.year}-03-31")
            
#         else:
#             current_fy_start = getdate(f"{today_date.year}-04-01")
#             current_fy_end   = getdate(f"{today_date.year + 1}-03-31")
            
        
        
#         if today_date != month_end_date and today_date != current_fy_start:
#             return
#         new_financial_year = today_date == current_fy_start

#         if frappe.db.get_value("Leave Type", sl_leave_type, "custom_leave_type") != "Sick Leave":
#             return

#         employees = frappe.db.get_all(
#             "Employee",
#             {
#                 "employment_type": ["in", ["Probation", "Contractual"]],
#                 "status": "Active",
#             },
#             ["name", "employment_type", "date_of_joining", "contract_end_date"],
#         )

#         frappe.log_error("sl eligible employee", f"{employees}")
#         for emp in employees:
#             try:
#                 joining_date = getdate(emp.date_of_joining)

#                 is_new_emp = True if month_start_date <= joining_date <= month_end_date else False
                
#                 if emp.employment_type == "Contractual" and emp.contract_end_date:
#                     if today_date > getdate(emp.contract_end_date):
#                         continue

#                 effective_to_date = current_fy_end
#                 if emp.employment_type == "Contractual" and emp.contract_end_date:
#                     effective_to_date = min(getdate(emp.contract_end_date), current_fy_end)

#                 current_alloc = frappe.db.get_all(
#                     "Leave Allocation",
#                     {
#                         "employee": emp.name,
#                         "leave_type": sl_leave_type,
#                         "docstatus": 1,
#                         "from_date": ["<=", today_date],
#                         "to_date": [">=", today_date],
#                     },
#                     ["name", "custom_last_allocation_date"],
#                     order_by="from_date desc",
#                     limit_page_length=1,
#                 )

#                 last_alloc_date = None
#                 if current_alloc and current_alloc[0]:
#                     if not current_alloc[0].custom_last_allocation_date:
#                         last_alloc_date = getdate(add_to_date(month_start_date, days=-1))
#                     else:
#                         last_alloc_date = getdate(current_alloc[0].custom_last_allocation_date)
#                 else:
#                     last_alloc_date = joining_date if month_start_date <= joining_date <= month_end_date else month_start_date
                
#                 if emp.name == "20135: KARAN KUMAR":
#                         frappe.log_error(f"last_alloc{emp.name}", f"{last_alloc_date} - {joining_date} - {month_start_date} - {month_end_date}")
                            
#                 already_allocated_this_month = True if last_alloc_date and last_alloc_date.year == today_date.year and last_alloc_date.month == today_date.month and last_alloc_date != current_fy_start else False
                
#                 if emp.name == "001100: CL Test Eleven":
#                     frappe.log_error("Already_allocated", f"{already_allocated_this_month} - last alloc date {last_alloc_date} - today date {today_date} - current fy start {current_fy_start}")
#                 if not new_financial_year:
#                     if current_alloc and not already_allocated_this_month:
                        
#                         alloc_doc = frappe.get_doc("Leave Allocation", current_alloc[0].name)
#                         new_allocation = flt(alloc_doc.total_leaves_allocated) + flt(monthly_sl)
                            
#                         if new_allocation != alloc_doc.total_leaves_allocated:
#                                 alloc_doc.db_set("total_leaves_allocated", new_allocation, update_modified=False)
#                                 date = today_date or frappe.flags.current_date or getdate()
#                                 if emp.name == "001100: CL Test Eleven":
#                                     frappe.log_error("New Allocation", f"{date} New Allocation {monthly_sl}")
#                                 custom_create_additional_leave_ledger_entry(alloc_doc, monthly_sl, date, is_accrual=1)
                            
#                                 frappe.get_doc({
#                                     "doctype": "Leave Accrual",
#                                     "parent": alloc_doc.name,
#                                     "parenttype": "Leave Allocation",
#                                     "parentfield": "custom_leave_accrual",
#                                     "from_date": date,
#                                     "to_date": effective_to_date,
#                                     # "eligible_days": eligible_days,
#                                     "leave_allocated": monthly_sl,
#                                 }).insert(ignore_permissions=True)

                                
#                                 alloc_doc.db_set(
#                                     "custom_last_allocation_date",
#                                     today_date,
#                                     update_modified=False
#                                 )
                        
                        
                        
#                         # alloc_doc.new_leaves_allocated = flt(alloc_doc.new_leaves_allocated) + monthly_sl
#                         # alloc_doc.custom_last_allocation_date = today_date
#                         # alloc_doc.save(ignore_permissions=True)
#                     elif not current_alloc:
                        
#                         if is_new_emp:
#                             frappe.log_error("is_new_emp", f"{emp.name} is new employee")
#                             total_days = month_end_date.day
                                                        
#                             remaining_days = total_days - joining_date.day + 1
                            
#                             c_monthly_sl = flt((remaining_days / total_days) * monthly_sl, 2)
                                                    
#                         else:
#                             c_monthly_sl = monthly_sl
                        
                            
#                         new_alloc = frappe.get_doc({ 
#                             "doctype": "Leave Allocation",
#                             "employee": emp.name,
#                             "leave_type": sl_leave_type,
#                             "from_date": today_date,
#                             "to_date": effective_to_date,
#                             "new_leaves_allocated": c_monthly_sl,
#                             "custom_last_allocation_date": today_date,
                            
#                         })
#                         new_alloc.insert(ignore_permissions=True)
#                         new_alloc.submit()
                        
#                         frappe.get_doc({
#                                     "doctype": "Leave Accrual",
#                                     "parent": new_alloc.name,
#                                     "parenttype": "Leave Allocation",
#                                     "parentfield": "custom_leave_accrual",
#                                     "from_date": today_date,
#                                     "to_date": effective_to_date,
#                                     # "eligible_days": eligible_days,
#                                     "leave_allocated": monthly_sl,
#                                 }).insert(ignore_permissions=True)
                        
                        
#                 else:
#                     prev_fy_end = getdate(f"{today_date.year}-03-31")
#                     last_year_balance = get_leave_balance_on(
#                         emp.name,
#                         sl_leave_type,
#                         prev_fy_end,
#                     ) or 0
                    
#                     # prev_fy_alloc = frappe.db.get_all(
#                     #     "Leave Allocation",
#                     #     {
#                     #         "employee": emp.name,
#                     #         "leave_type": sl_leave_type,
#                     #         "docstatus": 1,
#                     #         "from_date": ["<=", prev_fy_end],
#                     #         "to_date": [">=", prev_fy_end],
#                     #     },
#                     #     ["custom_last_allocation_date"],
#                     #     order_by="from_date desc",
#                     #     limit_page_length=1,
#                     # )

#                     # if prev_fy_alloc and prev_fy_alloc[0].custom_last_allocation_date:
#                     #     last_alloc_date = getdate(prev_fy_alloc[0].custom_last_allocation_date)
#                     # else:
#                     #     last_alloc_date = joining_date
                
#                     # if date_diff(today_date, last_alloc_date) >= allocate_after_days:
#                     #     new_leaves = 1
#                     # else:

#                     fy_alloc = frappe.get_doc({
#                         "doctype": "Leave Allocation",
#                         "employee": emp.name,
#                         "leave_type": sl_leave_type,
#                         "from_date": current_fy_start,
#                         "to_date": effective_to_date,
#                         "custom_opening_balance": last_year_balance,
#                         "new_leaves_allocated": 0,
#                         "custom_last_allocation_date": current_fy_start,
#                     })
#                     fy_alloc.insert(ignore_permissions=True)
#                     fy_alloc.submit()

#             except Exception:
#                 frappe.log_error(
#                     f"error_allocate_sl_{emp.name}",
#                     frappe.get_traceback(),
#                 )
#                 continue

#         frappe.db.commit()
#         frappe.log_error(
#             "SL Allocation Job Completed",
#             f"Scheduler run completed on {today_date}",
#         )

#     except Exception:
#         frappe.log_error(
#             "error_allocate_sl_main",
#             frappe.get_traceback(),
#         )

    



# # * SCHEDULER METHOD TO SET CURRENT REPORTING MANAGER AND HOLIDAY LIST IN THE EMPLOYEE
# #* THIS WILL RUN EVERY DAY
# @frappe.whitelist()
# def set_approvers_in_employee(dt=None):
#     try:
#         if dt:
#             from_date = getdate(dt)
#         else:
#             from_date = getdate()
        
#         frappe.log_error("Set Approvers in Employee Job Started", "Set Approvers in Employee Job Started")
#         employees = frappe.db.get_all("Employee", {"status": "Active"}, ["name", "holiday_list"])
#         if employees:
#             for emp in employees:
#                 try:
                    
#                     emp_doc = frappe.get_doc("Employee", emp.name)
                    
#                     if emp_doc:
#                         if emp_doc.get("custom_reporting_manager"):
#                             current_rm = None
                            
                    

#                         for row in emp_doc.get("custom_reporting_manager"):
#                             if row.get("effective_from") and getdate(row.get("effective_from") <= getdate(today())):
#                                 current_rm = row.get("employee")

#                         if current_rm:
#                             if emp_doc.get("reports_to") != current_rm:
#                                 emp_doc.reports_to = current_rm
                    
                            
#                             current_rm_user = emp_doc.get("user_id") if frappe.db.get_value("User", emp_doc.get("user_id")) else None

#                             if current_rm_user:
#                                 if emp_doc.get("expense_approver") != current_rm_user:
#                                     emp_doc.expense_approver = current_rm_user
                                
#                                 if emp_doc.get("leave_approver") != current_rm_user:
#                                     emp_doc.leave_approver = current_rm_user
                                    
#                                 if emp_doc.get("shift_request_approver") != current_rm_user:
#                                     emp_doc.shift_request_approver = current_rm_user
                    
#                     emp_doc.save(ignore_permissions=True)          
#                     # current_emp_shift_approver = frappe.db.get_value("Employee", emp.name, "shift_request_approver") or None
#                     # current_emp_leave_approver = frappe.db.get_value("Employee", emp.name, "leave_approver") or None
#                     # current_emp_reports_to = frappe.db.get_value("Employee", emp.name, "reports_to") or None
                    
                    
#                     # current_holiday_list = get_current_holiday_list(emp.name, from_date)
#                     # frappe.log_error("Holiday List", f"{current_holiday_list} {emp.holiday_list}")
#                     # if current_holiday_list:
#                     #     if not emp.holiday_list:
#                     #         frappe.db.set_value("Employee", emp.name, "holiday_list", current_holiday_list)
                        
#                     #     elif emp.holiday_list != current_holiday_list:
#                     #         frappe.db.set_value("Employee", emp.name, "holiday_list", current_holiday_list)
                            

                    
                    
#                     # emp_rm = get_emp_reporting_manager(emp.name)
#                     # emp_rm_emp = frappe.db.get_value("Employee", {"user_id": emp_rm}, "name") if emp_rm else None
#                     # if not emp_rm_emp:
#                     #     frappe.log_error(f"Reporting Manager Employee Not Found for User ID: {emp_rm}", f"Employee: {emp.name}")
                    
#                     # if emp_rm:
#                     #     if current_emp_shift_approver != emp_rm:
#                     #         frappe.db.set_value("Employee", emp.name, "shift_request_approver", emp_rm)
#                     #     if current_emp_leave_approver != emp_rm:
#                     #         frappe.db.set_value("Employee", emp.name, "leave_approver", emp_rm)                        
#                     #     if current_emp_reports_to != emp_rm_emp:
#                     #         frappe.db.set_value("Employee", emp.name, "reports_to", emp_rm_emp)
                                                                                
#                 except Exception as e:
#                     frappe.log_error(f"error_set_approvers_in_employee_{emp.name}", frappe.get_traceback())
#                     continue
            
#             frappe.db.commit()
#         frappe.log_error("Set Approvers in Employee Job Completed", "Set Approvers in Employee Job Completed")
        
        
#     except Exception as e:        
#         frappe.log_error(
#             f"error_set_approvers_in_employee",
#             frappe.get_traceback(),
#         )




# def get_employees_by_branch(branch):
#     return frappe.get_all(
#         "Employee",
#         filters={
#             "status": "Active",
#             "branch": branch,
#         },
#         pluck="name",
#     )

# def process_employee_attendance(employee, att_date):
#     try:
#         shift_type = get_employee_shift(employee, att_date)

#         if not shift_type:
#             log_attendance_error(employee, att_date, "Shift not assigned")
#             return

#         shift = frappe.db.get_value(
#             "Shift Type",
#             shift_type,
#             [
#                 "start_time",
#                 "end_time",
#                 "late_entry_grace_period",
#                 "working_hours_threshold_for_half_day",
#                 "working_hours_threshold_for_absent",
#             ],
#             as_dict=True,
#         )

#         is_holiday = is_holiday_or_weekoff(employee, att_date)

#         logs = frappe.db.sql(
#             """
#             SELECT name, time
#             FROM `tabEmployee Checkin`
#             WHERE employee=%s
#             AND DATE(time)=%s
#             ORDER BY time ASC
#             """,
#             (employee, att_date),
#             as_dict=True,
#         )

#         if not logs:
#             if is_holiday:
#                 return

#             save_attendance_record(
#                 employee,
#                 att_date,
#                 shift_type,
#                 None,
#                 None,
#                 0,
#                 {"status": "Absent", "late_entry": 0},
#             )
#             return

#         if len(logs) == 1:
#             if is_holiday:
#                 return

#             save_attendance_record(
#                 employee,
#                 att_date,
#                 shift_type,
#                 logs[0]["time"],
#                 None,
#                 0,
#                 {"status": "Partially", "late_entry": 0},
#                 logs[0]["name"],
#                 logs[0]["name"],
#             )
#             return

#         in_time = normalize_to_minute(logs[0]["time"])
#         out_time = normalize_to_minute(logs[-1]["time"])

#         if in_time and out_time and out_time > in_time:
#             working_seconds = (out_time - in_time).total_seconds()
#             working_hours = working_seconds / 3600
#         else:
#             working_hours = 0

#         result = calculate_attendance_result(
#             employee,
#             att_date,
#             shift,
#             in_time,
#             out_time,
#             working_hours,
#             logs[0]["name"],
#             logs[-1]["name"],
#             skip_shift_time_rules=False,
#         )

#         save_attendance_record(
#             employee,
#             att_date,
#             shift_type,
#             in_time,
#             out_time,
#             working_hours,
#             result,
#             logs[0]["name"],
#             logs[-1]["name"],
#         )

#     except Exception as e:
#         log_attendance_error(employee, att_date, "Process Attendance Failed", e)

# def revert_penalty_leave(attendance_name):
#     try:
#         att = frappe.get_doc("Attendance", attendance_name)

#         if not att.custom_is_penalize:
#             return

#         leave_type = att.custom_penalty_leave_type
#         leave_count = att.custom_penalty_leave_count
#         attendance_date = att.attendance_date

#         frappe.db.delete(
#             "Leave Ledger Entry",
#             {
#                 "employee": att.employee,
#                 "leave_type": leave_type,
#                 "from_date": attendance_date,
#                 "custom_is_penalty": 1,              # ✅ recommended if you have this field
#                 "custom_attendance":att.name,
#             }
#         )

#         att.db_set({
#             "custom_penalty_leave_type": None,
#             "custom_penalty_leave_count": 0,
#             "custom_is_penalize": 0
#         })

#         frappe.db.commit()
#     except Exception as e:
#         frappe.log_error("error_revert_penalty_leave", frappe.get_traceback())

# def save_attendance_record(
#     employee,
#     date,
#     shift_type,
#     in_time,
#     out_time,
#     working_hours,
#     result,
#     first_checkin_id=None,
#     last_checkin_id=None,
# ):
#     employee_details = frappe.db.get_value(
#         "Employee",
#         employee,
#         ["employee_name", "department", "company", "branch"],
#         as_dict=True,
#     )

#     attendance_name = frappe.db.exists(
#         "Attendance",
#         {
#             "employee": employee,
#             "attendance_date": date,
#             "docstatus": ["!=", 2],
#         },
#     )

#     old_status = None
#     if attendance_name:
#         old_status = frappe.db.get_value("Attendance", attendance_name, "status")

#     values = {
#         "in_time": in_time,
#         "out_time": out_time,
#         "working_hours": working_hours,
#         "status": result["status"],
#         "late_entry": result["late_entry"],
#         "employee_name": employee_details.employee_name,
#         "department": employee_details.department,
#         "company": employee_details.company,
#         "custom_branch": employee_details.branch,
#         "shift": shift_type,
#     }


#     if attendance_name:
#         frappe.db.set_value(
#             "Attendance",
#             attendance_name,
#             values,
#             update_modified=False,
#         )

#         att_name = attendance_name


#     else:
#         att_name = frappe.generate_hash(length=12)

#         frappe.db.sql(
#             """
#             INSERT INTO `tabAttendance`
#             (name, employee, employee_name, department, company,
#              attendance_date, shift, in_time, out_time,
#              working_hours, status, late_entry, custom_branch,
#              docstatus, creation, modified, owner, modified_by)

#             VALUES (%s,%s,%s,%s,%s,
#                     %s,%s,%s,%s,
#                     %s,%s,%s,%s,
#                     1, NOW(), NOW(), %s, %s)
#             """,
#             (
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
#                 result["status"],
#                 result["late_entry"],
#                 employee_details.branch,
#                 frappe.session.user,
#                 frappe.session.user,
#             ),
#         )


#     if first_checkin_id:
#         frappe.db.set_value(
#             "Employee Checkin",
#             first_checkin_id,
#             "attendance",
#             att_name,
#             update_modified=False,
#         )

#     if last_checkin_id and last_checkin_id != first_checkin_id:
#         frappe.db.set_value(
#             "Employee Checkin",
#             last_checkin_id,
#             "attendance",
#             att_name,
#             update_modified=False,
#         )


#     if old_status in ("Absent", "Half Day") and result["status"] == "Present":
#         revert_penalty_leave(att_name)

#     return att_name



# def calculate_attendance_result(
#     employee,
#     date,
#     shift,
#     in_time,
#     out_time,
#     working_hours,
#     first_checkin_id=None,
#     last_checkin_id=None,
#     skip_shift_time_rules=False,
# ):

#     result = {
#         "status": "Absent",
#         "late_entry": 0,
#     }


#     if not out_time:
#         result["status"] = "Partially"
#         return result

#     half_day_hours = float(shift.working_hours_threshold_for_half_day or 8)
#     absent_hours = float(shift.working_hours_threshold_for_absent or 3)

#     if working_hours <= absent_hours:
#         result["status"] = "Absent"
#     elif working_hours < half_day_hours:
#         result["status"] = "Half Day"
#     else:
#         result["status"] = "Present"

#     if (
#         result["status"] != "Absent"
#         and not skip_shift_time_rules
#         and in_time
#         and shift.late_entry_grace_period
#     ):
#         shift_start = combine_datetime(date, shift.start_time)

#         latest_allowed = add_to_date(
#             shift_start,
#             minutes=int(shift.late_entry_grace_period),
#         )

#         if in_time > latest_allowed:
#             result["late_entry"] = 0.5
#             result["status"] = "Half Day"

#     return result


# def get_holiday_type(employee, date):

#     holiday_list = get_current_holiday_list(employee, date)

#     if not holiday_list:
#         holiday_list = frappe.db.get_value("Employee", employee, "holiday_list")

#     if not holiday_list:
#         return None

#     holiday = frappe.db.get_value(
#         "Holiday",
#         {
#             "parent": holiday_list,
#             "holiday_date": date
#         },
#         ["weekly_off", "custom_is_restricted_holiday"],
#         as_dict=True
#     )

#     if not holiday:
#         return None

#     if holiday.weekly_off:
#         return "Weekly Off"
#     elif holiday.custom_is_restricted_holiday:
#         return "Restricted Holiday"
#     else:
#         return "Holiday"


























#################-----------Updated CODE-------------################




import frappe
from frappe.utils import getdate, today,add_days,now_datetime,add_to_date, date_diff, get_last_day, get_first_day

from datetime import date,datetime
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

from frappe.utils import get_datetime
from datetime import datetime, time,timedelta
from frappe.utils import flt
import calendar




from jkmpcl_hr.py.utils import get_current_holiday_list, custom_create_additional_leave_ledger_entry, get_ceo_employees


# from jkmpcl_hr.py.utils import send_notification_email
from jkmpcl_hr.py.utils import create_shift_assignment_rec, send_notification_email, get_emp_reporting_manager

# @frappe.whitelist(allow_guest=True)
# def create_shift_assignments(dt=None):
#     frappe.log_error("start_create_shift_assignments", "Scheduler Started")
#     today_date = getdate(today()) if not dt else getdate(dt)
#     start_year = today_date.year if today_date.month >= 4 else today_date.year - 1
    
#     emp_filters = {"status": "Active"}
#     create_and_assign_shift_assignments_srinagar(today_date, start_year, emp_filters)
#     create_and_assign_shift_assignments_jammu(today_date, start_year, emp_filters)
#     frappe.log_error("end_create_shift_assignments", "Scheduler Ended")




# def create_and_assign_shift_assignments_srinagar(today_date, start_year, emp_filters):
#     frappe.log_error("start_create_and_assign_shift_assignments_srinagar", "Scheduler Started FOR Srinagar")
    
#     apr_start_date = getdate(f"{start_year}-04-01")
#     mar_end_date = getdate(f"{start_year+1}-03-31")
#     # mar_end_date = date(start_year + 1, 3, 31)
    
#     sep_end_sri  = getdate(f"{start_year}-09-30")
#     oct_start_sri = getdate(f"{start_year}-10-01")
    
#     # sep_end_sri  = date(start_year, 9, 30)
#     # oct_start_sri = date(start_year, 10, 1)

#     emp_filters["branch"] = "Jammu and Kashmir Milk Producers Co-operative Ltd Cheshmashahi Srinagar"
#     emp_list = frappe.db.get_list("Employee", filters=emp_filters, fields=["name", "default_shift", "custom_attendance_source"])
        
#     if not emp_list:
#         return
        
    
#     error_emp = []
#     ds_not_set_emp = []
    
#     for emp in emp_list:
#         try:
#             emp_id = emp.get("name")
#             default_shift = emp.get("default_shift")
            
#             eight_hours_sa_exists = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", apr_start_date], "end_date":[">=", sep_end_sri]}, limit=1)
#             seven_hours_sa_exists = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", oct_start_sri], "end_date":[">=", mar_end_date]}, limit=1)
            
#             emp_default_shift_details = frappe.db.get_values("Shift Type", default_shift, ["custom_shift_type", "custom_hours", "custom_branch"], as_dict=True)
            
#             if not emp_default_shift_details:
#                 ds_not_set_emp.append(emp_id)
#                 continue
            
#             if emp_default_shift_details[0].get("custom_hours") == "7hours":
#                 if emp.get("custom_attendance_source") == "Field" and emp_default_shift_details[0].get("custom_shift_type") == "General":
#                     seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
                    
#                     eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
                
#                 if emp.get("custom_attendance_source") == "Punch" and emp_default_shift_details[0].get("custom_shift_type") == "General":
#                     seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Punch"}, "name")
                    
#                     eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Punch"}, "name")
#                 else:
#                     seven_hours_shift_id = default_shift
#                     eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours",         "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
                            
#             elif emp_default_shift_details[0].get("custom_hours") == "8hours":
#                 if emp.get("custom_attendance_source") == "Field" and emp_default_shift_details[0].get("custom_shift_type") == "General":
#                     eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
#                     seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
                    
#                 if emp.get("custom_attendance_source") == "Punch" and emp_default_shift_details[0].get("custom_shift_type") == "General":
#                     eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Punch"}, "name")
#                     seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Punch"}, "name")
#                 else:                                
#                     eight_hours_shift_id = default_shift
#                     seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
            
#             if not eight_hours_sa_exists:
#                 create_shift_assignment_rec(emp_id, apr_start_date, sep_end_sri, eight_hours_shift_id)
            
#             if not seven_hours_sa_exists:
#                 create_shift_assignment_rec(emp_id, oct_start_sri, mar_end_date, seven_hours_shift_id)
                
                        
#             # return emp_default_shift_details
#             # if not eight_hours_sa_exists:
                
            
#         except Exception as e:
#             error_emp.append({emp_id: str(e)})
#             frappe.log_error(f"error_create_and_assign_shift_assignments_srinagar_{emp_id}", frappe.get_traceback())
#             continue
    
#     frappe.log_error("end_create_and_assign_shift_assignments_srinagar", f"Scheduler Ended FOR Srinagar\n ds_not_setupfor_this_emp: {ds_not_set_emp}")
    
    
    
# def create_and_assign_shift_assignments_jammu(today_date, start_year, emp_filters):
#     # apr_start_date = date(start_year, 4, 1)
#     # mar_end_date = date(start_year + 1, 3, 31)
#     frappe.log_error("start_create_and_assign_shift_assignments_jammu", "Scheduler Started FOR Jammu")
    
#     apr_start_date = getdate(f"{start_year}-04-01")
#     mar_end_date = getdate(f"{start_year+120137}-03-31")
    
#     # nov_end_jammu = date(start_year, 11, 30)
#     # dec_start_jammu = date(start_year, 12, 1)
#     # jan_end_jammu = date(start_year + 1, 1, 31)
    
#     nov_end_jammu = getdate(f"{start_year}-11-30")
#     dec_start_jammu = getdate(f"{start_year}-12-01")
#     jan_end_jammu = getdate(f"{start_year+1}-01-31")
#     feb_start_jammu = getdate(f"{start_year+1}-02-01")
    
#     emp_filters["branch"] = "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu"
#     emp_list = frappe.db.get_list("Employee", filters=emp_filters, fields=["name", "default_shift", "gender", "custom_attendance_source"])
    
#     if not emp_list:
#         return
    
#     error_emp = []
#     ds_not_set_emp = []
    
#     for emp in emp_list:
#         try:
#             emp_id = emp.get("name")
#             default_shift = emp.get("default_shift")
            
#             if not default_shift:
#                     ds_not_set_emp.append(emp_id)
#                     continue
#             emp_default_shift_details = frappe.db.get_values("Shift Type", default_shift, ["custom_shift_type", "custom_hours", "custom_branch"], as_dict=True)
            
#             if emp.get("gender") == "Female" and emp.get("custom_attendance_source") == "Field":
            
#                 eight_hours_sa_exists_first = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", apr_start_date], "end_date":[">=", nov_end_jammu]}, limit=1)
#                 seven_hours_sa_exists = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", dec_start_jammu], "end_date":[">=", jan_end_jammu]}, limit=1)
#                 eight_hours_sa_exists_second = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", feb_start_jammu], "end_date":[">=", mar_end_date]}, limit=1)
                
                
#                 if emp_default_shift_details[0].get("custom_hours") == "7hours":
                    
#                     if emp_default_shift_details[0].get("custom_shift_type") == "General":
                        
#                         seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
                        
#                         eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
#                     else:
#                         seven_hours_shift_id = default_shift
#                         eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
                                
#                 elif emp_default_shift_details[0].get("custom_hours") == "8hours":
#                     if emp_default_shift_details[0].get("custom_shift_type") == "General":
#                         eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
#                         seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
#                     else:
                    
#                         eight_hours_shift_id = default_shift
#                         seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
                
#                 if not eight_hours_sa_exists_first:
#                     create_shift_assignment_rec(emp_id, apr_start_date, nov_end_jammu, eight_hours_shift_id)
                
#                 if not seven_hours_sa_exists:
#                     create_shift_assignment_rec(emp_id, dec_start_jammu, jan_end_jammu, seven_hours_shift_id)
                    
#                 if not eight_hours_sa_exists_second:
#                     create_shift_assignment_rec(emp_id, feb_start_jammu, mar_end_date, eight_hours_shift_id)

            
#             else:
#                 sa_exists = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", apr_start_date], "end_date":[">=", mar_end_date]}, limit=1)
                    
#                 if emp_default_shift_details[0].get("custom_hours") == "7hours":
                    
#                     if emp.get("custom_attendance_source") == "Field" and emp_default_shift_details[0].get("custom_shift_type") == "General":
#                         eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
#                     else:
#                         eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
                                
#                 elif emp_default_shift_details[0].get("custom_hours") == "8hours":
#                     if emp.get("custom_attendance_source") == "Field" and emp_default_shift_details[0].get("custom_shift_type") == "General":
#                         eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch"), "custom_attendance_source": "Field"}, "name")
#                     else:                    
#                         eight_hours_shift_id = default_shift
                
#                 if not sa_exists:
#                     create_shift_assignment_rec(emp_id, apr_start_date, mar_end_date, eight_hours_shift_id)
                
#             # return emp_default_shift_details
#             # if not eight_hours_sa_exists_first:
        
#         except Exception as e:
#             error_emp.append({emp_id: str(e)})
#             frappe.log_error(f"error_create_and_assign_shift_assignments_jammu_{emp_id}", frappe.get_traceback())
#             continue
    
#     frappe.log_error("end_create_and_assign_shift_assignments_jammu", f"Scheduler Ended FOR Jammu \n ds_not_setupfor_this_emp: {ds_not_set_emp}")
    
    

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
    frappe.log_error("run_attendance_for_my_branch", f"Running attendance for branch: {branch} and date:{att_date}")
    run_daily_attendance(getdate(att_date), branch=branch)

    frappe.db.commit()

    return {
        "success": True,
        "message": f"Attendance processed for branch: {branch}"
    }

# def run_daily_attendance(att_date=None, only_for_jammu=False, branch=None):

#     frappe.log_error("start_run_daily_attendance", f"Scheduler Started FOR Date: {att_date}")

#     if not att_date:
#         att_date = add_days(getdate(), -1)
#     else:
#         att_date = getdate(att_date)
#     if only_for_jammu:
#         frappe.log_error("run_daily_attendance_only_for_jammu", f"Running attendance only for Jammu branch for date: {att_date}")
#         employees = frappe.get_all(
#             "Employee",
#             filters={
#                 "status": ["in", ["Active", "Suspended"]],
#                 "branch": "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu",
#             },
#             pluck="name",
#         )
#     else:
#         filters = {"status": ["in", ["Active", "Suspended"]]}

#         if branch:
#             filters["branch"] = branch
#         frappe.log_error("run_daily_attendance_filters", f"Filters applied: {filters}")
#         employees = frappe.get_all("Employee", filters=filters, pluck="name")
#         frappe.log_error("run_daily_attendance_emplist", f"Employees fetched: {len(employees)}")

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

#             # shift_start_time =  frappe.db.get_value(
#             #     "Shift Type", shift_type, "start_time"
#             # )
            
#             # shift_end_time =  frappe.db.get_value(
#             #     "Shift Type", shift_type, "end_time"
#             # )
            
#             # begin_checkin_in_minutes = frappe.db.get_value(
#             #     "Shift Type", shift_type, "begin_check_in_before_shift_start_time"
#             # )
            
#             # allow_checkout_in_minutes = frappe.db.get_value(
#             #     "Shift Type", shift_type, "allow_check_out_after_shift_end_time"
#             # )
            
            
#             # new_shift_start_time = add_to_date(get_datetime(f"{att_date} {shift_start_time}"), minutes=-begin_checkin_in_minutes)
#             # new_shift_end_time = add_to_date(get_datetime(f"{att_date} {shift_end_time}"), minutes=allow_checkout_in_minutes)
            
#             # frappe.log_error(f"shift_value_type{emp}", f" shift start time {shift_start_time} shift end time {shift_end_time}  new_start {new_shift_start_time} new_end {new_shift_end_time}")
            
            
#             is_holiday = is_holiday_or_weekoff(emp, att_date)
#             off_day_approved = has_approved_off_day_work(emp, att_date)

#             is_holiday_work = False

#             if shift_custom_type == "24 hours":

#                 first_in, last_out, first_checkin_id, last_checkin_id, working_hours, log_count = (
#                     get_24_hour_working_hours(emp, att_date, shift_type)
#                 )

#                 if log_count == 0:
#                     if is_holiday:
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
#                         is_holiday_work=False,
#                     )
#                     continue

#                 if is_holiday:
#                     is_holiday_work = True

#                 if log_count == 1:
#                     create_or_update_attendance(
#                         emp,
#                         att_date,
#                         None,
#                         None,
#                         0,
#                         first_checkin_id,
#                         last_checkin_id,
#                         skip_shift_time_rules=True,
#                         is_holiday_work=is_holiday_work,
#                     )
#                     continue

#                 create_or_update_attendance(
#                     emp,
#                     att_date,
#                     first_in,
#                     last_out,
#                     working_hours,
#                     first_checkin_id,
#                     last_checkin_id,
#                     skip_shift_time_rules=True,
#                     is_holiday_work=is_holiday_work,
#                 )
#                 continue

#             if shift_custom_type == "Night":
#                 # new_shift_end_time = add_to_date(get_datetime(f"{att_date} {shift_end_time}"), days=1, minutes=allow_checkout_in_minutes)
                
#                 in_time, out_time, first_id, last_id, working_hours, log_count = (
#                     get_night_shift_logs(emp, att_date)
#                 )

#                 if log_count == 0:
#                     if is_holiday:
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
#                         is_holiday_work=False,
#                     )
#                     continue

#                 if is_holiday:
#                     is_holiday_work = True

#                 if log_count == 1:
#                     create_or_update_attendance(
#                         emp,
#                         att_date,
#                         None,
#                         None,
#                         0,
#                         first_id,
#                         last_id,
#                         skip_shift_time_rules=True,
#                         is_holiday_work=is_holiday_work,
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
#                     is_holiday_work=is_holiday_work,
#                 )
#                 continue

            
#             previous_date = add_days(att_date, -1)
#             prev_shift = get_employee_shift(emp, previous_date)
            
            
            
#             logs = frappe.db.sql(
#                 """
#                 SELECT name, time
#                 FROM `tabEmployee Checkin`
#                 WHERE employee=%s
#                 AND DATE(time)=%s
#                 ORDER BY time ASC
#             """,
#                 (emp, att_date),
#                 as_dict=True,
#             )
#             # logs = frappe.db.sql(
#             #     """
#             #     SELECT name, time
#             #     FROM `tabEmployee Checkin`
#             #     WHERE employee = %s
#             #     AND time >= %s
#             #     AND time <= %s
#             #     ORDER BY time ASC
#             #     """,
#             #     (emp, new_shift_start_time, new_shift_end_time),
#             #     as_dict=True,
#             # )

#             logs = filter_close_checkins(logs, threshold_minutes=2)

#             if not logs:
#                 if is_holiday:
#                     continue

#                 create_or_update_attendance(
#                     emp,
#                     att_date,
#                     None,
#                     None,
#                     0,
#                     None,
#                     None,
#                     skip_shift_time_rules=False,
#                     is_holiday_work=False,
#                 )
#                 continue

#             if is_holiday:
#                 is_holiday_work = True

#             if len(logs) < 2:
#                 create_or_update_attendance(
#                     emp,
#                     att_date,
#                     None,
#                     None,
#                     0,
#                     logs[0]["name"],
#                     logs[-1]["name"],
#                     skip_shift_time_rules=False,
#                     is_holiday_work=is_holiday_work,
#                 )
#                 continue

#             in_time = normalize_to_minute(logs[0]["time"])
#             out_time = normalize_to_minute(logs[-1]["time"])

#             if in_time and out_time and out_time > in_time:
#                 working_seconds = (out_time - in_time).total_seconds()
#                 working_hours = working_seconds / 3600
#             else:
#                 working_hours = 0

#             if working_hours <= 0:
#                 create_or_update_attendance(
#                     emp,
#                     att_date,
#                     None,
#                     None,
#                     0,
#                     logs[0]["name"],
#                     logs[-1]["name"],
#                     skip_shift_time_rules=False,
#                     is_holiday_work=is_holiday_work,
#                 )
#                 continue

#             create_or_update_attendance(
#                 emp,
#                 att_date,
#                 in_time,
#                 out_time,
#                 working_hours,
#                 logs[0]["name"],
#                 logs[-1]["name"],
#                 skip_shift_time_rules=False,
#                 is_holiday_work=is_holiday_work,
#             )

#         except Exception as e:
#             log_attendance_error(emp, att_date, "Main Scheduler Failed", e)

#     frappe.db.commit()


# =====================================================
# HANDLE SUSPENSION LOG
# =====================================================
def handle_suspension_log(doc):

    if not doc.custom_suspended_from_date:
        return

    from_date = doc.custom_suspended_from_date
    to_date = doc.custom_suspended_to_date
    remark = doc.custom_suspended_remark

    # ---------------- CHILD TABLE ----------------
    existing_row = None

    for row in doc.custom_employee_suspension_history:
        if str(row.from_date) == str(from_date):
            existing_row = row
            break

    if existing_row:
        if to_date:
            existing_row.to_date = to_date
            existing_row.remark = remark
    else:
        doc.append("custom_employee_suspension_history", {
            "from_date": from_date,
            "to_date": to_date,
            "remark": remark
        })

    # ---------------- DB LOG ----------------
    existing_log = frappe.db.get_value(
        "Suspended Employee Log",
        {
            "employee": doc.name,
            "from_date": from_date
        },
        ["name", "to_date"],
        as_dict=True
    )

    if existing_log:

        if not existing_log.to_date and to_date:
            frappe.db.set_value(
                "Suspended Employee Log",
                existing_log.name,
                "to_date",
                to_date
            )

    #     elif existing_log.to_date:
    #         create_new_log(doc)

    # else:
    #     create_new_log(doc)



def update_employee_status():

    today_date = getdate(today())

    employees = frappe.get_all("Employee", fields=[
        "name",
        "status",
        "custom_suspended_from_date",
        "custom_suspended_to_date"
    ])

    for emp in employees:

        if not emp.custom_suspended_from_date:
            continue

        from_date = getdate(emp.custom_suspended_from_date)
        to_date = emp.custom_suspended_to_date and getdate(emp.custom_suspended_to_date)

        # -------------------------------
        # ✅ STATUS LOGIC (FINAL)
        # -------------------------------
        if today_date < from_date:
            new_status = "Active"

        else:
            # 🔥 MAIN RULE
            if not to_date:
                new_status = "Suspended"

            elif today_date <= to_date:
                new_status = "Suspended"

            else:
                new_status = "Active"

        # -------------------------------
        # ✅ UPDATE IF CHANGED
        # -------------------------------
        if emp.status != new_status:

            frappe.db.set_value("Employee", emp.name, "status", new_status)

            # create log when becomes suspended
            if new_status == "Suspended":
                emp_doc = frappe.get_doc("Employee", emp.name)
                handle_suspension_log(emp_doc)

    frappe.db.commit()


def run_daily_attendance(att_date=None, only_for_jammu=False, branch=None):
    update_employee_status()
    frappe.log_error("start_run_daily_attendance", f"Scheduler Started FOR Date: {att_date}")


    ceo_employees = get_ceo_employees()
    
    if not att_date:
        att_date = add_days(getdate(), -1)
    else:
        att_date = getdate(att_date)


    # if not regularize_attendance:
    # ==============================
    # Fetch Employees
    # ==============================
    
    
    
    if only_for_jammu:
        if ceo_employees:
            
            employees = frappe.get_all(
                "Employee",
                filters={
                    "status": ["in", ["Active", "Suspended"]],
                    "date_of_joining":["<=", att_date],
                    "branch": "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu",
                    "name": ["not in", ceo_employees]
                },
                pluck="name",
            )
        else:
            employees = frappe.get_all(
                "Employee",
                filters={
                    "status": ["in", ["Active", "Suspended"]],
                    "date_of_joining":["<=", att_date],
                    "branch": "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu",            
                },
                pluck="name",
            )
    else:
        filters = {
            "status": ["in", ["Active", "Suspended"]],
            "date_of_joining": ["<=", att_date]
        }        
        if branch:
            filters["branch"] = branch

        employees = frappe.get_all("Employee", filters=filters, pluck="name")

    # =========================================================
    # LOOP
    # =========================================================
    for emp in employees:
        try:
            # =====================================================
            # 🔥 STEP 1: SUSPENSION FIRST (HIGHEST PRIORITY)
            # =====================================================
            suspended = frappe.db.sql("""
                SELECT name FROM `tabSuspended Employee Log`
                WHERE employee=%s
                AND from_date <= %s
                AND (to_date IS NULL OR to_date >= %s)
                LIMIT 1
            """, (emp, att_date, att_date), as_dict=True)

            if suspended:

                # 🔴 CHECK EXISTING
                existing = frappe.db.exists("Attendance", {
                    "employee": emp,
                    "attendance_date": att_date,
                    "docstatus": ["!=", 2]
                })

                if existing:
                    att_name = existing

                    # FORCE UPDATE
                    frappe.db.set_value(
                        "Attendance",
                        att_name,
                        {
                            "status": "Suspended",
                            "working_hours": 0,
                            "in_time": None,
                            "out_time": None
                        },
                        update_modified=False
                    )

                else:
                    # CREATE DIRECTLY
                    emp_details = frappe.db.get_value(
                        "Employee",
                        emp,
                        ["employee_name", "department", "company", "branch"],
                        as_dict=True
                    )

                    att = frappe.get_doc({
                        "doctype": "Attendance",
                        "employee": emp,
                        "employee_name": emp_details.employee_name,
                        "department": emp_details.department,
                        "company": emp_details.company,
                        "attendance_date": att_date,
                        "status": "Suspended",
                        "custom_branch": emp_details.branch,
                        "custom_is_penalize": 0
                    })

                    att.insert(ignore_permissions=True)
                    att.submit()

                    att_name = att.name

                # =====================================================
                # 🔥 APPLY LEAVE (THIS CREATES LEDGER)
                # =====================================================
                revert_penalty_leave(att_name)

                deduct_leave_by_priority(
                    employee=emp,
                    date=att_date,
                    status="Suspended",
                    attendance=att_name,
                    force_lwp=True
                )

                # ❗ VERY IMPORTANT
                continue
            
            
            mark_attendance(emp, att_date)
            
            # if has_approved_leave(emp, att_date):
            #     continue

            # shift_type = get_employee_shift(emp, att_date)

            # if not shift_type:
            #     log_attendance_error(emp, att_date, "Shift not assigned")
            #     continue

            # shift_custom_type = frappe.db.get_value(
            #     "Shift Type", shift_type, "custom_shift_type"
            # )

            # is_holiday = is_holiday_or_weekoff(emp, att_date)
            # off_day_approved = has_approved_off_day_work(emp, att_date)
            # is_holiday_work = False

                # if existing:
                #     att_name = existing

                #     # FORCE UPDATE
                #     frappe.db.set_value(
                #         "Attendance",
                #         att_name,
                #         {
                #             "status": "Suspended",
                #             "working_hours": 0,
                #             "in_time": None,
                #             "out_time": None
                #         },
                #         update_modified=False
                #     )

                # else:
                #     # CREATE DIRECTLY
                #     emp_details = frappe.db.get_value(
                #         "Employee",
                #         emp,
                #         ["employee_name", "department", "company", "branch"],
                #         as_dict=True
                #     )

                #     att = frappe.get_doc({
                #         "doctype": "Attendance",
                #         "employee": emp,
                #         "employee_name": emp_details.employee_name,
                #         "department": emp_details.department,
                #         "company": emp_details.company,
                #         "attendance_date": att_date,
                #         "status": "Suspended",
                #         "custom_branch": emp_details.branch,
                #         "custom_is_penalize": 0
                #     })

                #     att.insert(ignore_permissions=True)
                #     att.submit()

                #     att_name = att.name

                # # =====================================================
                # # 🔥 APPLY LEAVE (THIS CREATES LEDGER)
                # # =====================================================
                # revert_penalty_leave(att_name)

                # deduct_leave_by_priority(
                #     employee=emp,
                #     date=att_date,
                #     status="Suspended",
                #     attendance=att_name,
                #     force_lwp=True
                # )

                # # ❗ VERY IMPORTANT
                # continue


            # # =====================================================
            # # 🔽 NORMAL FLOW
            # # =====================================================
            # if has_approved_leave(emp, att_date):
            #     continue

            # shift_type = get_employee_shift(emp, att_date)

            # if not shift_type:
            #     continue

            # shift_custom_type = frappe.db.get_value(
            #     "Shift Type", shift_type, "custom_shift_type"
            # )

            # is_holiday = is_holiday_or_weekoff(emp, att_date)
            # is_holiday_work = False

            # # =====================================================
            # # 24 HOURS
            # # =====================================================
            # if shift_custom_type == "24 hours":

            #     first_in, last_out, first_id, last_id, working_hours, log_count = (
            #         get_24_hour_working_hours(emp, att_date, shift_type)
            #     )

            #     if log_count == 0:
            #         if is_holiday:
            #             continue

            #         create_or_update_attendance(emp, att_date, None, None, 0)
            #         continue

            #     if is_holiday:
            #         is_holiday_work = True

            #     create_or_update_attendance(
            #         emp, att_date,
            #         first_in, last_out, working_hours,
            #         first_id, last_id,
            #         skip_shift_time_rules=True,
            #         is_holiday_work=is_holiday_work
            #     )
            #     continue

            # # =====================================================
            # # NIGHT SHIFT
            # # =====================================================
            # if shift_custom_type == "Night":

            #     in_time, out_time, first_id, last_id, working_hours, log_count = (
            #         get_night_shift_logs(emp, att_date)
            #     )

            #     if log_count == 0:
            #         if is_holiday:
            #             continue

            #         create_or_update_attendance(emp, att_date, None, None, 0)
            #         continue

            #     if is_holiday:
            #         is_holiday_work = True

            #     create_or_update_attendance(
            #         emp, att_date,
            #         in_time, out_time, working_hours,
            #         first_id, last_id,
            #         skip_shift_time_rules=True,
            #         is_holiday_work=is_holiday_work
            #     )
            #     continue

            # # =====================================================
            # # NORMAL SHIFT
            # # =====================================================
            # logs = frappe.db.sql("""
            #     SELECT name, time
            #     FROM `tabEmployee Checkin`
            #     WHERE employee=%s
            #     AND DATE(time)=%s
            #     ORDER BY time ASC
            # """, (emp, att_date), as_dict=True)

            # logs = filter_close_checkins(logs, threshold_minutes=2)

            # if not logs:
            #     if is_holiday:
            #         continue

            #     create_or_update_attendance(emp, att_date, None, None, 0)
            #     continue

            # if is_holiday:
            #     is_holiday_work = True

            # in_time = normalize_to_minute(logs[0]["time"])
            # out_time = normalize_to_minute(logs[-1]["time"])

            # working_hours = 0
            # if in_time and out_time and out_time > in_time:
            #     working_hours = (out_time - in_time).total_seconds() / 3600

            # create_or_update_attendance(
            #     emp, att_date,
            #     in_time, out_time, working_hours,
            #     logs[0]["name"], logs[-1]["name"],
            #     skip_shift_time_rules=False,
            #     is_holiday_work=is_holiday_work
            # )

        except Exception as e:
            log_attendance_error(emp, att_date, "Scheduler Failed", e)

    frappe.db.commit()


# =====================================================
# CHECK APPROVED TRAVEL REQUEST
# =====================================================
def has_approved_travel_request(employee, att_date):

    travel_exists = frappe.db.sql("""
        SELECT tr.name
        FROM `tabTravel Request` tr
        INNER JOIN `tabTravel Itinerary` ti
            ON ti.parent = tr.name
        WHERE tr.employee = %s
        AND tr.docstatus = 1
        AND DATE(%s) BETWEEN DATE(ti.departure_date)
        AND DATE(ti.arrival_date)
        LIMIT 1
    """, (employee, att_date), as_dict=True)

    return bool(travel_exists)


# =====================================================
# CHECK APPROVED TOUR REQUEST
# =====================================================
def has_approved_tour_request(employee, att_date):

    return frappe.db.exists(
        "Tour Request",
        {
            "employee": employee,
            "docstatus": 1,
            "workflow_state": "Approved by HR",
            "from_date": ["<=", att_date],
            "to_date": [">=", att_date]
        }
    )

def mark_attendance(emp, att_date):
    # =====================================================
    # TRAVEL REQUEST LOGIC
    # =====================================================
    if has_approved_travel_request(emp, att_date):

        existing_attendance = frappe.db.exists(
            "Attendance",
            {
                "employee": emp,
                "attendance_date": att_date,
                "docstatus": 1
            }
        )

        employee_details = frappe.db.get_value(
            "Employee",
            emp,
            ["employee_name", "department", "company", "branch"],
            as_dict=True
        )

        shift_type = get_employee_shift(emp, att_date)

        # =====================================================
        # UPDATE EXISTING ATTENDANCE
        # =====================================================
        if existing_attendance:

            # ---------------------------------------------
            # FIRST REMOVE PENALTY LEAVE
            # ---------------------------------------------
            revert_penalty_leave(existing_attendance)

            # ---------------------------------------------
            # UPDATE ATTENDANCE
            # ---------------------------------------------
            frappe.db.set_value(
                "Attendance",
                existing_attendance,
                {
                    "status": "Present",
                    "shift": shift_type,
                    "employee_name": employee_details.employee_name,
                    "department": employee_details.department,
                    "company": employee_details.company,
                    "custom_branch": employee_details.branch,
                    "custom_is_penalize": 0,
                    "custom_penalty_leave_count": "",
                    "custom_penalty_leave_type": "",
                    "custom_remark":"On Tour"
                },
                update_modified=False
            )
 
            frappe.db.commit()

            return existing_attendance

        # =====================================================
        # CREATE NEW ATTENDANCE
        # =====================================================
        else:

            att = frappe.get_doc({
                "doctype": "Attendance",
                "employee": emp,
                "employee_name": employee_details.employee_name,
                "department": employee_details.department,
                "company": employee_details.company,
                "attendance_date": att_date,
                "status": "Present",
                "shift": shift_type,
                "custom_branch": employee_details.branch,
                "custom_is_penalize": 0,
                "custom_penalty_leave_count": "",
                "custom_penalty_leave_type": "",
                "custom_remark":"On Tour"
            })

            att.insert(ignore_permissions=True)
            att.submit()

            frappe.db.commit()

            return att.name
    # Travel Request
    if has_approved_travel_request(emp, att_date):
        return

    # =====================================================
    # TOUR REQUEST LOGIC
    # =====================================================
    if has_approved_tour_request(emp, att_date):

        existing_attendance = frappe.db.exists(
            "Attendance",
            {
                "employee": emp,
                "attendance_date": att_date,
                "docstatus": 1
            }
        )

        employee_details = frappe.db.get_value(
            "Employee",
            emp,
            ["employee_name", "department", "company", "branch"],
            as_dict=True
        )

        shift_type = get_employee_shift(emp, att_date)

        # Update Existing Attendance
        if existing_attendance:

            revert_penalty_leave(existing_attendance)

            frappe.db.set_value(
                "Attendance",
                existing_attendance,
                {
                    "status": "Present",
                    "shift": shift_type,
                    "employee_name": employee_details.employee_name,
                    "department": employee_details.department,
                    "company": employee_details.company,
                    "custom_branch": employee_details.branch,
                    "custom_is_penalize": 0,
                    "custom_penalty_leave_count": "",
                    "custom_penalty_leave_type": "",
                    "custom_remark": "On Duty"
                },
                update_modified=False
            )

            frappe.db.commit()
            return existing_attendance

        # Create Attendance
        else:

            att = frappe.get_doc({
                "doctype": "Attendance",
                "employee": emp,
                "employee_name": employee_details.employee_name,
                "department": employee_details.department,
                "company": employee_details.company,
                "attendance_date": att_date,
                "status": "Present",
                "shift": shift_type,
                "custom_branch": employee_details.branch,
                "custom_is_penalize": 0,
                "custom_penalty_leave_count": "",
                "custom_penalty_leave_type": "",
                "custom_remark": "On Duty"
            })

            att.insert(ignore_permissions=True)
            att.submit()

            frappe.db.commit()
            return att.name
    
    if has_approved_leave(emp, att_date):
                return
    
    # ------- Sandwich Rule start-----------
    if apply_sandwich_rule(emp,att_date):
        return
    # ------- Sandwich Rule End-----------

    shift_type = get_employee_shift(emp, att_date)

    if not shift_type:
        log_attendance_error(emp, att_date, "Shift not assigned")
        return

    shift_custom_type = frappe.db.get_value(
        "Shift Type", shift_type, "custom_shift_type"
    )

    # is_holiday = is_holiday_or_weekoff(emp, att_date)
    # off_day_approved = has_approved_off_day_work(emp, att_date)
    # is_holiday_work = False
    
    # ==========================================================
    # ✅ HOLIDAY + OFF DAY LOGIC (FIXED)
    # ==========================================================
    holiday_type = get_holiday_type(emp, att_date)

    off_day_approved = has_approved_off_day_work(emp, att_date)

    frappe.log_error(
        "DEBUG OFF DAY",
        f"Emp: {emp}, Date: {att_date}, Holiday: {holiday_type}, OffDayApproved: {off_day_approved}"
    )

    if holiday_type:
        if off_day_approved:
            is_holiday_work = True
        else:
            is_holiday_work = False
    else:
        is_holiday_work = False

    # ==========================================================
    # 24 HOURS SHIFT
    # ==========================================================
    # if shift_custom_type == "24 hours":

    #     first_in, last_out, first_checkin_id, last_checkin_id, working_hours, log_count = (
    #         get_24_hour_working_hours(emp, att_date, shift_type)
    #     )

    #     if log_count == 0:
    #         if is_holiday:
    #             return

    #         create_or_update_attendance(
    #             emp, att_date, None, None, 0,
    #             None, None,
    #             skip_shift_time_rules=True,
    #             is_holiday_work=False,
    #         )
    #         return

    #     if is_holiday:
    #         is_holiday_work = True

    #     if log_count == 1:
    #         create_or_update_attendance(
    #             emp, att_date, None, None, 0,
    #             fNow in your mark_attendance() function add this:irst_checkin_id, last_checkin_id,
    #             skip_shift_time_rules=True,
    #             is_holiday_work=is_holiday_work,
    #         )
    #         return

    #     create_or_update_attendance(
    #         emp, att_date,
    #         first_in, last_out, working_hours,
    #         first_checkin_id, last_checkin_id,
    #         skip_shift_time_rules=True,
    #         is_holiday_work=is_holiday_work,
    #     )
    #     return
    if shift_custom_type == "24 hours":

        first_in, last_out, first_checkin_id, last_checkin_id, working_hours, log_count = (
            get_24_hour_working_hours(emp, att_date, shift_type)
        )

        if log_count == 0:
            if holiday_type:
                create_or_update_attendance(
                    emp, att_date, None, None, 0,
                    None, None,
                    skip_shift_time_rules=True,
                    is_holiday_work=False,
                    off_day_approved=off_day_approved,
                    holiday_type=holiday_type
                )
                frappe.db.set_value(
                    "Attendance",
                    {"employee": emp, "attendance_date": att_date},
                    "status",
                    holiday_type
                )
                return

            create_or_update_attendance(
                emp, att_date, None, None, 0,
                None, None,
                skip_shift_time_rules=True,
                is_holiday_work=False,
                off_day_approved=off_day_approved,
                holiday_type=holiday_type
            )
            return

        if log_count == 1:
            create_or_update_attendance(
                emp, att_date, None, None, 0,
                first_checkin_id, last_checkin_id,
                skip_shift_time_rules=True,
                is_holiday_work=is_holiday_work,
                off_day_approved=off_day_approved,
                holiday_type=holiday_type
            )
            return

        create_or_update_attendance(
            emp, att_date,
            first_in, last_out, working_hours,
            first_checkin_id, last_checkin_id,
            skip_shift_time_rules=True,
            is_holiday_work=is_holiday_work,
            off_day_approved=off_day_approved,
            holiday_type=holiday_type
        )
        return
    # ==========================================================
    # NIGHT SHIFT
    # ==========================================================
    # if shift_custom_type == "Night":

    #     in_time, out_time, first_id, last_id, working_hours, log_count = (
    #         get_night_shift_logs(emp, att_date)
    #     )

    #     if log_count == 0:
    #         if is_holiday:
    #             return

    #         create_or_update_attendance(
    #             emp, att_date, None, None, 0,
    #             None, None,
    #             skip_shift_time_rules=True,
    #             is_holiday_work=False,
    #         )
    #         return

    #     if is_holiday:
    #         is_holiday_work = True

    #     if log_count == 1:
    #         create_or_update_attendance(
    #             emp, att_date, None, None, 0,
    #             first_id, last_id,
    #             skip_shift_time_rules=True,
    #             is_holiday_work=is_holiday_work,
    #         )
    #         return

    #     create_or_update_attendance(
    #         emp, att_date,
    #         in_time, out_time, working_hours,
    #         first_id, last_id,
    #         skip_shift_time_rules=True,
    #         is_holiday_work=is_holiday_work,
    #     )
    #     return
    
    if shift_custom_type == "Night":

        in_time, out_time, first_id, last_id, working_hours, log_count = (
            get_night_shift_logs(emp, att_date)
        )

        if log_count == 0:
            if holiday_type:
                create_or_update_attendance(
                    emp, att_date, None, None, 0,
                    None, None,
                    skip_shift_time_rules=True,
                    is_holiday_work=False,
                    off_day_approved=off_day_approved,
                    holiday_type=holiday_type
                )
                frappe.db.set_value(
                    "Attendance",
                    {"employee": emp, "attendance_date": att_date},
                    "status",
                    holiday_type
                )
                return

            create_or_update_attendance(
                emp, att_date, None, None, 0,
                None, None,
                skip_shift_time_rules=True,
                is_holiday_work=False,
                off_day_approved=off_day_approved,
                holiday_type=holiday_type
            )
            return

        if log_count == 1:
            create_or_update_attendance(
                emp, att_date, None, None, 0,
                first_id, last_id,
                skip_shift_time_rules=True,
                is_holiday_work=is_holiday_work,
                off_day_approved=off_day_approved,
                holiday_type=holiday_type
            )
            return

        create_or_update_attendance(
            emp, att_date,
            in_time, out_time, working_hours,
            first_id, last_id,
            skip_shift_time_rules=True,
            is_holiday_work=is_holiday_work,
            off_day_approved=off_day_approved,
            holiday_type=holiday_type
        )
        return

    # ==========================================================
    # NORMAL SHIFT LOGIC
    # ==========================================================

    # logs = frappe.db.sql(
    #     """
    #     SELECT name, time
    #     FROM `tabEmployee Checkin`
    #     WHERE employee=%s
    #     AND DATE(time)=%s
    #     ORDER BY time ASC
    #     """,
    #     (emp, att_date),
    #     as_dict=True,
    # )

    # # ----------------------------------------------------------
    # # NEW LOGIC:
    # # If previous day was Night shift,
    # # ignore logs before previous OUT time
    # # ----------------------------------------------------------
    # previous_date = add_days(att_date, -1)
    # prev_shift = get_employee_shift(emp, previous_date)

    # if prev_shift:
    #     prev_shift_type = frappe.db.get_value(
    #         "Shift Type", prev_shift, "custom_shift_type"
    #     )

    #     if prev_shift_type == "Night":
            
    #         prev_att = frappe.db.get_value(
    #             "Attendance",
    #             {
    #                 "employee": emp,
    #                 "attendance_date": previous_date,
    #                 "docstatus": 1
    #             },
    #             ["out_time"],
    #             as_dict=True
    #         )

    #         # if prev_att and prev_att.out_time:
    #         #     logs = [
    #         #         log for log in logs
    #         #         if normalize_to_minute(log["time"]) > normalize_to_minute(prev_att.out_time) and normalize_to_minute(log["time"]) != normalize_to_minute(prev_att.out_time)
    #         #     ]
            
            
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

    # Night shift spillover fix
    previous_date = add_days(att_date, -1)
    prev_shift = get_employee_shift(emp, previous_date)

    if prev_shift:
        prev_shift_type = frappe.db.get_value(
            "Shift Type", prev_shift, "custom_shift_type"
        )

        if prev_shift_type == "Night":
            prev_att = frappe.db.get_value(
                "Attendance",
                {
                    "employee": emp,
                    "attendance_date": previous_date,
                    "docstatus": 1
                },
                ["out_time"],
                as_dict=True
            )

            if prev_att and prev_att.out_time:
                logs = [
                    log for log in logs
                    if normalize_to_minute(log["time"]) > normalize_to_minute(prev_att.out_time)
                ]

    logs = filter_close_checkins(logs, threshold_minutes=2)
    # # ----------------------------------------------------------

    # logs = filter_close_checkins(logs, threshold_minutes=2)

    # ==========================================================
    # NO LOGS CASE
    # ==========================================================
    if not logs:

        if holiday_type and not off_day_approved:
            att_id = create_or_update_attendance(
                emp,
                att_date,
                None,
                None,
                0,
                None,
                None,
                skip_shift_time_rules=True,
                is_holiday_work=False,
                off_day_approved=off_day_approved,
                holiday_type=holiday_type
            )

            frappe.db.set_value(
                "Attendance",
                att_id,
                "status",
                holiday_type
            )
            return

        create_or_update_attendance(
            emp, att_date,
            None, None, 0,
            None, None,
            skip_shift_time_rules=False,
            is_holiday_work=False,
        )
        return

    # holiday_type = get_holiday_type(emp, att_date)
    # if holiday_type:
    #     off_day_approved = has_approved_off_day_work(emp, att_date)

    #     if off_day_approved:
    #         is_holiday_work = True
    #     else:
    #         is_holiday_work = False

    if len(logs) < 2:
        create_or_update_attendance(
            emp, att_date,
            None, None, 0,
            logs[0]["name"], logs[-1]["name"],
            skip_shift_time_rules=False,
            is_holiday_work=is_holiday_work,
        )
        return

    in_time = normalize_to_minute(logs[0]["time"])
    out_time = normalize_to_minute(logs[-1]["time"])

    if in_time and out_time and out_time > in_time:
        working_seconds = (out_time - in_time).total_seconds()
        working_hours = working_seconds / 3600
    else:
        working_hours = 0

    if working_hours <= 0:
        att_id = create_or_update_attendance(
            emp, att_date,
            None, None, 0,
            logs[0]["name"], logs[-1]["name"],
            skip_shift_time_rules=False,
            is_holiday_work=is_holiday_work,
        )
        return att_id

    att_id = create_or_update_attendance(
        emp, att_date,
        in_time, out_time, working_hours,
        logs[0]["name"], logs[-1]["name"],
        skip_shift_time_rules=False,
        is_holiday_work=is_holiday_work,
        off_day_approved=off_day_approved,
        holiday_type=holiday_type
    )
    return att_id




# def mark_attendance(emp, att_date):
    
#     frappe.log_error("Mark Attendance Called", f"employee {emp}, att_date {att_date}")
#     if has_approved_leave(emp, att_date):
#                 return

#     shift_type = get_employee_shift(emp, att_date)

#     if not shift_type:
#         log_attendance_error(emp, att_date, "Shift not assigned")
#         return

#     shift_custom_type = frappe.db.get_value(
#         "Shift Type", shift_type, "custom_shift_type"
#     )

#     is_holiday = is_holiday_or_weekoff(emp, att_date)
#     off_day_approved = has_approved_off_day_work(emp, att_date)
#     is_holiday_work = False

#     # ==========================================================
#     # 24 HOURS SHIFT
#     # ==========================================================
#     if shift_custom_type == "24 hours":

#         first_in, last_out, first_checkin_id, last_checkin_id, working_hours, log_count = (
#             get_24_hour_working_hours(emp, att_date, shift_type)
#         )

#         if log_count == 0:
#             if is_holiday:
#                 return

#             create_or_update_attendance(
#                 emp, att_date, None, None, 0,
#                 None, None,
#                 skip_shift_time_rules=True,
#                 is_holiday_work=False,
#             )
#             return

#         if is_holiday:
#             is_holiday_work = True

#         if log_count == 1:
#             create_or_update_attendance(
#                 emp, att_date, None, None, 0,
#                 first_checkin_id, last_checkin_id,
#                 skip_shift_time_rules=True,
#                 is_holiday_work=is_holiday_work,
#             )
#             return

#         create_or_update_attendance(
#             emp, att_date,
#             first_in, last_out, working_hours,
#             first_checkin_id, last_checkin_id,
#             skip_shift_time_rules=True,
#             is_holiday_work=is_holiday_work,
#         )
#         return

#     # ==========================================================
#     # NIGHT SHIFT
#     # ==========================================================
#     if shift_custom_type == "Night":

#         in_time, out_time, first_id, last_id, working_hours, log_count = (
#             get_night_shift_logs(emp, att_date)
#         )

#         if log_count == 0:
#             if is_holiday:
#                 return

#             create_or_update_attendance(
#                 emp, att_date, None, None, 0,
#                 None, None,
#                 skip_shift_time_rules=True,
#                 is_holiday_work=False,
#             )
#             return

#         if is_holiday:
#             is_holiday_work = True

#         if log_count == 1:
#             create_or_update_attendance(
#                 emp, att_date, None, None, 0,
#                 first_id, last_id,
#                 skip_shift_time_rules=True,
#                 is_holiday_work=is_holiday_work,
#             )
#             return

#         create_or_update_attendance(
#             emp, att_date,
#             in_time, out_time, working_hours,
#             first_id, last_id,
#             skip_shift_time_rules=True,
#             is_holiday_work=is_holiday_work,
#         )
#         return

#     # ==========================================================
#     # NORMAL SHIFT LOGIC
#     # ==========================================================

#     logs = frappe.db.sql(
#         """
#         SELECT name, time
#         FROM `tabEmployee Checkin`
#         WHERE employee=%s
#         AND DATE(time)=%s
#         ORDER BY time ASC
#         """,
#         (emp, att_date),
#         as_dict=True,
#     )

#     # ----------------------------------------------------------
#     # NEW LOGIC:
#     # If previous day was Night shift,
#     # ignore logs before previous OUT time
#     # ----------------------------------------------------------
#     previous_date = add_days(att_date, -1)
#     prev_shift = get_employee_shift(emp, previous_date)

#     if prev_shift:
#         prev_shift_type = frappe.db.get_value(
#             "Shift Type", prev_shift, "custom_shift_type"
#         )

#         if prev_shift_type == "Night":
#             frappe.log_error("Night Shift Previous Day", f"Employee: {emp}, Previous Date: {previous_date}, Previous Shift: {prev_shift}")
#             prev_att = frappe.db.get_value(
#                 "Attendance",
#                 {
#                     "employee": emp,
#                     "attendance_date": previous_date,
#                     "docstatus": 1
#                 },
#                 ["out_time"],
#                 as_dict=True
#             )
#             frappe.log_error("Previous Day Attendance", f"Employee: {emp}, Previous Date: {previous_date}, Previous Attendance: {prev_att} logs {logs}")
#             if prev_att and prev_att.out_time:
#                 logs = [
#                     log for log in logs
#                     if normalize_to_minute(log["time"]) > normalize_to_minute(prev_att.out_time) and normalize_to_minute(log["time"]) != normalize_to_minute(prev_att.out_time)
#                 ]
#             frappe.log_error("Filtered Logs After Night Shift Check", f"Employee: {emp}, Previous Date: {previous_date}, Logs: {logs}")
#     # ----------------------------------------------------------

#     logs = filter_close_checkins(logs, threshold_minutes=2)

#     if not logs:
#         if is_holiday:
#             return

#         create_or_update_attendance(
#             emp, att_date,
#             None, None, 0,
#             None, None,
#             skip_shift_time_rules=False,
#             is_holiday_work=False,
#         )
#         return

#     if is_holiday:
#         is_holiday_work = True

#     if len(logs) < 2:
#         create_or_update_attendance(
#             emp, att_date,
#             None, None, 0,
#             logs[0]["name"], logs[-1]["name"],
#             skip_shift_time_rules=False,
#             is_holiday_work=is_holiday_work,
#         )
#         return

#     in_time = normalize_to_minute(logs[0]["time"])
#     out_time = normalize_to_minute(logs[-1]["time"])

#     if in_time and out_time and out_time > in_time:
#         working_seconds = (out_time - in_time).total_seconds()
#         working_hours = working_seconds / 3600
#     else:
#         working_hours = 0

#     if working_hours <= 0:
#         att_id = create_or_update_attendance(
#             emp, att_date,
#             None, None, 0,
#             logs[0]["name"], logs[-1]["name"],
#             skip_shift_time_rules=False,
#             is_holiday_work=is_holiday_work,
#         )
#         return att_id

#     att_id = create_or_update_attendance(
#         emp, att_date,
#         in_time, out_time, working_hours,
#         logs[0]["name"], logs[-1]["name"],
#         skip_shift_time_rules=False,
#         is_holiday_work=is_holiday_work,
#     )
#     return att_id


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
        is_holiday_work=False,
        off_day_approved=False,
        holiday_type=None
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
                "early_exit_grace_period",
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
        early_exit = 0
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
        
        # holiday_type = get_holiday_type(employee, date)
 
        # # 🔥 If holiday/weekoff work → only hours matter
        # if holiday_type:

        #     # ❌ No approval → ALWAYS holiday
        #     if not off_day_approved:
        #         status = holiday_type

        #     # ✅ Approved → check hours
        #     else:
        #         if working_hours >= half_day_hours:
        #             status = "Present"
        #         else:
        #             status = holiday_type
 
        # else:
        #     if working_hours <= absent_hours:
        #         status = "Absent"
        #     elif working_hours < half_day_hours:
        #         status = "Half Day"
        #     else:
        #         status = "Present"
 
 
 
        # if is_half_day_leave:
        #     status = "Half Day"
        # if single_checkin and not is_half_day_leave:
        #     status = "Partially"


        # ✅ Use passed-in holiday_type if available, else fetch fresh
        if not holiday_type:
            holiday_type = get_holiday_type(employee, date)
 
        # ✅ Use passed-in off_day_approved if True, else re-check DB
        # (covers Attendance Request approval path where off_day_approved=True
        # is explicitly passed, as well as normal scheduler path)
        if not off_day_approved:
            off_day_approved = bool(frappe.db.exists(
                "Off-Day Work Request",
                {
                    "employee": employee,
                    "date": date,
                    "workflow_state": "Approved",
                }
            ))
 
        if holiday_type:
            if not off_day_approved:
                # No approved off-day request → always holiday status
                status = holiday_type
            else:
                # Has approval → Present only if full hours worked
                if working_hours >= half_day_hours:
                    status = "Present"
                else:
                    # Single checkin, partial hours, or no out-punch
                    # → still preserve holiday status, NOT Partially/Absent
                    status = holiday_type
        else:
            if working_hours <= absent_hours:
                status = "Absent"
            elif working_hours < half_day_hours:
                status = "Half Day"
            else:
                status = "Present"
 
        if is_half_day_leave:
            status = "Half Day"
 
        # ✅ Only override to Partially on NON-holiday dates
        # On holiday dates single checkin must never become Partially
        if single_checkin and not is_half_day_leave and not holiday_type:
            status = "Partially"

        #------------------------------------------
            
        if status != "Absent":
            if in_time and out_time and not skip_shift_time_rules and not is_holiday_work:
 
                shift_start = combine_datetime(date, shift.start_time)
                shift_end = combine_datetime(date, shift.end_time)
                
                allowed_late_minutes = shift.late_entry_grace_period
                allowed_early_exit_minutes = shift.early_exit_grace_period
                    
                if allowed_late_minutes and int(allowed_late_minutes) > 0:
 
                    latest_allowed_in = add_to_date(
                        shift_start,
                        minutes=int(allowed_late_minutes)
                    )
 
                    if in_time > latest_allowed_in and not is_half_day_leave:
                        late_entry = 1
                        status = "Half Day"
                
                
                if not late_entry and allowed_early_exit_minutes and int(allowed_early_exit_minutes) > 0:
                    
                    latest_allowed_out = add_to_date(
                        shift_end,
                        minutes=-int(allowed_early_exit_minutes)
                    )
                        
                    if out_time < latest_allowed_out and not is_half_day_leave:
                        early_exit = 1
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
                "shift": shift_type,
                "in_time": in_time,
                "out_time": out_time,
                "working_hours": working_hours,
                "status": status,
                "late_entry": late_entry,
                "early_exit": early_exit,
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
                working_hours, status, late_entry, early_exit, custom_branch,
                docstatus, creation, modified, owner, modified_by)
 
                VALUES (%s,%s,%s,%s,%s,
                        %s,%s,%s,%s, %s,
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
                early_exit,
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
                
                if no_checkin_found or single_checkin:
                    revert_penalty_leave(att_name)
                    deduct_leave_by_priority(employee, date, status, att_name, force_lwp=True)
                else:
                    revert_penalty_leave(att_name)
                    deduct_leave_by_priority(employee, date, status, att_name, force_lwp=False)
                # elif single_checkin:
                #     revert_penalty_leave(att_name)
                #     deduct_leave_by_priority(employee, date, status, att_name, force_lwp=True)
                # else:
                #     revert_penalty_leave(att_name)
                
            else:
                half_day_status = "Present"
                revert_penalty_leave(att_name)
 
            frappe.db.set_value(
                "Attendance",
                att_name,
                "half_day_status",
                half_day_status,
                update_modified=False
            )

        # Clear old penalty first if status changed
        # if old_status and old_status != "Present" and status =="Present":
            # revert_penalty_leave(att_name)
        if is_holiday_work:
            revert_penalty_leave(att_name)
        # Apply penalty only if checkin exists
                
        if not is_holiday_work and not holiday_type:
        
            if not is_half_day_leave:
                if status == "Partially":
                    revert_penalty_leave(att_name)
                    deduct_leave_by_priority(employee, date, status, att_name, force_lwp=True)
                
                elif status == "Suspended":
                    revert_penalty_leave(att_name)
                    deduct_leave_by_priority(employee, date, status, att_name, force_lwp=True)
                
                elif status == "Absent" and no_checkin_found:
                    revert_penalty_leave(att_name)                    
                    deduct_leave_by_priority(employee, date, status, att_name, force_lwp=True)
                elif status in ["Absent", "Half Day"]:
                    revert_penalty_leave(att_name)
                    
                    deduct_leave_by_priority(
                        employee,
                        date,
                        status,
                        att_name
                    )
                else:
                    revert_penalty_leave(att_name)
            
                
        #     if status in ["Absent", "Half Day", "Partially"]:
    
        #         if not is_half_day_leave and not no_checkin_found:
    
        #             deduct_leave_by_priority(
        #                 employee,
        #                 date,
        #                 status,
        #                 att_name
        #             )
        

        # if holiday_type and not is_holiday_work and status != "Present":
        #     frappe.db.set_value(
        #     "Attendance",
        #     att_name,
        #     "status",
        #     holiday_type,
        #     update_modified=False
        # )
        

        # ✅ Final belt-and-suspenders guard:
        # On any holiday date, if status did not resolve to Present,
        # force it back to the correct holiday type.
        # This catches any edge case (single checkin, zero hours, etc.)
        # regardless of the path that set status above.
        if holiday_type and status not in ("Present",):
            frappe.db.set_value(
                "Attendance",
                att_name,
                "status",
                holiday_type,
                update_modified=False
            )
        
        # if old_status in ("Absent", "Half Day","Partially") and status == "Present":
        #     revert_penalty_leave(att_name)
        return att_name
        
    except Exception as e:
        frappe.log_error("create_or_update attendance", frappe.get_traceback())
        log_attendance_error(
            employee,
            date,
            "Attendance Save Failed",
            e
        )


# * ------------------------------------------------------------------was using---------------------------------------------------------------------------------------
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
#         if employee == "001100: CL Test Eleven":
#                 frappe.log_error(f"mark attendance for {employee}", f"{date}  in time {in_time}  out time{out_time}")
#         no_checkin_found = not first_checkin_id and not last_checkin_id
#         frappe.log_error("Checkin Found or not", f"no checkin found {no_checkin_found}, first in {first_checkin_id}, last_check {last_checkin_id}")
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
#                 "early_exit_grace_period",
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
#         early_exit = 0
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
#                 shift_end = combine_datetime(date, shift.end_time)
                
#                 allowed_late_minutes = shift.late_entry_grace_period
#                 allowed_early_exit_minutes = shift.early_exit_grace_period
                
#                 if employee == "001100: CL Test Eleven":
#                     frappe.log_error(f"mark_attednance{employee}", f" allowed exit {allowed_early_exit_minutes}  allowed late minutes{allowed_late_minutes}")
                    
#                 if allowed_late_minutes and int(allowed_late_minutes) > 0:
 
#                     latest_allowed_in = add_to_date(
#                         shift_start,
#                         minutes=int(allowed_late_minutes)
#                     )
 
#                     if in_time > latest_allowed_in:
#                         late_entry = 1
#                         status = "Half Day"
                
                
#                 if not late_entry and allowed_early_exit_minutes and int(allowed_early_exit_minutes) > 0:
                    
#                     latest_allowed_out = add_to_date(
#                         shift_end,
#                         minutes=-int(allowed_early_exit_minutes)
#                     )
#                     if employee == "001100: CL Test Eleven":
#                         frappe.log_error(f"Early Exit {employee}", f" allowed exit{allowed_early_exit_minutes} allowed time {latest_allowed_out}  out time {out_time}  end time {shift_end}")
                        
#                     if out_time < latest_allowed_out:
#                         early_exit = 1
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
#             if employee == "001100: CL Test Eleven":
#                 frappe.log_error(f"Marking Attendance {employee}", f" early exit{early_exit}")
#             frappe.db.set_value(
#             "Attendance",
#             att_name,
#             {
#                 "shift": shift_type,
#                 "in_time": in_time,
#                 "out_time": out_time,
#                 "working_hours": working_hours,
#                 "status": status,
#                 "late_entry": late_entry,
#                 "early_exit": early_exit,
#                 "employee_name": employee_details.employee_name,
#                 "department": employee_details.department,
#                 "company": employee_details.company,
#                 "custom_branch": employee_details.branch,
#             },
#             update_modified=False
#         )
        
#         else:
#             frappe.log_error("Attendance not created", "assa")
#             att_name = frappe.generate_hash(length=12)
 
#             frappe.db.sql("""
#                 INSERT INTO `tabAttendance`
#                 (name, employee, employee_name, department, company,
#                 attendance_date, shift, in_time, out_time,
#                 working_hours, status, late_entry, early_exit, custom_branch,
#                 docstatus, creation, modified, owner, modified_by)
 
#                 VALUES (%s,%s,%s,%s,%s,
#                         %s,%s,%s,%s, %s,
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
#                 early_exit,
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
#         if is_holiday_work:
#             revert_penalty_leave(att_name)
#         # Apply penalty only if checkin exists
        
#         frappe.log_error("is holiday work",f"\n\n is holiday work {is_holiday_work} status {status}\n\n")
#         if not is_holiday_work:
#             if employee == "001100: CL Test Eleven":
#                 frappe.log_error("not holiday work", f"\n\n is not holiday work  {is_holiday_work}\n\n")
#             if status in ["Absent", "Half Day", "Partially"]:
#                 frappe.log_error("Status", f"\n\n  status {status}is in {['Absent', 'Half Day', 'Partially']}\n\n")
#                 frappe.log_error("checkin found", f"checkin found or not {no_checkin_found}")
#                 if not is_half_day_leave and not no_checkin_found:
#                     frappe.log_error("deducting Leave",f"\n\n deducting LEAVE by prio rity\n\n")
#                     deduct_leave_by_priority(
#                         employee,
#                         date,
#                         status,
#                         att_name
#                     )
        
 
 
        
#         # if old_status in ("Absent", "Half Day","Partially") and status == "Present":
#         #     revert_penalty_leave(att_name)
#         return att_name
        
#     except Exception as e:
#         frappe.log_error("create_or_update attendance", frappe.get_traceback())
#         log_attendance_error(
#             employee,
#             date,
#             "Attendance Save Failed",
#             e
#         )

# * ------------------------------------------------------------------was using---------------------------------------------------------------------------------------
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

def deduct_leave_by_priority(employee, date, status, attendance, force_lwp = False):
    
    priority = [
        "Casual Leave",
        "Sick Leave",
        "Privilege Leave",
        # "Leave Without Pay"
    ]

    if employee == "001100: CL Test Eleven":
            frappe.log_error(f"penalty already applied{employee}", f"is forced lwp {force_lwp}")
            
    if status == "Half Day":    
        total_penalty_days = 0.5
    else:
        total_penalty_days = 1.0   # Absent OR Partially

    remaining_days = total_penalty_days

    att = frappe.get_doc("Attendance", attendance)

    if att.custom_is_penalize:
        
        return

    if not force_lwp:
        for leave_type in priority:
            balance = flt(get_leave_balance_on(employee, leave_type, date), 2)

            if employee == "001100: CL Test Eleven":
                frappe.log_error(f"Leave Balance{employee}", f"{balance}")
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

    if att.status not in ["Weekly Off", "Holiday", "Restricted Holiday"]:
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
        else:
            frappe.log_error("error_deduct_leave_by_priority", f"NO lWP LEAVE TYPE FOUND")
        return

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
    
    
    correct_holiday_list = get_current_holiday_list(employee, date) or None
    
    doc = frappe.get_doc({
        "doctype": "Leave Ledger Entry",
        "employee": employee,
        "employee_name": employee_doc.employee_name,
        "company": employee_doc.company,
        "holiday_list": correct_holiday_list if correct_holiday_list else employee_doc.holiday_list,
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
    
    # assigned_shift = frappe.db.get_value(
    #     "Shift Assignment",
    #     {
    #         "employee": employee,
    #         "start_date": ("<=", date),
    #         "end_date": (">=", date),
    #         "status": "Active"
    #     },
    #     "shift_type"
    # )

    shift_assignment = frappe.db.get_list(
        "Shift Assignment",
        filters={
            "employee": employee,
            "start_date": ["<=", date],
            "status": "Active"
        },
        or_filters=[
            {"end_date": [">=", date]},
            {"end_date": ["is", "not set"]}
        ],
        fields=["shift_type"],
        # order_by="start_date desc",
        limit=1
    )

    assigned_shift = shift_assignment[0].shift_type if shift_assignment else None

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

    # shift_type = frappe.db.get_value(
    #     "Shift Type",
    #     emp.default_shift,
    #     "custom_shift_type"
    # )
    # if not shift_type:
    #     return emp.default_shift
    
    # shift = frappe.db.get_value(
    #     "Shift Type",
    #     {
    #         "custom_branch": emp.branch,
    #         "custom_shift_type": shift_type,
    #         "custom_attendance_source": emp.custom_attendance_source, 
    #         "custom_hours": f"{required_hours}hours"                 
    #     },
    #     "name"
    # )
    
    # 6️⃣ Return matched shift or fallback
    # return shift or emp.default_shift
    return emp.default_shift
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

def process_comp_off_by_branch(comp_off_date):
    if not comp_off_date:
        frappe.throw("Attendance Date required")
    
    emp = get_employee_from_user()
    if not emp:
        frappe.throw("No Employee linked with this user")
    branch = emp.branch
    
    process_comp_off_scheduler(comp_off_date=comp_off_date, branch=branch)    
    
    return {
        "success": True,
        "message": f"CompOff Generated processed for branch: {branch}"
    }

@frappe.whitelist()
def process_comp_off_scheduler(comp_off_date=None, branch=None):
    """
    Runs daily.
    Checks only comp_off_date.
    """

    if not comp_off_date:
        comp_off_date = add_days(getdate(), -1)
    else:
        comp_off_date = getdate(comp_off_date)

    frappe.log_error("start_process_comp_off_scheduler", f"Scheduler Started FOR Date: {comp_off_date}")
    if branch:
        requests = frappe.get_all(
            "Off-Day Work Request",
            filters={
                "workflow_state": "Approved",
                "date": comp_off_date,
                "docstatus": 1,
                "branch":branch,
                "comp_off_created": 0
            },
            fields=["name", "employee", "date"]
        )
    else:
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
            # continue
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

        frappe.db.set_value(
            "Off-Day Work Request",
            req["name"],
            {
                "attendance": attendance,
                "leave_allocation": allocation.get("name"),
                "comp_off_created": 1
            }
        )
        try:
            handle_workflow_notification(req["name"])
        except Exception as e:
            frappe.log_error("handle notification error", f"{frappe.get_traceback()}")    
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


# def get_holiday_details(employee, date):
#     holiday_list = frappe.db.get_value(
#         "Employee",
#         employee,
#         "holiday_list"
#     )
    
#     #* FOR SAFETY
#     correct_holiday_list = None
    
#     current_holiday_list = get_current_holiday_list(employee, date)
    
#     if current_holiday_list:
#         correct_holiday_list = current_holiday_list
#     else:
#         correct_holiday_list = holiday_list
    
#     if not correct_holiday_list:
#         return None

#     holiday = frappe.db.get_value(
#         "Holiday",
#         {
#             "parent": correct_holiday_list,
#             "holiday_date": date
#         },
#         [
#             "weekly_off",
#             "custom_is_restricted_holiday",
#             "custom_restricted_holiday_date"
#         ],
#         as_dict=True
#     )

#     if not holiday:
#         return None

#     return {
#         "is_wo": bool(holiday.weekly_off),
#         "is_rh": bool(holiday.custom_is_restricted_holiday),
#         "pair_date": holiday.custom_restricted_holiday_date
#     }

# def get_holiday_details(employee, date):

#     doj = frappe.db.get_value("Employee", employee, "date_of_joining")

#     if doj and getdate(date) < getdate(doj):
#         return None

#     holiday_list = frappe.db.get_value("Employee", employee, "holiday_list")

#     correct_holiday_list = get_current_holiday_list(employee, date) or holiday_list

#     if not correct_holiday_list:
#         return None

#     holiday = frappe.db.get_value(
#         "Holiday",
#         {
#             "parent": correct_holiday_list,
#             "holiday_date": date
#         },
#         [
#             "weekly_off",
#             "custom_is_restricted_holiday",
#             "custom_restricted_holiday_date"
#         ],
#         as_dict=True
#     )

#     if not holiday:
#         return None

#     return {
#         "is_wo": bool(holiday.weekly_off),
#         "is_rh": False,  # ✅ treat RH as normal holiday
#         "pair_date": holiday.custom_restricted_holiday_date
#     }





# ---- get_holiday_details with RH treated as normal holiday (no pairing) START ----

def get_holiday_details(employee, date):

    doj = frappe.db.get_value("Employee", employee, "date_of_joining")

    if doj and getdate(date) < getdate(doj):
        return None

    holiday_list = frappe.db.get_value("Employee", employee, "holiday_list")
    correct_holiday_list = get_current_holiday_list(employee, date) or holiday_list

    if not correct_holiday_list:
        return None

    holiday = frappe.db.get_value(
        "Holiday",
        {
            "parent": correct_holiday_list,
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

    # Determine is_rh with DOJ edge case handled
    is_rh = bool(holiday.custom_is_restricted_holiday)
    pair_date = holiday.custom_restricted_holiday_date

    if is_rh and pair_date and doj:
        doj_date = getdate(doj)
        pair_date_obj = getdate(pair_date)
        current_date_obj = getdate(date)

        # Employee joined between the two RH dates → treat as normal Holiday
        # Case 1: pair is earlier, employee joined after pair but before/on current date
        # Case 2: pair is later, employee joined after current date but before/on pair date
        if (pair_date_obj < doj_date <= current_date_obj) or (current_date_obj < doj_date <= pair_date_obj):
            is_rh = False

    return {
        "is_wo": bool(holiday.weekly_off),
        "is_rh": is_rh,
        "pair_date": pair_date
    }

# ---- get_holiday_details with RH treated as normal holiday (no pairing) END ----





# =========================================================
# RH ONLY HANDLER
# =========================================================


# def handle_rh_only(req, attendance, holiday):

#     pair_date = holiday.get("pair_date")
#     if not pair_date:
#         return

#     pair_holiday = get_holiday_details(req["employee"], pair_date)

#     # RH + WO (past or future) → immediate
#     if pair_holiday and pair_holiday["is_wo"]:
#         allocation = create_comp_off(req["employee"], req["date"])

#         # Update Request
#         frappe.db.set_value(
#             "Off-Day Work Request",
#             req["name"],
#             {
#                 "attendance": attendance,
#                 "leave_allocation": allocation.get("name"),
#                 "comp_off_created": 1
#             }
#         )
#         handle_workflow_notification(req["name"])
#         return

#     # Pair is future RH-only → skip
#     if pair_date > req["date"]:
#         return

#     # Pair is past RH-only → both must be present
#     pair_attendance = get_attendance(req["employee"], pair_date)
#     if pair_attendance:
#         allocation = create_comp_off(req["employee"], req["date"])

#         # Update Request
#         frappe.db.set_value(
#             "Off-Day Work Request",
#             req["name"],
#             {
#                 "attendance": attendance,
#                 "leave_allocation": allocation.get("name"),
#                 "comp_off_created": 1
#             }
#         )
#         handle_workflow_notification(req["name"])




# ------ RH ONLY HANDLER with RH treated as normal holiday (no pairing) START ------

def handle_rh_only(req, attendance, holiday):

    pair_date = holiday.get("pair_date")
    if not pair_date:
        return

    pair_holiday = get_holiday_details(req["employee"], pair_date)

    # RH + WO (past or future) → immediate comp-off
    if pair_holiday and pair_holiday["is_wo"]:
        allocation = create_comp_off(req["employee"], req["date"])
        frappe.db.set_value(
            "Off-Day Work Request",
            req["name"],
            {
                "attendance": attendance,
                "leave_allocation": allocation.get("name"),
                "comp_off_created": 1
            }
        )
        handle_workflow_notification(req["name"])
        return

    # Pair is future RH-only → skip, will be re-evaluated when that date is processed
    if pair_date > req["date"]:
        return

    # Pair is past RH-only → employee MUST have been Present on that day too
    pair_attendance = get_attendance(req["employee"], pair_date)
    if not pair_attendance:
        # Employee was absent/on Restricted Holiday on the paired RH date → no comp-off
        frappe.log_error(
            "handle_rh_only_skipped",
            f"No 'Present' attendance on paired RH date {pair_date} "
            f"for {req['employee']}. Skipping comp-off for {req['date']}."
        )
        return

    # Both RH dates have Present attendance → grant comp-off
    allocation = create_comp_off(req["employee"], req["date"])
    frappe.db.set_value(
        "Off-Day Work Request",
        req["name"],
        {
            "attendance": attendance,
            "leave_allocation": allocation.get("name"),
            "comp_off_created": 1
        }
    )
    handle_workflow_notification(req["name"])

# ------ RH ONLY HANDLER with RH treated as normal holiday (no pairing) END ------



# =========================================================
# Comp Off ALLOCATION CREATION
# =========================================================


def create_comp_off(employee, date):
    """
    Creates 1 Comp-Off Leave Allocation
    Validity: 45 days
    """

    date = getdate(date)
    frappe.log_error("create_comp_off", f"Creating Comp-Off for employee: {employee} on date: {date}")
    
    al_created = already_created(employee, date)
    
    if al_created:        
        frappe.log_error("compoff_already_created", "already created")
        return {"name":al_created}

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
# Comp Off ALLOCATION expire status set
# =========================================================

@frappe.whitelist()
def expire_comp_off_leave_allocations():
    expired_allocations = frappe.get_all(
        "Leave Allocation",
        filters={
            "leave_type": "Compensatory Off",
            "docstatus": 1,
            "custom_leave_status": ["!=", "Expire"],
            "to_date": ["<", today()]  # Only expired allocations
        },
        fields=["name", "to_date"]
    )

    for allocation in expired_allocations:
        doc = frappe.get_doc("Leave Allocation", allocation.name)

        # Set status as Expire
        doc.db_set("custom_leave_status", "Expire", update_modified=False)

        # # Add timeline comment
        # doc.add_comment(
        #     "Info",
        #     f"Compensatory Off leave allocation expired automatically. "
        #     f"Valid until {allocation.to_date}."
        # )

    frappe.db.commit()


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
        },
        "name",        
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


# # * METHOD TO ALLOCATE CASUAL LEAVE AND SICK LEAVE TO CONFIRMED EMPLOYEES
# # * THIS METHOD WILL RUN EVERY FIRST DAY OF THE FINANCIAL YEAR, I.E., 1ST APRIL
# @frappe.whitelist()
# def allocate_leaves_to_confirmed_employee(dt=None):
#     try:
#         frappe.log_error("Leave Allocation Job Started", "Allocating Casual Leave And Sick Leave")
#         if dt:
#             today_date = getdate(dt)
#         else:
#             today_date = getdate()
#         financial_year_start = getdate(f"{today_date.year}-04-01")
#         financial_year_end = getdate(f"{today_date.year + 1}-03-31")
        
#         if today_date == financial_year_start:
            
#             is_casual_leave_type = True if frappe.db.get_value("Leave Type", "Casual Leave", ["custom_leave_type"]) == "Casual Leave" else False
            
#             is_sick_leave_type = True if frappe.db.get_value("Leave Type", "Sick Leave", ["custom_leave_type"]) == "Sick Leave" else False
            
#             confirmed_employees = frappe.get_all("Employee", {"employment_type": "Confirmed", "status": "Active"}, ["name"])
            
#             if is_casual_leave_type or is_sick_leave_type:
#             # if is_casual_leave_type:
#                 for emp in confirmed_employees:
                    
#                     if is_casual_leave_type and not frappe.db.exists("Leave Allocation", {"employee": emp.name, "leave_type": "Casual Leave", "from_date":["<=", financial_year_start], "to_date": [">=", financial_year_end]}):
#                     # if is_casual_leave_type:
#                         try:                                                                                                                            
#                             cl_leave_allocation = frappe.get_doc({
#                                 "doctype": "Leave Allocation",
#                                 "employee": emp.name,
#                                 "leave_type": "Casual Leave",
#                                 "from_date": financial_year_start,
#                                 "to_date": financial_year_end,
#                                 "new_leaves_allocated": 12,
#                                 "custom_last_allocation_date": today_date
#                             })
#                             cl_leave_allocation.insert(ignore_permissions=True)
#                             cl_leave_allocation.submit()
#                         except Exception as e:
#                             frappe.log_error(f"error_allocate_casual_leaves_{emp.name}", frappe.get_traceback())
                            
                            
                    
#                     if is_sick_leave_type and not frappe.db.exists("Leave Allocation", {"employee": emp.name, "leave_type": "Sick Leave", "from_date":["<=", financial_year_start], "to_date": [">=", financial_year_end]}):
#                         try:
                            
#                             last_year_leave_balance = get_leave_balance_on(emp.name, "Sick Leave", getdate(f"{financial_year_start.year}-03-31"))
                            
#                             if last_year_leave_balance > flt(28, 2):
#                                 sl_opening_balance = flt(28,2)
#                                 extra_sl = flt(last_year_leave_balance - flt(28,2), 2)
#                             else:
#                                 sl_opening_balance = last_year_leave_balance
#                                 extra_sl = 0                                         
#                             sl_leave_allocation = frappe.get_doc({
#                                 "doctype": "Leave Allocation",
#                                 "employee": emp.name,
#                                 "leave_type": "Sick Leave",
#                                 "from_date": financial_year_start,
#                                 "to_date": financial_year_end,
#                                 "new_leaves_allocated": 7,
#                                 "custom_opening_balance": sl_opening_balance,
#                                 "custom_last_allocation_date": today_date,
#                                 "custom_extra_sl_carry_forwarded_to_pl": extra_sl
#                             })
#                             sl_leave_allocation.insert(ignore_permissions=True)
#                             sl_leave_allocation.submit()
                            
#                             if extra_sl > 0:
#                                 extra_sl_allocation = frappe.get_doc({
#                                     "doctype": "Leave Allocation",
#                                     "employee": emp.name,
#                                     "leave_type": "Privilege Leave",
#                                     "from_date": financial_year_start,
#                                     "to_date": financial_year_end,
#                                     "new_leaves_allocated": extra_sl,
#                                     "carry_forward": 1,
#                                     "custom_extra_sl_carry_forwarded_to_pl": extra_sl,
#                                     "custom_last_allocation_date": today_date
#                                 })
#                                 extra_sl_allocation.insert(ignore_permissions=True)
#                                 extra_sl_allocation.submit()
                            
                            
#                         except Exception as e:
#                             frappe.log_error(f"error_allocate_sick_leaves_{emp.name}", frappe.get_traceback())
                            
#                 frappe.db.commit()                                
#             frappe.log_error("Leave Allocation Job Completed", "Completed Allocating Casual Leave and Sick Leave")
#     except Exception as e:
#         frappe.log_error(f"error_allocate_leaves_main", frappe.get_traceback())





# ----- Confirmed EMP. LEave Accrual with Branch Filter START -----

@frappe.whitelist()
def allocate_leaves_to_confirmed_employee(dt=None, branch=None):
    if branch:
        branch = branch.strip().strip('"').strip("'")

        if not frappe.db.exists("Branch", branch):
            frappe.throw(f"Invalid branch: {branch}")
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
            
            filters = {
                "employment_type": "Confirmed",
                "status": "Active"
            }

            if branch:
                filters["branch"] = branch

            confirmed_employees = frappe.get_all(
                "Employee",
                filters,
                ["name", "branch"]
            )
            
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
                                    # "carry_forward": 1,
                                    "carry_forward": 0, # PL cary forward Bug resolution
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

# ----- Confirmed EMP. LEave Accrual with Branch Filter END -----




# # * METHOD TO ALLOCATE CASUAL LEAVE TO PROBATION AND CONTRACTUAL EMPLOYEES
# # * THIS METHOD WILL RUN EVERY FIRST DAY OF THE MONTH
# @frappe.whitelist()
# def allocate_cl_to_probation_and_contract_employees(dt=None):
#     try:
#         frappe.log_error("CL Allocation to Probation and Contractual Employees Job Started", "CL Allocation to Probation and Contractual Employees rty")
#         if dt:
#             today_date = getdate(dt)
#         else:
#             today_date = getdate()
            
#         month_start_date = getdate(f"{today_date.year}-{today_date.month}-01")
        
#         if today_date == month_start_date:
                
        
#             fy_start_date = getdate(f"{today_date.year - 1}-04-01") if today_date.month < 4 else getdate(f"{today_date.year}-04-01")
#             fy_end_date   = getdate(f"{today_date.year}-03-31") if today_date.month < 4 else getdate(f"{today_date.year + 1}-03-31")
#             # return f_year_end_date
            
#             cl_leave_type = "Casual Leave"
            
#             is_casual_leave = True if frappe.db.get_value("Leave Type", cl_leave_type, "custom_leave_type") == "Casual Leave" else False
            
#             if is_casual_leave:
            
#                 p_and_employees = frappe.db.get_all("Employee", {"employment_type": ["in", ["Probation", "Contractual"]], "status": "Active"},["name", "employment_type", "contract_end_date", "date_of_joining"])
                            
#                 for emp in p_and_employees:
#                     try:                        
#                         if emp.employment_type == "Contractual" and emp.contract_end_date and getdate(emp.contract_end_date) > month_start_date:
#                             to_date = min(getdate(emp.contract_end_date), fy_end_date)
#                         else:
#                             to_date = fy_end_date

#                         # from_date = max(fy_start_date, emp.date_of_joining)
#                         allocation_det = frappe.db.get_all("Leave Allocation", {"employee": emp.name, "leave_type": cl_leave_type, "docstatus": 1, "from_date": ["<=", today_date], "to_date": [">=", today_date]}, "name", order_by="from_date desc", limit_page_length=1)
                        
#                         allocation_name = allocation_det[0].name if allocation_det else None
                        
#                         if allocation_name:
#                             allocation = frappe.get_doc("Leave Allocation", allocation_name)
                        
                            
#                             last_cl_allocation_date = getdate(allocation.custom_last_allocation_date)
#                             if last_cl_allocation_date and (last_cl_allocation_date >= today_date or last_cl_allocation_date.month == today_date.month):
#                                 frappe.log_error(f"last_allocation_date: {last_cl_allocation_date}", f"Employee: {emp.name} {last_cl_allocation_date.month} {today_date.month} 123")
#                                 continue
                            
#                             new_allocation = flt(allocation.total_leaves_allocated) + flt(1)
                            
#                             if new_allocation != allocation.total_leaves_allocated:
#                                 allocation.db_set("total_leaves_allocated", new_allocation, update_modified=False)

#                                 date = today_date or frappe.flags.current_date or getdate()
#                                 custom_create_additional_leave_ledger_entry(allocation, 1, date, is_accrual=1)
                            
#                                 frappe.get_doc({
#                                     "doctype": "Leave Accrual",
#                                     "parent": allocation.name,
#                                     "parenttype": "Leave Allocation",
#                                     "parentfield": "custom_leave_accrual",
#                                     "from_date": month_start_date,
#                                     "to_date": to_date,
#                                     "leave_allocated": 1,
#                                 }).insert(ignore_permissions=True)

                                
#                                 allocation.db_set(
#                                     "custom_last_allocation_date",
#                                     today_date,
#                                     update_modified=False
#                                 )
#                             # allocation.new_leaves_allocated += 1
#                             # allocation.custom_last_allocation_date = today_date
#                             # allocation.save(ignore_permissions=True)
                        
#                         else:
#                             allocation = frappe.get_doc({
#                                 "doctype": "Leave Allocation",
#                                 "employee": emp.name,
#                                 "leave_type": cl_leave_type,
#                                 "from_date": month_start_date,
#                                 "to_date": to_date,
#                                 "new_leaves_allocated": 1,
#                                 "custom_last_allocation_date": today_date
#                             })
#                             allocation.insert(ignore_permissions=True)
#                             allocation.submit()
#                             frappe.get_doc({
#                                     "doctype": "Leave Accrual",
#                                     "parent": allocation.name,
#                                     "parenttype": "Leave Allocation",
#                                     "parentfield": "custom_leave_accrual",
#                                     "from_date": month_start_date,
#                                     "to_date": to_date,
#                                     "leave_allocated": 1,
#                             }).insert(ignore_permissions=True)
                            
#                     except Exception as e:
#                         frappe.log_error(f"error_allocate_cl_to_probation_and_contract_employees_{emp.name}", f"{frappe.get_traceback()} \n \n {month_start_date} {to_date}")
#                         continue
#                 frappe.db.commit()
#             frappe.log_error("CL Allocation to Probation and Contractual Employees Job Completed", "CL Allocated to Probation and Contractual Employees")
        
#     except Exception as e:
#         frappe.log_error(f"error_main_allocate_cl_to_probation_and_contract_employees", frappe.get_traceback())


# ------ NEW METHOD for Casual Leave Allocation to Probation and Contractual Employees with Branch Filter START -----

@frappe.whitelist()
def allocate_cl_to_probation_and_contract_employees(dt=None, branch=None):
    if branch:
        branch = branch.strip().strip('"').strip("'")

        if not frappe.db.exists("Branch", branch):
            frappe.throw(f"Invalid branch: {branch}")

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
            
                filters = {
                    "employment_type": ["in", ["Probation", "Contractual"]],
                    "status": "Active"
                }

                if branch:
                    filters["branch"] = branch

                p_and_employees = frappe.db.get_all(
                    "Employee",
                    filters,
                    ["name", "employment_type", "contract_end_date", "date_of_joining", "branch"]
                )
                            
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
                            
                            new_allocation = flt(allocation.total_leaves_allocated) + flt(1)
                            
                            if new_allocation != allocation.total_leaves_allocated:
                                allocation.db_set("total_leaves_allocated", new_allocation, update_modified=False)

                                date = today_date or frappe.flags.current_date or getdate()
                                custom_create_additional_leave_ledger_entry(allocation, 1, date, is_accrual=1)
                            
                                frappe.get_doc({
                                    "doctype": "Leave Accrual",
                                    "parent": allocation.name,
                                    "parenttype": "Leave Allocation",
                                    "parentfield": "custom_leave_accrual",
                                    "from_date": month_start_date,
                                    "to_date": to_date,
                                    "leave_allocated": 1,
                                }).insert(ignore_permissions=True)

                                
                                allocation.db_set(
                                    "custom_last_allocation_date",
                                    today_date,
                                    update_modified=False
                                )
                            # allocation.new_leaves_allocated += 1
                            # allocation.custom_last_allocation_date = today_date
                            # allocation.save(ignore_permissions=True)
                        
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
                            frappe.get_doc({
                                    "doctype": "Leave Accrual",
                                    "parent": allocation.name,
                                    "parenttype": "Leave Allocation",
                                    "parentfield": "custom_leave_accrual",
                                    "from_date": month_start_date,
                                    "to_date": to_date,
                                    "leave_allocated": 1,
                            }).insert(ignore_permissions=True)
                            
                    except Exception as e:
                        frappe.log_error(f"error_allocate_cl_to_probation_and_contract_employees_{emp.name}", f"{frappe.get_traceback()} \n \n {month_start_date} {to_date}")
                        continue
                frappe.db.commit()
            frappe.log_error("CL Allocation to Probation and Contractual Employees Job Completed", "CL Allocated to Probation and Contractual Employees")
        
    except Exception as e:
        frappe.log_error(f"error_main_allocate_cl_to_probation_and_contract_employees", frappe.get_traceback())

# ------ NEW METHOD for Casual Leave Allocation to Probation and Contractual Employees with Branch Filter END -----


# # * METHOD TO ALLOCATE SICK LEAVE TO PROBATION AND CONTRACTUAL EMPLOYEES
# # * THIS METHOD WILL RUN EVERY DAY
# @frappe.whitelist()
# def allocate_sl_to_probation_and_contract_employees(dt=None):
#     try:
#         if dt:
#             today_date = getdate(dt)
#         else:
#             today_date = getdate()
            
#         # today_date = getdate()
#         monthly_sl = flt(0.58)
#         frappe.log_error(f"monthly {monthly_sl}", f"{monthly_sl}")
        
#         sl_leave_type = "Sick Leave"

#         month_end_date = getdate(get_last_day(today_date))
#         month_start_date = getdate(get_first_day(today_date))
        
#         if today_date.month < 4:
#             current_fy_start = getdate(f"{today_date.year - 1}-04-01")
#             current_fy_end   = getdate(f"{today_date.year}-03-31")
            
#         else:
#             current_fy_start = getdate(f"{today_date.year}-04-01")
#             current_fy_end   = getdate(f"{today_date.year + 1}-03-31")
            
        
        
#         if today_date != month_end_date and today_date != current_fy_start:
#             return
#         new_financial_year = today_date == current_fy_start

#         if frappe.db.get_value("Leave Type", sl_leave_type, "custom_leave_type") != "Sick Leave":
#             return

#         employees = frappe.db.get_all(
#             "Employee",
#             {
#                 "employment_type": ["in", ["Probation", "Contractual"]],
#                 "status": "Active",
#                 "date_of_joining": ["<=", month_end_date]
#             },
#             ["name", "employment_type", "date_of_joining", "contract_end_date"],
#         )

#         frappe.log_error("sl eligible employee", f"{employees}")
#         for emp in employees:
#             try:
#                 joining_date = getdate(emp.date_of_joining)

#                 is_new_emp = True if month_start_date <= joining_date <= month_end_date else False
                
#                 if emp.employment_type == "Contractual" and emp.contract_end_date:
#                     if today_date > getdate(emp.contract_end_date):
#                         continue

#                 effective_to_date = current_fy_end
#                 if emp.employment_type == "Contractual" and emp.contract_end_date:
#                     effective_to_date = min(getdate(emp.contract_end_date), current_fy_end)

#                 current_alloc = frappe.db.get_all(
#                     "Leave Allocation",
#                     {
#                         "employee": emp.name,
#                         "leave_type": sl_leave_type,
#                         "docstatus": 1,
#                         "from_date": ["<=", today_date],
#                         "to_date": [">=", today_date],
#                     },
#                     ["name", "custom_last_allocation_date"],
#                     order_by="from_date desc",
#                     limit_page_length=1,
#                 )

#                 last_alloc_date = None
#                 if current_alloc and current_alloc[0]:
#                     if not current_alloc[0].custom_last_allocation_date:
#                         last_alloc_date = getdate(add_to_date(month_start_date, days=-1))
#                     else:
#                         last_alloc_date = getdate(current_alloc[0].custom_last_allocation_date)
#                 else:
#                     last_alloc_date = joining_date if month_start_date <= joining_date <= month_end_date else month_start_date
                
#                 if emp.name == "20135: KARAN KUMAR":
#                         frappe.log_error(f"last_alloc{emp.name}", f"{last_alloc_date} - {joining_date} - {month_start_date} - {month_end_date}")
                            
#                 already_allocated_this_month = True if last_alloc_date and last_alloc_date.year == today_date.year and last_alloc_date.month == today_date.month and last_alloc_date != current_fy_start else False
                
#                 if emp.name == "001100: CL Test Eleven":
#                     frappe.log_error("Already_allocated", f"{already_allocated_this_month} - last alloc date {last_alloc_date} - today date {today_date} - current fy start {current_fy_start}")
#                 if not new_financial_year:
#                     if current_alloc and not already_allocated_this_month:
                        
#                         alloc_doc = frappe.get_doc("Leave Allocation", current_alloc[0].name)
#                         new_allocation = flt(alloc_doc.total_leaves_allocated) + flt(monthly_sl)
                            
#                         if new_allocation != alloc_doc.total_leaves_allocated:
#                                 alloc_doc.db_set("total_leaves_allocated", new_allocation, update_modified=False)
#                                 date = today_date or frappe.flags.current_date or getdate()
#                                 if emp.name == "001100: CL Test Eleven":
#                                     frappe.log_error("New Allocation", f"{date} New Allocation {monthly_sl}")
#                                 custom_create_additional_leave_ledger_entry(alloc_doc, monthly_sl, date, is_accrual=1)
                            
#                                 frappe.get_doc({
#                                     "doctype": "Leave Accrual",
#                                     "parent": alloc_doc.name,
#                                     "parenttype": "Leave Allocation",
#                                     "parentfield": "custom_leave_accrual",
#                                     "from_date": date,
#                                     "to_date": effective_to_date,
#                                     # "eligible_days": eligible_days,
#                                     "leave_allocated": monthly_sl,
#                                 }).insert(ignore_permissions=True)

                                
#                                 alloc_doc.db_set(
#                                     "custom_last_allocation_date",
#                                     today_date,
#                                     update_modified=False
#                                 )
                        
                        
                        
#                         # alloc_doc.new_leaves_allocated = flt(alloc_doc.new_leaves_allocated) + monthly_sl
#                         # alloc_doc.custom_last_allocation_date = today_date
#                         # alloc_doc.save(ignore_permissions=True)
#                     elif not current_alloc:
                        
#                         if is_new_emp:
#                             frappe.log_error("is_new_emp", f"{emp.name} is new employee")
#                             total_days = month_end_date.day
                                                        
#                             remaining_days = total_days - joining_date.day + 1
                            
#                             c_monthly_sl = flt((remaining_days / total_days) * monthly_sl, 2)
                                                    
#                         else:
#                             c_monthly_sl = monthly_sl
                        
                            
#                         new_alloc = frappe.get_doc({ 
#                             "doctype": "Leave Allocation",
#                             "employee": emp.name,
#                             "leave_type": sl_leave_type,
#                             "from_date": today_date,
#                             "to_date": effective_to_date,
#                             "new_leaves_allocated": c_monthly_sl,
#                             "custom_last_allocation_date": today_date,
                            
#                         })
#                         new_alloc.insert(ignore_permissions=True)
#                         new_alloc.submit()
                        
#                         frappe.get_doc({
#                                     "doctype": "Leave Accrual",
#                                     "parent": new_alloc.name,
#                                     "parenttype": "Leave Allocation",
#                                     "parentfield": "custom_leave_accrual",
#                                     "from_date": today_date,
#                                     "to_date": effective_to_date,
#                                     # "eligible_days": eligible_days,
#                                     "leave_allocated": monthly_sl,
#                                 }).insert(ignore_permissions=True)
                        
                        
#                 else:
#                     prev_fy_end = getdate(f"{today_date.year}-03-31")
#                     last_year_balance = get_leave_balance_on(
#                         emp.name,
#                         sl_leave_type,
#                         prev_fy_end,
#                     ) or 0
                    
#                     # prev_fy_alloc = frappe.db.get_all(
#                     #     "Leave Allocation",
#                     #     {
#                     #         "employee": emp.name,
#                     #         "leave_type": sl_leave_type,
#                     #         "docstatus": 1,
#                     #         "from_date": ["<=", prev_fy_end],
#                     #         "to_date": [">=", prev_fy_end],
#                     #     },
#                     #     ["custom_last_allocation_date"],
#                     #     order_by="from_date desc",
#                     #     limit_page_length=1,
#                     # )

#                     # if prev_fy_alloc and prev_fy_alloc[0].custom_last_allocation_date:
#                     #     last_alloc_date = getdate(prev_fy_alloc[0].custom_last_allocation_date)
#                     # else:
#                     #     last_alloc_date = joining_date
                
#                     # if date_diff(today_date, last_alloc_date) >= allocate_after_days:
#                     #     new_leaves = 1
#                     # else:

#                     fy_alloc = frappe.get_doc({
#                         "doctype": "Leave Allocation",
#                         "employee": emp.name,
#                         "leave_type": sl_leave_type,
#                         "from_date": current_fy_start,
#                         "to_date": effective_to_date,
#                         "custom_opening_balance": last_year_balance,
#                         "new_leaves_allocated": 0,
#                         "custom_last_allocation_date": current_fy_start,
#                     })
#                     fy_alloc.insert(ignore_permissions=True)
#                     fy_alloc.submit()

#             except Exception:
#                 frappe.log_error(
#                     f"error_allocate_sl_{emp.name}",
#                     frappe.get_traceback(),
#                 )
#                 continue

#         frappe.db.commit()
#         frappe.log_error(
#             "SL Allocation Job Completed",
#             f"Scheduler run completed on {today_date}",
#         )

#     except Exception:
#         frappe.log_error(
#             "error_allocate_sl_main",
#             frappe.get_traceback(),
#         )




# --- NEW METHOD for Sick Leave Allocation to Probation and Contractual Employees with Branch Filter START -----

@frappe.whitelist()
def allocate_sl_to_probation_and_contract_employees(dt=None, branch=None):
    if branch:
        branch = branch.strip().strip('"').strip("'")

        if not frappe.db.exists("Branch", branch):
            frappe.throw(f"Invalid branch: {branch}")
    try:
        if dt:
            today_date = getdate(dt)
        else:
            today_date = getdate()
            
        # today_date = getdate()
        monthly_sl = flt(0.58)
        frappe.log_error(f"monthly {monthly_sl}", f"{monthly_sl}")
        
        sl_leave_type = "Sick Leave"

        month_end_date = getdate(get_last_day(today_date))
        month_start_date = getdate(get_first_day(today_date))
        
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

        filters = {
            "employment_type": ["in", ["Probation", "Contractual"]],
            "status": "Active",
            "date_of_joining": ["<=", month_end_date]
        }

        if branch:
            filters["branch"] = branch

        employees = frappe.db.get_all(
            "Employee",
            filters,
            ["name", "employment_type", "date_of_joining", "contract_end_date", "branch"],
        )

        frappe.log_error("sl eligible employee", f"{employees}")
        for emp in employees:
            try:
                joining_date = getdate(emp.date_of_joining)

                is_new_emp = True if month_start_date <= joining_date <= month_end_date else False
                
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
                if current_alloc and current_alloc[0]:
                    if not current_alloc[0].custom_last_allocation_date:
                        last_alloc_date = getdate(add_to_date(month_start_date, days=-1))
                    else:
                        last_alloc_date = getdate(current_alloc[0].custom_last_allocation_date)
                else:
                    last_alloc_date = joining_date if month_start_date <= joining_date <= month_end_date else month_start_date
                
                if emp.name == "20135: KARAN KUMAR":
                        frappe.log_error(f"last_alloc{emp.name}", f"{last_alloc_date} - {joining_date} - {month_start_date} - {month_end_date}")
                            
                already_allocated_this_month = True if last_alloc_date and last_alloc_date.year == today_date.year and last_alloc_date.month == today_date.month and last_alloc_date != current_fy_start else False
                
                if emp.name == "001100: CL Test Eleven":
                    frappe.log_error("Already_allocated", f"{already_allocated_this_month} - last alloc date {last_alloc_date} - today date {today_date} - current fy start {current_fy_start}")
                if not new_financial_year:
                    if current_alloc and not already_allocated_this_month:
                        
                        alloc_doc = frappe.get_doc("Leave Allocation", current_alloc[0].name)
                        new_allocation = flt(alloc_doc.total_leaves_allocated) + flt(monthly_sl)
                            
                        if new_allocation != alloc_doc.total_leaves_allocated:
                                alloc_doc.db_set("total_leaves_allocated", new_allocation, update_modified=False)
                                date = today_date or frappe.flags.current_date or getdate()
                                if emp.name == "001100: CL Test Eleven":
                                    frappe.log_error("New Allocation", f"{date} New Allocation {monthly_sl}")
                                custom_create_additional_leave_ledger_entry(alloc_doc, monthly_sl, date, is_accrual=1)
                            
                                frappe.get_doc({
                                    "doctype": "Leave Accrual",
                                    "parent": alloc_doc.name,
                                    "parenttype": "Leave Allocation",
                                    "parentfield": "custom_leave_accrual",
                                    "from_date": date,
                                    "to_date": effective_to_date,
                                    # "eligible_days": eligible_days,
                                    "leave_allocated": monthly_sl,
                                }).insert(ignore_permissions=True)

                                
                                alloc_doc.db_set(
                                    "custom_last_allocation_date",
                                    today_date,
                                    update_modified=False
                                )
                        
                        
                        
                        # alloc_doc.new_leaves_allocated = flt(alloc_doc.new_leaves_allocated) + monthly_sl
                        # alloc_doc.custom_last_allocation_date = today_date
                        # alloc_doc.save(ignore_permissions=True)
                    elif not current_alloc:
                        
                        if is_new_emp:
                            frappe.log_error("is_new_emp", f"{emp.name} is new employee")
                            total_days = month_end_date.day
                                                        
                            remaining_days = total_days - joining_date.day + 1
                            
                            c_monthly_sl = flt((remaining_days / total_days) * monthly_sl, 2)
                                                    
                        else:
                            c_monthly_sl = monthly_sl
                        
                            
                        new_alloc = frappe.get_doc({ 
                            "doctype": "Leave Allocation",
                            "employee": emp.name,
                            "leave_type": sl_leave_type,
                            "from_date": today_date,
                            "to_date": effective_to_date,
                            "new_leaves_allocated": c_monthly_sl,
                            "custom_last_allocation_date": today_date,
                            
                        })
                        new_alloc.insert(ignore_permissions=True)
                        new_alloc.submit()
                        
                        frappe.get_doc({
                                    "doctype": "Leave Accrual",
                                    "parent": new_alloc.name,
                                    "parenttype": "Leave Allocation",
                                    "parentfield": "custom_leave_accrual",
                                    "from_date": today_date,
                                    "to_date": effective_to_date,
                                    # "eligible_days": eligible_days,
                                    "leave_allocated": monthly_sl,
                                }).insert(ignore_permissions=True)
                        
                        
                else:
                    prev_fy_end = getdate(f"{today_date.year}-03-31")
                    last_year_balance = get_leave_balance_on(
                        emp.name,
                        sl_leave_type,
                        prev_fy_end,
                    ) or 0
                    
                    # prev_fy_alloc = frappe.db.get_all(
                    #     "Leave Allocation",
                    #     {
                    #         "employee": emp.name,
                    #         "leave_type": sl_leave_type,
                    #         "docstatus": 1,
                    #         "from_date": ["<=", prev_fy_end],
                    #         "to_date": [">=", prev_fy_end],
                    #     },
                    #     ["custom_last_allocation_date"],
                    #     order_by="from_date desc",
                    #     limit_page_length=1,
                    # )

                    # if prev_fy_alloc and prev_fy_alloc[0].custom_last_allocation_date:
                    #     last_alloc_date = getdate(prev_fy_alloc[0].custom_last_allocation_date)
                    # else:
                    #     last_alloc_date = joining_date
                
                    # if date_diff(today_date, last_alloc_date) >= allocate_after_days:
                    #     new_leaves = 1
                    # else:

                    fy_alloc = frappe.get_doc({
                        "doctype": "Leave Allocation",
                        "employee": emp.name,
                        "leave_type": sl_leave_type,
                        "from_date": current_fy_start,
                        "to_date": effective_to_date,
                        "custom_opening_balance": last_year_balance,
                        "new_leaves_allocated": 0,
                        "custom_last_allocation_date": current_fy_start,
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

# --- NEW METHOD for Sick Leave Allocation to Probation and Contractual Employees with Branch Filter END -----



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
                    
                    emp_doc = frappe.get_doc("Employee", emp.name)
                    
                    if emp_doc:
                        if emp_doc.get("custom_reporting_manager"):
                            current_rm = None
                            
                    

                        for row in emp_doc.get("custom_reporting_manager"):
                            if row.get("effective_from") and getdate(row.get("effective_from") <= getdate(today())):
                                current_rm = row.get("employee")

                        if current_rm:
                            if emp_doc.get("reports_to") != current_rm:
                                emp_doc.reports_to = current_rm
                    
                            
                            current_rm_user = emp_doc.get("user_id") if frappe.db.get_value("User", emp_doc.get("user_id")) else None

                            if current_rm_user:
                                if emp_doc.get("expense_approver") != current_rm_user:
                                    emp_doc.expense_approver = current_rm_user
                                
                                if emp_doc.get("leave_approver") != current_rm_user:
                                    emp_doc.leave_approver = current_rm_user
                                    
                                if emp_doc.get("shift_request_approver") != current_rm_user:
                                    emp_doc.shift_request_approver = current_rm_user
                    
                    emp_doc.save(ignore_permissions=True)          
                    # current_emp_shift_approver = frappe.db.get_value("Employee", emp.name, "shift_request_approver") or None
                    # current_emp_leave_approver = frappe.db.get_value("Employee", emp.name, "leave_approver") or None
                    # current_emp_reports_to = frappe.db.get_value("Employee", emp.name, "reports_to") or None
                    
                    
                    # current_holiday_list = get_current_holiday_list(emp.name, from_date)
                    # frappe.log_error("Holiday List", f"{current_holiday_list} {emp.holiday_list}")
                    # if current_holiday_list:
                    #     if not emp.holiday_list:
                    #         frappe.db.set_value("Employee", emp.name, "holiday_list", current_holiday_list)
                        
                    #     elif emp.holiday_list != current_holiday_list:
                    #         frappe.db.set_value("Employee", emp.name, "holiday_list", current_holiday_list)
                            

                    
                    
                    # emp_rm = get_emp_reporting_manager(emp.name)
                    # emp_rm_emp = frappe.db.get_value("Employee", {"user_id": emp_rm}, "name") if emp_rm else None
                    # if not emp_rm_emp:
                    #     frappe.log_error(f"Reporting Manager Employee Not Found for User ID: {emp_rm}", f"Employee: {emp.name}")
                    
                    # if emp_rm:
                    #     if current_emp_shift_approver != emp_rm:
                    #         frappe.db.set_value("Employee", emp.name, "shift_request_approver", emp_rm)
                    #     if current_emp_leave_approver != emp_rm:
                    #         frappe.db.set_value("Employee", emp.name, "leave_approver", emp_rm)                        
                    #     if current_emp_reports_to != emp_rm_emp:
                    #         frappe.db.set_value("Employee", emp.name, "reports_to", emp_rm_emp)
                                                                                
                except Exception as e:
                    frappe.log_error(f"error_set_approvers_in_employee_{emp.name}", frappe.get_traceback())
                    continue
            
            frappe.db.commit()
        frappe.log_error("Set Approvers in Employee Job Completed", "Set Approvers in Employee Job Completed")
        
        
    except Exception as e:        
        frappe.log_error(
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

# def revert_penalty_leave(attendance_name):
#     try:
#         att = frappe.get_doc("Attendance", attendance_name)

#         if not att.custom_is_penalize:
#             return

#         leave_type = att.custom_penalty_leave_type
#         leave_count = att.custom_penalty_leave_count
#         attendance_date = att.attendance_date

#         frappe.db.delete(
#             "Leave Ledger Entry",
#             {
#                 "employee": att.employee,
#                 "leave_type": leave_type,
#                 "from_date": attendance_date,
#                 "custom_is_penalty": 1,              # ✅ recommended if you have this field
#                 "custom_attendance":att.name,
#             }
#         )

#         att.db_set({
#             "custom_penalty_leave_type": None,
#             "custom_penalty_leave_count": 0,
#             "custom_is_penalize": 0
#         })

#         frappe.db.commit()
#     except Exception as e:
#         frappe.log_error("error_revert_penalty_leave", frappe.get_traceback())

def revert_penalty_leave(attendance_name):
    try:

        # frappe.log_error("START", attendance_name)

        att = frappe.get_doc("Attendance", attendance_name)

        leave_type = att.custom_penalty_leave_type
        attendance_date = att.attendance_date

        # frappe.log_error(
        #     "DEBUG",
        #     f"""
        #     Employee: {att.employee}
        #     Leave Type: {leave_type}
        #     Date: {attendance_date}
        #     Penalize: {att.custom_is_penalize}
        #     """
        # )

        # =====================================================
        # GET LEDGER ENTRIES
        # =====================================================
        ledger_entries = frappe.get_all(
            "Leave Ledger Entry",
            filters={
                "employee": att.employee,
                "leave_type": leave_type,
                "from_date": attendance_date,
                "custom_is_penalty": 1,
                "custom_attendance": att.name
            },
            fields=["name", "docstatus", "is_expired"]
        )

        # frappe.log_error(
        #     "LEDGER FOUND",
        #     str(ledger_entries)
        # )

        # =====================================================
        # REMOVE ENTRIES
        # =====================================================
        for row in ledger_entries:

            ledger_doc = frappe.get_doc(
                "Leave Ledger Entry",
                row.name
            )

            frappe.log_error(
                "PROCESSING",
                ledger_doc.name
            )

            # SET EXPIRED
            frappe.db.set_value(
                "Leave Ledger Entry",
                ledger_doc.name,
                "is_expired",
                1,
                update_modified=False
            )

            frappe.db.commit()

            ledger_doc.reload()

            # frappe.log_error(
            #     "AFTER UPDATE",
            #     f"{ledger_doc.name} -> is_expired = {ledger_doc.is_expired}"
            # )

            # CANCEL
            if ledger_doc.docstatus == 1:
                ledger_doc.cancel()

            # frappe.log_error(
            #     "CANCELLED",
            #     ledger_doc.name
            # )

            # DELETE
            frappe.delete_doc(
                "Leave Ledger Entry",
                ledger_doc.name,
                force=1,
                ignore_permissions=True
            )

            # frappe.log_error(
            #     "DELETED",
            #     ledger_doc.name
            # )

        # =====================================================
        # RESET ATTENDANCE
        # =====================================================
        frappe.db.set_value(
            "Attendance",
            att.name,
            {
                "custom_penalty_leave_type": None,
                "custom_penalty_leave_count": 0,
                "custom_is_penalize": 0
            },
            update_modified=False
        )

        frappe.db.commit()

    except Exception:
        frappe.db.rollback()

        frappe.log_error(
            frappe.get_traceback(),
            "error_revert_penalty_leave"
        )
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


# def get_holiday_type(employee, date):

#     holiday_list = get_current_holiday_list(employee, date)

#     if not holiday_list:
#         holiday_list = frappe.db.get_value("Employee", employee, "holiday_list")

#     if not holiday_list:
#         return None

#     holiday = frappe.db.get_value(
#         "Holiday",
#         {
#             "parent": holiday_list,
#             "holiday_date": date
#         },
#         ["weekly_off", "custom_is_restricted_holiday"],
#         as_dict=True
#     )

#     if not holiday:
#         return None

#     if holiday.weekly_off:
#         return "Weekly Off"
#     elif holiday.custom_is_restricted_holiday:
#         return "Restricted Holiday"
#     else:
#         return "Holiday"

def get_holiday_type(employee, date):

    doj = frappe.db.get_value("Employee", employee, "date_of_joining")

    if doj:
        doj = getdate(doj)
        date = getdate(date)

    # ============================
    # HOLIDAY LIST
    # ============================
    holiday_list = get_current_holiday_list(employee, date)

    if not holiday_list:
        holiday_list = frappe.db.get_value("Employee", employee, "holiday_list")

    if not holiday_list:
        return None

    # ============================
    # FETCH HOLIDAY
    # ============================
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

    # ============================
    # WEEKLY OFF
    # ============================
    if holiday.weekly_off:
        return "Weekly Off"

    # ============================
    # 🔥 RESTRICTED HOLIDAY LOGIC
    # ============================
    if holiday.custom_is_restricted_holiday:

        pair_date = holiday.custom_restricted_holiday_date

        if doj and pair_date:
            pair_date = getdate(pair_date)

            # ✅ CONDITION: Pair crosses DOJ
            if (pair_date < doj <= date) or (date < doj <= pair_date):
                return "Holiday"

        if pair_date:
            pair_date_obj = getdate(pair_date)

            # Only apply this rule when the pair date is BEFORE current date
            # (i.e., the first RH already passed and employee was absent on it)
            if pair_date_obj < date:
                pair_att_status = frappe.db.get_value(
                    "Attendance",
                    {
                        "employee": employee,
                        "attendance_date": pair_date_obj,
                        "docstatus": ["!=", 2]
                    },
                    "status"
                )

                # If the paired RH attendance exists and was "Restricted Holiday"
                # (meaning employee was absent on that first RH),
                # then this second RH should become a plain Absent
                if pair_att_status == "Restricted Holiday":
                    return None  # None → caller treats as non-holiday → Absent + LWP

        # ❌ OTHERWISE KEEP RH
        return "Restricted Holiday"

    # ============================
    # NORMAL HOLIDAY
    # ============================
    return "Holiday"
# --------------------------------- Sandwich Leave Logic ---------------------------------

def get_approved_leave_on_date(employee, date):
    """
    Returns True if employee has a fully approved non-half-day
    leave application covering the given date.
    """
    return frappe.db.exists(
        "Leave Application",
        {
            "employee": employee,
            "status": "Approved",
            "leave_type": "Leave Without Pay",
            "docstatus": 1,
            "from_date": ("<=", date),
            "to_date": (">=", date),
            "half_day": 0
        }
    )


# def apply_sandwich_rule(employee, att_date):
#     """
#     Sandwich Rule:
#     If att_date is a Holiday / Weekly Off / Restricted Holiday,
#     AND the previous day AND the next day both have approved leave,
#     then att_date is also marked as 'On Leave' with LWP deducted.

#     Returns True if sandwich rule was applied.
#     """
#     # 1. Must be a holiday/weekoff
#     holiday_type = get_holiday_type(employee, att_date)
#     if not holiday_type:
#         return False

#     # 2. Both neighbours must be on approved leave
#     prev_date = add_days(att_date, -1)
#     next_date = add_days(att_date, 1)

#     if not get_approved_leave_on_date(employee, prev_date):
#         return False

#     if not get_approved_leave_on_date(employee, next_date):
#         return False

#     frappe.log_error(
#         "sandwich_rule_triggered",
#         f"Employee: {employee}, Date: {att_date}, Holiday: {holiday_type}"
#     )

#     # 3. Get shift
#     shift_type = get_employee_shift(employee, att_date)
#     if not shift_type:
#         frappe.log_error(
#             "sandwich_rule_no_shift",
#             f"Employee: {employee}, Date: {att_date} — shift not found, skipping."
#         )
#         return False

#     # 4. Get employee details
#     employee_details = frappe.db.get_value(
#         "Employee",
#         employee,
#         ["employee_name", "department", "company", "branch"],
#         as_dict=True
#     )

#     # 5. Check if attendance already exists
#     attendance_name = frappe.db.exists(
#         "Attendance",
#         {
#             "employee": employee,
#             "attendance_date": att_date,
#             "docstatus": ["!=", 2]
#         }
#     )

#     if attendance_name:
#         att_name = attendance_name
#         # Revert any existing penalty first (idempotent)
#         revert_penalty_leave(att_name)
#         frappe.db.set_value(
#             "Attendance",
#             att_name,
#             {
#                 "shift": shift_type,
#                 "status": "On Leave",
#                 "in_time": None,
#                 "out_time": None,
#                 "working_hours": 0,
#                 "late_entry": 0,
#                 "early_exit": 0,
#                 "custom_branch": employee_details.branch,
#                 "custom_remark": "Sandwich rule triggered - auto-marked as On Leave with LWP deduction",
#             },
#             update_modified=False
#         )
#     else:
#         att_name = frappe.generate_hash(length=12)
#         frappe.db.sql("""
#             INSERT INTO `tabAttendance`
#             (name, employee, employee_name, department, company,
#              attendance_date, shift, in_time, out_time,
#              working_hours, status, late_entry, early_exit, custom_branch,
#              docstatus, creation, modified, owner, modified_by, custom_remark)
#             VALUES (%s,%s,%s,%s,%s,
#                     %s,%s,%s,%s,%s,
#                     %s,%s,%s,%s,
#                     1, NOW(), NOW(), %s, %s)
#         """, (
#             att_name,
#             employee,
#             employee_details.employee_name,
#             employee_details.department,
#             employee_details.company,
#             att_date,
#             shift_type,
#             None, None, 0,
#             "On Leave",
#             0, 0,
#             employee_details.branch,
#             frappe.session.user,
#             frappe.session.user,
#             "Sandwich rule triggered - auto-marked as On Leave with LWP deduction"
#         ))
#         frappe.db.commit()

#     # 6. Always deduct LWP for sandwiched day
#     deduct_leave_by_priority(
#         employee=employee,
#         date=att_date,
#         status="Absent",   # full day = 1 day deduction
#         attendance=att_name,
#         force_lwp=True     # sandwiched holiday always = LWP
#     )

#     frappe.log_error(
#         "sandwich_rule_applied",
#         f"Employee: {employee}, Date: {att_date}, Att: {att_name}"
#     )
#     return True


def apply_sandwich_rule(employee, att_date):
    """
    Extended Sandwich Rule:

    If one or more consecutive Holiday / Weekly Off / Restricted Holiday
    exist between two approved LWP leaves,
    then all intermediate holidays become sandwich leave.
    """

    holiday_type = get_holiday_type(employee, att_date)

    if not holiday_type:
        return False

    # ------------------------------------------------------------------
    # Find LEFT boundary leave
    # ------------------------------------------------------------------

    left_date = add_days(att_date, -1)

    while get_holiday_type(employee, left_date):
        left_date = add_days(left_date, -1)

    left_leave = get_approved_leave_on_date(employee, left_date)

    # ------------------------------------------------------------------
    # Find RIGHT boundary leave
    # ------------------------------------------------------------------

    right_date = add_days(att_date, 1)

    while get_holiday_type(employee, right_date):
        right_date = add_days(right_date, 1)

    right_leave = get_approved_leave_on_date(employee, right_date)

    if not left_leave or not right_leave:
        return False

    # ------------------------------------------------------------------
    # Mark ALL in-between holidays as sandwich leave
    # ------------------------------------------------------------------

    current_date = left_date

    while current_date <= right_date:

        if get_holiday_type(employee, current_date):

            shift_type = get_employee_shift(employee, current_date)

            if not shift_type:
                current_date = add_days(current_date, 1)
                continue

            employee_details = frappe.db.get_value(
                "Employee",
                employee,
                ["employee_name", "department", "company", "branch"],
                as_dict=True
            )

            attendance_name = frappe.db.exists(
                "Attendance",
                {
                    "employee": employee,
                    "attendance_date": current_date,
                    "docstatus": ["!=", 2]
                }
            )

            if attendance_name:

                revert_penalty_leave(attendance_name)

                frappe.db.set_value(
                    "Attendance",
                    attendance_name,
                    {
                        "shift": shift_type,
                        "status": "On Leave",
                        "in_time": None,
                        "out_time": None,
                        "working_hours": 0,
                        "late_entry": 0,
                        "early_exit": 0,
                        "custom_branch": employee_details.branch,
                        "custom_remark": "Sandwich rule triggered - auto-marked as On Leave with LWP deduction",
                    },
                    update_modified=False
                )

                att_name = attendance_name

            else:

                att_name = frappe.generate_hash(length=12)

                frappe.db.sql("""
                    INSERT INTO `tabAttendance`
                    (
                        name,
                        employee,
                        employee_name,
                        department,
                        company,
                        attendance_date,
                        shift,
                        in_time,
                        out_time,
                        working_hours,
                        status,
                        late_entry,
                        early_exit,
                        custom_branch,
                        docstatus,
                        creation,
                        modified,
                        owner,
                        modified_by,
                        custom_remark
                    )
                    VALUES
                    (
                        %s,%s,%s,%s,%s,
                        %s,%s,%s,%s,%s,
                        %s,%s,%s,%s,
                        1,NOW(),NOW(),%s,%s,%s
                    )
                """, (
                    att_name,
                    employee,
                    employee_details.employee_name,
                    employee_details.department,
                    employee_details.company,
                    current_date,
                    shift_type,
                    None,
                    None,
                    0,
                    "On Leave",
                    0,
                    0,
                    employee_details.branch,
                    frappe.session.user,
                    frappe.session.user,
                    "Sandwich rule triggered - auto-marked as On Leave with LWP deduction"
                ))

            deduct_leave_by_priority(
                employee=employee,
                date=current_date,
                status="Absent",
                attendance=att_name,
                force_lwp=True
            )

            frappe.log_error(
                "sandwich_rule_applied",
                f"Employee: {employee}, Date: {current_date}"
            )

        current_date = add_days(current_date, 1)

    frappe.db.commit()

    return True


def on_leave_application_approved(doc, method):
    """
    Fired on Leave Application on_submit / on_update_after_submit.
    Retroactively applies sandwich rule if this new leave
    completes a sandwich around an already-processed holiday.
    """
    if doc.status != "Approved":
        return

    if doc.half_day:
        return  # Half day leaves cannot create a sandwich

    # The two candidate dates that could now be sandwiched:
    # 1. The day just BEFORE this leave starts
    #    (holiday sitting between an older leave and this new one)
    # 2. The day just AFTER this leave ends
    #    (holiday sitting between this new leave and an older one)
    candidates = [
        add_days(getdate(doc.from_date), -1),
        add_days(getdate(doc.to_date), 1)
    ]

    for candidate_date in candidates:
        try:
            holiday_type = get_holiday_type(doc.employee, candidate_date)
            if not holiday_type:
                continue  # Not a holiday, skip

            sandwiched = apply_sandwich_rule(doc.employee, candidate_date)

            if sandwiched:
                frappe.log_error(
                    "sandwich_rule_retro_applied",
                    f"Employee: {doc.employee}, "
                    f"Sandwiched date: {candidate_date}, "
                    f"Triggered by Leave: {doc.name}"
                )

        except Exception:
            frappe.log_error(
                f"sandwich_retro_error_{doc.employee}_{candidate_date}",
                frappe.get_traceback()
            )