import frappe
from calendar import monthrange
from frappe.utils import getdate, today,add_days,now_datetime, get_last_day, get_first_day, add_months, month_diff, flt
from jkmpcl_hr.py.utils import get_emp_reporting_manager
from frappe import _
# import calendar
from datetime import date,datetime
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

from jkmpcl_hr.py.utils import create_shift_assignment_rec
from calendar import monthrange
from frappe.utils import getdate




def on_update(doc, event):
    # pass
    update_cl_and_sl_after_confirmation(doc)
    # set_approvers(doc)

def validate(doc, event):
    set_approvers(doc)

    current_date = getdate(today())

    doj = doc.date_of_joining
    from_date = doc.custom_suspended_from_date
    to_date = doc.custom_suspended_to_date

    # =====================================================
    # ✅ NEW VALIDATION (DOJ CHECK)
    # =====================================================
    if doj and from_date:
        doj = getdate(doj)
        from_date = getdate(from_date)

        if from_date < doj:
            frappe.throw(
                f"Suspension From Date ({from_date}) cannot be before Date of Joining ({doj})."
            )

    # =====================================================
    # ✅ OPTIONAL: TO DATE VALIDATION
    # =====================================================

    if from_date and to_date:
        to_date = getdate(to_date)

        if to_date < from_date:
            frappe.throw(
                "Suspension To Date cannot be before Suspension From Date."
            )

    # -------------------------------------------------
    # STATUS LOGIC
    # -------------------------------------------------
    if from_date:
        from_date = getdate(from_date)
        to_date = to_date and getdate(to_date)

        if current_date < from_date:
            doc.status = "Active"
        else:
            if not to_date:
                doc.status = "Suspended"
            elif current_date <= to_date:
                doc.status = "Suspended"
            else:
                doc.status = "Active"

    # -------------------------------------------------
    # HANDLE LOG
    # -------------------------------------------------
    if doc.custom_suspended_from_date:
        handle_suspension_log(doc)

    # -------------------------------------------------
    # HQ Type Handle Function
    # -------------------------------------------------    
    
    validate_geofence_settings(doc)

def validate_geofence_settings(doc):

    # Geofence is enabled -> HQ Type is mandatory
    if not doc.custom_head_quarter_type:
        frappe.throw(_("Please select Head Quarter Type."))

    # Plant / MCC / BMC -> Warehouse is mandatory
    if doc.custom_head_quarter_type in ("Plant", "MCC", "BMC"):
        if not doc.custom_warehouse:
            frappe.throw(_("Please select Warehouse."))
        doc.custom_supplier = None

    # MPP -> Supplier is mandatory
    elif doc.custom_head_quarter_type == "MPP":
        if not doc.custom_supplier:
            frappe.throw(_("Please select Supplier."))
        doc.custom_warehouse = None


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

        elif existing_log.to_date:
            create_new_log(doc)

    else:
        create_new_log(doc)


# =====================================================
# CREATE NEW LOG
# ==========================jkmpcl_hr/py/scheduler_method.py===========================
def create_new_log(doc):

    log = frappe.new_doc("Suspended Employee Log")

    log.employee = doc.name
    log.posting_date = today()
    log.from_date = doc.custom_suspended_from_date
    log.to_date = doc.custom_suspended_to_date

    log.insert(ignore_permissions=True)


