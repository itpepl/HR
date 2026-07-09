import frappe
from frappe.utils import getdate
from frappe.utils import now, add_to_date
from frappe.utils import strip_html
from frappe.utils import cint, getdate
from jkmpcl_hr.jkmpcl_hr.doctype.attendance_lock.attendance_lock import AttendanceLock
from frappe.utils import (
    add_days,
    date_diff,
    formatdate
)


@frappe.whitelist()
def get_shift_requests(
    view_type="self",
    filters=None,
    order_by="from_date desc",
    limit_page_length=None,
    limit_start=0,
):
    try:
        user = frappe.session.user

        filters = frappe.parse_json(filters) if filters else []

        if isinstance(filters, dict):
            filters = [[k, "=", v] for k, v in filters.items()]

        employee = frappe.db.get_value(
            "Employee",
            {"user_id": user},
            "name"
        )

        if not employee:
            frappe.throw("Employee not linked with current user")

        # -------------------------
        # TEAM LOGIC
        # -------------------------
        if view_type == "self":
            filters.append(["employee", "=", employee])

        elif view_type == "team":
            today = frappe.utils.today()

            candidate_employees = frappe.db.sql("""
                SELECT DISTINCT parent
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
            }, pluck="parent")

            employee_list = []

            if candidate_employees:
                placeholders = ", ".join(["%s"] * len(candidate_employees))

                all_entries = frappe.db.sql("""
                    SELECT parent, user, parentfield, effective_from
                    FROM `tabApprover`
                    WHERE parent IN ({placeholders})
                    AND effective_from <= %s
                    AND parenttype = 'Employee'
                    AND parentfield IN (
                        'custom_reporting_manager',
                        'custom_review_manager',
                        'custom_hr_manager'
                    )
                    ORDER BY parent ASC, parentfield ASC, effective_from DESC
                """.format(placeholders=placeholders),
                    tuple(candidate_employees) + (today,),
                    as_dict=True
                )

                seen = {}
                for entry in all_entries:
                    key = (entry["parent"], entry["parentfield"])
                    if key not in seen:
                        seen[key] = entry

                employee_set = set()
                for (emp, field), entry in seen.items():
                    if entry["user"] == user:
                        employee_set.add(emp)

                employee_list = [
                    emp for emp in employee_set
                    if emp != employee
                ]

            if not employee_list:
                employee_list = ["__none__"]

            filters.append(["employee", "in", employee_list])

        else:
            frappe.throw("Invalid view_type. Use 'self' or 'team'.")

        # -------------------------
        # Total count (without pagination)
        # -------------------------
        total_records = frappe.get_list(
            "Shift Request",
            filters=filters
        )

        # -------------------------
        # Main records with pagination
        # -------------------------
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
                "docstatus",
                "custom_remarks",
                "creation",
                "department",
                "company"
            ],
            order_by=order_by,
            limit_page_length=cint(limit_page_length) if limit_page_length else None,
            limit_start=cint(limit_start)
        )

        # -------------------------
        # Shift Request has no workflow
        # status field: Draft / Approved / Rejected
        #
        # enable = True  → status is "Draft"
        # enable = False → anything else (Approved, Rejected, etc.)
        # -------------------------
        for row in records:
            if row.get("custom_remarks"):
                row["custom_remarks"] = strip_html(
                    row["custom_remarks"]
                ).strip()

            status_val = row.get("status") or ""

            # enable = True only when status is "Draft"
            row["enable"] = (status_val == "Draft")

            row.pop("docstatus", None)

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


@frappe.whitelist()
def bulk_shift_request_action(names, action):
    """
    Bulk Approve/Reject Shift Requests

    Args:
        names: JSON list of Shift Request names
        action: "Approved" or "Rejected"
    """

    if isinstance(names, str):
        names = frappe.parse_json(names)

    if not names or not isinstance(names, list):
        return {
            "success": False,
            "message": "No records provided."
        }

    if action not in ("Approved", "Rejected"):
        return {
            "success": False,
            "message": "Invalid action. Use 'Approved' or 'Rejected'."
        }

    success = []

    for name in names:
        try:
            doc = frappe.get_doc("Shift Request", name)

            # Skip cancelled documents
            if doc.docstatus == 2:
                continue

            # Skip already processed documents
            if doc.status in ("Approved", "Rejected"):
                continue

            doc.status = action
            doc.flags.skip_approver_validation = True
            doc.save(ignore_permissions=True)

            # Submit if draft
            if doc.docstatus == 0:
                doc.submit()

            success.append(name)

        except Exception:
            frappe.clear_messages()
            frappe.local.response.pop("_server_messages", None)
            frappe.log_error(
                frappe.get_traceback(),
                f"Bulk Shift Request Action Error - {name}"
            )

    if success:
        return {
            "success": True,
            "message": f"{len(success)} document(s) {action.lower()} successfully."
        }

    return {
        "success": False,
        "message": f"No documents were {action.lower()} successfully."
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
        approver = data.get("approver")
        status = data.get("status")
        name = data.get("name")

        if not employee:
            return {
                "success": False,
                "message": "Employee is required",
                "data": None
            }

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
                    f"Attendance is locked for {month}. "
                    f"Shift Request cannot be created.",
                    title="Attendance Locked"
                )

        # -----------------------------
        # UPDATE FLOW
        # -----------------------------
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

        # -----------------------------
        # CREATE FLOW
        # -----------------------------
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

    except frappe.ValidationError as e:
        frappe.clear_messages()
        return {
            "success": False,
            "message": str(e),
            "data": None
        }
    except Exception as e:
        frappe.log_error(
            frappe.get_traceback(),
            "Shift Request API Error"
        )
        return {
            "success": False,
            "message": "Unable to process Shift Request. Please contact Administrator.",
            "data": None
        }



def get_required_shift_hours(dt, branch, is_female):

    if not dt:
        return None

    dt = getdate(dt)
    current_month = dt.month

    branch_doc = frappe.get_doc("Branch", branch)

    if not hasattr(branch_doc, "custom_branch_hours_setting"):
        return None

    for row in branch_doc.custom_branch_hours_setting:

        gender_match = False

        # =========================
        # Gender Match
        # =========================

        if row.gender == "All":
            gender_match = True

        elif row.gender == "Female" and is_female:
            gender_match = True

        elif row.gender == "Male" and not is_female:
            gender_match = True

        # =========================
        # Month Match
        # =========================

        if (
            gender_match
            and row.from_month <= current_month <= row.to_month
        ):
            return row.hours

    return None


@frappe.whitelist()
def determine_shift_types(
    doctype,
    txt,
    searchfield,
    start,
    page_len,
    filters
):

    try:

        branch = filters.get("branch")
        date_str = filters.get("as_on_date")
        employee_id = filters.get("emp_id")

        if not branch or not employee_id:
            return []

        # =========================
        # Date
        # =========================

        as_on_date = getdate(date_str) if date_str else None

        # =========================
        # Employee Details
        # =========================

        employee = frappe.db.get_value(
            "Employee",
            employee_id,
            [
                "custom_attendance_source",
                "gender",
                "user_id"
            ],
            as_dict=True
        )

        if not employee:
            return []

        emp_attendance_source = employee.custom_attendance_source
        employee_gender = employee.gender
        user_id = employee.user_id

        conditions = {}

        # =========================
        # Role Validation
        # =========================

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

        employee_roles = frappe.get_roles(user_id) if user_id else []

        allow_24_hours = bool(
            set(employee_roles).intersection(set(allowed_roles))
        )

        # =========================
        # Attendance Source Logic
        # =========================

        is_field = False

        if emp_attendance_source == "Biometric":

            conditions["custom_attendance_source"] = [
                "not in",
                ["Field", "Punch"]
            ]

        elif emp_attendance_source == "Punch":

            conditions["custom_attendance_source"] = [
                "!=",
                "Field"
            ]

        elif emp_attendance_source == "Field":

            is_field = True

            conditions["custom_attendance_source"] = [
                "!=",
                "Punch"
            ]

        # =========================
        # Gender Logic
        # =========================

        is_female = (
            employee_gender == "Female"
            and is_field
        )

        # =========================
        # Dynamic Hours Logic
        # =========================

        required_hours = get_required_shift_hours(
            as_on_date,
            branch,
            is_female
        )

        if required_hours:
            conditions["custom_hours"] = required_hours

        # =========================
        # Branch Filter
        # =========================

        conditions["custom_branch"] = branch

        # =========================
        # Excluded Shift Types
        # =========================

        branch_doc = frappe.get_doc("Branch", branch)

        excluded_shifts = []

        if hasattr(branch_doc, "custom_excluded_shift_types"):

            for row in branch_doc.custom_excluded_shift_types:

                if row.exclude and row.shift_type:
                    excluded_shifts.append(row.shift_type)

        if excluded_shifts:
            conditions["name"] = ["not in", excluded_shifts]

        # =========================
        # Hide 24 Hours Shift
        # =========================

        if not allow_24_hours:
            conditions["custom_shift_type"] = [
                "!=",
                "24 hours"
            ]

        # =========================
        # Fetch Shift Types
        # =========================

        shift_types = frappe.db.get_list(
            "Shift Type",
            filters=conditions,
            fields=["name"],
            order_by="name",
            start=start,
            page_length=page_len,
            ignore_permissions=True
        )

        return [[d.name, d.name] for d in shift_types] or []

    except Exception as e:

        frappe.log_error(
            title="determine_shift_types_error",
            message=frappe.get_traceback()
        )

        frappe.throw(str(e))

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
