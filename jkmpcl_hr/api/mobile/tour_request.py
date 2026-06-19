# import frappe
# from frappe import _
# from frappe.utils import today, getdate, date_diff,formatdate,cint

# @frappe.whitelist(allow_guest=False)
# def create_tour_request(from_date, to_date, purpose_of_travel):
#     try:
#         # Mandatory field validation
#         if not from_date:
#             frappe.throw(_("From Date is mandatory"))

#         if not to_date:
#             frappe.throw(_("To Date is mandatory"))

#         if not purpose_of_travel:
#             frappe.throw(_("Purpose of Travel is mandatory"))

#         from_date = getdate(from_date)
#         to_date = getdate(to_date)

#         # To Date cannot be earlier than From Date
#         if to_date < from_date:
#             frappe.throw(
#                 _("Invalid Date Range. To Date cannot be before From Date.")
#             )

#         # Travel duration must be exactly 1 day
#         days_diff = date_diff(to_date, from_date)

#         if days_diff != 1:
#             frappe.throw(
#                 _("Tour duration must be exactly 1 day. Please select a To Date that is one day after the From Date.")
#             )

#         employee = frappe.db.get_value(
#             "Employee",
#             {"user_id": frappe.session.user},
#             ["name", "employee_name"],
#             as_dict=True
#         )

#         if not employee:
#             frappe.throw(
#                 _("Employee record not found for the logged-in user.")
#             )

#         # Check overlapping Tour Request
#         existing_tour = frappe.db.sql("""
#             SELECT name
#             FROM `tabTour Request`
#             WHERE employee = %s
#                 AND docstatus != 2
#                 AND from_date <= %s
#                 AND to_date >= %s
#             LIMIT 1
#         """, (
#             employee.name,
#             to_date,
#             from_date
#         ), as_dict=True)

#         if existing_tour:
#             frappe.throw(
#                 _("Tour Request already exists for this date range: {0}").format(
#                     existing_tour[0].name
#                 )
#             )

#         doc = frappe.get_doc({
#             "doctype": "Tour Request",
#             "employee": employee.name,
#             "travel_request_date": today(),
#             "from_date": from_date,
#             "to_date": to_date,
#             "purpose_of_travel": purpose_of_travel
#         })

#         doc.insert(ignore_permissions=True)
#         frappe.db.commit()

#         return {
#             "status": "success",
#             "message": "Tour Request created successfully.",
#             "tour_request": doc.name
#         }

#     except frappe.ValidationError as e:
#         return {
#             "status": "error",
#             "message": str(e)
#         }

#     except Exception:
#         frappe.log_error(
#             frappe.get_traceback(),
#             "Create Tour Request API Error"
#         )

#         return {
#             "status": "error",
#             "message": "An unexpected error occurred while creating the Tour Request."
#         }
# # @frappe.whitelist()
# # def get_my_tour_requests(page=1, page_size=20):
# #     page = int(page)
# #     page_size = int(page_size)

# #     employee = frappe.db.get_value(
# #         "Employee",
# #         {"user_id": frappe.session.user},
# #         "name"
# #     )

# #     if not employee:
# #         frappe.throw("Employee record not found for logged in user")

# #     start = (page - 1) * page_size

# #     total_count = frappe.db.count(
# #         "Tour Request",
# #         {"employee": employee}
# #     )

# #     data = frappe.get_all(
# #         "Tour Request",
# #         filters={"employee": employee},
# #         fields=[
# #             "name",
# #             "employee",
# #             "employee_name",
# #             "travel_request_date",
# #             "from_date",
# #             "to_date",
# #             "purpose_of_travel",
# #             "workflow_state",
# #             "docstatus"
# #         ],
# #         order_by="creation desc",
# #         start=start,
# #         limit_page_length=page_size
# #     )

# #     for row in data:
# #         row["travel_request_date"] = (
# #             formatdate(row["travel_request_date"], "dd-MM-yyyy")
# #             if row.get("travel_request_date") else ""
# #         )

# #         row["from_date"] = (
# #             formatdate(row["from_date"], "dd-MM-yyyy")
# #             if row.get("from_date") else ""
# #         )

# #         row["to_date"] = (
# #             formatdate(row["to_date"], "dd-MM-yyyy")
# #             if row.get("to_date") else ""
# #         )