def set_approvers(doc):
    try:
        # if doc.name:
        #     actual_emp_rm = get_emp_reporting_manager(doc.name)
        #     if actual_emp_rm:
        #         emp_rm_emp = frappe.db.get_value("Employee", {"user_id": actual_emp_rm}, "name") if actual_emp_rm else None
        #         if doc.shift_request_approver != actual_emp_rm:
        #             frappejkmpcl_hr/py/scheduler_method.py.db.set_value("Employee", doc.name, "shift_request_approver", actual_emp_rm)
        #         if doc.leave_approver != actual_emp_rm:
        #             frappe.db.set_value("Employee", doc.name, "leave_approver", actual_emp_rm)
        #         if emp_rm_emp and doc.reports_to != emp_rm_emp:
        #             frappe.db.set_value("Employee", doc.name, "reports_to", emp_rm_emp)
        
        if not doc.custom_reporting_manager:
            return
        
        current_rm = ""
        current_rm_user = ""
        
        for row in doc.custom_reporting_manager:        
            if row.effective_from and getdate(row.effective_from) <= getdate(today()):
                current_rm = row.employee
        
        if current_rm and current_rm != doc.name:
                        
            if doc.reports_to != current_rm:
                doc.reports_to = current_rm
            current_rm_user = frappe.db.get_value("Employee", current_rm, "user_id") or ''
            if current_rm_user:
                if doc.shift_request_approver != current_rm_user:
                    doc.shift_request_approver = current_rm_user
                    
                if doc.leave_approver != current_rm_user:
                    doc.leave_approver = current_rm_user
                
                if doc.expense_approver != current_rm_user:
                    doc.expense_approver = current_rm_user
            
    except Exception as e:
        frappe.log_error("error_set_approvers_on_employee_update", frappe.get_traceback())
        
            
            

def after_insert(doc, event):

    allocate_cl_on_employee_creation(doc)
    auto_create_shift_assignment(doc)


# =========================================================
# AUTO CREATE SHIFT ASSIGNMENT
# =========================================================

from datetime import timedelta
from frappe.utils import getdate, cint


def auto_create_shift_assignment(doc, method=None):

    try:

        if not doc.default_shift:
            frappe.log_error(
                "Default Shift not found on Employee",
                "Shift Assignment Debug"
            )
            return

        if not doc.branch:
            frappe.log_error(
                "Branch not found on Employee",
                "Shift Assignment Debug"
            )
            return

        if not doc.date_of_joining:
            frappe.log_error(
                "Date Of Joining not found on Employee",
                "Shift Assignment Debug"
            )
            return

        attendance_source = doc.custom_attendance_source or ""
        is_female = doc.gender == "Female"
        joining_date = getdate(doc.date_of_joining)

        branch_doc = frappe.get_doc("Branch", doc.branch)

        if not branch_doc.custom_branch_hours_setting:
            return

        assignments = []

        # ==========================================
        # PREPARE ASSIGNMENTS
        # ==========================================

        for row in branch_doc.custom_branch_hours_setting:

            if not is_gender_match(row.gender, is_female):
                continue

            shift_type = get_shift_type_from_hours(
                branch=doc.branch,
                default_shift=doc.default_shift,
                hours=row.hours,
                attendance_source=attendance_source
            )

            if not shift_type:

                frappe.log_error(
                    f"""
                    Employee : {doc.name}
                    Branch : {doc.branch}
                    Hours : {row.hours}
                    Attendance Source : {attendance_source}
                    Shift Type Not Found
                    """,
                    "Shift Assignment Debug"
                )

                continue

            start_date, end_date = get_month_range_dates(
                row.from_month,
                row.to_month,
                joining_date
            )

            if end_date < joining_date:
                continue

            if joining_date > start_date:
                start_date = joining_date

            assignments.append({
                "gender": row.gender,
                "shift_type": shift_type,
                "start_date": start_date,
                "end_date": end_date,
                "from_month": cint(row.from_month),
                "to_month": cint(row.to_month)
            })

        if not assignments:
            return

        # ==========================================
        # SORT
        # Gender-specific rows first
        # ==========================================

        # assignments.sort(
        #     key=lambda d: (
        #         1 if d["gender"] == "All" else 0,
        #         d["start_date"]
        #     )
        # )

        final_assignments = []

        for assignment in assignments:

            # if assignment["gender"] != "All":

            #     final_assignments.append(assignment)
            #     continue

            start_date = assignment["start_date"]
            end_date = assignment["end_date"]

            for existing in final_assignments:

                overlap = (
                    start_date <= existing["end_date"]
                    and end_date >= existing["start_date"]
                )

                if overlap:

                    start_date = existing["end_date"] + timedelta(days=1)

            if start_date > end_date:
                continue

            assignment["start_date"] = start_date

            final_assignments.append(assignment)

        # ==========================================
        # SORT FINAL ASSIGNMENTS
        # ==========================================

        final_assignments.sort(
            key=lambda d: d["start_date"]
        )

        # ==========================================
        # CREATE SHIFT ASSIGNMENTS
        # ==========================================

        for assignment in final_assignments:

            create_shift_assignment(
                employee=doc.name,
                shift_type=assignment["shift_type"],
                start_date=assignment["start_date"],
                end_date=assignment["end_date"]
            )

            frappe.log_error(
                title="Shift Assignment Debug",
                message=f"""
                Employee : {doc.name}
                Shift Type : {assignment['shift_type']}
                Start Date : {assignment['start_date']}
                End Date : {assignment['end_date']}
                Gender Rule : {assignment['gender']}
                """
            )

    except Exception:

        frappe.log_error(
            frappe.get_traceback(),
            "Auto Shift Assignment Error"
        )

