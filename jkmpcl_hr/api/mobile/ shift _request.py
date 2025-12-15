import frappe
# from jkmpcl_hr.py.api import determine_shift_types
@frappe.whitelist()
def get_shift_requests(employeeId=None, start_date=None, end_date=None):

    try:
        filters = {}

        if employeeId:
            filters["employee"] = employeeId

        if start_date and end_date:
            filters["from_date"] = [">=", start_date]
            filters["to_date"] = ["<=", end_date]

        order_by = "from_date desc"

        shift_requests = frappe.get_all(
            "Shift Request",
            filters=filters,
            fields=["shift_type", "employee", "approver", "from_date", "to_date", "name","status"],
            order_by=order_by
        )

        return {
            "success": True,
            "message": "Shift requests fetched successfully",
            "data": shift_requests
        }

    except Exception as e:
        error_message = f"Error fetching shift requests: {str(e)}"
        frappe.log_error(error_message, "Shift Request API Error")

        return {
            "success": False,
            "message": error_message,
            "data": None
        }

@frappe.whitelist()
def create_shift_request(data):

    try:
        if isinstance(data, str):
            data = frappe.parse_json(data)

        employee = data.get("employee")
        shift_type = data.get("shift_type")
        from_date = data.get("from_date")
        to_date = data.get("to_date")
        remarks = data.get("remarks")  
        approver=data.get("approver")

        if not employee or not shift_type or not from_date or not to_date:
            return {
                "success": False,
                "message": "Missing required fields",
                "data": None
            }
        print(f"\n\n Employee: {employee}, Shift Type: {shift_type}, From Date: {from_date}, To Date: {to_date}, Remarks: {remarks} \n\n")
        shift_request = frappe.get_doc({
            "doctype": "Shift Request",
            "employee": employee,
            "shift_type": shift_type,
            "from_date": from_date,
            "to_date": to_date,
            "remarks": remarks,
            "approver": approver
        })
        # ✅ THIS LINE IS CRITICAL
        shift_request.flags.skip_approver_validation = True

        shift_request.insert(ignore_permissions=True)

        return {
            "success": True,
            "message": "Shift request created successfully",
            "data": {"name": shift_request.name}
        }

    except Exception as e:
        error_message = f"Error creating shift request: {str(e)}"
        frappe.log_error(error_message, "Shift Request Create API Error")

        return {
            "success": False,
            "message": error_message,
            "data": None
        }


@frappe.whitelist()
def shift_type_list(branch=None):

    try:
        filters = {}

        if branch:
            filters["custom_branch"] = branch

 
        shift_types = frappe.get_all(
            "Shift Type",
            filters=filters,
            fields=["name", "start_time", "end_time"],
            order_by="name asc"
        )

        return {
            "success": True,
            "message": "Shift types fetched successfully",
            "data": shift_types
        }

    except Exception as e:
        error_message = f"Error fetching shift types: {str(e)}"
        frappe.log_error(error_message, "Shift Type API Error")

        return {
            "success": False,
            "message": error_message,
            "data": None
        }



import frappe
from frappe.utils import getdate
from frappe.utils import now, add_to_date

import frappe
from frappe.utils import getdate

@frappe.whitelist()
def determine_shift_types(doctype, txt, searchfield, start, page_len, filters):
    branch = filters.get("branch")
    date_str = filters.get("as_on_date")
    employee_id = filters.get("emp_id")

    if not branch:
        return []

    as_on_date = getdate(date_str) if date_str else getdate()

    if branch == "Srinagar":
        if 4 <= as_on_date.month <= 9:
            required_hours = "8hours"
        else:
            required_hours = "7hours"

    elif branch == "Jammu":
        is_female = (
            frappe.db.get_value("Employee", employee_id, "gender") == "Female"
        )

        if is_female:
            if (4 <= as_on_date.month <= 11) or (2 <= as_on_date.month <= 3):
                required_hours = "8hours"
            else:
                required_hours = "7hours"
        else:
            required_hours = "8hours"

    else:
        return []

    conditions = {
        "custom_hours": required_hours,
        "custom_branch": branch
    }

    # ✅ FIX ADDED HERE
    shift_types = frappe.db.get_list(
        "Shift Type",
        filters=conditions,
        fields=["name"],
        order_by="name",
        start=start,
        page_length=page_len,
        ignore_permissions=True
    )

    return [[s.name, s.name] for s in shift_types] or []


@frappe.whitelist()
def shift_type_list(branch, date=None, employee=None):

    result = determine_shift_types(
        doctype="Shift Type",
        txt="",
        searchfield="name",
        start=0,
        page_len=1000,
        filters={
            "branch": branch,
            "as_on_date": date,
            "emp_id": employee
        }
    ) or []

    shift_types = [{"name": row[0]} for row in result]

    return {
        "success": True,
        "data": shift_types
    }
