import frappe
from frappe.utils import getdate, today,add_days,now_datetime, get_last_day, get_first_day
# import calendar
from datetime import date,datetime
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

from jkmpcl_hr.py.utils import create_shift_assignment_rec




def on_update(doc, event):
    pass


def after_insert(doc, event):
    
    allocate_cl_on_employee_creation(doc)
    
    if not doc.default_shift:
        return

    today_date = getdate(today())
    branch = doc.branch
    start_year = today_date.year if today_date.month >= 4 else today_date.year - 1

    
    if branch == "Jammu and Kashmir Milk Producers Co-operative Ltd Cheshmashahi Srinagar":
        create_shift_assignment_for_srinagar(today_date, doc.name, doc.default_shift, start_year)

    elif branch == "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu":
        if doc.gender == "Female":
            print(f"\n\n CALLED For Female \n\n")
            create_shift_assignment_for_jammu(today_date, doc.name, doc.default_shift, start_year,is_female=True)
        else:
            create_shift_assignment_for_jammu(today_date, doc.name, doc.default_shift, start_year)
            
    
    employment_type = frappe.db.get_value("Employee", doc.name, "employment_type")
    

def create_shift_assignment_for_srinagar(today_date, emp_id, default_shift_type_id, start_year):
    
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
            eight_hours_shift_id = default_shift_type_id
            seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "7hours"}, "name")
        
        if default_shift_hours == "7hours":
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



def create_shift_assignment_for_jammu(today_date, emp_id, default_shift_type_id, start_year, is_female = False):
    
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
            eight_hours_shift_id = default_shift_type_id
            seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "7hours"}, "name")
        
        if default_shift_hours == "7hours":
            seven_hours_shift_id = default_shift_type_id
            eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_branch": default_shift_branch, "custom_shift_type": default_shift_type, "custom_hours": "8hours"}, "name")

    else:
        frappe.throw("error_create_shift_assignment_for_srinagar", f"No Shift Details found for the default shift {default_shift_type_id}")
        return

    if is_female:
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
        
        
            
            
        print(f"\n\n  {assign_all} \n {assign_second_eight_hours} \n {assign_seven_hours} \n\n")
        
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
    if not employee.date_of_joining:
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

    
    if employee.employment_type == "Probation":
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

