import frappe
from frappe.utils import getdate, strip_html
from frappe.utils import formatdate
from frappe.utils import cint


@frappe.whitelist(allow_guest=False)
def create_off_day_work(data):
    try:
        if isinstance(data, str):
            data = frappe.parse_json(data)

        employee = data.get("employee")
        date = data.get("date")
        remarks = data.get("remarks")
        if not employee or not date:
            return {
                "success": False,
                "message": "Employee and Date are required"
            }

        date = getdate(date)
        exists = frappe.db.exists(
            "Off-Day Work Request",
            {
                "employee": employee,
                "date": date,
                "docstatus": ["!=", 2],
                "workflow_state": ["!=", "Rejected"],
            },
        )
        if exists:
            return {
                "success": False,
                "message": "Off Day Work Request already exists for this date"
            }
        doc = frappe.new_doc("Off-Day Work Request")
        doc.employee = employee
        doc.date = date
        doc.remarks = remarks
        # doc.workflow_state = "Approved"

        doc.insert(ignore_permissions=True)

        approver = frappe.db.get_list(
            "Approver",
            filters={
                "parent": employee,
                "effective_from": ["<=", frappe.utils.now_datetime()],
                "parentfield": "custom_reporting_manager",
            },
            fields=["user"],
            order_by="effective_from desc",
            ignore_permissions=True,
            limit=1,
        )
        approver_user = approver[0].user if approver else None

        if approver_user == frappe.session.user:
            # bypass workflow permission checks by writing the state directly
            frappe.db.set_value(
                "Off-Day Work Request",
                doc.name,
                "workflow_state",
                "Approved",
            )

        frappe.db.commit()
        return {
            "success": True,
            "message": "Off Day Work Request created successfully",
            "data": {
                "off_day_work_request_id": doc.name
            }
        }
    except frappe.DuplicateEntryError:
        return {
            "success": False,
            "message": "Off Day Work Request already exists for this date"
        }

    except frappe.ValidationError as e:
        return {
            "success": False,
            "message": strip_html(str(e))
        }
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Off Day Work Create API Error"
        )

        return {
            "success": False,
            "message": "Unable to create Off Day Work Request. Please contact administrator."
        }

@frappe.whitelist()
def off_day_status_list():
    return {
        "success": True,
        "message": "Off Day Work Statuses fetched successfully",
        "data": ["Pending", "Rejected", "Approved"]
    }
   


# @frappe.whitelist(allow_guest=False)
# def get_off_day_work_list(
#     employee,
#     status=None,
#     comp_off_created=None,
#     from_date=None,
#     to_date=None,
#     limit=10,
#     page=1,
# ):

#     try:

#         if not employee:
#             return {
#                 "success": False,
#                 "message": "Employee is required"
#             }
#         filters = {
#             "employee": employee,
#             "docstatus": ["!=", 2],
#         }

#         if status:
#             filters["workflow_state"] = status

#         if comp_off_created in ("0", "1", 0, 1, True, False):
#             filters["comp_off_created"] = int(comp_off_created)

#         if from_date and to_date:
#             filters["date"] = ["between", [from_date, to_date]]
#         elif from_date:
#             filters["date"] = [">=", from_date]
#         elif to_date:
#             filters["date"] = ["<=", to_date]
#         limit = int(limit)
#         page = int(page)

#         offset = (page - 1) * limit

#         total_records = frappe.db.count(
#             "Off-Day Work Request",
#             filters=filters,
#         )
#         records = frappe.get_all(
#             "Off-Day Work Request",
#             filters=filters,
#             fields=[
#                 "name",
#                 "date",
#                 "workflow_state",
#                 "docstatus",
#                 "comp_off_created",
#             ],
#             order_by="date desc",
#             limit_start=offset,
#             limit_page_length=limit,
#         )

#         data = []

#         for row in records:

#             status_value = (
#                 row.workflow_state
#                 or ("Submitted" if row.docstatus == 1 else "Open")
#             )

#             data.append({
#                 "id": row.name,
#                 "date": formatdate(row.date),
#                 "raw_date": row.date,
#                 "status": status_value,
#                 "comp_off_created": bool(row.comp_off_created),
#             })

#         return {
#             "success": True,
#             "message": "Off Day Work Requests fetched successfully",
#             "data": data,
#             "pagination": {
#                 "page": page,
#                 "limit": limit,
#                 "total_records": total_records,
#                 "total_pages": (
#                     (total_records + limit - 1) // limit
#                     if limit else 1
#                 ),
#             },
#         }

#     except Exception:
#         frappe.log_error(
#             frappe.get_traceback(),
#             "Off Day Work List API Error"
#         )

#         return {
#             "success": False,
#             "message": "Unable to fetch Off Day Work Requests"
#         }