# =========================================================
# GENDER CHECK
# =========================================================

def is_gender_match(setting_gender, is_female):

    # if setting_gender == "All":
    #     return True

    if setting_gender == "Female" and is_female:
        return True

    if setting_gender == "Male" and not is_female:
        return True

    return False


# =========================================================
# FIND SHIFT TYPE
# =========================================================
def get_shift_type_from_hours(
    branch,
    default_shift,
    hours,
    attendance_source=None
):

    default_shift_doc = frappe.db.get_value(
        "Shift Type",
        default_shift,
        ["custom_shift_type"],
        as_dict=True
    )

    if not default_shift_doc:
        return None

    # ==========================================
    # First Priority:
    # Match Attendance Source
    # ==========================================

    if attendance_source:

        shift_type = frappe.db.get_value(
            "Shift Type",
            {
                "custom_branch": branch,
                "custom_shift_type": default_shift_doc.custom_shift_type,
                "custom_hours": hours,
                "custom_attendance_source": attendance_source
            },
            "name"
        )

        if shift_type:
            return shift_type

    # ==========================================
    # Second Priority:
    # Attendance Source Blank
    # ==========================================

    shift_type = frappe.db.get_value(
        "Shift Type",
        {
            "custom_branch": branch,
            "custom_shift_type": default_shift_doc.custom_shift_type,
            "custom_hours": hours,
            "custom_attendance_source": ["in", ["", None]]
        },
        "name"
    )

    if shift_type:
        return shift_type

    # ==========================================
    # Final Fallback:
    # Ignore Attendance Source Completely
    # ==========================================

    return frappe.db.get_value(
        "Shift Type",
        {
            "custom_branch": branch,
            "custom_shift_type": default_shift_doc.custom_shift_type,
            "custom_hours": hours
        },
        "name"
    )

# =========================================================
# DATE RANGE
# =========================================================

def get_month_range_dates(
    from_month,
    to_month,
    joining_date
):

    joining_date = getdate(joining_date)

    from_month = int(from_month)
    to_month = int(to_month)

    # Fiscal year starts from April
    if joining_date.month >= 4:
        fiscal_start_year = joining_date.year
    else:
        fiscal_start_year = joining_date.year - 1



    if from_month >= 4:
        start_year = fiscal_start_year
    else:
        start_year = fiscal_start_year + 1

    if to_month >= 4:
        end_year = fiscal_start_year
    else:
        end_year = fiscal_start_year + 1

    start_date = getdate(
        f"{start_year}-{from_month:02d}-01"
    )

    last_day = monthrange(
        end_year,
        to_month
    )[1]

    end_date = getdate(
        f"{end_year}-{to_month:02d}-{last_day}"
    )

    return start_date, end_date

# =========================================================
# CREATE SHIFT ASSIGNMENT
# =========================================================

