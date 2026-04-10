import frappe
from frappe.utils import getdate, today,add_days,now_datetime, get_last_day, get_first_day, add_months, month_diff, flt
from jkmpcl_hr.py.utils import get_emp_reporting_manager

# import calendar
from datetime import date,datetime
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

from jkmpcl_hr.py.utils import create_shift_assignment_rec




def on_update(doc, event):
    # pass
    update_cl_and_sl_after_confirmation(doc)
    # set_approvers(doc)

def validate(doc, event):
    set_approvers(doc)
def set_approvers(doc):
    try:
        # if doc.name:
        #     actual_emp_rm = get_emp_reporting_manager(doc.name)
        #     if actual_emp_rm:
        #         emp_rm_emp = frappe.db.get_value("Employee", {"user_id": actual_emp_rm}, "name") if actual_emp_rm else None
        #         if doc.shift_request_approver != actual_emp_rm:
        #             frappe.db.set_value("Employee", doc.name, "shift_request_approver", actual_emp_rm)
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
    
    if not doc.default_shift:
        return

    today_date = getdate(today())
    branch = doc.branch
    start_year = today_date.year if today_date.month >= 4 else today_date.year - 1

    
    if branch == "Jammu and Kashmir Milk Producers Co-operative Ltd Cheshmashahi Srinagar":
        if doc.custom_attendance_source == "Field":
            create_shift_assignment_for_srinagar(today_date, doc.name, doc.default_shift, start_year, is_field=True)
        elif doc.custom_attendance_source == "Punch":
            create_shift_assignment_for_srinagar(today_date, doc.name, doc.default_shift, start_year, is_punch=True)
        else:
            create_shift_assignment_for_srinagar(today_date, doc.name, doc.default_shift, start_year)

    elif branch == "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu":
        
        if doc.custom_attendance_source == "Field":
            if doc.gender == "Female":
                create_shift_assignment_for_jammu(today_date, doc.name, doc.default_shift, start_year, is_female=True, is_field=True)
            else:
                create_shift_assignment_for_jammu(today_date, doc.name, doc.default_shift, start_year, is_field=True)
            
        else:
            create_shift_assignment_for_jammu(today_date, doc.name, doc.default_shift, start_year)

            
    
    employment_type = frappe.db.get_value("Employee", doc.name, "employment_type")
    

def create_shift_assignment_for_srinagar(today_date, emp_id, default_shift_type_id, start_year, is_field = False, is_punch = False):
    
    assign_both = False
    assign_seven_hours = False

    eight_hours_shift_id = ""
    seven_hours_shift_id = ""

    emp_default_shift_details = frappe.db.get_values("Shift Type", default_shift_type_id, ["custom_shift_type", "custom_hours", "custom_branch"], as_dict=True)
    
    if emp_default_shift_details and emp_default_shift_details[0]:
        default_shift_type = emp_default_shift_details[0].get("custom_shift_type")
        default_shift_hours = emp_default_shift_details[0].get("custom_hours")
        default_shift_branch = emp_default_shift_details[0].get("custom_branch")
        
        if default_shift_hours == "8hours":
            
            if is_field and default_shift_type == "General":
                eight_hours_shift_id=frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "8hours", "custom_attendance_source": "Field"}, "name")
                seven_hours_shift_id=frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "7hours", "custom_attendance_source": "Field"}, "name")
            elif is_punch and default_shift_type == "General":
                eight_hours_shift_id=frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "8hours", "custom_attendance_source": "Punch"}, "name")
                seven_hours_shift_id=frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "7hours", "custom_attendance_source": "Punch"}, "name")
            else:
                eight_hours_shift_id = default_shift_type_id
                seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "7hours"}, "name")
        
        if default_shift_hours == "7hours":
            
            if is_field and default_shift_type == "General":
                seven_hours_shift_id=frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "7hours", "custom_attendance_source": "Field"}, "name")
                eight_hours_shift_id=frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "8hours", "custom_attendance_source": "Field"}, "name")
            elif is_punch and default_shift_type == "General":
                seven_hours_shift_id=frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "7hours", "custom_attendance_source": "Punch"}, "name")
                eight_hours_shift_id=frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "8hours", "custom_attendance_source": "Punch"}, "name")
            else:        
                seven_hours_shift_id = default_shift_type_id
                eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "8hours"}, "name")

    else:
        frappe.throw("error_create_shift_assignment_for_srinagar", f"No Shift Details found for the default shift {default_shift_type_id}")
        return

    eight_hours_start = getdate(f"{start_year}-04-01")
    eight_hours_end = getdate(f"{start_year}-09-30")
        
    seven_hours_start = getdate(f"{start_year}-10-01")
    seven_hours_end = getdate(f"{start_year + 1}-03-31")
    
    
    if 4 <= today_date.month <= 9:
        assign_both = True
    else:
        assign_seven_hours = True
        
    
    if assign_both:            
        create_shift_assignment_rec(emp_id, today_date, eight_hours_end,eight_hours_shift_id)
        create_shift_assignment_rec(emp_id, seven_hours_start, seven_hours_end, seven_hours_shift_id)
    
    elif assign_seven_hours:
        create_shift_assignment_rec(emp_id, today_date, seven_hours_end, seven_hours_shift_id)



