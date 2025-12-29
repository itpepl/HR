import frappe
from frappe.utils import getdate, today,add_days,now_datetime,add_to_date
from datetime import date,datetime
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
from frappe.utils import get_datetime
from datetime import datetime, time,timedelta


from jkmpcl_hr.py.utils import create_shift_assignment_rec

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
    emp_list = frappe.db.get_list("Employee", filters=emp_filters, fields=["name", "default_shift"])
        
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
                seven_hours_shift_id = default_shift
                eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
                            
            elif emp_default_shift_details[0].get("custom_hours") == "8hours":
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
    mar_end_date = getdate(f"{start_year+1}-03-31")
    
    # nov_end_jammu = date(start_year, 11, 30)
    # dec_start_jammu = date(start_year, 12, 1)
    # jan_end_jammu = date(start_year + 1, 1, 31)
    
    nov_end_jammu = getdate(f"{start_year}-11-30")
    dec_start_jammu = getdate(f"{start_year}-12-01")
    jan_end_jammu = getdate(f"{start_year+1}-01-31")
    feb_start_jammu = getdate(f"{start_year+1}-02-01")
    
    emp_filters["branch"] = "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu"
    emp_list = frappe.db.get_list("Employee", filters=emp_filters, fields=["name", "default_shift", "gender"])
    
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
            
            if emp.get("gender") == "Female":
            
                eight_hours_sa_exists_first = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", apr_start_date], "end_date":[">=", nov_end_jammu]}, limit=1)
                seven_hours_sa_exists = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", dec_start_jammu], "end_date":[">=", jan_end_jammu]}, limit=1)
                eight_hours_sa_exists_second = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", feb_start_jammu], "end_date":[">=", mar_end_date]}, limit=1)
                
                
                if emp_default_shift_details[0].get("custom_hours") == "7hours":
                    seven_hours_shift_id = default_shift
                    eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
                                
                elif emp_default_shift_details[0].get("custom_hours") == "8hours":
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
                    eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
                                
                elif emp_default_shift_details[0].get("custom_hours") == "8hours":
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
@frappe.whitelist()
def run_attendance_from_to(from_date,to_date):
    if not from_date or not to_date:
        frappe.throw("From Date and To Date are required")
    from_date = getdate(from_date)
    to_date = getdate(to_date)

    current_date = from_date

    while current_date <= to_date:
        run_daily_attendance(current_date)
        current_date = add_days(current_date, 1)

    return {
        "status": "success",
        "message": f"Attendance processed from {from_date} to {to_date}"
    }



def run_daily_attendance(att_date=None):    
    if not att_date:
        att_date = add_days(getdate(), -1)
    else:
        att_date = getdate(att_date)

    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        pluck="name"
    )

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

            # ==========================
            # ==========================
            if shift_custom_type == "24 Hours":
                first_in, last_out, checkin_id= get_24_hour_working_hours(
                    emp, att_date
                )
                if not first_in:
                    create_or_update_attendance(
                        emp,
                        att_date,
                        None,
                        None,
                        0,
                        None,
                        skip_shift_time_rules=True,
                        is_24_hour_shift=True
                    )
                else:
                    create_or_update_attendance(
                        emp,
                        att_date,
                        first_in,
                        last_out,
                        0,                    # 👈 NO working hours
                        checkin_id,
                        skip_shift_time_rules=True,
                        is_24_hour_shift=True
                    )

            # ==========================
            # ==========================
            # logs = frappe.db.sql("""
            #     SELECT
            #         MIN(time) AS in_time,
            #         MAX(time) AS out_time,
            #         COUNT(*) AS punches
            #     FROM `tabEmployee Checkin`
            #     WHERE employee=%s AND DATE(time)=%s
            # """, (emp, att_date), as_dict=True)[0]

            # if not logs or not logs["in_time"]:
            #     if is_holiday:
            #         continue
            #     create_or_update_attendance(
            #         emp, att_date, None, None, 0
            #     )
            #     continue

            # if logs["punches"] == 1:
            #     handle_missing_checkout(
            #         emp, att_date, logs["in_time"], shift_type
            #     )
            #     continue

            # in_time = logs["in_time"]
            # out_time = logs["out_time"]
            # working_hours = (out_time - in_time).total_seconds() / 3600

            # create_or_update_attendance(
            #     emp, att_date, in_time, out_time, working_hours
            # )
            logs = frappe.db.sql("""
                SELECT
                    name,
                    time
                FROM `tabEmployee Checkin`
                WHERE employee=%s
                AND DATE(time)=%s
                ORDER BY time ASC
            """, (emp, att_date), as_dict=True)

            if not logs:
                if is_holiday:
                    continue
                create_or_update_attendance(
                    emp, att_date, None, None, 0, None,skip_shift_time_rules=False
                )
                continue

            if len(logs) < 2:
                if is_holiday:
                    continue
                create_or_update_attendance(
                    emp, att_date, None, None, 0, logs[-1]["name"],skip_shift_time_rules=False
                )
                continue

            in_time = logs[0]["time"]
            out_time = logs[-1]["time"]
            working_hours = (out_time - in_time).total_seconds() / 3600

            if working_hours <= 0:
                create_or_update_attendance(
                    emp, att_date, None, None, 0, logs[-1]["name"],skip_shift_time_rules=False
                )
                continue

            create_or_update_attendance(
                emp,
                att_date,
                in_time,
                out_time,
                working_hours,
                logs[-1]["name"] ,skip_shift_time_rules=False  # ✅ MAX CHECKIN ID
            )

        except Exception as e:
            log_attendance_error(
                emp, att_date, "Main Scheduler Failed", e
            )

    frappe.db.commit()