def create_shift_assignment(
    employee,
    shift_type,
    start_date,
    end_date
):

    existing = frappe.db.exists(
        "Shift Assignment",
        {
            "employee": employee,
            "shift_type": shift_type,
            "start_date": start_date,
            "end_date": end_date,
            "docstatus": ["!=", 2]
        }
    )

    if existing:
        return

    # Prevent overlap
    overlap = frappe.db.sql(
        """
        SELECT name
        FROM `tabShift Assignment`
        WHERE employee = %s
        AND docstatus < 2
        AND (
            start_date <= %s
            AND IFNULL(end_date, '2199-12-31') >= %s
        )
        LIMIT 1
        """,
        (employee, end_date, start_date),
        as_dict=True
    )

    if overlap:

        frappe.log_error(
            f"""
            Employee : {employee}
            Existing Assignment : {overlap[0].name}
            New Shift : {shift_type}
            Start : {start_date}
            End : {end_date}
            """,
            "Shift Overlap Found"
        )

        return

    shift_doc = frappe.get_doc({
        "doctype": "Shift Assignment",
        "employee": employee,
        "shift_type": shift_type,
        "start_date": start_date,
        "end_date": end_date
    })

    shift_doc.insert(ignore_permissions=True)

    if shift_doc.docstatus == 0:
        shift_doc.submit()

    frappe.log_error(
        f"Shift Assignment Created : {shift_doc.name}",
        "Shift Assignment Debug"
    )





#     if not doc.default_shift:
#         return

#     today_date = getdate(today())
#     branch = doc.branch
#     start_year = today_date.year if today_date.month >= 4 else today_date.year - 1

    
#     if branch == "Jammu and Kashmir Milk Producers Co-operative Ltd Cheshmashahi Srinagar":
#         if doc.custom_attendance_source == "Field":
#             create_shift_assignment_for_srinagar(today_date, doc.name, doc.default_shift, start_year, is_field=True)
#         elif doc.custom_attendance_source == "Punch":
#             create_shift_assignment_for_srinagar(today_date, doc.name, doc.default_shift, start_year, is_punch=True)
#         else:
#             create_shift_assignment_for_srinagar(today_date, doc.name, doc.default_shift, start_year)

#     elif branch == "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu":
        
#         if doc.custom_attendance_source == "Field":
#             if doc.gender == "Female":
#                 create_shift_assignment_for_jammu(today_date, doc.name, doc.default_shift, start_year, is_female=True, is_field=True)
#             else:
#                 create_shift_assignment_for_jammu(today_date, doc.name, doc.default_shift, start_year, is_field=True)
            
#         else:
#             create_shift_assignment_for_jammu(today_date, doc.name, doc.default_shift, start_year)

            
    
#     employment_type = frappe.db.get_value("Employee", doc.name, "employment_type")
    

# def create_shift_assignment_for_srinagar(today_date, emp_id, default_shift_type_id, start_year, is_field = False, is_punch = False):
    
#     assign_both = False
#     assign_seven_hours = False

#     eight_hours_shift_id = "jkmpcl_hr/py/scheduler_method.py"
#     seven_hours_shift_id = ""

#     emp_default_shift_details = frappe.db.get_values("Shift Type", default_shift_type_id, ["custom_shift_type", "custom_hours", "custom_branch"], as_dict=True)
    
#     if emp_default_shift_details and emp_default_shift_details[0]:
#         default_shift_type = emp_default_shift_details[0].get("custom_shift_type")
#         default_shift_hours = emp_default_shift_details[0].get("custom_hours")
#         default_shift_branch = emp_default_shift_details[0].get("custom_branch")
        
#         if default_shift_hours == "8hours":
            
#             if is_field and default_shift_type == "General":
#                 eight_hours_shift_id=frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "8hours", "custom_attendance_source": "Field"}, "name")
#                 seven_hours_shift_id=frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "7hours", "custom_attendance_source": "Field"}, "name")
#             elif is_punch and default_shift_type == "General":
#                 eight_hours_shift_id=frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "8hours", "custom_attendance_source": "Punch"}, "name")
#                 seven_hours_shift_id=frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "7hours", "custom_attendance_source": "Punch"}, "name")
#             else:
#                 eight_hours_shift_id = default_shift_type_id
#                 seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "7hours"}, "name")
        
