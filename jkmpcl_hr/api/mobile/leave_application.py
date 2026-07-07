import os
import uuid
import frappe
from frappe.utils import getdate,strip_html
from frappe.utils.file_manager import save_file
import shutil
import re
from jkmpcl_hr.py.utils import get_other_department_emp
from frappe import _
import traceback
from jkmpcl_hr.jkmpcl_hr.doctype.attendance_lock.attendance_lock import AttendanceLock
from frappe.utils import (
    add_days,
    date_diff,
    formatdate,cint
)

@frappe.whitelist()
def validate_leave_for_mobile(
    leave_type,
    from_date,
    to_date,
    no_of_surviving_children=None,
    adopting_child_age=None,
    half_day=0
):
    try:
        leave_details = frappe.get_doc("Leave Type", leave_type)

        response_data = {}

        # Compensatory Off rules
        if leave_details.is_compensatory:

            if from_date != to_date:
                return {
                    "success": False,
                    "message": _("For Compensatory Off, From Date and To Date must be the same."),
                    "data": None
                }
        
            # Half Day not allowed for Compensatory Off
            if cint(half_day):
                return {
                    "success": False,
                    "message": _("Half Day leave is not allowed for Compensatory Off."),
                    "data": None
                }
            if leave_details.custom_applied_once:
                response_data["total_leave_days"] = 1.0

        # Maternity / Adoption rules
        if leave_details.custom_leave_type in [
            "Maternity Leave",
            "Child Adoption Leave",
            "Special Maternity Leave"
        ]:

            if int(no_of_surviving_children or 0) > 2:
                return {
                    "success": False,
                    "message": _(
                        "You are not eligible for {0}. Please choose another Leave Type."
                    ).format(leave_details.custom_leave_type),
                    "data": None
                }

            if (
                leave_details.custom_leave_type == "Child Adoption Leave"
                and not (adopting_child_age and float(adopting_child_age) <= 1)
            ):
                return {
                    "success": False,
                    "message": _(
                        "You are not eligible for {0}. Please choose another Leave Type."
                    ).format(leave_details.custom_leave_type),
                    "data": None
                }

        return {
            "success": True,
            "message": _("Validation successful"),
            "data": response_data
        }

    except Exception as e:
        frappe.log_error("Leave Mobile Validation API Error", frappe.get_traceback())
        frappe.clear_messages()

        return {
            "success": False,
            "message": f"Internal error while validating leave: {str(e)}",
            "data": None
        }

@frappe.whitelist()
def get_days_for_ml(employee, leave_type, maternity_leave_type=None, from_date=None):
    try:
        from frappe.utils import getdate, date_diff, flt
        from math import floor
        import calendar

        if from_date:
            from_date = getdate(from_date)
        else:
            from_date = getdate()

        joining_date = frappe.db.get_value(
            "Employee", employee, "date_of_joining"
        )

        if not joining_date:
            return {
                "success": False,
                "message": f"Date of Joining not set for Employee {employee}",
                "data": None
            }

        joining_date = getdate(joining_date)
        serving_days = date_diff(from_date, joining_date)

        year = from_date.year
        total_days_in_year = 366 if calendar.isleap(year) else 365

        # Special Maternity Leave
        if leave_type == "Special Maternity Leave":
            return {
                "success": True,
                "message": "Days calculated successfully",
                "data": {
                    "days": 90
                }
            }

        # Miscarriage / Abortion case
        if leave_type == "Maternity Leave" and maternity_leave_type in [
            "Miscarriage",
            "Abortion"
        ]:
            full_entitlement = 42
        else:
            full_entitlement = 90

        # Completed 1 year
        if serving_days >= total_days_in_year:
            return {
                "success": True,
                "message": "Days calculated successfully",
                "data": {
                    "days": full_entitlement
                }
            }

        # LWP leave types
        lwp_leave_types = frappe.get_all(
            "Leave Type",
            filters={"is_lwp": 1},
            pluck="name",
        )

        # Working days count
        working_days = len(
            frappe.get_all(
                "Attendance",
                filters={
                    "employee": employee,
                    "attendance_date": ["between", [joining_date, from_date]],
                    "status": ["in", ["Present", "Work From Home", "Half Day", "On Leave"]],
                    "leave_type": ["not in", lwp_leave_types],
                },
                pluck="name",
            )
        )

        pro_rata_days = (full_entitlement * working_days) / total_days_in_year

        integer_part = floor(pro_rata_days)
        decimal_part = pro_rata_days - integer_part

        final_days = integer_part + 1 if decimal_part >= 0.5 else integer_part

        return {
            "success": True,
            "message": "Days calculated successfully",
            "data": {
                "days": flt(final_days)
            }
        }

    except Exception:
        frappe.log_error("error_get_days_for_ml", frappe.get_traceback())

        return {
            "success": False,
            "message": "Error while calculating maternity leave days",
            "data": None
        }