# #     return {
# #         "page": page,
# #         "page_size": page_size,
# #         "total_records": total_count,
# #         "total_pages": (total_count + page_size - 1) // page_size,
# #         "data": data
# #     }


# @frappe.whitelist()
# def get_my_tour_requests(
#     filters=None,
#     order_by="creation desc",
#     limit_page_length=None,
#     limit_start=0
# ):
#     try:
#         user = frappe.session.user

#         # Parse filters
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

#         # Always show only logged-in employee records
#         filters.append(["employee", "=", employee])

#         # Total count
#         total_records = frappe.db.count(
#             "Tour Request",
#             filters=filters
#         )

#         # Records with pagination
#         records = frappe.get_list(
#             "Tour Request",
#             filters=filters,
#             fields=[
#                 "name",
#                 "employee",
#                 "employee_name",
#                 "travel_request_date",
#                 "from_date",
#                 "to_date",
#                 "purpose_of_travel",
#                 "workflow_state",
#                 "docstatus",
#                 "creation"
#             ],
#             order_by=order_by,
#             limit_page_length=cint(limit_page_length) if limit_page_length else None,
#             limit_start=cint(limit_start)
#         )

#         # Format dates
#         for row in records:
#             row["travel_request_date"] = (
#                 formatdate(row["travel_request_date"], "dd-MM-yyyy")
#                 if row.get("travel_request_date") else ""
#             )

#             row["from_date"] = (
#                 formatdate(row["from_date"], "dd-MM-yyyy")
#                 if row.get("from_date") else ""
#             )

#             row["to_date"] = (
#                 formatdate(row["to_date"], "dd-MM-yyyy")
#                 if row.get("to_date") else ""
#             )

#         return {
#             "success": True,
#             "data": records,
#             "total_records": total_records,
#             "count": len(records),
#             "message": "Tour Request List Loaded Successfully!"
#         }

#     except Exception as e:
#         frappe.log_error(
#             frappe.get_traceback(),
#             "Tour Request API Error"
#         )
#         return {
#             "success": False,
#             "message": str(e)
#         }

# @frappe.whitelist(allow_guest=False)
# def update_tour_request(tour_request, from_date, to_date, purpose_of_travel):
#     try:
#         # Mandatory field validation
#         if not tour_request:
#             frappe.throw(_("Tour Request ID is mandatory"))

#         if not from_date:
#             frappe.throw(_("From Date is mandatory"))

#         if not to_date:
#             frappe.throw(_("To Date is mandatory"))

#         if not purpose_of_travel:
#             frappe.throw(_("Purpose of Travel is mandatory"))

#         from_date = getdate(from_date)
#         to_date = getdate(to_date)

#         # Date validation
#         if to_date < from_date:
#             frappe.throw(
#                 _("Invalid Date Range. To Date cannot be before From Date.")
#             )

#         # Tour duration validation
#         days_diff = date_diff(to_date, from_date)

#         if days_diff != 1:
#             frappe.throw(
#                 _("Tour duration must be exactly 1 day. Please select a To Date that is one day after the From Date.")
#             )

#         # Get logged-in employee
#         employee = frappe.db.get_value(
#             "Employee",
#             {"user_id": frappe.session.user},
#             ["name", "employee_name"],
#             as_dict=True
#         )

#         if not employee:
#             frappe.throw(
#                 _("Employee record not found for the logged-in user.")
#             )

#         # Check Tour Request exists
#         if not frappe.db.exists("Tour Request", tour_request):
#             frappe.throw(
#                 _("Tour Request not found.")
#             )

#         doc = frappe.get_doc("Tour Request", tour_request)

#         # Allow only owner employee to update
#         if doc.employee != employee.name:
#             frappe.throw(
#                 _("You are not authorized to update this Tour Request.")
#             )

#         # Allow update only in Draft state
#         if doc.docstatus != 0:
#             frappe.throw(
#                 _("Only Draft Tour Requests can be updated.")
#             )

#         # Update fields
#         doc.from_date = from_date
#         doc.to_date = to_date
#         doc.purpose_of_travel = purpose_of_travel

#         doc.save(ignore_permissions=True)
#         frappe.db.commit()