#         if default_shift_hours == "7hours":
            
#             if is_field and default_shift_type == "General":
#                 seven_hours_shift_id=frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "7hours", "custom_attendance_source": "Field"}, "name")
#                 eight_hours_shift_id=frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "8hours", "custom_attendance_source": "Field"}, "name")
#             elif is_punch and default_shift_type == "General":
#                 seven_hours_shift_id=frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "7hours", "custom_attendance_source": "Punch"}, "name")
#                 eight_hours_shift_id=frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "8hours", "custom_attendance_source": "Punch"}, "name")
#             else:        
#                 seven_hours_shift_id = default_shift_type_id
#                 eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "8hours"}, "name")

#     else:
#         frappe.throw("error_create_shift_assignment_for_srinagar", f"No Shift Details found for the default shift {default_shift_type_id}")
#         return

#     eight_hours_start = getdate(f"{start_year}-04-01")
#     eight_hours_end = getdate(f"{start_year}-09-30")
        
#     seven_hours_start = getdate(f"{start_year}-10-01")
#     seven_hours_end = getdate(f"{start_year + 1}-03-31")
    
    
#     if 4 <= today_date.month <= 9:
#         assign_both = True
#     else:
#         assign_seven_hours = True
        
    
#     if assign_both:            
#         create_shift_assignment_rec(emp_id, today_date, eight_hours_end,eight_hours_shift_id)
#         create_shift_assignment_rec(emp_id, seven_hours_start, seven_hours_end, seven_hours_shift_id)
    
#     elif assign_seven_hours:
#         create_shift_assignment_rec(emp_id, today_date, seven_hours_end, seven_hours_shift_id)



# def create_shift_assignment_for_jammu(today_date, emp_id, default_shift_type_id, start_year, is_female = False, is_field=False):
    
#     assign_all = False
#     assign_seven_hours = False
#     assign_second_eight_hours = False
        
#     eight_hours_shift_id = ""
#     seven_hours_shift_id = ""

#     emp_default_shift_details = frappe.db.get_values("Shift Type", default_shift_type_id, ["custom_shift_type", "custom_hours", "custom_branch"], as_dict=True)
    
#     if emp_default_shift_details and emp_default_shift_details[0]:
#         default_shift_type = emp_default_shift_details[0].get("custom_shift_type")
#         default_shift_hours = emp_default_shift_details[0].get("custom_hours")
#         default_shift_branch = emp_default_shift_details[0].get("custom_branch")
        
#         if default_shift_hours == "8hours":
#             if is_field and default_shift_type == "General":
#                 seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "7hours", "custom_attendance_source": "Field"}, "name")
#                 eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "8hours", "custom_attendance_source": "Field"}, "name")                
#             else:
#                 eight_hours_shift_id = default_shift_type_id
#                 seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "7hours"}, "name")
                
        
#         if default_shift_hours == "7hours":
#             if is_field and default_shift_type == "General":
#                 seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "7hours", "custom_attendance_source": "Field"}, "name")
#                 eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "8hours", "custom_attendance_source": "Field"}, "name") 
#             else:
#                 seven_hours_shift_id = default_shift_type_id
#                 eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "8hours"}, "name")

#     else:
#         frappe.throw("error_create_shift_assignment_for_srinagar", f"No Shift Details found for the default shift {default_shift_type_id}")
#         return

#     if is_female and is_field:
#         first_eight_hours_start = getdate(f"{start_year}-04-01")
#         first_eight_hours_end = getdate(f"{start_year}-11-30")
            
#         seven_hours_start = getdate(f"{start_year}-12-01")
#         seven_hours_end = getdate(f"{start_year + 1}-01-31")
        
#         second_eight_hours_start = getdate(f"{start_year + 1}-02-01")
#         second_eight_hours_end = getdate(f"{start_year + 1}-03-31")
        