#leave type list api
# @frappe.whitelist()
# def get_leave_types():
#     try:
#         leave_types = frappe.get_all(
#             "Leave Type",
#             pluck="name"
#         )

#     except Exception as e:
#         frappe.log_error("Error While Getting Leave Types", str(e))
#         frappe.clear_messages()
#         frappe.local.response["message"] = {
#             "success": False,
#             "message": f"Error while fetching leave types: {str(e)}",
#             "data": None
#         }

#     else:
#         frappe.local.response["message"] = {
#             "success": True,
#             "message": "Leave types fetched successfully",
#             "data": leave_types
#         }

@frappe.whitelist()
def get_leave_types(employeeId, as_on_date=None):

    try:
        from frappe.utils import today
        from hrms.hr.doctype.leave_application.leave_application import get_leave_details

        if not employeeId:
            frappe.throw("Employee is required")

        if not as_on_date:
            as_on_date = today()

        leave_details = get_leave_details(
            employee=employeeId,
            date=as_on_date
        ) or {}
        allocated = leave_details.get("leave_allocation")
        lwps = leave_details.get("lwps")

        if not allocated:
            allocated = {}

        if not lwps:
            lwps = []

        allowed_leave_types = []

        for k in allocated.keys():
            allowed_leave_types.append(k)

        for l in lwps:
            allowed_leave_types.append(l)

        
        open_leave_types = get_open_leave_types(employeeId)
        if not open_leave_types:
            open_leave_types = []

        final_leave_types = []

        for lt in allowed_leave_types:
            if lt not in final_leave_types:
                final_leave_types.append(lt)
        for lt in open_leave_types:
            if lt not in final_leave_types:
                final_leave_types.append(lt)

    except Exception:

        frappe.log_error(
            "Mobile Leave API Crash",
            frappe.get_traceback()
        )

        frappe.local.response["message"] = {
            "success": False,
            "message": "Internal Server Error",
            "data": None
        }

    else:

        frappe.local.response["message"] = {
            "success": True,
            "message": "Leave types fetched successfully",
            "data": final_leave_types
        }



@frappe.whitelist()
def get_open_leave_types(employee=None):

    from frappe.utils import getdate, add_years

    only_for_female_leave_types = [
        "Maternity Leave",
        "Child Adoption Leave",
        "Special Maternity Leave"
    ]

    if not employee:
        return []

    gender = frappe.db.get_value("Employee", employee, "gender")
    joining_date = frappe.db.get_value("Employee", employee, "date_of_joining")

    is_female = gender == "Female"

    if is_female:

        if joining_date and getdate() >= add_years(joining_date, 2):
            return frappe.get_all(
                "Leave Type",
                filters={"custom_is_open_leave": 1},
                pluck="name",
                ignore_permissions=True
            ) or []

        return frappe.get_all(
            "Leave Type",
            filters={
                "custom_is_open_leave": 1,
                "name": ["not in", ["Special Maternity Leave"]]
            },
            pluck="name",
            ignore_permissions=True
        ) or []

    return frappe.get_all(
        "Leave Type",
        filters={
            "custom_is_open_leave": 1,
            "name": ["not in", only_for_female_leave_types]
        },
        pluck="name",
        ignore_permissions=True
    ) or []


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

from frappe.model.workflow import get_transitions
# @frappe.whitelist()
# def list(
#     filters=None,
#     or_filters=None,
#     fields=["name","employee","leave_type","from_date","to_date","status","workflow_state","total_leave_days","leave_approver_name","workflow_state","description","custom_half_day_time","half_day_date","half_day","custom_proof_document"],
#     order_by=None,
#     limit_page_length=0,
#     limit_start=0,
# ):
#     try:
#         employee = frappe.db.get_value(
#             "Employee",
#             {"user_id": frappe.session.user},
#             "name"
#         )

#         if not employee:
#             frappe.throw("Employee not linked with current user")