#         return {
#             "status": "success",
#             "message": "Tour Request updated successfully.",
#             "data": {
#                 "tour_request": doc.name,
#                 "employee": doc.employee,
#                 "employee_name": doc.employee_name,
#                 "workflow_state": doc.workflow_state,
#                 "travel_request_date": str(doc.travel_request_date),
#                 "from_date": str(doc.from_date),
#                 "to_date": str(doc.to_date),
#                 "purpose_of_travel": doc.purpose_of_travel,
#                 "docstatus": doc.docstatus
#             }
#         }

#     except frappe.ValidationError as e:
#         return {
#             "status": "error",
#             "message": str(e)
#         }

#     except Exception:
#         frappe.log_error(
#             frappe.get_traceback(),
#             "Update Tour Request API Error"
#         )

#         return {
#             "status": "error",
#             "message": "An unexpected error occurred while updating the Tour Request."
#         }


import frappe
from frappe import _
from frappe.utils import getdate, date_diff, today


@frappe.whitelist()
def create_tour_request(data):
    try:
        if isinstance(data, str):
            data = frappe.parse_json(data)

        name = data.get("name")
        from_date = data.get("from_date")
        to_date = data.get("to_date")
        purpose_of_travel = data.get("purpose_of_travel")

        # -----------------------------
        # Mandatory Validation
        # -----------------------------
        if not from_date:
            return {
                "success": False,
                "message": "From Date is required",
                "data": None
            }

        if not to_date:
            return {
                "success": False,
                "message": "To Date is required",
                "data": None
            }

        if not purpose_of_travel:
            return {
                "success": False,
                "message": "Purpose of Travel is required",
                "data": None
            }

        from_date = getdate(from_date)
        to_date = getdate(to_date)

        # -----------------------------
        # Date Validation
        # -----------------------------
        if to_date < from_date:
            frappe.throw(
                _("To Date cannot be before From Date.")
            )

        days_diff = date_diff(to_date, from_date)

        if days_diff != 1:
            frappe.throw(
                _("Tour duration must be exactly 1 day. Please select a To Date that is one day after the From Date.")
            )

        # -----------------------------
        # Employee Validation
        # -----------------------------
        employee = frappe.db.get_value(
            "Employee",
            {"user_id": frappe.session.user},
            ["name", "employee_name"],
            as_dict=True
        )

        if not employee:
            frappe.throw(
                _("Employee record not found for the logged-in user.")
            )

        # -----------------------------
        # UPDATE FLOW
        # -----------------------------
        if name:

            if not frappe.db.exists("Tour Request", name):
                return {
                    "success": False,
                    "message": "Tour Request not found",
                    "data": None
                }

            doc = frappe.get_doc("Tour Request", name)

            if doc.employee != employee.name:
                frappe.throw(
                    _("You are not authorized to update this Tour Request.")
                )

            if doc.docstatus != 0:
                frappe.throw(
                    _("Only Draft Tour Requests can be updated.")
                )

            # Check overlapping requests excluding current record
            existing_tour = frappe.db.sql("""
                SELECT name
                FROM `tabTour Request`
                WHERE employee = %s
                    AND name != %s
                    AND docstatus != 2
                    AND from_date <= %s
                    AND to_date >= %s
                LIMIT 1
            """, (
                employee.name,
                name,
                to_date,
                from_date
            ), as_dict=True)

            if existing_tour:
                frappe.throw(
                    _("Tour Request already exists for this date range: {0}")
                    .format(existing_tour[0].name)
                )

            doc.from_date = from_date
            doc.to_date = to_date
            doc.purpose_of_travel = purpose_of_travel

            doc.save(ignore_permissions=True)

            return {
                "success": True,
                "message": "Tour Request updated successfully",
                "data": {
                    "name": doc.name,
                    "employee": doc.employee,
                    "employee_name": doc.employee_name,
                    "status": doc.workflow_state,
                    "docstatus": doc.docstatus
                }
            }

        # -----------------------------
        # CREATE FLOW
        # -----------------------------
        else:

            # Check overlapping requests
            existing_tour = frappe.db.sql("""
                SELECT name
                FROM `tabTour Request`
                WHERE employee = %s
                    AND docstatus != 2
                    AND from_date <= %s
                    AND to_date >= %s
                LIMIT 1
            """, (
                employee.name,
                to_date,
                from_date
            ), as_dict=True)

            if existing_tour:
                frappe.throw(
                    _("Tour Request already exists for this date range: {0}")
                    .format(existing_tour[0].name)
                )

            doc = frappe.get_doc({
                "doctype": "Tour Request",
                "employee": employee.name,
                "travel_request_date": today(),
                "from_date": from_date,
                "to_date": to_date,
                "purpose_of_travel": purpose_of_travel
            })

            doc.insert(ignore_permissions=True)

            return {
                "success": True,
                "message": "Tour Request created successfully",
                "data": {
                    "name": doc.name,
                    "employee": doc.employee,
                    "employee_name": doc.employee_name,
                    "status": doc.workflow_state,
                    "docstatus": doc.docstatus
                }
            }

    except frappe.ValidationError as e:
        frappe.clear_messages()
        return {
            "success": False,
            "message": str(e),
            "data": None
        }

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Tour Request API Error"
        )

        return {
            "success": False,
            "message": "Unable to process Tour Request. Please contact Administrator.",
            "data": None
        }
  


