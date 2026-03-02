import frappe
from frappe.utils import getdate
from frappe.utils import now, add_to_date
from frappe.utils import strip_html
from frappe.utils import cint

# from jkmpcl_hr.py.api import determine_shift_types
# @frappe.whitelist()
# def get_shift_requests(employeeId=None, start_date=None, end_date=None):

#     try:
#         filters = {}

#         if employeeId:
#             filters["employee"] = employeeId

#         if start_date and end_date:
#             filters["from_date"] = [">=", start_date]
#             filters["to_date"] = ["<=", end_date]

#         order_by = "from_date desc"

#         shift_requests = frappe.get_all(
#             "Shift Request",
#             filters=filters,
#             fields=["shift_type", "employee", "approver", "from_date", "to_date", "name","status","custom_remarks"],
#             order_by=order_by
#         )

#         return {
#             "success": True,
#             "message": "Shift requests fetched successfully",
#             "data": shift_requests
#         }

#     except Exception as e:
#         error_message = f"Error fetching shift requests: {str(e)}"
#         frappe.log_error(error_message, "Shift Request API Error")

#         return {
#             "success": False,
#             "message": error_message,
#             "data": None
#         }
@frappe.whitelist()
def get_shift_requests(
    view_type="self",   # self / team
    filters=None,
    order_by="from_date desc",
    limit_page_length=None,
    limit_start=0,
):
    try:
        user = frappe.session.user

        # Parse filters safely
        filters = frappe.parse_json(filters) if filters else []

        if isinstance(filters, dict):
            filters = [[k, "=", v] for k, v in filters.items()]

        # Get employee linked with logged-in user
        employee = frappe.db.get_value(
            "Employee",
            {"user_id": user},
            "name"
        )

        if not employee:
            frappe.throw("Employee not linked with current user")

        if view_type == "self":
            filters.append(["employee", "=", employee])

        elif view_type == "team":
            filters.append(["employee", "!=", employee])

        else:
            frappe.throw("Invalid view_type. Use 'self' or 'team'.")

        # 🔹 Total count (without pagination)
        total_records = frappe.get_list(
            "Shift Request",
            filters=filters
        )

        # 🔹 Main records with pagination
        records = frappe.get_list(
            "Shift Request",
            filters=filters,
            fields=[
                "name",
                "employee",
                "employee_name",
                "shift_type",
                "from_date",
                "to_date",
                "status",
                "approver",
                "workflow_state",
                "custom_remarks",
                "creation",
                "department",
                "company"
            ],
            order_by=order_by,
            limit_page_length=cint(limit_page_length) if limit_page_length else None,
            limit_start=cint(limit_start)
        )

        # Clean HTML from remarks (if any)
        for row in records:
            if row.get("custom_remarks"):
                row["custom_remarks"] = strip_html(row["custom_remarks"]).strip()

        return {
            "success": True,
            "data": records,
            "total_records": len(total_records),
            "count": len(records),
            "message": "Shift Request List Loaded Successfully!"
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Shift Request API Error")
        return {
            "success": False,
            "message": str(e)
        }

# @frappe.whitelist()
# def create_shift_request(data):

#     try:
#         if isinstance(data, str):
#             data = frappe.parse_json(data)

#         employee = data.get("employee")
#         shift_type = data.get("shift_type")
#         from_date = data.get("from_date")
#         to_date = data.get("to_date")
#         remarks = data.get("remarks")  
#         approver=data.get("approver")

#         if not employee or not shift_type or not from_date or not to_date:
#             return {
#                 "success": False,
#                 "message": "Missing required fields",
#                 "data": None
#             }
#         shift_request = frappe.get_doc({
#             "doctype": "Shift Request",
#             "employee": employee,
#             "shift_type": shift_type,
#             "from_date": from_date,
#             "to_date": to_date,
#             "custom_remarks": remarks,
#             "approver": approver
#         })
#         # ✅ THIS LINE IS CRITICAL
#         shift_request.flags.skip_approver_validation = True

#         shift_request.insert(ignore_permissions=True)

#         return {
#             "success": True,
#             "message": "Shift request created successfully",
#             "data": {"name": shift_request.name}
#         }

#     except Exception as e:
#         error_message = f"Error creating shift request: {str(e)}"
#         frappe.log_error(error_message, "Shift Request Create API Error")

#         return {
#             "success": False,
#             "message": error_message,
#             "data": None
#         }

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
        approver = data.get("approver")
        status = data.get("status")  # Approved / Rejected / None
        name = data.get("name")  # Required if updating existing request
        if not employee:
            return {
                "success": False,
                "message": "Employee is required",
                "data": None
            }

        if status and name:

            shift_request = frappe.get_doc("Shift Request", name)

            if shift_request.docstatus == 2:
                return {
                    "success": False,
                    "message": "Document already cancelled",
                    "data": None
                }

            shift_request.status = status
            shift_request.custom_remarks = remarks

            shift_request.flags.skip_approver_validation = True
            shift_request.save(ignore_permissions=True)
            if shift_request.docstatus == 0:
                shift_request.submit()

            return {
                "success": True,
                "message": f"Shift request {status} and submitted successfully",
                "data": {
                    "name": shift_request.name,
                    "status": shift_request.status,
                    "docstatus": shift_request.docstatus
                }
            }
        else:
            if not shift_type or not from_date or not to_date:
                return {
                    "success": False,
                    "message": "Missing required fields",
                    "data": None
                }

            shift_request = frappe.get_doc({
                "doctype": "Shift Request",
                "employee": employee,
                "shift_type": shift_type,
                "from_date": from_date,
                "to_date": to_date,
                "custom_remarks": remarks,
                "approver": approver
            })

            shift_request.flags.skip_approver_validation = True
            shift_request.insert(ignore_permissions=True)

            return {
                "success": True,
                "message": "Shift request created successfully",
                "data": {
                    "name": shift_request.name,
                    "status": shift_request.status,
                    "docstatus": shift_request.docstatus
                }
            }

    except Exception as e:
        error_message = f"Error in Shift Request API: {str(e)}"
        frappe.log_error(error_message, "Shift Request API Error")

        return {
            "success": False,
            "message": error_message,
            "data": None
        }
        
        
import frappe
from frappe.utils import getdate


# @frappe.whitelist()
# def determine_shift_types(doctype, txt, searchfield, start, page_len, filters):

#     branch = filters.get("branch")
#     date_str = filters.get("as_on_date")
#     employee_id = filters.get("emp_id")

#     if not branch or not employee_id:
#         return []

#     as_on_date = getdate(date_str) if date_str else getdate()

#     emp_attendance_source = frappe.get_value(
#         "Employee",
#         employee_id,
#         "custom_attendance_source"
#     )

#     conditions = {}

#     allowed_roles_str = frappe.db.get_single_value(
#         "HR Settings",
#         "custom_roles_allowed_to_assign_24hours_shift"
#     )

#     allowed_roles = []
#     if allowed_roles_str:
#         allowed_roles = [
#             r.strip()
#             for r in allowed_roles_str.split(",")
#             if r.strip()
#         ]

#     # Roles of current employee user
#     user_id = frappe.db.get_value("Employee", employee_id, "user_id")

#     employee_roles = []

#     if user_id:
#         employee_roles = frappe.get_roles(user_id)
#     print(employee_roles)
#     allow_24_hours = bool(
#         set(employee_roles).intersection(set(allowed_roles))
#     )
#     # ---------------------------------------------------------
#     # BRANCH SPECIFIC LOGIC
#     # ---------------------------------------------------------

#     if branch == "Jammu and Kashmir Milk Producers Co-operative Ltd Cheshmashahi Srinagar":

#         if emp_attendance_source:

#             if emp_attendance_source == "Biometric":
#                 conditions["custom_attendance_source"] = [
#                     "not in",
#                     ["Field", "Punch"]
#                 ]

#             elif emp_attendance_source == "Punch":
#                 conditions["custom_attendance_source"] = [
#                     "!=",
#                     "Field"
#                 ]
#                 conditions["name"] = [
#                     "not in",
#                     [
#                         "Srinagar-General-8hours",
#                         "Srinagar-General-7hours"
#                     ]
#                 ]

#             elif emp_attendance_source == "Field":
#                 conditions["custom_attendance_source"] = [
#                     "!=",
#                     "Punch"
#                 ]
#                 conditions["name"] = [
#                     "not in",
#                     [
#                         "Srinagar-General-8hours",
#                         "Srinagar-General-7hours"
#                     ]
#                 ]

#         if 4 <= as_on_date.month <= 9:
#             required_hours = "8hours"
#         else:
#             required_hours = "7hours"

#     elif branch == "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu":

#         if emp_attendance_source:

#             if emp_attendance_source in ["Biometric", "Punch"]:
#                 conditions["custom_attendance_source"] = [
#                     "not in",
#                     ["Field", "Punch"]
#                 ]

#             elif emp_attendance_source == "Field":
#                 conditions["name"] = [
#                     "not in",
#                     [
#                         "Jammu-General-8hours",
#                         "Jammu-General-7hours"
#                     ]
#                 ]

#         gender = frappe.db.get_value(
#             "Employee",
#             employee_id,
#             "gender"
#         )

#         is_female = gender == "Female"

#         if is_female:
#             if (4 <= as_on_date.month <= 11) or (2 <= as_on_date.month <= 3):
#                 required_hours = "8hours"
#             else:
#                 required_hours = "7hours"
#         else:
#             required_hours = "8hours"

#     else:
#         return []

#     # ---------------------------------------------------------
#     # FINAL FILTER CONDITIONS
#     # ---------------------------------------------------------

#     conditions.update({
#         "custom_hours": required_hours,
#         "custom_branch": branch
#     })

#     # 🔴 Hide 24 hours shift if role not allowed
#     if not allow_24_hours:
#         conditions["custom_shift_type"] = ["!=", "24 hours"]

#     # ---------------------------------------------------------
#     # FETCH SHIFT TYPES
#     # ---------------------------------------------------------

#     shift_types = frappe.db.get_list(
#         "Shift Type",
#         filters=conditions,
#         fields=["name"],
#         order_by="name",
#         start=start,
#         page_length=page_len,
#         ignore_permissions=True
#     )

#     return [[s.name, s.name] for s in shift_types] or []

@frappe.whitelist()
def determine_shift_types(doctype, txt, searchfield, start, page_len, filters):

    branch = filters.get("branch")
    date_str = filters.get("as_on_date")
    employee_id = filters.get("emp_id")

    if not branch or not employee_id:
        return []

    # ✅ If date not provided, do NOT auto use today
    as_on_date = getdate(date_str) if date_str else None

    emp_attendance_source = frappe.get_value(
        "Employee",
        employee_id,
        "custom_attendance_source"
    )

    conditions = {}

    allowed_roles_str = frappe.db.get_single_value(
        "HR Settings",
        "custom_roles_allowed_to_assign_24hours_shift"
    )

    allowed_roles = []
    if allowed_roles_str:
        allowed_roles = [
            r.strip()
            for r in allowed_roles_str.split(",")
            if r.strip()
        ]

    # Roles of current employee user
    user_id = frappe.db.get_value("Employee", employee_id, "user_id")
    employee_roles = []

    if user_id:
        employee_roles = frappe.get_roles(user_id)

    allow_24_hours = bool(
        set(employee_roles).intersection(set(allowed_roles))
    )

    required_hours = None  # ✅ default

    # ---------------------------------------------------------
    # BRANCH SPECIFIC LOGIC
    # ---------------------------------------------------------

    if branch == "Jammu and Kashmir Milk Producers Co-operative Ltd Cheshmashahi Srinagar":

        if emp_attendance_source:

            if emp_attendance_source == "Biometric":
                conditions["custom_attendance_source"] = [
                    "not in",
                    ["Field", "Punch"]
                ]

            elif emp_attendance_source == "Punch":
                conditions["custom_attendance_source"] = ["!=", "Field"]
                conditions["name"] = [
                    "not in",
                    ["Srinagar-General-8hours", "Srinagar-General-7hours"]
                ]

            elif emp_attendance_source == "Field":
                conditions["custom_attendance_source"] = ["!=", "Punch"]
                conditions["name"] = [
                    "not in",
                    ["Srinagar-General-8hours", "Srinagar-General-7hours"]
                ]

        # ✅ Apply month logic ONLY if date provided
        if as_on_date:
            if 4 <= as_on_date.month <= 9:
                required_hours = "8hours"
            else:
                required_hours = "7hours"

    elif branch == "Jammu and Kashmir Milk Producers Co-operative Ltd Satwari Jammu":

        if emp_attendance_source:

            if emp_attendance_source in ["Biometric", "Punch"]:
                conditions["custom_attendance_source"] = [
                    "not in",
                    ["Field", "Punch"]
                ]

            elif emp_attendance_source == "Field":
                conditions["name"] = [
                    "not in",
                    ["Jammu-General-8hours", "Jammu-General-7hours"]
                ]

        gender = frappe.db.get_value("Employee", employee_id, "gender")
        is_female = gender == "Female"

        # ✅ Apply month logic ONLY if date provided
        if as_on_date:
            if is_female:
                if (4 <= as_on_date.month <= 11) or (2 <= as_on_date.month <= 3):
                    required_hours = "8hours"
                else:
                    required_hours = "7hours"
            else:
                required_hours = "8hours"

    else:
        return []

    # ---------------------------------------------------------
    # FINAL FILTER CONDITIONS
    # ---------------------------------------------------------

    conditions["custom_branch"] = branch

    # ✅ Apply hours filter only if date provided
    if required_hours:
        conditions["custom_hours"] = required_hours

    # ✅ Hide 24 hours shift if role not allowed
    if not allow_24_hours:
        conditions["custom_shift_type"] = ["!=", "24 hours"]

    # ---------------------------------------------------------
    # FETCH SHIFT TYPES
    # ---------------------------------------------------------

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


# ---------------------------------------------------------
# API WRAPPER
# ---------------------------------------------------------

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