#         employee_list = [employee]

#         filters = frappe.parse_json(filters) if filters else []

#         if isinstance(filters, dict):
#             filters = [[k, "=", v] for k, v in filters.items()]

#         filters.append(["employee", "in", employee_list])

#         parsed_fields = frappe.parse_json(fields)

#         if "employee" not in parsed_fields:
#             parsed_fields.append("employee")

#         leave_application_list_raw = frappe.get_list(
#             "Leave Application",
#             filters=filters,
#             or_filters=or_filters,
#             fields=parsed_fields,
#             order_by=order_by,
#             limit_page_length=limit_page_length,
#             limit_start=limit_start
#         )

#         total_count = len(leave_application_list_raw)

#     except Exception as e:
#         frappe.log_error("Error While Getting Leave Application List", str(e))
#         frappe.clear_messages()
#         frappe.local.response["message"] = {
#             "success": False,
#             "message": str(e),
#             "data": None
#         }

#     else:
#         frappe.local.response["message"] = {
#             "success": True,
#             "message": "Leave Application List Loaded Successfully!",
#             "data": leave_application_list_raw,
#             "count": total_count
#         }


# @frappe.whitelist()
# def list(
#     view_type="self",   # self / team
#     filters=None,
#     fields=None,
#     order_by="creation desc",
#     limit_page_length=None,
#     limit_start=0,
# ):
#     try:
#         user = frappe.session.user

#         # Parse filters safely
#         filters = frappe.parse_json(filters) if filters else []

#         if isinstance(filters, dict):
#             filters = [[k, "=", v] for k, v in filters.items()]

#         # Get logged-in employee
#         employee = frappe.db.get_value(
#             "Employee",
#             {"user_id": user},
#             "name"
#         )

#         if not employee:
#             frappe.throw("Employee not linked with current user")

#         if view_type == "self":
#             filters.append(["employee", "=", employee])


#         elif view_type == "team":
#             filters.append(["employee", "!=", employee])

#         else:
#             frappe.throw("Invalid view_type. Use 'self' or 'team'.")

#         leave_list = frappe.get_list(
#             "Leave Application",
#             filters=filters,
#             fields=fields or [
#                 "name","employee","employee_name",
#                 "leave_type","from_date","to_date",
#                 "status","workflow_state","total_leave_days",
#                 "leave_approver_name","description",
#                 "custom_half_day_time","half_day_date",
#                 "half_day","custom_proof_document"
#             ],
#             order_by=order_by,
#             limit_page_length=limit_page_length,
#             limit_start=limit_start
#         )
#         total_records = frappe.get_list(
#             "Leave Application",
#             filters=filters
#         )
#         return {
#             "success": True,
#             "data": leave_list,
#             "count": len(leave_list),
#             "total_count": len(total_records),
#             "message": "Leave Application List Loaded Successfully!",
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Leave List API Error")
#         return {
#             "success": False,
#             "message": str(e)
#         }


