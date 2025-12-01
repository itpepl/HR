import frappe
from frappe.utils import getdate, today
from datetime import date



@frappe.whitelist(allow_guest=True)
def create_shift_assignments():
    today_date = getdate(today())
    start_year = today_date.year if today_date.month >= 4 else today_date.year - 1
    
    emp_filters = {"status": "Active"}
    create_and_assign_shift_assignments_srinagar(today_date, start_year, emp_filters)
    create_and_assign_shift_assignments_jammu(today_date, start_year, emp_filters)
    
def create_and_assign_shift_assignments_srinagar(today_date, start_year, emp_filters):
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
                            
            elif emp_default_shift_details.get("custom_hours") == "8hours":
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
    
    
def create_and_assign_shift_assignments_jammu(today_date, start_year, emp_filters):
    # apr_start_date = date(start_year, 4, 1)
    # mar_end_date = date(start_year + 1, 3, 31)
    
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
    emp_list = frappe.db.get_list("Employee", filters=emp_filters, fields=["name", "default_shift"])
    
    if not emp_list:
        return
    
    error_emp = []
    ds_not_set_emp = []
    
    for emp in emp_list:
        try:
            emp_id = emp.get("name")
            default_shift = emp.get("default_shift")
            
            eight_hours_sa_exists_first = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", apr_start_date], "end_date":[">=", nov_end_jammu]}, limit=1)
            seven_hours_sa_exists = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", dec_start_jammu], "end_date":[">=", jan_end_jammu]}, limit=1)
            eight_hours_sa_exists_second = frappe.db.get_all("Shift Assignment", {"employee": emp_id, "start_date":["<=", feb_start_jammu], "end_date":[">=", mar_end_date]}, limit=1)
            
            
            emp_default_shift_details = frappe.db.get_values("Shift Type", default_shift, ["custom_shift_type", "custom_hours", "custom_branch"], as_dict=True)
            
            if not emp_default_shift_details:
                ds_not_set_emp.append(emp_id)
                continue
            
            if emp_default_shift_details[0].get("custom_hours") == "7hours":
                seven_hours_shift_id = default_shift
                eight_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "8hours", "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
                            
            elif emp_default_shift_details.get("custom_hours") == "8hours":
                eight_hours_shift_id = default_shift
                seven_hours_shift_id = frappe.db.get_value("Shift Type", {"custom_shift_type": emp_default_shift_details[0].get("custom_shift_type"), "custom_hours": "7hours", "custom_branch": emp_default_shift_details[0].get("custom_branch")}, "name")
            
            if not eight_hours_sa_exists_first:
                create_shift_assignment_rec(emp_id, apr_start_date, nov_end_jammu, eight_hours_shift_id)
            
            if not seven_hours_sa_exists:
                create_shift_assignment_rec(emp_id, dec_start_jammu, jan_end_jammu, seven_hours_shift_id)
                
            if not eight_hours_sa_exists_second:
                create_shift_assignment_rec(emp_id, feb_start_jammu, mar_end_date, eight_hours_shift_id)
                        
            # return emp_default_shift_details
            # if not eight_hours_sa_exists_first:
                
            
        except Exception as e:
            error_emp.append({emp_id: str(e)})
            frappe.log_error(f"error_create_and_assign_shift_assignments_srinagar_{emp_id}", frappe.get_traceback())
            continue

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

