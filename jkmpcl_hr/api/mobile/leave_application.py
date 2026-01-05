import os
import uuid
import frappe
from frappe.utils import getdate
from frappe.utils.file_manager import save_file
import shutil

from jkmpcl_hr.py.utils import get_other_department_emp


#leave type list api
@frappe.whitelist()
def get_leave_types():
    try:
        leave_types = frappe.get_all(
            "Leave Type",
            pluck="name"
        )

    except Exception as e:
        frappe.log_error("Error While Getting Leave Types", str(e))
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success": False,
            "message": f"Error while fetching leave types: {str(e)}",
            "data": None
        }

    else:
        frappe.local.response["message"] = {
            "success": True,
            "message": "Leave types fetched successfully",
            "data": leave_types
        }


@frappe.whitelist()
def get_user_for_cc(emp_id):
    try:
        user_list = get_other_department_emp(emp_id) or []

    except Exception as e:
        frappe.log_error("Error While Getting Users", str(e))
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success": False,
            "message": f"Error while fetching Users: {str(e)}",
            "data": None
        }
    else:
        frappe.local.response["message"] = {
            "success": True,
            "message": "User fetched successfully",
            "data": user_list
        }


@frappe.whitelist()
def list(
    filters=None,
    or_filters=None,
    fields=["name","employee","leave_type","from_date","to_date","status","total_leave_days","leave_approver_name","leave_approver_name","workflow_state","description","custom_half_day_time","half_day_date","half_day"],
    order_by=None,
    limit_page_length=0,
    limit_start=0,
):
    try:
        employee = frappe.db.get_value(
            "Employee",
            {"user_id": frappe.session.user},
            "name"
        )

        if not employee:
            frappe.throw("Employee not linked with current user")

        employee_list = [employee]

        filters = frappe.parse_json(filters) if filters else []

        if isinstance(filters, dict):
            filters = [[k, "=", v] for k, v in filters.items()]

        filters.append(["employee", "in", employee_list])

        parsed_fields = frappe.parse_json(fields)

        if "employee" not in parsed_fields:
            parsed_fields.append("employee")

        leave_application_list_raw = frappe.get_list(
            "Leave Application",
            filters=filters,
            or_filters=or_filters,
            fields=parsed_fields,
            order_by=order_by,
            limit_page_length=limit_page_length,
            limit_start=limit_start
        )

        total_count = len(leave_application_list_raw)

    except Exception as e:
        frappe.log_error("Error While Getting Leave Application List", str(e))
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success": False,
            "message": str(e),
            "data": None
        }

    else:
        frappe.local.response["message"] = {
            "success": True,
            "message": "Leave Application List Loaded Successfully!",
            "data": leave_application_list_raw,
            "count": total_count
        }






@frappe.whitelist()
def create(**args):
    try:

        mandatory_fields = {
            "employee": "Employee",
            "leave_type": "Leave Type",
            "from_date": "From Date",
            "to_date": "To Date",
            "posting_date": "Posting Date",
            "status": "Status"
        }

        for field, label in mandatory_fields.items():
            if not args.get(field):
                frappe.throw(f"Please Fill {label}", frappe.MandatoryError)

        if not args.get("leave_approver"):
            leave_approver = frappe.db.get_value(
                "Employee",
                args.get("employee"),
                "leave_approver"
            )

            if not leave_approver:
                leave_approver = frappe.db.get_value(
                    "Employee",
                    args.get("employee"),
                    "reports_to"
                )

            if not leave_approver:
                frappe.throw("Leave Approver not set for this Employee")

            leave_approver_name = frappe.db.get_value(
                "Employee",
                {"user_id":leave_approver},
                "employee_name"
            )
            args["leave_approver"] = leave_approver
            args["leave_approver_name"] = leave_approver_name

        args["from_date"] = getdate(args.get("from_date"))
        args["to_date"] = getdate(args.get("to_date"))
        args["posting_date"] = getdate(args.get("posting_date"))

        if args.get("half_day") in ("1", "true", "True"):
            if not args.get("half_day_date"):
                frappe.throw("Half Day Date is required")
            args["half_day_date"] = getdate(args.get("half_day_date"))

        if args.get("custom_email_cc"):
            args["custom_email_cc"] = frappe.parse_json(args.get("custom_email_cc"))

        leave_doc = frappe.get_doc({
            "doctype": "Leave Application",
            **args
        })

        leave_doc.insert(ignore_permissions=True)

        temp_files = []
        uploaded_files = frappe.request.files.getlist("file")

        if uploaded_files:
            temp_dir = frappe.get_site_path("private", "leave_temp")
            os.makedirs(temp_dir, exist_ok=True)

            for f in uploaded_files:
                ext = os.path.splitext(f.filename)[1]
                temp_name = f"{uuid.uuid4().hex}{ext}"
                temp_path = os.path.join(temp_dir, temp_name)

                with open(temp_path, "wb") as tmp:
                    shutil.copyfileobj(f.stream, tmp)

                temp_files.append(temp_path)

            frappe.enqueue(
                "jkmpcl_hr.api.mobile.leave_application.upload_leave_files",
                queue="short",
                leave_application=leave_doc.name,
                temp_files=temp_files
            )

        return {
            "success": True,
            "message": "Leave Application Created",
            "data": {"leave_application": leave_doc.name}
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Leave Create API Error")
        return {
            "success": False,
            "message": str(e),
            "data": None
        }



def upload_leave_files(leave_application, temp_files):
    try:
        for path in temp_files:
            if not os.path.exists(path):
                continue

            with open(path, "rb") as f:
                content = f.read()

            save_file(
                fname=os.path.basename(path),
                content=content,
                dt="Leave Application",
                dn=leave_application,
                is_private=0
            )

            os.remove(path)  # cleanup

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Leave File Upload Job Error"
        )


@frappe.whitelist()
def status_list():
    return {
        "success": True,
        "message": "Status fetched successfully",
        "data": [
            {
                "status": "Open",
                "color": "#FFA500"  
            },
            {
                "status": "Approved",
                "color": "#4CAF50"  
            },
            {
                "status": "Rejected",
                "color": "#F44336"   
            },
            {
                "status": "Cancelled",
                "color": "#9E9E9E"  
            }
        ]
    }
    
    
@frappe.whitelist()
def get_valid_comp_off(employeeId, from_date, to_date, leave_type_name):
    from_date = getdate(from_date)
    to_date = getdate(to_date)

    if from_date != to_date:
        return {
            "valid": False,
            "message": "Compensatory Off is applicable for only one day.",
            "allowed_date": from_date
        }

    leave_allocation = frappe.db.get_all(
        "Leave Allocation",
        filters={
            "employee": employeeId,
            "leave_type": leave_type_name,
            "docstatus": 1,
            "from_date": ["<=", from_date],
            "to_date": [">=", from_date]
        },
        fields=["name"],
        order_by="from_date asc"
    )

    if not leave_allocation:
        return {
            "valid": False,
            "message": "No valid Compensatory Off allocation found."
        }

    for allocation in leave_allocation:
        record = frappe.db.get_value(
            "Off-Day Work Request",
            {
                "employee": employeeId,
                "comp_off_created": 1,
                "leave_allocation": allocation.name,
                "leave_application": ["is", "not set"],
                "docstatus": 1
            },
            ["name", "date"],
            as_dict=True
        )

        if record:
            return {
                "valid": True,
                "date": record.date,
                "message": "Valid Compensatory Off available."
            }

    return {
        "valid": False,
        "message": "Compensatory Off already used or expired."
    }
