import frappe
from frappe import _
from frappe.utils import cint, getdate, today
from frappe.query_builder import DocType

from jkmpcl_hr.py.utils import get_roles_from_hr_settings_by_module



@frappe.whitelist()
def get_users_with_role(doctype, txt, searchfield, start, page_len, filters):
    """
    Custom query method for user link field filtered by role.
    Returns list of tuples: [(user_name, full_name), ...]
    """
    role = filters.get("role")
    
    if not role:
        return []

    # get usernames from Has Role
    users = frappe.get_all("Has Role", filters={"role": role}, pluck="parent") or []
    if not users:
        return []

    # get enabled users and return as list of tuples
    user_list = frappe.get_all(
        "User",
        filters=[["User", "name", "in", users], ["User", "enabled", "=", 1], ["User", "name", "!=", "Administrator"]],
        fields=["name", "full_name"],
        order_by="full_name asc"
    )
    
    # convert to list of tuples: [(name, full_name), ...]
    return [(u.get("name"), u.get("full_name") or "") for u in user_list]



@frappe.whitelist()
def get_reporting_managers(department):
    """
    Return approvers for a department for all three parentfields.
    Returns dict with parentfield as key and list of approvers as value.
    """
    parentfields = [
        "custom_reporting_manager",
        "custom_review_manager",
        "custom_hr_manager"
    ]
    
    result = {}
    for pf in parentfields:
        result[pf] = frappe.get_all(
            "Approver",
            filters={"parent": department, "parentfield": pf},
            fields=["effective_from", "role", "user", "employee"],
            order_by="effective_from asc"
        )
    
    return result


@frappe.whitelist()
def add_custom_hr_rows_to_employees(department, rows):
    """
    rows: list of dicts [{role, user, effective_from}, ...]
    Adds only these rows to every Employee with department=department, avoiding duplicates.
    """
    if not department or not rows:
        return {"added": 0}

    # ensure rows is a Python list (frappe.call may send as list/object)
    if isinstance(rows, str):
        import json
        rows = json.loads(rows)

    employees = frappe.get_all("Employee", filters={"department": department}, fields=["name"])
    if not employees:
        return {"added": 0}

    total_added = 0
    for e in employees:
        emp = frappe.get_doc("Employee", e.name)
        existing = {
            (r.role, r.user, (str(r.effective_from) if r.effective_from else ""))
            for r in (emp.get("custom_hr_manager") or [])
        }

        added = False
        for r in rows:
            key = (r.get("role"), r.get("user"), (str(r.get("effective_from")) if r.get("effective_from") else ""))
            if key not in existing:
                emp.append("custom_hr_manager", {
                    "role": r.get("role"),
                    "user": r.get("user"),
                    "effective_from": r.get("effective_from") or None
                })
                existing.add(key)
                added = True
                total_added += 1

        if added:
            emp.save(ignore_permissions=True)

    frappe.db.commit()
    return {"added": total_added}


