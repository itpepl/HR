import frappe


@frappe.whitelist()
def get_manual_punches(
    employee,
    start_date=None,
    end_date=None,
    limit=None
):
    filters = {"employee": employee}

    # Date range filters
    if start_date:
        filters["to_date"] = [">=", start_date]

    if end_date:
        filters["from_date"] = ["<=", end_date]

    # Total record count
    total_records = frappe.db.count(
        "Attendance Request",
        filters=filters
    )

    # Prepare args for get_all
    get_all_args = {
        "doctype": "Attendance Request",
        "filters": filters,
        "fields": [
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
            "workflow_state"
        ],
        "order_by": "from_date desc"
    }

    # Apply limit only if passed
    if limit:
        get_all_args["limit_page_length"] = int(limit)

    records = frappe.get_all(**get_all_args)

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
                "message": "Missing required fields"
            }

        # Create document
        doc = frappe.get_doc({
            "doctype": "Attendance Request",
            "employee": employee,
            "from_date": date,
            "to_date": date,
            "reason": request_type,            
            "custom_punch_type": punch_type,  
            "custom_in_time": in_time,
            "custom_out_time": out_time,
            "explanation": remarks
        })

        doc.insert(ignore_permissions=True)
        doc.submit()  

        return {
            "success": True,
            "message": "Manual punch created successfully",
            "data": doc.name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Manual Punch API Error")
        return {
            "success": False,
            "message": str(e)
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