@frappe.whitelist()
def list(
    view_type="self",   # self / team
    filters=None,
    fields=None,
    order_by="creation desc",
    limit_page_length=None,
    limit_start=0,
):
    try:
        user = frappe.session.user

        # Parse filters safely
        filters = frappe.parse_json(filters) if filters else []

        if isinstance(filters, dict):
            filters = [[k, "=", v] for k, v in filters.items()]

        # Get logged-in employee
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

        leave_list = frappe.get_list(
            "Leave Application",
            filters=filters,
            fields=fields or [
                "name", "employee", "employee_name",
                "leave_type", "from_date", "to_date",
                "status", "workflow_state", "total_leave_days",
                "leave_approver_name", "description",
                "custom_half_day_time", "half_day_date",
                "half_day", "custom_proof_document",
                "docstatus",
            ],
            order_by=order_by,
            limit_page_length=limit_page_length,
            limit_start=limit_start
        )

        total_records = frappe.get_list(
            "Leave Application",
            filters=filters
        )

        # -------------------------
        # Detect current user's manager role in team view
        # -------------------------
        current_manager_role = None  # 'reporting', 'review', or 'hr'

        if view_type == "team":
            today = frappe.utils.today()

            role_check = frappe.db.sql("""
                SELECT DISTINCT parentfield
                FROM `tabApprover`
                WHERE user = %(user)s
                AND effective_from <= %(today)s
                AND parenttype = 'Employee'
                AND parentfield IN (
                    'custom_reporting_manager',
                    'custom_review_manager',
                    'custom_hr_manager'
                )
            """, {
                "user": user,
                "today": today
            }, pluck="parentfield")

            # Priority: if user has multiple roles, pick the highest level
            if 'custom_hr_manager' in role_check:
                current_manager_role = 'hr'
            elif 'custom_review_manager' in role_check:
                current_manager_role = 'review'
            elif 'custom_reporting_manager' in role_check:
                current_manager_role = 'reporting'

        # -------------------------
        # Workflow states
        # ⚠️ Replace with your actual Leave Application workflow state names
        # -------------------------
        REPORTING_MGR_APPROVED_STATES = {
            "Pending Review Manager Approval",
            "Approved by Reporting Manager",
            "Approved by Review Manager",
            "Pending HR Approval",
            "Approved by HR Manager",
            "Approved",
        }

        REVIEW_MGR_APPROVED_STATES = {
            "Approved by Review Manager",
            "Pending HR Approval",
            "Approved by HR Manager",
            "Approved",
        }

        # -------------------------
        # Build final records with enable flag
        # -------------------------
        for row in leave_list:
            if view_type == "team" and current_manager_role:
                wf = row.get("workflow_state") or ""
                ds = row.get("docstatus", 0)

                if current_manager_role == "reporting":
                    # Reporting manager acts first — never enable
                    row["enable"] = False

                elif current_manager_role == "review":
                    # enable until reporting manager has approved
                    row["enable"] = not (
                        wf in REPORTING_MGR_APPROVED_STATES or ds == 1
                    )

                elif current_manager_role == "hr":
                    # enable until review manager has approved
                    row["enable"] = not (
                        wf in REVIEW_MGR_APPROVED_STATES or ds == 1
                    )
            else:
                row["enable"] = False

        # -------------------------
        # Sort so enable=True rows appear first.
        # Python's sort is stable, so within each group (True/False)
        # rows keep the relative order from the original order_by.
        # -------------------------
        leave_list = sorted(leave_list, key=lambda r: not r["enable"])

        # -------------------------
        # Clean up response fields
        # -------------------------
        for row in leave_list:
            # Remove docstatus from response if not in original fields
            if not fields or "docstatus" not in fields:
                row.pop("docstatus", None)

        return {
            "success": True,
            "data": leave_list,
            "count": len(leave_list),
            "total_records": len(total_records),
            "message": "Leave Application List Loaded Successfully!",
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Leave List API Error")
        return {
            "success": False,
            "message": str(e)
        }


from jkmpcl_hr.py.utils import get_emp_reporting_manager

from frappe.utils import today, getdate


# @frappe.whitelist()
# def create(**args):
#     try:

#         mandatory_fields = {
#             "employee": "Employee",
#             "leave_type": "Leave Type",
#             "from_date": "From Date",
#             "to_date": "To Date",
#             "posting_date": "Posting Date",
#             "status": "Status"
#         }

#         for field, label in mandatory_fields.items():
#             if not args.get(field):
#                 frappe.throw(f"Please Fill {label}", frappe.MandatoryError)
#         employee = args.get("employee")

#         if not args.get("leave_approver"):

#             leave_approver = get_emp_reporting_manager(
#                 employee,
#                 args.get("from_date") or today()
#             )
#             if not leave_approver:
#                 leave_approver = frappe.db.get_value(
#                     "Employee",
#                     employee,
#                     "leave_approver"
#                 )
#             leave_approver_name = frappe.db.get_value(
#                 "Employee",
#                 {"user_id": leave_approver},
#                 "employee_name"
#             )
#             args["leave_approver"] = leave_approver
#             args["leave_approver_name"] = leave_approver_name

#         args["from_date"] = getdate(args.get("from_date"))
#         args["to_date"] = getdate(args.get("to_date"))
#         args["posting_date"] = getdate(args.get("posting_date"))
#         args["custom_off_day_date"]=getdate(args.get("custom_off_day_date"))
#         args["custom_maternity_leave_type"]=args.get("custom_maternity_leave_type")
#         args["custom_no_of_surviving_children"]=args.get("custom_no_of_surviving_children")
#         # args["custom_off_day_date"]=getdate(args.get("custom_off_day_date"))
#         # args["custom_off_day_date"]=getdate(args.get("custom_off_day_date"))
        
#         if args.get("half_day") in ("1", "true", "True"):
#             if not args.get("half_day_date"):
#                 frappe.throw("Half Day Date is required")

#             args["half_day_date"] = getdate(args.get("half_day_date"))

#             if args.get("custom_half_day_time"):
#                 args["custom_half_day_time"] = args.get("custom_half_day_time")


#         if args.get("custom_email_cc"):
#             args["custom_email_cc"] = frappe.parse_json(args.get("custom_email_cc"))

#         leave_doc = frappe.get_doc({
#             "doctype": "Leave Application",
#             **args
#         })

#         leave_doc.insert(ignore_permissions=True)

#         temp_files = []
#         uploaded_files = frappe.request.files.getlist("file")

#         if uploaded_files:
#             temp_dir = frappe.get_site_path("private", "leave_temp")
#             os.makedirs(temp_dir, exist_ok=True)

#             for f in uploaded_files:
#                 ext = os.path.splitext(f.filename)[1]
#                 temp_name = f"{uuid.uuid4().hex}{ext}"
#                 temp_path = os.path.join(temp_dir, temp_name)

#                 with open(temp_path, "wb") as tmp:
#                     shutil.copyfileobj(f.stream, tmp)

#                 temp_files.append(temp_path)

#             frappe.enqueue(
#                 "jkmpcl_hr.api.mobile.leave_application.upload_leave_files",
#                 queue="short",
#                 leave_application=leave_doc.name,
#                 temp_files=temp_files
#             )

#         return {
#             "success": True,
#             "message": "Leave Application Created",
#             "data": {"leave_application": leave_doc.name}
#         }

#     except Exception as e:

#         frappe.log_error(
#             frappe.get_traceback(),
#             "Leave Create API Error"
#         )

#         clean_msg = re.sub(r"<[^>]*>", "", str(e))

#         return {
#             "success": False,
#             "message": clean_msg,
#             "data": None
#         }
@frappe.whitelist()
def create(**args):
    try:
        import os
        import uuid
        import shutil
        import re
        from frappe.utils import getdate, today, formatdate

        mandatory_fields = {
            "employee": "Employee",
            "leave_type": "Leave Type",
            "from_date": "From Date",
            "to_date": "To Date",
            "posting_date": "Posting Date",
            "status": "Status",
        }

        for field, label in mandatory_fields.items():
            if not args.get(field):
                frappe.throw(f"Please Fill {label}", frappe.MandatoryError)

        employee = args.get("employee")

        # -----------------------------
        # DATE CONVERSION
        # -----------------------------
        from_date = getdate(args.get("from_date"))
        to_date = getdate(args.get("to_date"))

        args["from_date"] = from_date
        args["to_date"] = to_date
        args["posting_date"] = getdate(args.get("posting_date"))

        # -----------------------------
        # Attendance Lock Check
        # -----------------------------
        for i in range(date_diff(to_date, from_date) + 1):

            d = add_days(from_date, i)

            lock_name = AttendanceLock.is_attendance_locked(
                d,
                employee
            )

            if lock_name:

                month = frappe.db.get_value(
                    "Attendance Lock",
                    lock_name,
                    "month"
                )

                if not month:
                    month = formatdate(d, "MMMM yyyy")

                frappe.throw(
                    f"Attendance is locked for {month}",
                    title="Attendance Lock"
                )

        # -----------------------------
        # APPROVER LOGIC
        # -----------------------------
        if not args.get("leave_approver"):

            leave_approver = get_emp_reporting_manager(
                employee,
                from_date or today(),
            )

            if not leave_approver:
                leave_approver = frappe.db.get_value(
                    "Employee",
                    employee,
                    "leave_approver",
                )

            leave_approver_name = frappe.db.get_value(
                "Employee",
                {"user_id": leave_approver},
                "employee_name",
            )

            args["leave_approver"] = leave_approver
            args["leave_approver_name"] = leave_approver_name

        # -----------------------------
        # OPTIONAL FIELDS
        # -----------------------------
        if args.get("custom_off_day_date"):
            args["custom_off_day_date"] = getdate(args.get("custom_off_day_date"))

        if args.get("half_day") in ("1", "true", "True"):
            if not args.get("half_day_date"):
                frappe.throw("Half Day Date is required")
            args["half_day_date"] = getdate(args.get("half_day_date"))

        if args.get("custom_maternity_leave_type"):
            args["custom_maternity_leave_type"] = str(args.get("custom_maternity_leave_type"))

        if args.get("custom_no_of_surviving_children"):
            args["custom_no_of_surviving_children"] = int(args.get("custom_no_of_surviving_children"))

        if args.get("custom_adopting_child_age"):
            args["custom_adopting_child_age"] = float(args.get("custom_adopting_child_age"))

        if args.get("custom_email_cc"):
            args["custom_email_cc"] = frappe.parse_json(args.get("custom_email_cc"))

        # -----------------------------
        # LEAVE VALIDATION (UNCHANGED)
        # -----------------------------
        leave_details = frappe.get_doc("Leave Type", args.get("leave_type"))

        if leave_details.is_compensatory:
            if from_date != to_date:
                return {
                    "success": False,
                    "message": "For Compensatory Off, From Date and To Date must be the same.",
                    "data": None,
                }

        if leave_details.custom_leave_type in [
            "Maternity Leave",
            "Child Adoption Leave",
            "Special Maternity Leave",
        ]:

            children = args.get("custom_no_of_surviving_children")
            adopting_age = args.get("custom_adopting_child_age")

            if int(children or 0) > 2:
                return {
                    "success": False,
                    "message": f"You are not eligible for {leave_details.custom_leave_type}. Please choose another Leave Type.",
                    "data": None,
                }

            if (
                leave_details.custom_leave_type == "Child Adoption Leave"
                and not (adopting_age and float(adopting_age) <= 1)
            ):
                return {
                    "success": False,
                    "message": f"You are not eligible for {leave_details.custom_leave_type}. Please choose another Leave Type.",
                    "data": None,
                }

        # -----------------------------
        # CREATE DOCUMENT
        # -----------------------------
        leave_doc = frappe.get_doc({
            "doctype": "Leave Application",
            **args,
        })

        leave_doc.insert(ignore_permissions=True)

        # -----------------------------
        # FILE UPLOAD (UNCHANGED)
        # -----------------------------
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
                temp_files=temp_files,
            )

        return {
            "success": True,
            "message": "Leave Application Created",
            "data": {"leave_application": leave_doc.name},
        }

    except Exception as e:
        import traceback

        error_message = None

        if frappe.local.message_log:
            log = frappe.local.message_log[0]
            error_message = log.get("message") if isinstance(log, dict) else str(log)

        if not error_message:
            error_message = str(e)

        error_message = strip_html(str(error_message))

        frappe.log_error(
            title="Leave Application API Error",
            message=traceback.format_exc()
        )

        return {
            "success": False,
            "message": error_message,
            "data": None,
        }



