import frappe
from frappe.utils import getdate, strip_html
from frappe.utils import formatdate

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

        doc.insert(ignore_permissions=True)

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
    


@frappe.whitelist(allow_guest=False)
def get_off_day_work_list(
    employee,
    status=None,
    comp_off_created=None,
    from_date=None,
    to_date=None,
    limit=10,
    page=1,
):

    try:

        if not employee:
            return {
                "success": False,
                "message": "Employee is required"
            }
        filters = {
            "employee": employee,
            "docstatus": ["!=", 2],
        }

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
            ],
            order_by="date desc",
            limit_start=offset,
            limit_page_length=limit,
        )

        data = []

        for row in records:

            status_value = (
                row.workflow_state
                or ("Submitted" if row.docstatus == 1 else "Open")
            )

            data.append({
                "id": row.name,
                "date": formatdate(row.date),
                "raw_date": row.date,
                "status": status_value,
                "comp_off_created": bool(row.comp_off_created),
            })

        return {
            "success": True,
            "message": "Off Day Work Requests fetched successfully",
            "data": data,
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