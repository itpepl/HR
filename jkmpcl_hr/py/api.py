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
    branch = filters.get("branch")
    date_str = filters.get("as_on_date")
    employee_id = filters.get("emp_id")
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
        
        print(f"\n\n \n\n")
        if 4 <= as_on_date.month <= 9:   
            required_hours = "8hours"
        else:                          
            required_hours = "7hours"

        
        conditions["custom_hours"]= required_hours
        
        
        print(f"\n\n  required hours {required_hours} \n\n")
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
    elif branch == "Jammu":
        
        is_female = True if frappe.db.get_value("Employee", employee_id, "gender") == "Female" else False
    
        if is_female:        
            if (4<= as_on_date.month <= 11) or (2 <= as_on_date.month <= 3):
                required_hours = "8hours"
            else:
                required_hours = "7hours"
        else:
            required_hours = "8hours"
        
        conditions["custom_hours"]= required_hours
        
        
        print(f"\n\n  required hours {required_hours} \n\n")
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
        