import frappe


@frappe.whitelist()
def get_tour_requests(
    filters=None,
    limit_page_length=20,
    limit_start=0
):
    try:
        # Parse Filters
        filters = frappe.parse_json(filters) if filters else {}

        department = filters.get("Department")
        employee = filters.get("employee")
        from_date = filters.get("from_date")
        to_date = filters.get("to_date")
        status = filters.get("status")

        tour_filters = {}

        # Department Filter
        if department:
            employees = frappe.get_all(
                "Employee",
                filters={"department": department},
                pluck="name"
            )

            if not employees:
                return {
                    "success": True,
                    "message": "No employees found for this department",
                    "total_records": 0,
                    "page_size": int(limit_page_length),
                    "current_page": 1,
                    "total_pages": 0,
                    "returned_records": 0,
                    "data": []
                }

            tour_filters["employee"] = ["in", employees]

        # Employee Filter
        if employee:
            tour_filters["employee"] = employee

        # Status Filter (Workflow State)
        if status:
            tour_filters["workflow_state"] = status

        # Date Range Filter
        if from_date and to_date:
            tour_filters["from_date"] = ["<=", to_date]
            tour_filters["to_date"] = [">=", from_date]

        # Total Records
        total_records = frappe.db.count(
            "Tour Request",
            filters=tour_filters
        )

        # Get Records
        records = frappe.get_all(
            "Tour Request",
            filters=tour_filters,
            fields=[
                "name",
                "employee",
                "employee_name",
                "from_date",
                "to_date",
                "purpose_of_travel",
                "workflow_state",
                "creation"
            ],
            order_by="creation desc",
            limit_start=int(limit_start),
            limit_page_length=int(limit_page_length)
        )

        # Convert workflow_state to status
        for row in records:
            row["status"] = row.pop("workflow_state", "")

        page_size = int(limit_page_length)
        current_page = (int(limit_start) // page_size) + 1 if page_size else 1
        total_pages = (
            (total_records + page_size - 1) // page_size
            if page_size else 1
        )

        return {
            "success": True,
            "message": "Tour Requests fetched successfully",
            "total_records": total_records,
            "page_size": page_size,
            "current_page": current_page,
            "total_pages": total_pages,
            "returned_records": len(records),
            "data": records
        }

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Get Tour Requests API"
        )

        return {
            "success": False,
            "message": str(frappe.get_traceback()),
            "data": []
        }
    

@frappe.whitelist(allow_guest=False)
def get_workflow_states(workflow_name):
    """
    Get all workflow states from Workflow child table
    """

    if not workflow_name:
        return {
            "success": False,
            "message": "Workflow name is required"
        }

    if not frappe.db.exists("Workflow", workflow_name):
        return {
            "success": False,
            "message": f"Workflow '{workflow_name}' not found"
        }

    workflow = frappe.get_doc("Workflow", workflow_name)

    states = []

    for row in workflow.states:
        states.append({
            "state": row.state,
            
        })

    return {
        "success": True,
        "workflow_name": workflow.name,
        "total_states": len(states),
        "states": states
    }