import frappe
from frappe.utils import getdate, today,add_days,now_datetime
from datetime import date,datetime
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
from frappe.utils import get_datetime
from datetime import datetime, time


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
    is_seven_hours_period = False
    
    if today_date >= oct_start_sri:
        is_seven_hours_period = True

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
    
    emp_filters["branch"] = "Jammu"
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
    
    
def create_shift_assignment_rec(emp_id, from_date, to_date, shift_type_id):
    
    doc = frappe.get_doc({
                    "doctype": "Shift Assignment",
                    "employee": emp_id,
                    # "employee_name": emp_display
                    "shift_type": shift_type_id,
                    "start_date": from_date,
                    "end_date": to_date,
                })  

                # If Shift Assignment doctype requires additional fields (company etc.)
                # set them here. Example:
                # doc.company = frappe.db.get_single_value("Global Defaults", "default_company")


    doc.insert(ignore_permissions=True)
    doc.submit()    
    frappe.db.commit()

# =========================================================
# MAIN SCHEDULER METHOD
# =========================================================

def run_daily_attendance():
    yesterday = add_days(getdate(), -1)

    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        pluck="name"
    )

    for emp in employees:
        try:
            # 1️⃣ Approved leave
            if has_approved_leave(emp, yesterday):
                continue

            # 2️⃣ Shift required
            shift_type = get_employee_shift(emp, yesterday)
            if not shift_type:
                log_attendance_error(emp, yesterday, "Shift not assigned")
                continue

            shift_custom_type = frappe.db.get_value(
                "Shift Type", shift_type, "custom_shift_type"
            )

            # 3️⃣ Holiday / Week off
            is_holiday = is_holiday_or_weekoff(emp, yesterday)

            # ==========================
            # 🕒 24 HOURS SHIFT LOGIC
            # ==========================
            if shift_custom_type == "24 Hours":
                working_hours, in_time, out_time = get_24_hour_working_hours(
                    emp, yesterday
                )

                if working_hours == 0:
                    if is_holiday:
                        continue
                    create_or_update_attendance(
                        emp, yesterday, None, None, 0
                    )
                    continue

                create_or_update_attendance(
                    emp, yesterday, in_time, out_time, working_hours
                )
                continue

            # ==========================
            # 🕘 NORMAL SHIFT LOGIC
            # ==========================
            logs = frappe.db.sql("""
                SELECT
                    MIN(time) AS in_time,
                    MAX(time) AS out_time,
                    COUNT(*) AS punches
                FROM `tabEmployee Checkin`
                WHERE employee=%s AND DATE(time)=%s
            """, (emp, yesterday), as_dict=True)[0]

            if not logs or not logs["in_time"]:
                if is_holiday:
                    continue
                create_or_update_attendance(
                    emp, yesterday, None, None, 0
                )
                continue

            if logs["punches"] == 1:
                handle_missing_checkout(
                    emp, yesterday, logs["in_time"], shift_type
                )
                continue

            in_time = logs["in_time"]
            out_time = logs["out_time"]
            working_hours = (out_time - in_time).total_seconds() / 3600

            create_or_update_attendance(
                emp, yesterday, in_time, out_time, working_hours
            )

        except Exception as e:
            log_attendance_error(
                emp, yesterday, "Main Scheduler Failed", e
            )

    frappe.db.commit()

def get_24_hour_working_hours(employee, date):
    logs = frappe.db.sql("""
        SELECT time
        FROM `tabEmployee Checkin`
        WHERE employee=%s
          AND time BETWEEN %s AND %s
        ORDER BY time ASC
    """, (
        employee,
        f"{date} 00:00:00",
        f"{date} 23:59:59"
    ), as_dict=True)

    if not logs or len(logs) < 2:
        return 0, None, None

    total_seconds = 0
    first_in = None
    last_out = None

    for i in range(0, len(logs) - 1, 2):
        in_time = logs[i].time
        out_time = logs[i + 1].time

        if not first_in:
            first_in = in_time

        last_out = out_time
        total_seconds += (out_time - in_time).total_seconds()

    return total_seconds / 3600, first_in, last_out


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
                employee, date, in_time, None, 0
            )
            return

        working_hours = (out_time - in_time).total_seconds() / 3600

        create_or_update_attendance(
            employee, date, in_time, out_time, working_hours
        )

    except Exception as e:
        log_attendance_error(
            employee, date, "Missing Checkout Failed", e
        )



# =========================================================
# ATTENDANCE CREATE / UPDATE (SAFE)
# =========================================================

def create_or_update_attendance(employee, date, in_time, out_time, working_hours):
    try:
        shift_type = get_employee_shift(employee, date)
        if not shift_type:
            return

        shift = frappe.db.get_value(
            "Shift Type",
            shift_type,
            [
                "working_hours_threshold_for_half_day",
                "working_hours_threshold_for_absent"
            ],
            as_dict=True
        )

        half_day = float(shift.working_hours_threshold_for_half_day or 8)
        absent = float(shift.working_hours_threshold_for_absent or 3)

        if working_hours <= absent:
            status = "Absent"
        elif working_hours < half_day:
            status = "Half Day"
        else:
            status = "Present"

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

        if status in ["Absent", "Half Day"]:
            deduct_leave_by_priority(employee, date, status, att.name)

        return att.name

    except Exception as e:
        log_attendance_error(
            employee, date, "Attendance Save Failed", e
        )


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

    for leave_type in priority:
        if leave_type != "Leave Without Pay":
            balance = get_leave_balance_on(
                employee, leave_type, date
            )
            if balance < leave_days:
                continue

        create_leave_ledger(
            employee, leave_type, date, status, attendance
        )
        break




def get_leave_balance(employee, leave_type, date):
    try:
        return frappe.get_value(
            "Leave Ledger Entry",
            {"employee": employee, "leave_type": leave_type},
            "sum(leaves)"
        ) or 0
    except Exception:
        return 0


# =========================================================
# LEAVE LEDGER ENTRY
# =========================================================

def create_leave_ledger(employee, leave_type, date, status, attendance):
    if frappe.db.exists(
        "Leave Ledger Entry",
        {
            "employee": employee,
            "from_date": date,
            "transaction_name": attendance
        }
    ):
        return

    leave_days = 0.5 if status == "Half Day" else 1

    doc = frappe.get_doc({
        "doctype": "Leave Ledger Entry",
        "employee": employee,
        "leave_type": leave_type,
        "posting_date": date,
        "from_date": date,
        "to_date": date,
        "leaves": -leave_days,
        "transaction_type": "Attendance",
        "transaction_name": attendance
    })

    doc.insert(ignore_permissions=True)
    doc.submit()



# =========================================================
# SHIFT HELPERS
# =========================================================

def get_employee_shift(employee, date):
    shift = frappe.db.get_value(
        "Shift Assignment",
        {
            "employee": employee,
            "start_date": ("<=", date),
            "end_date": (">=", date),
            "status": "Active"
        },
        "shift_type"
    )

    if shift:
        return shift

    return frappe.db.get_value(
        "Employee", employee, "default_shift"
    )

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