def create_shift_assignment_for_jammu(today_date, emp_id, default_shift_type_id, start_year, is_female = False, is_field=False):
    
    assign_all = False
    assign_seven_hours = False
    assign_second_eight_hours = False
        
    eight_hours_shift_id = ""
    seven_hours_shift_id = ""

    emp_default_shift_details = frappe.db.get_values("Shift Type", default_shift_type_id, ["custom_shift_type", "custom_hours", "custom_branch"], as_dict=True)
    
    if emp_default_shift_details and emp_default_shift_details[0]:
        default_shift_type = emp_default_shift_details[0].get("custom_shift_type")
        default_shift_hours = emp_default_shift_details[0].get("custom_hours")
        default_shift_branch = emp_default_shift_details[0].get("custom_branch")
        
        if default_shift_hours == "8hours":
            if is_field and default_shift_type == "General":
                seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "7hours", "custom_attendance_source": "Field"}, "name")
                eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "8hours", "custom_attendance_source": "Field"}, "name")                
            else:
                eight_hours_shift_id = default_shift_type_id
                seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "7hours"}, "name")
                
        
        if default_shift_hours == "7hours":
            if is_field and default_shift_type == "General":
                seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "7hours", "custom_attendance_source": "Field"}, "name")
                eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "8hours", "custom_attendance_source": "Field"}, "name") 
            else:
                seven_hours_shift_id = default_shift_type_id
                eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "8hours"}, "name")

    else:
        frappe.throw("error_create_shift_assignment_for_srinagar", f"No Shift Details found for the default shift {default_shift_type_id}")
        return

    if is_female and is_field:
        first_eight_hours_start = getdate(f"{start_year}-04-01")
        first_eight_hours_end = getdate(f"{start_year}-11-30")
            
        seven_hours_start = getdate(f"{start_year}-12-01")
        seven_hours_end = getdate(f"{start_year + 1}-01-31")
        
        second_eight_hours_start = getdate(f"{start_year + 1}-02-01")
        second_eight_hours_end = getdate(f"{start_year + 1}-03-31")
        
        print(f"\n\n {today_date.month} sdsad\n\n")
        
        if 4 <= today_date.month <= 11:
            assign_all = True        
        
        elif today_date.month == 12 or today_date.month == 1:
            assign_seven_hours = True
            assign_second_eight_hours = True
            
        elif 2<= today_date.month <=3:
            assign_second_eight_hours = True
                                        
        try:
            # pass
            if assign_all:                        
                create_shift_assignment_rec(emp_id, today_date,first_eight_hours_end, eight_hours_shift_id)
                
                create_shift_assignment_rec(emp_id, seven_hours_start, seven_hours_end, seven_hours_shift_id)
                
                create_shift_assignment_rec(emp_id, second_eight_hours_start,second_eight_hours_end, eight_hours_shift_id)
                
            elif assign_seven_hours:    
                create_shift_assignment_rec(emp_id, today_date, seven_hours_end, seven_hours_shift_id)
                create_shift_assignment_rec(emp_id, second_eight_hours_start,second_eight_hours_end, eight_hours_shift_id)

            elif assign_second_eight_hours:
                create_shift_assignment_rec(emp_id, today_date,second_eight_hours_end, eight_hours_shift_id)
        except Exception as e:
            frappe.log_error("error_shift_assignment", frappe.get_traceback())
            frappe.throw(e)
    
    else:
        try:
            shift_end_date = getdate(f"{start_year +1}-03-31")
            create_shift_assignment_rec(emp_id, today_date, shift_end_date, eight_hours_shift_id)    
        except Exception as e:
            frappe.log_error("error_shift_assignment", frappe.get_traceback())
            frappe.throw(e)
    

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
                frappe.db.set_value("Leave Ledger Entry", {"custom_is_penalty": 0, "employee": employee, "transaction_type": "Leave Allocation", "transaction_name": current_alloc[0].name}, "to_date", add_days(getdate(confirmation_date), -1))
                # alloc_doc.to_date = confirmation_date
                # alloc_doc.save(ignore_permissions=True)
            
            
            if current_sl_alloc:
                frappe.db.set_value("Leave Allocation", current_sl_alloc[0].name, "to_date", add_days(getdate(confirmation_date), -1))
                frappe.db.set_value("Leave Allocation", current_sl_alloc[0].name, "custom_last_allocation_date", getdate())
                frappe.db.set_value("Leave Ledger Entry", {"custom_is_penalty": 0, "employee": employee, "transaction_type": "Leave Allocation", "transaction_name": current_sl_alloc[0].name}, "to_date", add_days(getdate(confirmation_date), -1))
            
            
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
                "custom_opening_balance_on_confirmed": round(remaining_sl_balance),
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