# * METHOD TO GET THE SHIFT TYPE BASED ON THE DATE AND BRANCH
@frappe.whitelist()
def determine_shift_types(doctype, txt, searchfield, start, page_len, filters):
    try:
        branch = filters.get("branch")
        date_str = filters.get("as_on_date")
        employee_id = filters.get("emp_id")
        gender = filters.get("gender", False)
        emp_attendance_source = filters.get("attendance_source", frappe.get_value("Employee", employee_id, "custom_attendance_source")) 
        
        conditions = {}    
                
        current_user = frappe.session.user

        user_roles = frappe.get_roles(current_user)
        
        allowed_roles = get_roles_from_hr_settings_by_module("custom_roles_allowed_to_assign_24hours_shift")

        if not any(r in user_roles for r in allowed_roles):
            conditions["custom_shift_type"] = ["!=", "24 hours"]

        if not branch:
            return []

        
        as_on_date = getdate(date_str) if date_str else getdate()
        if branch == "Jammu and Kashmir Milk Producers Co-operative Ltd Cheshmashahi Srinagar": 
            
            
            if emp_attendance_source:
                if emp_attendance_source == "Biometric":
                    conditions["custom_attendance_source"] = ["not in", ["Field", "Punch"]]
                
                elif emp_attendance_source == "Punch":
                    conditions["custom_attendance_source"] = ["!=", "Field"]
                    # conditions["name"] = ["!=", "Jammu-General-8hours"]
                    conditions["name"] = ["not in", ["Srinagar-General-8hours", "Srinagar-General-7hours"]]
                    
                    

                    
                elif emp_attendance_source == "Field":
                    conditions["custom_attendance_source"] = ["!=", "Punch"]
                    # conditions["name"] = ["!=", "Srinagar-General-8hours"]
                    conditions["name"] = ["not in", ["Srinagar-General-8hours", "Srinagar-General-7hours"]]
                    
            
            
            if 4 <= as_on_date.month <= 9:   
                required_hours = "8hours"
            else:                          
                required_hours = "7hours"
            
            conditions["custom_hours"]= required_hours
            
            
            if branch:
                conditions["custom_branch"] = branch

            shift_types = frappe.db.get_list(
                "Shift Type",
                filters=conditions,
                fields=["name"],
                order_by="name",
                start=start,
                page_length=page_len
            )

            return [[s.name, s.name] for s in shift_types]
        elif branch == "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu":
            is_field = False
            
            if emp_attendance_source:
                if emp_attendance_source in ["Biometric", "Punch"]:
                    conditions["custom_attendance_source"] = ["not in", ["Field", "Punch"]]
                        
                elif emp_attendance_source == "Field":
                    is_field = True
                    
                    conditions["name"] = ["not in", ["Jammu-General-8hours", "Jammu-General-7hours"]]
                    
            
            if not gender:
                is_female = True if frappe.db.get_value("Employee", employee_id, "gender") == "Female" and is_field else False
            else:
                is_female = True if gender == "Female" and is_field else False
        
            if is_female:        
                if (4<= as_on_date.month <= 11) or (2 <= as_on_date.month <= 3):
                    required_hours = "8hours"
                else:
                    required_hours = "7hours"
            else:
                required_hours = "8hours"
            
            conditions["custom_hours"]= required_hours
            
            if branch:
                conditions["custom_branch"] = branch

            shift_types = frappe.db.get_list(
                "Shift Type",
                filters=conditions,
                fields=["name"],
                order_by="name",
                start=start,
                page_length=page_len
            )
            frappe.log_error(f"shift_types_jammu", str(shift_types))
            return [[s.name, s.name] for s in shift_types] if shift_types else []
        else:
            return []
    except Exception as e:
        frappe.log_error(f"error_determine_shift_types", frappe.get_traceback())
        frappe.throw(e)
        


import frappe
from frappe.utils import getdate, today


# =====================================================
# 🔹 CORE CHECK FUNCTION
# =====================================================
def is_employee_suspended(employee, check_date=None):

    if not employee:
        return False

    if not check_date:
        check_date = getdate(today())
    else:
        check_date = getdate(check_date)

    emp = frappe.db.get_value(
        "Employee",
        employee,
        ["custom_suspended_from_date", "custom_suspended_to_date"],
        as_dict=True
    )

    if not emp or not emp.custom_suspended_from_date:
        return False

    from_date = getdate(emp.custom_suspended_from_date)
    to_date = emp.custom_suspended_to_date and getdate(emp.custom_suspended_to_date)

    # -------------------------------
    # ✅ STATUS LOGIC
    # -------------------------------
    if check_date < from_date:
        return False

    if not to_date:
        return True   # 🔥 suspended indefinitely

    if from_date <= check_date <= to_date:
        return True

    return False


# =====================================================
# 🔹 GLOBAL VALIDATION FUNCTION
# =====================================================
def block_suspended_employee(doc, method=None):

    employee = getattr(doc, "employee", None)

    if not employee:
        return

    # ----------------------------------------
    # 🔥 Pick correct date field dynamically
    # ----------------------------------------
    check_date = (
        getattr(doc, "from_date", None)
        or getattr(doc, "attendance_date", None)
        or getattr(doc, "start_date", None)
        or getattr(doc, "posting_date", None)
        or today()
    )

    if is_employee_suspended(employee, check_date):

        frappe.throw(
            f"Employee {employee} is Suspended. Action not allowed on {check_date}."
        )