def upload_leave_files(leave_application, temp_files):
    try:
        from frappe.utils.file_manager import save_file

        first_file_url = None

        for path in temp_files:

            if not os.path.exists(path):
                continue

            with open(path, "rb") as f:
                content = f.read()

            file_doc = save_file(
                fname=os.path.basename(path),
                content=content,
                dt="Leave Application",
                dn=leave_application,
                is_private=0,
            )

            if not first_file_url:
                first_file_url = file_doc.file_url

            os.remove(path)

        if first_file_url:
            frappe.db.set_value(
                "Leave Application",
                leave_application,
                "custom_proof_document",
                first_file_url,
            )

            frappe.db.commit()

    except Exception:

        frappe.log_error(
            frappe.get_traceback(),
            "Leave File Upload Job Error",
        )
# def upload_leave_files(leave_application, temp_files):
#     try:
#         for path in temp_files:
#             if not os.path.exists(path):
#                 continue

#             with open(path, "rb") as f:
#                 content = f.read()

#             save_file(
#                 fname=os.path.basename(path),
#                 content=content,
#                 dt="Leave Application",
#                 dn=leave_application,
#                 is_private=0
#             )

#             os.remove(path)  # cleanup

#     except Exception:
#         frappe.log_error(
#             frappe.get_traceback(),
#             "Leave File Upload Job Error"
#         )


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
            leave_app_exists = frappe.db.exists("Leave Application", {"employee": employeeId, "custom_off_day_work_request": record.name, "docstatus": ["!=", 2]}, "name")
            
            if leave_app_exists:
                record = None
                continue
            else:
                return {
                    "valid": True,
                    "date": record.date,
                    "name":record.name,
                    "message": "Valid Compensatory Off available."
                }

    return {
        "valid": False,
        "message": "Compensatory Off already used or expired."
    }
