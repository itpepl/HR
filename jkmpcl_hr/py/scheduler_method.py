import frappe
from frappe.utils import getdate, today,add_days,now_datetime
from datetime import date,datetime
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

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

    emp_filters["branch"] = "Srinagar"
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



#Auto Attendance Marking Script
def run_daily_attendance():
    yesterday = add_days(getdate(), -1)
    employees = frappe.get_all("Employee", filters={"status": "Active"}, pluck="name")

    for emp in employees:
        if has_approved_leave(emp, yesterday):
            continue

        logs = frappe.db.sql("""
            SELECT
                MIN(time) AS in_time,
                MAX(time) AS out_time,
                COUNT(*) AS punches
            FROM `tabEmployee Checkin`
            WHERE employee = %s
            AND DATE(time) = %s
        """, (emp, yesterday), as_dict=True)[0]

        # No punches → Absent
        if not logs or not logs.in_time:
            create_or_update_attendance(emp, yesterday, None, None, 0)
            continue

        # Only 1 punch → missing checkout
        if logs.punches == 1:
            handle_missing_checkout(emp, yesterday, logs.in_time)
            continue

        # Multiple punches → calculate working hours
        in_time = logs.in_time
        out_time = logs.out_time

        working_hours = (out_time - in_time).total_seconds() / 3600

        create_or_update_attendance(
            emp,
            yesterday,
            in_time,
            out_time,
            working_hours
        )



        if not logs or not logs["in_time"]:
            create_or_update_attendance(emp, yesterday, None, None, 0)
            continue

        if logs["punches"] == 1:
            handle_missing_checkout(emp, yesterday, logs["in_time"])
            continue


        in_time = logs["in_time"]
        out_time = logs["out_time"]


        working_hours = (out_time - in_time).total_seconds() / 3600

        create_or_update_attendance(
            emp, yesterday,
            in_time, out_time,
            working_hours
        )

    frappe.db.commit()
    
def has_approved_leave(employee, date):
    leave = frappe.db.exists("Leave Application", {
        "employee": employee,
        "status": "Approved",
        "from_date": ("<=", date),
        "to_date": (">=", date)
    })
    return leave

def handle_missing_checkout(employee, date, in_time):

    working_hours = 0
    status = "Absent"

    attendance_name = create_or_update_attendance(employee, date, in_time, None, working_hours)
    deduct_leave_by_priority(employee, date, status,attendance_name)


def deduct_leave_by_priority(employee, date, status,attendance=None):

    leave_priority = [
        "Casual Leave",
        "Sick Leave",
        "Privilege Leave",
        "Leave Without Pay"
    ]
    leave_days = 0.5 if status == "Half Day" else 1
    for leave_type in leave_priority:

        balance = get_leave_balance(employee, leave_type, date)

        if balance >= leave_days or leave_type == "Leave Without Pay":
            
            create_leave_ledger(employee, leave_type, date, status,attendance)
            break



def get_leave_balance(employee, leave_type, date):
    try:
        balance = get_leave_balance_on(employee, leave_type, date)
        return balance or 0
    except:
        return 0
    
    
    
def create_or_update_attendance(employee, date, in_time, out_time, working_hours):

    shift_type = frappe.db.get_value("Employee", employee, "default_shift")
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

    half_day_threshold = float(shift.working_hours_threshold_for_half_day or 8)
    absent_threshold = float(shift.working_hours_threshold_for_absent or 3)
        # Create leave ledger if Absent or Half Day


    if working_hours == 0:
        status = "Absent"

    elif working_hours <= absent_threshold:
        status = "Absent"

    elif working_hours < half_day_threshold:
        status = "Half Day"

    else:
        status = "Present"

    attendance_name = frappe.db.exists("Attendance", {
        "employee": employee,
        "attendance_date": date,
        "docstatus": ["!=", 2]
    })

    if attendance_name:
        att = frappe.get_doc("Attendance", attendance_name)
        att.in_time = in_time
        att.out_time = out_time
        att.working_hours = working_hours
        att.status = status
        att.save(ignore_permissions=True)
        if att.docstatus == 0:
            att.submit()
        return

    attendance = frappe.get_doc({
        "doctype": "Attendance",
        "employee": employee,
        "attendance_date": date,
        "shift": shift_type,
        "in_time": in_time,
        "out_time": out_time,
        "working_hours": working_hours,
      
        "status": status    
    })
    if status in ["Absent", "Half Day"]:

        leave_type = get_employee_leave_type(employee)
        if leave_type:
            create_leave_ledger(employee, leave_type, date, status)
    attendance.insert(ignore_permissions=True)
    attendance.submit()



def get_employee_leave_type(employee):
    policy = frappe.db.get_value("Leave Policy Assignment", {
        "employee": employee,
        "docstatus": 1
    }, "leave_policy")

    if not policy:
        return None

    leave_type = frappe.db.get_value("Leave Policy Detail", {
        "parent": policy
    }, "leave_type")

    return leave_type

def create_leave_ledger(employee, leave_type, date, status,attendance):
    if not leave_type:
        return

    # Prevent duplicate leave entry
    already = frappe.db.exists("Leave Ledger Entry", {
        "employee": employee,
        "leave_type": leave_type,
        "from_date": date
    })
    if already:
        return

    # Half day will deduct 0.5
    leave_days = 0.5 if status == "Half Day" else 1
    doc = frappe.get_doc({
        "doctype": "Leave Ledger Entry",
        "employee": employee,
        "leave_type": leave_type,
        "posting_date": date,
        "from_date": date,
        "to_date": date,
        "leave_allocation": None,
        "leaves": -abs(leave_days),
        "transaction_type": "Attendance",
        "transaction_name":attendance,
    })

    doc.insert(ignore_permissions=True)
    doc.submit()
    