@frappe.whitelist(allow_guest=False)
def get_off_day_work_list(
    view_type="self",
    employee=None,
    status=None,
    comp_off_created=None,
    from_date=None,
    to_date=None,
    limit=10,
    page=1,
):

    try:
        user = frappe.session.user

        # -------------------------
        # Current Employee
        # -------------------------
        current_employee = frappe.db.get_value(
            "Employee",
            {"user_id": user},
            "name"
        )

        if not current_employee:
            return {
                "success": False,
                "message": "Employee not linked with current user"
            }

        # -------------------------
        # TEAM LOGIC
        # -------------------------
        if view_type == "self":
            employee_list = [current_employee]

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
                    if emp != current_employee
                ]

        else:
            return {
                "success": False,
                "message": "Invalid view_type. Use 'self' or 'team'."
            }

        if not employee_list:
            employee_list = ["__none__"]

        # -------------------------
        # Base filters
        # -------------------------
        filters = {
            "employee": ["in", employee_list],
            "docstatus": ["!=", 2],
        }

        # -------------------------
        # Employee override
        # -------------------------
        if employee:
            if view_type == "self" and employee != current_employee:
                return {
                    "success": False,
                    "message": "You can only view your own data"
                }
            filters["employee"] = employee

        if status:
            filters["workflow_state"] = status

        if comp_off_created in ("0", "1", 0, 1, True, False):
            filters["comp_off_created"] = int(comp_off_created)

        if from_date and to_date:
            filters["date"] = ["between", [from_date, to_date]]
        elif from_date:
            filters["date"] = [">=", from_date]
        elif to_date:
            filters["date"] = ["<=", to_date]

        limit = int(limit)
        page = int(page)
        offset = (page - 1) * limit

        total_records = frappe.db.count(
            "Off-Day Work Request",
            filters=filters,
        )

        records = frappe.get_all(
            "Off-Day Work Request",
            filters=filters,
            fields=[
                "name",
                "date",
                "workflow_state",
                "docstatus",
                "comp_off_created",
                "employee",
                "employee_name",
            ],
            order_by="date desc",
            limit_start=offset,
            limit_page_length=limit,
        )

        # -------------------------
        # Workflow has only 3 states:
        # Pending → Approved / Rejected
        # enable = True only when Pending (still actionable)
        # enable = False when Approved or Rejected (final states)
        # This applies to ALL roles (reporting / review / hr) equally
        # -------------------------
        FINAL_STATES = {"Approved", "Rejected"}

        data = []

        for row in records:

            status_value = (
                row.workflow_state
                or ("Submitted" if row.docstatus == 1 else "Open")
            )

            data.append({
                "id": row.name,
                "employee": row.employee,
                "employee_name": row.employee_name,
                "date": formatdate(row.date),
                "raw_date": row.date,
                "status": status_value,
                "comp_off_created": bool(row.comp_off_created),
                "enable": row.workflow_state not in FINAL_STATES,
            })

        return {
            "success": True,
            "message": "Off Day Work Requests fetched successfully",
            "data": data,
            "view_type": view_type,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_records": total_records,
                "total_pages": (
                    (total_records + limit - 1) // limit
                    if limit else 1
                ),
            },
        }

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Off Day Work List API Error"
        )

        return {
            "success": False,
            "message": "Unable to fetch Off Day Work Requests"
        }


# @frappe.whitelist()
# def get_off_day_work_list(
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
#             "Off-Day Work Request",
#             filters=filters
#         )
#         records = frappe.get_list(
#             "Off-Day Work Request",
#             filters=filters,
#             fields=[
#                 "name",
#                 "date",
#                 "workflow_state",
#                 "docstatus",
#                 "comp_off_created",
#                 "department",
#                 "company",
#                 "branch",
#                 "shift",
#                 "employee_name"            ],
#             order_by=order_by,
#             limit_page_length=cint(limit_page_length) if limit_page_length else None,
#             limit_start=cint(limit_start)
#         )

#         # for row in records:
#         #     if row.get("custom_note"):
#         #         row["custom_note"] = strip_html(row["custom_note"]).strip()

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
def get_off_day_work_list(
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
            "Off-Day Work Request",
            filters=filters
        )

        records = frappe.get_list(
            "Off-Day Work Request",
            filters=filters,
            fields=[
                "name",
                "date",
                "workflow_state",
                "docstatus",
                "comp_off_created",
                "department",
                "company",
                "branch",
                "shift",
                "employee_name",
            ],
            order_by=order_by,
            limit_page_length=cint(limit_page_length) if limit_page_length else None,
            limit_start=cint(limit_start)
        )

        # -------------------------
        # Workflow has only 3 states:
        # Pending → Approved / Rejected
        # enable = True only when Pending (still actionable)
        # enable = False when Approved or Rejected (final states)
        # -------------------------
        FINAL_STATES = {"Approved", "Rejected"}

        for row in records:
            row["enable"] = row.get("workflow_state") not in FINAL_STATES

        return {
            "success": True,
            "data": records,
            "total_records": len(total_records),
            "count": len(records),
            "message": "Off Day Work List Loaded Successfully!"
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Off Day Work List API Error")
        return {
            "success": False,
            "message": str(e)
        }
        
@frappe.whitelist(allow_guest=False)
def get_off_day_work_detail(name):

    try:

        if not name:
            return {
                "success": False,
                "message": "Request ID is required"
            }

        doc = frappe.get_doc("Off-Day Work Request", name)

        data = {
            "id": doc.name,
            "date": formatdate(doc.date),
            "raw_date": doc.date,
            "status": doc.workflow_state,
            "employee": doc.employee,
            "employee_name": doc.employee_name,
            "department": doc.department,
            "company": doc.company,
            "branch": doc.branch,
            "shift": doc.shift,
            "remarks": doc.remarks,
            "comp_off_created": bool(doc.comp_off_created),
            "attendance": doc.attendance,
            "leave_allocation": doc.leave_allocation,
        }

        return {
            "success": True,
            "message": "Off Day Work Request details fetched",
            "data": data,
        }

    except frappe.DoesNotExistError:
        return {
            "success": False,
            "message": "Off Day Work Request not found"
        }

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Off Day Work Detail API Error"
        )

        return {
            "success": False,
            "message": "Unable to fetch Off Day Work Request details"
        }