#         print(f"\n\n {today_date.month} sdsad\n\n")
        
#         if 4 <= today_date.month <= 11:
#             assign_all = True        
        
#         elif today_date.month == 12 or today_date.month == 1:
#             assign_seven_hours = True
#             assign_second_eight_hours = True
            
#         elif 2<= today_date.month <=3:
#             assign_second_eight_hours = True
                                        
#         try:
#             # pass
#             if assign_all:                        
#                 create_shift_assignment_rec(emp_id, today_date,first_eight_hours_end, eight_hours_shift_id)
                
#                 create_shift_assignment_rec(emp_id, seven_hours_start, seven_hours_end, seven_hours_shift_id)
                
#                 create_shift_assignment_rec(emp_id, second_eight_hours_start,second_eight_hours_end, eight_hours_shift_id)
                
#             elif assign_seven_hours:    
#                 create_shift_assignment_rec(emp_id, today_date, seven_hours_end, seven_hours_shift_id)
#                 create_shift_assignment_rec(emp_id, second_eight_hours_start,second_eight_hours_end, eight_hours_shift_id)

#             elif assign_second_eight_hours:
#                 create_shift_assignment_rec(emp_id, today_date,second_eight_hours_end, eight_hours_shift_id)
#         except Exception as e:
#             frappe.log_error("error_shift_assignment", frappe.get_traceback())
#             frappe.throw(e)
    
#     else:
#         try:
#             shift_end_date = getdate(f"{start_year +1}-03-31")
#             create_shift_assignment_rec(emp_id, today_date, shift_end_date, eight_hours_shift_id)    
#         except Exception as e:
#             frappe.log_error("error_shift_assignment", frappe.get_traceback())
#             frappe.throw(e)
    

# * METHOD TO ALLOCATE CASUAL LEAVE ON EMPLOYEE CREATION BASED ON EMPLOYMENT TYPE AND DATE OF JOINING
def allocate_cl_on_employee_creation(employee):
    try:
        if not employee.date_of_joining or not employee.employment_type:
            return

        # Check CL Leave Type
        leave_type = "Casual Leave"
        correct_leave_type = ""
        if not frappe.db.get_value("Leave Type", leave_type, "custom_leave_type") == "Casual Leave":
            leave_type = frappe.db.get_value("Leave Type", {"custom_leave_type": "Casual Leave"}, "name")
        else:
            correct_leave_type = leave_type

        
        joining_date = getdate(employee.date_of_joining)
        from_date = joining_date

        fy_end_date = get_fy_end_date(joining_date)

        
        if employee.employment_type in ["Probation", "Confirmed"]:
            to_date = fy_end_date

        elif employee.employment_type == "Contractual":
            contract_end = getdate(employee.contract_end_date) if employee.contract_end_date else fy_end_date
            to_date = min(fy_end_date, contract_end)
        else:
            return  

        # Calculate CL
        cl_days = calculate_prorata_cl(joining_date)

        # Avoid duplicate allocation
        if frappe.db.exists(
            "Leave Allocation",
            {
                "employee": employee.name,
                "leave_type": correct_leave_type,
                "from_date": from_date,
                "to_date": to_date,
                "docstatus": ["!=", 2],
            },
        ):
            frappe.log_error("error_allocate_cl_on_employee_creation", f"Leave Allocation already exists for Employee {employee.name} from {from_date} to {to_date}")
            return

        # print(f"\n\n  {cl_days} \n\n")
        # Create Leave Allocation
        allocation = frappe.get_doc({
            "doctype": "Leave Allocation",
            "employee": employee.name,
            "employee_name": employee.employee_name,
            "leave_type": leave_type,
            "from_date": from_date,
            "to_date": to_date,
            "new_leaves_allocated": cl_days,
            "custom_last_allocation_date": from_date,
            "carry_forward": 0,
        })

        allocation.insert(ignore_permissions=True)
        allocation.submit()
    except Exception as e:
        frappe.log_error("error_allocate_cl_on_employee_creation", frappe.get_traceback())
        frappe.throw(e)



