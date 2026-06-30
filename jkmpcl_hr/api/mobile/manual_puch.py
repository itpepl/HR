import frappe
from frappe.utils import getdate, cint,cstr
from frappe import _
from frappe.utils import strip_html
from frappe.utils import get_datetime

from frappe.utils import cint
from jkmpcl_hr.py.utils import get_emp_reporting_manager, get_emp_hr_manager, get_ceo_user,get_emp_review_manager
from jkmpcl_hr.jkmpcl_hr.doctype.attendance_lock.attendance_lock import AttendanceLock
from frappe.utils import (
    add_days,
    date_diff,
    formatdate
)


# @frappe.whitelist()
# def get_manual_punches(
#     view_type="self",
#     filters=None,
#     order_by="creation desc",
#     limit_page_length=None,
#     limit_start=0,
# ):
#     try:
#         user = frappe.session.user

#         filters = frappe.parse_json(filters) if filters else []

#         if isinstance(filters, dict):
#             filters = [[k, "=", v] for k, v in filters.items()]

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

#         # Total Count (without pagination)
#         total_records = frappe.get_list(
#             "Attendance Request",
#             filters=filters
#         )

#         records = frappe.get_list(
#             "Attendance Request",
#             filters=filters,
#             fields=[
#                 "name",
#                 "employee",
#                 "employee_name",
#                 "from_date",
#                 "to_date",
#                 "explanation",
#                 "reason",
#                 "custom_punch_type",
#                 "custom_in_time",
#                 "custom_out_time",
#                 "workflow_state",
#                 "custom_note",
#                 "creation",
#                 "department",
#                 "company",
#                 "branch",
#                 "shift"
#             ],
#             order_by=order_by,
#             limit_page_length=cint(limit_page_length) if limit_page_length else None,
#             limit_start=cint(limit_start)
#         )

#         for row in records:
#             if row.get("custom_note"):
#                 row["custom_note"] = strip_html(row["custom_note"]).strip()

#         return {
#             "success": True,
#             "data": records,
#             "total_records": len(total_records),   # total matching records
#             "count": len(records),            # current page count
#             "message": "Manual Punch List Loaded Successfully!"
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Manual Punch List API Error")
#         return {
#             "success": False,
#             "message": str(e)
#         }

