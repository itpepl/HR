import frappe
from frappe import _
from frappe.utils import today, getdate, date_diff,formatdate

@frappe.whitelist(allow_guest=False)
def create_tour_request(from_date, to_date, purpose_of_travel):
    try:
        # Mandatory field validation
        if not from_date:
            frappe.throw(_("From Date is mandatory"))

        if not to_date:
            frappe.throw(_("To Date is mandatory"))

        if not purpose_of_travel:
            frappe.throw(_("Purpose of Travel is mandatory"))

        from_date = getdate(from_date)
        to_date = getdate(to_date)

        # To Date cannot be earlier than From Date
        if to_date < from_date:
            frappe.throw(
                _("Invalid Date Range. To Date cannot be before From Date.")
            )

        # Travel duration must be exactly 1 day
        days_diff = date_diff(to_date, from_date)

        if days_diff != 1:
            frappe.throw(
                _("Tour duration must be exactly 1 day. Please select a To Date that is one day after the From Date.")
            )

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

        # Check overlapping Tour Request
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
                _("Tour Request already exists for this date range: {0}").format(
                    existing_tour[0].name
                )
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
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Tour Request created successfully.",
            "tour_request": doc.name
        }

    except frappe.ValidationError as e:
        return {
            "status": "error",
            "message": str(e)
        }

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Create Tour Request API Error"
        )

        return {
            "status": "error",
            "message": "An unexpected error occurred while creating the Tour Request."
        }
@frappe.whitelist()
def get_my_tour_requests(page=1, page_size=20):
    page = int(page)
    page_size = int(page_size)

    employee = frappe.db.get_value(
        "Employee",
        {"user_id": frappe.session.user},
        "name"
    )

    if not employee:
        frappe.throw("Employee record not found for logged in user")

    start = (page - 1) * page_size

    total_count = frappe.db.count(
        "Tour Request",
        {"employee": employee}
    )

    data = frappe.get_all(
        "Tour Request",
        filters={"employee": employee},
        fields=[
            "name",
            "employee",
            "employee_name",
            "travel_request_date",
            "from_date",
            "to_date",
            "purpose_of_travel",
            "workflow_state",
            "docstatus"
        ],
        order_by="creation desc",
        start=start,
        limit_page_length=page_size
    )

    for row in data:
        row["travel_request_date"] = (
            formatdate(row["travel_request_date"], "dd-MM-yyyy")
            if row.get("travel_request_date") else ""
        )

        row["from_date"] = (
            formatdate(row["from_date"], "dd-MM-yyyy")
            if row.get("from_date") else ""
        )

        row["to_date"] = (
            formatdate(row["to_date"], "dd-MM-yyyy")
            if row.get("to_date") else ""
        )

    return {
        "page": page,
        "page_size": page_size,
        "total_records": total_count,
        "total_pages": (total_count + page_size - 1) // page_size,
        "data": data
    }


@frappe.whitelist(allow_guest=False)
def update_tour_request(tour_request, from_date, to_date, purpose_of_travel):
    try:
        # Mandatory field validation
        if not tour_request:
            frappe.throw(_("Tour Request ID is mandatory"))

        if not from_date:
            frappe.throw(_("From Date is mandatory"))

        if not to_date:
            frappe.throw(_("To Date is mandatory"))

        if not purpose_of_travel:
            frappe.throw(_("Purpose of Travel is mandatory"))

        from_date = getdate(from_date)
        to_date = getdate(to_date)

        # Date validation
        if to_date < from_date:
            frappe.throw(
                _("Invalid Date Range. To Date cannot be before From Date.")
            )

        # Tour duration validation
        days_diff = date_diff(to_date, from_date)

        if days_diff != 1:
            frappe.throw(
                _("Tour duration must be exactly 1 day. Please select a To Date that is one day after the From Date.")
            )

        # Get logged-in employee
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

        # Check Tour Request exists
        if not frappe.db.exists("Tour Request", tour_request):
            frappe.throw(
                _("Tour Request not found.")
            )

        doc = frappe.get_doc("Tour Request", tour_request)

        # Allow only owner employee to update
        if doc.employee != employee.name:
            frappe.throw(
                _("You are not authorized to update this Tour Request.")
            )

        # Allow update only in Draft state
        if doc.docstatus != 0:
            frappe.throw(
                _("Only Draft Tour Requests can be updated.")
            )

        # Update fields
        doc.from_date = from_date
        doc.to_date = to_date
        doc.purpose_of_travel = purpose_of_travel

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Tour Request updated successfully.",
            "data": {
                "tour_request": doc.name,
                "employee": doc.employee,
                "employee_name": doc.employee_name,
                "workflow_state": doc.workflow_state,
                "travel_request_date": str(doc.travel_request_date),
                "from_date": str(doc.from_date),
                "to_date": str(doc.to_date),
                "purpose_of_travel": doc.purpose_of_travel,
                "docstatus": doc.docstatus
            }
        }

    except frappe.ValidationError as e:
        return {
            "status": "error",
            "message": str(e)
        }

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Update Tour Request API Error"
        )

        return {
            "status": "error",
            "message": "An unexpected error occurred while updating the Tour Request."
        }