@frappe.whitelist()
def calculate_prorata_cl(joining_date):
    joining_date = getdate(joining_date)
    
    total_days = get_last_day(joining_date).day
    remaining_days = total_days - joining_date.day + 1
    
    return round(remaining_days / total_days, 2)
    
def get_fy_end_date(joining_date):
    joining_date = getdate(joining_date)
    if joining_date.month < 4:
        return getdate(f"{joining_date.year}-03-31")
    else:
        return getdate(f"{joining_date.year + 1}-03-31")
    
    
def update_cl_and_sl_after_confirmation(doc):
    try:
        old_doc = doc.get_doc_before_save()
        if not old_doc:
            return

        if (
            old_doc.employment_type != "Confirmed"
            and doc.employment_type == "Confirmed"
            and not doc.custom_leave_allocated_on_confirmation
        ):
            employee = doc.name
            leave_type = "Casual Leave"
            sl_leave_type = "Sick Leave"
            confirmed_sl = 7
            monthly_sl = flt(0.58)
            confirmation_date = doc.final_confirmation_date
            
            
            if not confirmation_date:
                frappe.throw("Confirmation Date is required to allocate Casual Leave after confirmation.")
                frappe.log_error("error_update_cl_after_confirmation", f"Confirmation Date missing for Employee {employee}")
                return

            if confirmation_date.month < 4:
                fy_end = getdate(f"{confirmation_date.year}-03-31")
            else:
                fy_end = getdate(f"{confirmation_date.year + 1}-03-31")


            remaining_balance = get_leave_balance_on(employee=employee,leave_type=leave_type,date=confirmation_date) or 0

            remaining_sl_balance = get_leave_balance_on(employee=employee,leave_type=sl_leave_type,date=confirmation_date) or 0
            
            current_alloc = frappe.get_all(
                "Leave Allocation",
                filters={
                    "employee": employee,
                    "leave_type": leave_type,
                    "from_date": ["<=", confirmation_date],
                    "to_date": [">=", confirmation_date],
                    "docstatus": 1
                },
                fields=["name"],
                limit=1
            )

            current_sl_alloc = frappe.get_all(
                "Leave Allocation",
                filters={
                    "employee": employee,
                    "leave_type": sl_leave_type,
                    "from_date": ["<=", confirmation_date],
                    "to_date": [">=", confirmation_date],
                    "docstatus": 1
                },
                fields=["name"],
                limit=1
            )
                        
            if current_alloc:
                frappe.db.set_value("Leave Allocation", current_alloc[0].name, "to_date", add_days(getdate(confirmation_date), -1))
                frappe.db.set_value("Leave Allocation", current_alloc[0].name, "custom_last_allocation_date", getdate())
                # frappe.db.set_value("Leave Ledger Entry", {"custom_is_penalty": 0, "employee": employee, "transaction_type": "Leave Allocation", "transaction_name": current_alloc[0].name}, "to_date", add_days(getdate(confirmation_date), -1))
                # alloc_doc.to_date = confirmation_date
                # alloc_doc.save(ignore_permissions=True)
            
            
            if current_sl_alloc:
                frappe.db.set_value("Leave Allocation", current_sl_alloc[0].name, "to_date", add_days(getdate(confirmation_date), -1))
                frappe.db.set_value("Leave Allocation", current_sl_alloc[0].name, "custom_last_allocation_date", getdate())
                # frappe.db.set_value("Leave Ledger Entry", {"custom_is_penalty": 0, "employee": employee, "transaction_type": "Leave Allocation", "transaction_name": current_sl_alloc[0].name}, "to_date", add_days(getdate(confirmation_date), -1))
            
            
            next_month_start = get_first_day(add_months(confirmation_date, 1))

            months_remaining = month_diff(fy_end, next_month_start)


            new_alloc = frappe.get_doc({
                "doctype": "Leave Allocation",
                "employee": employee,
                "leave_type": leave_type,
                "from_date": confirmation_date,
                "to_date": fy_end,
                "custom_opening_balance_on_confirmed": remaining_balance,
                "new_leaves_allocated": months_remaining,
                "custom_last_allocation_date": confirmation_date,
                "description": "Auto CL allocation after confirmation"
            })

            new_alloc.insert(ignore_permissions=True)
            new_alloc.submit()
            # SL Allocation after confirmation
            
            
            sl_months_remaining = month_diff(fy_end, confirmation_date)
            
            new_sl = flt(sl_months_remaining) * monthly_sl
            
            sl_alloc = frappe.get_doc({
                "doctype": "Leave Allocation",
                "employee": employee,
                "leave_type": sl_leave_type,
                "from_date": confirmation_date or next_month_start,
                "to_date": fy_end,
                "custom_opening_balance_on_confirmed": remaining_sl_balance,
                "new_leaves_allocated": round(new_sl),
                "custom_last_allocation_date": confirmation_date,
                "description": "Auto SL allocation after confirmation"
            })
            sl_alloc.insert(ignore_permissions=True)
            sl_alloc.submit()
            doc.custom_leave_allocated_on_confirmation = 1            
            frappe.db.set_value("Employee", doc.name, "custom_leave_allocated_on_confirmation", 1)
            
    except Exception as e:
        frappe.log_error("error_update_cl_and_sl_after_confirmation", frappe.get_traceback())
        frappe.throw(str(e))