@frappe.whitelist()
def get_manual_punches(
    view_type="self",
    filters=None,
    order_by="creation desc",
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

            # Step 1: Get all employees where current user appears as approver
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

                # Step 2: Fetch ALL approver rows for candidate employees
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

                # Step 3: Per (employee + parentfield), keep only latest row
                seen = {}
                for entry in all_entries:
                    key = (entry["parent"], entry["parentfield"])
                    if key not in seen:
                        seen[key] = entry

                # Step 4: Include employee if current user is latest approver
                # for ANY parentfield, exclude current employee themselves
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
        # Total Count (without pagination)
        # -------------------------
        total_records = frappe.get_list(
            "Attendance Request",
            filters=filters
        )

        records = frappe.get_list(
            "Attendance Request",
            filters=filters,
            fields=[
                "name",
                "employee",
                "employee_name",
                "from_date",
                "to_date",
                "explanation",
                "reason",
                "custom_punch_type",
                "custom_in_time",
                "custom_out_time",
                "workflow_state",
                "docstatus",
                "custom_note",
                "creation",
                "department",
                "company",
                "branch",
                "shift"
            ],
            order_by=order_by,
            limit_page_length=cint(limit_page_length) if limit_page_length else None,
            limit_start=cint(limit_start)
        )

        # -------------------------
        # Detect current user's manager role in team view
        # -------------------------
        current_manager_role = None  # 'reporting', 'review', 'hr'

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

            if 'custom_hr_manager' in role_check:
                current_manager_role = 'hr'
            elif 'custom_review_manager' in role_check:
                current_manager_role = 'review'
            elif 'custom_reporting_manager' in role_check:
                current_manager_role = 'reporting'

        # -------------------------
        # Workflow states from screenshot
        #
        # Reporting Manager acts on  → Pending
        # Review Manager acts on     → Approved by Reporting Manager
        # HR acts on                 → Approved by Review Manager
        # CEO acts on                → Approved by HR
        #
        # Final states (no action possible)
        # -------------------------
        FINAL_STATES = {
            "Final Approved",
            "Rejected",
            "Rejected by Reporting Manager",
            "Rejected by Review Manager",
            "Rejected by HR",
        }

        # States that mean Reporting Manager has approved
        REPORTING_MGR_APPROVED_STATES = {
            "Approved by Reporting Manager",
            "Approved by Review Manager",
            "Approved by HR",
            "Final Approved",
        }

        # States that mean Review Manager has approved
        REVIEW_MGR_APPROVED_STATES = {
            "Approved by Review Manager",
            "Approved by HR",
            "Final Approved",
        }

        # -------------------------
        # Build response
        # -------------------------
        for row in records:
            if row.get("custom_note"):
                row["custom_note"] = strip_html(row["custom_note"]).strip()

            wf = row.get("workflow_state") or ""
            ds = row.get("docstatus", 0)

            if view_type == "self":
                # Self view: enable if not in a final state
                row["enable"] = wf not in FINAL_STATES

            elif view_type == "team" and current_manager_role:

                if current_manager_role == "reporting":
                    # Reporting manager acts on Pending only
                    row["enable"] = wf == "Pending"

                elif current_manager_role == "review":
                    # Enable only if reporting manager has approved
                    row["enable"] = wf in REPORTING_MGR_APPROVED_STATES

                elif current_manager_role == "hr":
                    # Enable only if review manager has approved
                    row["enable"] = wf in REVIEW_MGR_APPROVED_STATES

                else:
                    row["enable"] = False
            else:
                row["enable"] = False

            # Remove docstatus from response
            row.pop("docstatus", None)

        return {
            "success": True,
            "data": records,
            "total_records": len(total_records),
            "count": len(records),
            "message": "Manual Punch List Loaded Successfully!"
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Manual Punch List API Error")
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist(allow_guest=False)
def create_manual_punch(data):
    try:
        if isinstance(data, str):
            data = frappe.parse_json(data)

        employee = data.get("employee")
        date = data.get("date")
        request_type = data.get("request_type")
        punch_type = data.get("punch_type")
        in_time = data.get("in_time")
        out_time = data.get("out_time")
        remarks = data.get("remarks")

        if not (employee and date and request_type and remarks):
            return {
                "success": False,
                "message": "Employee, Date, Request Type and Remarks are required"
            }

        # ✅ define from_date & to_date BEFORE using
        from_date = date
        to_date = date

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
        # WARNING LOGIC
        # -----------------------------
        warning_message = ""

        # ❗ Skip warning for Field Visit
        if request_type != "Field Visit":
            warning_data = get_manual_punch_note(
                employeeId=employee,
                from_date=date,
                current_punch_type=punch_type
            )

            if warning_data.get("show_warning"):
                warning_message = warning_data.get("message")

        # -----------------------------
        # CREATE ATTENDANCE REQUEST
        # -----------------------------
        doc = frappe.get_doc({
            "doctype": "Attendance Request",
            "employee": employee,
            "from_date": date,
            "to_date": date,
            "reason": request_type,
            "custom_punch_type": punch_type,
            "custom_in_time": in_time,
            "custom_out_time": out_time,
            "explanation": remarks,
            "custom_note": warning_message or None
        })

        doc.insert(ignore_permissions=True)

        return {
            "success": True,
            "message": "Manual punch created successfully",
            "data": {
                "attendance_request_id": doc.name
            }
        }

    except frappe.DuplicateEntryError:
        return {
            "success": False,
            "message": "Attendance request already exists for this date."
        }

    except frappe.ValidationError as e:
        return {
            "success": False,
            "message": frappe.utils.strip_html(str(e))
        }

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Manual Punch API Error")
        return {
            "success": False,
            "message": "Unable to create manual punch. Please contact admin."
        }


@frappe.whitelist()
def request_type_list():
    return {
            "success": True,
            "message": "Request types fetched successfully",
            "data": ["Miss Punch","Field Visit"]
        }
@frappe.whitelist()
def request_type_list(employee=None):

    user = frappe.session.user

    settings = frappe.get_single("HR Settings")

    from_time = get_datetime(settings.custom_system_error_window_from) \
        if settings.custom_system_error_window_from else None

    to_time = get_datetime(settings.custom_system_error_window_to) \
        if settings.custom_system_error_window_to else None

    allowed_role = settings.custom_allowed_role

    now = get_datetime()

    show_system_error = False

    if from_time and to_time:
        if from_time <= now <= to_time:
            show_system_error = True

    user_roles = frappe.get_roles(user)

    if allowed_role and allowed_role in user_roles:
        show_system_error = True

    attendance_source = None

    if employee:
        attendance_source = frappe.db.get_value(
            "Employee",
            employee,
            "custom_attendance_source"
        )

    options = []

    if show_system_error:
        options.append("System Error")

    if attendance_source == "Biometric":
        options.extend(["Miss Punch", "Field Visit"])

    elif attendance_source in ("Field", "Punch"):
        options.append("Miss Punch")

    return {
        "success": True,
        "message": "Request types fetched successfully",
        "data": list(set(options))
    }

@frappe.whitelist()
def punch_type_list():
    return {
        "success": True,
        "message": "Punch types fetched successfully",
        "data": ["In", "Out", "Both"]
    }




# @frappe.whitelist()
# def get_manual_punch_note(employeeId, from_date,request_type=None, current_punch_type=None, current_name=None):
#     if not employeeId or not from_date:
#         return {
#             "show_warning": False,
#             "count": 0,
#             "limit": 0,
#             "message": ""
#         }
#     if request_type == "Field Visit":
#         return {
#             "show_warning": False,
#             "count": 0,
#             "limit": 0,
#             "message": ""
#         }

#     manual_punch_limit = cint(
#         frappe.db.get_single_value("HR Settings", "custom_manual_punch_count") or 0
#     )

#     ref_date = getdate(from_date)
#     month = ref_date.month
#     year = ref_date.year

#     def punch_count(pt):
#         if not pt:
#             return 0
#         pt = str(pt).lower().strip()
#         if pt == "both":
#             return 2
#         if pt in ("in", "out"):
#             return 1
#         return 0

#     filters = {
#         "employee": employeeId,
#         "reason": "Miss Punch",
#         "docstatus": ["<", 2]
#     }

#     if current_name:
#         filters["name"] = ["!=", current_name]

#     existing = frappe.get_all(
#         "Attendance Request",
#         filters=filters,
#         fields=["custom_punch_type", "from_date"]
#     )
#     print(f"\n\nExisting manual punches for employee {employeeId} {filters} in month {month}-{year}: {existing}\n\n")
#     total = 0
#     for row in existing:
#         d = getdate(row.from_date)
#         if d.month == month and d.year == year:
#             total += punch_count(row.custom_punch_type)
#             print(f"Existing Punch: {row.custom_punch_type} on {row.from_date} counts as {punch_count(row.custom_punch_type)} punches")

#     total += punch_count(current_punch_type)

#     show_warning = manual_punch_limit and total > manual_punch_limit

#     message = ""
#     if show_warning:
#         message = _(
#             "Manual Punch limit exceeded for {0}-{1}. Used {2} out of {3}."
#         ).format(year, str(month).zfill(2), total, manual_punch_limit)

#     return {
#         "show_warning": show_warning,
#         "count": total,
#         "limit": manual_punch_limit,
#         "message": message
#     }








#------------ UPDATED CODE (16-04-2026) to handle Field Visit request type and show warning only for Miss Punch type --------------

# @frappe.whitelist()
# def get_manual_punch_note(employeeId, from_date, request_type=None, current_punch_type=None, current_name=None):
#     if not employeeId or not from_date:
#         return {
#             "show_warning": False,
#             "count": 0,
#             "limit": 0,
#             "message": ""
#         }

#     if request_type != "Miss Punch":
#         return {
#             "show_warning": False,
#             "count": 0,
#             "limit": 0,
#             "message": ""
#         }

#     # 🔥 Current logged-in user
#     current_user = frappe.session.user
#     print(f"\n\nCurrent User: {current_user}\n\n")

#     # 🔥 Get approvers
#     reporting_manager = get_emp_reporting_manager(employeeId, from_date)
#     hr_manager = get_emp_hr_manager(employeeId, from_date)
#     ceo_user = get_ceo_user()

#     # 🔥 Check if current user is approver
#     is_approver = current_user in [reporting_manager, hr_manager, ceo_user]

#     manual_punch_limit = cint(
#         frappe.db.get_single_value("HR Settings", "custom_manual_punch_count") or 0
#     )

#     ref_date = getdate(from_date)
#     month = ref_date.month
#     year = ref_date.year

#     def punch_count(pt):
#         if not pt:
#             return 0
#         pt = str(pt).lower().strip()
#         if pt == "both":
#             return 2
#         if pt in ("in", "out"):
#             return 1
#         return 0

#     filters = {
#         "employee": employeeId,
#         "reason": "Miss Punch",
#         "docstatus": ["<", 2]
#     }

#     if current_name:
#         filters["name"] = ["!=", current_name]

#     existing = frappe.get_all(
#         "Attendance Request",
#         filters=filters,
#         fields=["custom_punch_type", "from_date"]
#     )

#     total = 0
#     for row in existing:
#         d = getdate(row.from_date)
#         if d.month == month and d.year == year:
#             total += punch_count(row.custom_punch_type)

#     # ✅ Include current selection
#     total += punch_count(current_punch_type)

#     show_warning = manual_punch_limit and total > manual_punch_limit

#     message = ""

#     if show_warning:
#         if is_approver:
#             # ✅ Approver Message
#             message = _("Waiver limit has been exhausted (Attempt No. {0})").format(total)
#         else:
#             # ✅ Employee Message
#             message = _("The waiver limit is over, so CEO approval is required. (Attempt No. {0})").format(total)

#     return {
#         "show_warning": show_warning,
#         "count": total,
#         "limit": manual_punch_limit,
#         "message": message
#     }


#------------ UPDATED CODE (08-06-2026) to handle that attempt no show only --------------

@frappe.whitelist()
def get_manual_punch_note(
    employeeId,
    from_date,
    request_type=None,
    current_punch_type=None,
    current_name=None
):

    if not employeeId or not from_date:
        return {
            "show_warning": False,
            "count": 0,
            "limit": 0,
            "message": ""
        }

    if request_type != "Miss Punch":
        return {
            "show_warning": False,
            "count": 0,
            "limit": 0,
            "message": ""
        }

    current_user = frappe.session.user

    reporting_manager = get_emp_reporting_manager(employeeId, from_date)
    review_manager = get_emp_review_manager(employeeId)
    hr_manager = get_emp_hr_manager(employeeId, from_date)
    ceo_user = get_ceo_user()

    is_approver = current_user in [
        reporting_manager,
        review_manager,
        hr_manager,
        ceo_user
    ]

    manual_punch_limit = cint(
        frappe.db.get_single_value(
            "HR Settings",
            "custom_manual_punch_count"
        ) or 0
    )

    ref_date = getdate(from_date)
    month = ref_date.month
    year = ref_date.year

    def punch_count(pt):
        if not pt:
            return 0

        pt = cstr(pt).strip().lower()

        if pt == "both":
            return 2

        if pt in ("in", "out"):
            return 1

        return 0

    filters = {
        "employee": employeeId,
        "reason": "Miss Punch",
        "docstatus": ["<", 2]
    }

    existing = frappe.get_all(
        "Attendance Request",
        filters=filters,
        fields=[
            "name",
            "custom_punch_type",
            "from_date",
            "creation"
        ],
        order_by="creation asc"
    )

    total = 0

    # Editing existing document
    if current_name:

        for row in existing:

            if row.name == current_name:
                break

            try:
                d = getdate(row.from_date)

                if d.month == month and d.year == year:
                    total += punch_count(row.custom_punch_type)

            except Exception:
                continue

    # New document
    else:

        for row in existing:

            try:
                d = getdate(row.from_date)

                if d.month == month and d.year == year:
                    total += punch_count(row.custom_punch_type)

            except Exception:
                continue

    # Add current request
    total += punch_count(current_punch_type)

    show_warning = (
        manual_punch_limit > 0
        and total > manual_punch_limit
    )

    message = ""

    if show_warning:
        if is_approver:
            message = _(
                "Waiver limit has been exhausted (Attempt No. {0})"
            ).format(total)

        else:
            message = _(
                "The waiver limit is over, so CEO approval is required. (Attempt No. {0})"
            ).format(total)

    return {
        "show_warning": show_warning,
        "count": total,
        "limit": manual_punch_limit,
        "message": message
    }