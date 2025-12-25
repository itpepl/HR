import frappe
from frappe.utils import getdate, cint
from frappe import _
from frappe.utils import strip_html

@frappe.whitelist()
def get_manual_punches(
    employee,
    start_date=None,
    end_date=None,
    limit=None
):
    filters = {"employee": employee}

    if start_date:
        filters["to_date"] = [">=", start_date]

    if end_date:
        filters["from_date"] = ["<=", end_date]

    total_records = frappe.db.count(
        "Attendance Request",
        filters=filters
    )

    records = frappe.get_all(
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
            "custom_note",
            "creation"
        ],
        # order_by="from_date desc",
        order_by="creation desc",
        
        limit_page_length=int(limit) if limit else None
    )

    # 🔥 CLEAN HTML → TEXT
    for row in records:
        if row.get("custom_note"):
            row["custom_note"] = strip_html(row["custom_note"]).strip()

    return {
        "data": records,
        "total_records": total_records
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
            "data": ["Manual Punch","Field Visit"]
        }


@frappe.whitelist()
def punch_type_list():
    return {
        "success": True,
        "message": "Punch types fetched successfully",
        "data": ["In", "Out", "Both"]
    }




@frappe.whitelist()
def get_manual_punch_note(employeeId, from_date,request_type=None, current_punch_type=None, current_name=None):
    if not employeeId or not from_date:
        return {
            "show_warning": False,
            "count": 0,
            "limit": 0,
            "message": ""
        }
    if request_type == "Field Visit":
        return {
            "show_warning": False,
            "count": 0,
            "limit": 0,
            "message": ""
        }

    manual_punch_limit = cint(
        frappe.db.get_single_value("HR Settings", "custom_manual_punch_count") or 0
    )

    ref_date = getdate(from_date)
    month = ref_date.month
    year = ref_date.year

    def punch_count(pt):
        if not pt:
            return 0
        pt = str(pt).lower().strip()
        if pt == "both":
            return 2
        if pt in ("in", "out"):
            return 1
        return 0

    filters = {
        "employee": employeeId,
        "reason": "Manual Punch",
        "docstatus": ["<", 2]
    }

    if current_name:
        filters["name"] = ["!=", current_name]

    existing = frappe.get_all(
        "Attendance Request",
        filters=filters,
        fields=["custom_punch_type", "from_date"]
    )

    total = 0
    for row in existing:
        d = getdate(row.from_date)
        if d.month == month and d.year == year:
            total += punch_count(row.custom_punch_type)

    total += punch_count(current_punch_type)

    show_warning = manual_punch_limit and total > manual_punch_limit

    message = ""
    if show_warning:
        message = _(
            "Manual Punch limit exceeded for {0}-{1}. Used {2} out of {3}."
        ).format(year, str(month).zfill(2), total, manual_punch_limit)

    return {
        "show_warning": show_warning,
        "count": total,
        "limit": manual_punch_limit,
        "message": message
    }