# ? ENQUEUE FUNCTION
# ! jkmpcl_hr.py.employee.rename_selected_employees
@frappe.whitelist()
def rename_selected_employees(max_minutes=30):
    """
    Enqueue the rename job in the background.

    Args:
        employee_list (list | str): List of Employee IDs to process (can be JSON string)
        max_minutes (int): Max minutes the background job can run
    """
    import json
    from frappe.utils.background_jobs import enqueue


    employee_list = frappe.db.get_list("Employee", "name", pluck='name')
    # ? PARSE IF STRING
    if isinstance(employee_list, str):
        try:
            employee_list = json.loads(employee_list)
        except Exception:
            frappe.throw("Invalid employee list format. Must be a valid JSON array.")

    # ? ENQUEUE BACKGROUND JOB
    enqueue(
        "jkmpcl_hr.py.employee.rename_selected_employees_background",
        employee_list=employee_list,
        queue="long",
        timeout=max_minutes * 60,
    )
    
    # rename_selected_employees(employee_list)

    return f"Rename job enqueued for {len(employee_list)} employees."

def rename_selected_employees_background(employee_list):
    """
    Background job to rename employees, commit per employee, and log errors with traceback.
    """
    renamed_employees = []
    frappe.log_error("rename_started", "Started")
    for emp_id in employee_list:
        try:
            emp = frappe.get_doc("Employee", emp_id)
            old_id = emp.name
            emp_code = emp.employee_number if emp.employee_number else emp.attendance_device_id if emp.attendance_device_id else None
            
            if not emp_code:
                frappe.log_error(f"error_rename_selected_employees_background{emp.name}", "No Employee Code")
            
            new_id = f"{emp_code}:{emp.employee_name}"

            # Skip if new ID already exists
            if frappe.db.exists("Employee", new_id):
                continue

            # Rename and commit immediately
            frappe.rename_doc("Employee", old_id, new_id, force=True)
            frappe.db.commit()

            # Log success
            frappe.log_error(
                message=f"Renamed employee: {old_id}", title="Employee Renamed"
            )
            renamed_employees.append(old_id)

        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(
                message=f"Failed to rename {emp_id}: {str(e)}\nTraceback:\n{frappe.get_traceback()}",
                title="Employee Rename Failed",
            )
            continue
    
    # frappe.log_error("rename_ended")
    
    frappe.log_error(
        message=f"Background rename job completed. Total renamed: {len(renamed_employees)}",
        title="Employee Rename Job Completed",
    )

    return renamed_employees