def get_24_hour_working_hours(employee, date):
    logs = frappe.db.sql("""
        SELECT name, time
        FROM `tabEmployee Checkin`
        WHERE employee=%s
          AND DATE(time)=%s
        ORDER BY time ASC
    """, (employee, date), as_dict=True)

    # ❌ No logs or single log
    if not logs or len(logs) < 2:
        return None, None, None

    first_in = logs[0]["time"]     # ✅ First punch
    last_out = logs[-1]["time"]    # ✅ Last punch
    last_checkin_id = logs[-1]["name"]

    return first_in, last_out, last_checkin_id


# =========================================================
# LEAVE CHECK
# =========================================================

def has_approved_leave(employee, date):
    return frappe.db.exists(
        "Leave Application",
        {
            "employee": employee,
            "status": "Approved",
            "from_date": ("<=", date),
            "to_date": (">=", date)
        }
    )



# =========================================================
# HOLIDAY / WEEK OFF
# =========================================================

def is_holiday_or_weekoff(employee, date):
    holiday_list = frappe.db.get_value(
        "Employee", employee, "holiday_list"
    )

    if not holiday_list:
        log_attendance_error(
            employee, date, "Holiday list not set"
        )
        return False

    return frappe.db.exists(
        "Holiday",
        {
            "parent": holiday_list,
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



# =========================================================
# ATTENDANCE CREATE / UPDATE (SAFE)
# =========================================================

# def create_or_update_attendance(employee, date, in_time, out_time, working_hours):
#     try:
#         shift_type = get_employee_shift(employee, date)
#         if not shift_type:
#             return

#         shift = frappe.db.get_value(
#             "Shift Type",
#             shift_type,
#             [
#                 "working_hours_threshold_for_half_day",
#                 "working_hours_threshold_for_absent"
#             ],
#             as_dict=True
#         )

#         half_day = float(shift.working_hours_threshold_for_half_day or 8)
#         absent = float(shift.working_hours_threshold_for_absent or 3)

#         if working_hours <= absent:
#             status = "Absent"
#         elif working_hours < half_day:
#             status = "Half Day"
#         else:
#             status = "Present"

#         attendance_name = frappe.db.exists(
#             "Attendance",
#             {
#                 "employee": employee,
#                 "attendance_date": date,
#                 "docstatus": ["!=", 2]
#             }
#         )

#         if attendance_name:
#             att = frappe.get_doc("Attendance", attendance_name)
#             if att.docstatus == 1:
#                 return att.name

#             att.update({
#                 "in_time": in_time,
#                 "out_time": out_time,
#                 "working_hours": working_hours,
#                 "status": status
#             })
#             att.save(ignore_permissions=True)
#             att.submit()
#         else:
#             att = frappe.get_doc({
#                 "doctype": "Attendance",
#                 "employee": employee,
#                 "attendance_date": date,
#                 "shift": shift_type,
#                 "in_time": in_time,
#                 "out_time": out_time,
#                 "working_hours": working_hours,
#                 "status": status
#             })
#             att.insert(ignore_permissions=True)
#             att.submit()

#         if status in ["Absent", "Half Day"]:
#             deduct_leave_by_priority(employee, date, status, att.name)

#         return att.name

#     except Exception as e:
#         log_attendance_error(
#             employee, date, "Attendance Save Failed", e
#         )

def create_or_update_attendance(employee, date, in_time, out_time, working_hours,checkin_id=None,skip_shift_time_rules=True):
    try:
        shift_type = get_employee_shift(employee, date)
        if not shift_type:
            return
        shift = frappe.db.get_value(
            "Shift Type",
            shift_type,
            [
                "start_time",
                "end_time",
                "begin_check_in_before_shift_start_time",
                "allow_check_out_after_shift_end_time",
                "working_hours_threshold_for_half_day",
                "working_hours_threshold_for_absent"
            ],
            as_dict=True
        )
        

        half_day_hours = float(shift.working_hours_threshold_for_half_day or 8)
        absent_hours = float(shift.working_hours_threshold_for_absent or 3)

        if working_hours <= absent_hours:
            status = "Absent"
        elif working_hours < half_day_hours:
            status = "Half Day"
        else:
            status = "Present"
        if in_time and out_time and not skip_shift_time_rules:
            print(in_time,out_time,skip_shift_time_rules)
            shift_start = combine_datetime(date, shift.start_time)
            shift_end = combine_datetime(date, shift.end_time)

            allowed_late_minutes = shift.begin_check_in_before_shift_start_time

            allowed_late_minutes = shift.begin_check_in_before_shift_start_time

            if allowed_late_minutes and int(allowed_late_minutes) > 0:
                latest_allowed_in = add_to_date(
                    shift_start, minutes=int(allowed_late_minutes)
                )

                if in_time > latest_allowed_in:
                    status = "Half Day"


        # if in_time and out_time:
        #     shift_start = combine_datetime(date, shift.start_time)
        #     shift_end = combine_datetime(date, shift.end_time)

        #     allowed_late_minutes = int(
        #         shift.begin_check_in_before_shift_start_time or 0
        #     )
        #     allowed_early_minutes = int(
        #         shift.allow_check_out_after_shift_end_time or 0
        #     )

        #     latest_allowed_in = add_to_date(
        #         shift_start, minutes=allowed_late_minutes
        #     )

        #     earliest_allowed_out = add_to_date(
        #         shift_end, minutes=-allowed_early_minutes
        #     )

        #     if in_time > latest_allowed_in:
        #         status = "Half Day"

            # if out_time < earliest_allowed_out:
            #     status = "Half Day"


        attendance_name = frappe.db.exists(
            "Attendance",
            {
                "employee": employee,
                "attendance_date": date,
                "docstatus": ["!=", 2]
            }
        )

        if attendance_name:
            att = frappe.get_doc("Attendance", attendance_name)
            if att.docstatus == 1:
                return att.name

            att.update({
                "in_time": in_time,
                "out_time": out_time,
                "working_hours": working_hours,
                "status": status
            })
            att.save(ignore_permissions=True)
            att.submit()
        else:
            att = frappe.get_doc({
                "doctype": "Attendance",
                "employee": employee,
                "attendance_date": date,
                "shift": shift_type,
                "in_time": in_time,
                "out_time": out_time,
                "working_hours": working_hours,
                "status": status
            })
            att.insert(ignore_permissions=True)
            att.submit()

        emp_checkin=frappe.get_doc("Employee Checkin",checkin_id)
        emp_checkin.attendance=att.name
        emp_checkin.save()
        if status in ["Absent", "Half Day"]:
            deduct_leave_by_priority(employee, date, status, att.name)

        return att.name

    except Exception as e:
        log_attendance_error(
            employee, date, "Attendance Save Failed", e
        )

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
# =========================================================
# LEAVE DEDUCTION
# =========================================================
def deduct_leave_by_priority(employee, date, status, attendance):
    priority = [
        "Casual Leave",
        "Sick Leave",
        "Privilege Leave",
        "Leave Without Pay"
    ]

    leave_days = 0.5 if status == "Half Day" else 1
    att = frappe.get_doc("Attendance", attendance)
    for leave_type in priority:
        leave_type_doc = frappe.get_cached_doc("Leave Type", leave_type)

        if leave_type_doc.is_lwp:
            continue

        balance = get_leave_balance_on(employee, leave_type, date)

        if balance < leave_days:
            continue

        att.db_set({
            "custom_penalty_leave_type": leave_type,
            "custom_penalty_leave_count": leave_days,
            "custom_is_penalize": 1
        })

        create_leave_ledger(
            employee, leave_type, date, status, attendance
        )

        return  


    lwp_type = next(
        (lt for lt in priority
         if frappe.get_cached_doc("Leave Type", lt).is_lwp),
        None
    )

    if lwp_type:
        att.db_set({
            "custom_penalty_leave_type": lwp_type,
            "custom_penalty_leave_count": leave_days,
            "custom_is_penalize": 1
        })



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

def create_leave_ledger(employee, leave_type, date, status, attendance):
    employee_doc = frappe.get_cached_doc("Employee", employee)
    leave_type_doc = frappe.get_cached_doc("Leave Type", leave_type)

    if leave_type_doc.is_lwp:
        return

    leave_days = 0.5 if status == "Half Day" else 1
    allocation = get_leave_allocation(employee, leave_type, date)

    if not allocation:
        return

    if frappe.db.exists(
        "Leave Ledger Entry",
        {
            "employee": employee,
            "from_date": date,
            "transaction_type": "Leave Allocation",
            "transaction_name": allocation,
            "custom_is_panalty": 1
        }
    ):
        return

    doc = frappe.get_doc({
        "doctype": "Leave Ledger Entry",
        "employee": employee,
        "employee_name": employee_doc.employee_name,
        "company": employee_doc.company,
        "holiday_list": employee_doc.holiday_list,

        "leave_type": leave_type,
        "posting_date": date,
        "from_date": date,
        "to_date": date,

        "leaves": -leave_days,
        "is_lwp": 0,
        "custom_is_panalty": 1,

        "transaction_type": "Leave Allocation",
        "transaction_name": allocation
    })

    doc.insert(ignore_permissions=True)
    doc.submit()



# =========================================================
# SHIFT HELPERS
# =========================================================

def get_required_hours_by_date(date):
    date = getdate(date)
    return 8 if 4 <= date.month <= 9 else 7

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

    default_shift = frappe.db.get_value(
        "Employee", employee, "default_shift"
    )

    if not default_shift:
        return None

    shift_type = frappe.db.get_value(
        "Shift Type", default_shift, "custom_shift_type"
    )

    if not shift_type:
        return default_shift

    required_hours = get_required_hours_by_date(date)

    branch = frappe.db.get_value("Employee", employee, "branch")

    shift = frappe.db.get_value(
        "Shift Type",
        {
            "branch": branch,
            "shift_type": shift_type,        # General / 24 hours
            "hours": f"{required_hours}hours"
        },
        "name"
    )

    if shift:
        return shift

    return default_shift

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

def process_comp_off_scheduler():
    """
    Runs daily.
    Checks only YESTERDAY.
    """
    yesterday = add_days(getdate(), -1)

    requests = frappe.get_all(
        "Off-Day Work Request",
        filters={
            "workflow_state": "Approved",
            "date": yesterday,
            "docstatus": 1,
            "comp_off_created": 0
        },
        fields=["name", "employee", "date"]
    )

    for req in requests:
        
        try:
            process_working_day(req)
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Comp-Off Scheduler Error - {req.name}"
            )


# =========================================================
# PROCESS SINGLE REQUEST
# =========================================================


def process_working_day(req):
    """
    Main entry point per Off-Day Working Request
    """

    attendance = get_attendance(req["employee"], req["date"])
    if not attendance:
        return

    holiday = get_holiday_details(req["employee"], req["date"])
    if not holiday:
        return

    # WO OR Normal Holiday OR RH+WO
    if holiday["is_wo"] or not holiday["is_rh"]:
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
        return

    leave_type = frappe.db.get_value(
        "Leave Type",
        {
            "is_compensatory": 1
        },
        "custom_validity_days"
    )   
    validity_days = leave_type if leave_type else 45

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

